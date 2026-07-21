"""发票管理 API：发票 CRUD、关联报销单、附件归档、凭证草稿。"""
import os
import re
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import invoice as m
from app.models import reimburse as rm
from app.schemas import invoice as s
from app.utils.codegen import gen_invoice_code

router = APIRouter(prefix="/invoices", tags=["invoices"])

# 归档目录：开发默认放在项目根目录 uploads/invoices，生产可通过环境变量覆盖
ARCHIVE_DIR = Path(os.getenv("INVOICE_ARCHIVE_DIR", "./uploads/invoices"))


def _get_or_404(db: Session, pk: int) -> m.Invoice:
    obj = db.get(m.Invoice, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="发票不存在")
    return obj


def _build_invoice(payload: s.InvoiceCreate) -> m.Invoice:
    """用 schema 创建 Invoice ORM 对象（含明细行）。"""
    data = payload.model_dump(exclude={"details"})
    obj = m.Invoice(**data)
    for d in payload.details:
        obj.details.append(m.InvoiceDetail(**d.model_dump()))
    return obj


def _find_duplicate(db: Session, no: str, code: Optional[str]) -> Optional[m.Invoice]:
    """按 发票代码+号码 判定是否为重复发票（数电票 code 为空时仅按号码，且排除带代码的纸票以免误判）。"""
    no_norm = (no or "").strip()
    code_norm = (code or "").strip()
    stmt = select(m.Invoice).where(m.Invoice.no == no_norm)
    if code_norm:
        stmt = stmt.where(m.Invoice.code == code_norm)
    else:
        stmt = stmt.where(m.Invoice.code.is_(None))
    return db.scalar(stmt)


def _replace_details(obj: m.Invoice, details: List[s.InvoiceDetailCreate]) -> None:
    """更新时整单替换明细行。"""
    obj.details.clear()
    for d in details:
        obj.details.append(m.InvoiceDetail(**d.model_dump()))


def _archive_filename(invoice: m.Invoice) -> str:
    """按规则生成归档文件名：日期_类型_路线_旅客_金额_票号后4位.pdf。"""
    date_part = invoice.invoice_date.strftime("%Y%m%d") if invoice.invoice_date else ""
    type_part = (invoice.invoice_type or "发票").replace(" ", "")
    route_part = (invoice.route_info or "").replace(" ", "")
    traveler_part = (invoice.traveler or "").replace(" ", "")
    total_amount = sum((d.total or Decimal(0)) for d in invoice.details)
    amount_part = f"{total_amount:.2f}"
    no_part = (invoice.no or "")[-4:] if invoice.no else ""
    parts = [p for p in [date_part, type_part, route_part, traveler_part, amount_part, no_part] if p]
    base = "_".join(parts)
    base = re.sub(r"[^\w\-_.\u4e00-\u9fff]", "_", base) or "invoice"
    return f"{base}.pdf"


def _safe_filename(name: str) -> str:
    return re.sub(r"[^\w\-_.\u4e00-\u9fff]", "_", name)


# ================= CRUD =================
@router.get("", response_model=list[s.InvoiceRead])
def list_invoices(
    keyword: Optional[str] = None,
    reimbursement_bill_id: Optional[int] = None,
    unlinked: Optional[bool] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    stmt = select(m.Invoice).options(selectinload(m.Invoice.details))
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(
            (m.Invoice.no.like(like))
            | (m.Invoice.seller_name.like(like))
            | (m.Invoice.buyer_name.like(like))
            | (m.Invoice.account.like(like))
        )
    if reimbursement_bill_id is not None:
        stmt = stmt.where(m.Invoice.reimbursement_bill_id == reimbursement_bill_id)
    if unlinked is True:
        stmt = stmt.where(m.Invoice.reimbursement_bill_id.is_(None))
    if start_date:
        stmt = stmt.where(m.Invoice.invoice_date >= start_date)
    if end_date:
        stmt = stmt.where(m.Invoice.invoice_date <= end_date)
    stmt = stmt.order_by(m.Invoice.created_at.desc())
    return db.scalars(stmt).all()


@router.post("", response_model=s.InvoiceRead, status_code=201)
def create_invoice(payload: s.InvoiceCreate, db: Session = Depends(get_db)):
    # 唯一性校验：同一发票号码不允许重复录入（防重复报销）
    dup = _find_duplicate(db, payload.no, payload.code)
    if dup:
        dup_info = f"号码 {payload.no}" + (f"（代码 {payload.code}）" if payload.code else "")
        raise HTTPException(
            status_code=409,
            detail=f"发票已存在（{dup_info}），请勿重复录入。",
        )
    # 生成 16 位可读发票编码（并发安全，见 app/utils/codegen.py）
    obj = _build_invoice(payload)
    obj.invoice_code = gen_invoice_code(db, payload.invoice_type, payload.invoice_date)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{iid}", response_model=s.InvoiceRead)
def get_invoice(iid: int, db: Session = Depends(get_db)):
    stmt = select(m.Invoice).where(m.Invoice.id == iid).options(selectinload(m.Invoice.details))
    obj = db.scalar(stmt)
    if not obj:
        raise HTTPException(status_code=404, detail="发票不存在")
    return obj


@router.put("/{iid}", response_model=s.InvoiceRead)
def update_invoice(iid: int, payload: s.InvoiceUpdate, db: Session = Depends(get_db)):
    obj = _get_or_404(db, iid)
    data = payload.model_dump(exclude={"details"}, exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    if payload.details is not None:
        _replace_details(obj, payload.details)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{iid}")
def delete_invoice(iid: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, iid)
    db.delete(obj)
    db.commit()
    return {"ok": True}


# ================= P1: 关联报销单 =================
@router.post("/{iid}/link/{bid}", response_model=s.InvoiceRead)
def link_invoice(iid: int, bid: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, iid)
    bill = db.get(rm.ReimbursementBill, bid)
    if not bill:
        raise HTTPException(status_code=404, detail="报销单不存在")
    obj.reimbursement_bill_id = bid
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/{iid}/unlink", response_model=s.InvoiceRead)
def unlink_invoice(iid: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, iid)
    obj.reimbursement_bill_id = None
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/batch-link")
def batch_link_invoices(invoice_ids: List[int], bill_id: int, db: Session = Depends(get_db)):
    bill = db.get(rm.ReimbursementBill, bill_id)
    if not bill:
        raise HTTPException(status_code=404, detail="报销单不存在")
    updated = 0
    for iid in invoice_ids:
        obj = db.get(m.Invoice, iid)
        if obj:
            obj.reimbursement_bill_id = bill_id
            updated += 1
    db.commit()
    return {"ok": True, "updated": updated}


# 报销单金额/税额按关联发票自动汇总（在报销单读取时计算）
@router.get("/by-bill/{bid}/summary")
def invoice_summary_by_bill(bid: int, db: Session = Depends(get_db)):
    stmt = select(
        func.coalesce(func.sum(m.InvoiceDetail.amount), Decimal(0)).label("amount"),
        func.coalesce(func.sum(m.InvoiceDetail.tax), Decimal(0)).label("tax"),
        func.coalesce(func.sum(m.InvoiceDetail.total), Decimal(0)).label("total"),
        func.count(m.Invoice.id).label("invoice_count"),
    ).select_from(m.Invoice).join(m.Invoice.details).where(m.Invoice.reimbursement_bill_id == bid)
    row = db.execute(stmt).one()
    return {
        "amount": row.amount,
        "tax": row.tax,
        "total": row.total,
        "invoice_count": row.invoice_count,
    }


# ================= P2: 附件归档 =================
@router.post("/{iid}/attachment", response_model=s.InvoiceRead)
async def upload_attachment(iid: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    obj = _get_or_404(db, iid)
    suffix = (file.filename or "").lower().split(".")[-1]
    if suffix not in ("pdf", "ofd"):
        raise HTTPException(status_code=400, detail="只接受 PDF 或 OFD 发票文件")

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    # 统一转 pdf 后缀归档；OFD 优先保留原始格式，但老板规则要求最终只要 PDF，这里保存为 PDF
    # 若原始是 OFD，先按 .ofd 保存一份，再约定后续转换为 PDF（当前环境可能缺少 OFD->PDF 工具，先保存 ofd）
    if suffix == "ofd":
        filename = _archive_filename(obj).replace(".pdf", ".ofd")
    else:
        filename = _archive_filename(obj)

    path = ARCHIVE_DIR / filename
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)

    obj.attachment_path = str(path)
    db.commit()
    db.refresh(obj)
    return obj


# ================= P2: 凭证草稿 =================
@router.post("/voucher-draft")
def generate_voucher_draft(invoice_ids: List[int], db: Session = Depends(get_db)):
    """根据发票生成会计凭证分录草稿（借：入账科目 / 应交税费-应交增值税-进项税额，贷：应付账款-待认证/银行存款）。"""
    stmt = select(m.Invoice).where(m.Invoice.id.in_(invoice_ids)).options(selectinload(m.Invoice.details))
    invoices = db.scalars(stmt).all()
    if not invoices:
        raise HTTPException(status_code=400, detail="未选择有效发票")

    entries = []
    for inv in invoices:
        for d in inv.details:
            # 入账科目：优先发票头上的结算科目，其次按业务类型映射
            debit_account = inv.account or _default_account(inv.invoice_type, d.biz_type)
            # 进项税科目
            tax_account = "应交税费-应交增值税-进项税额"
            # 贷方科目：已认证则应付账款/银行存款；未认证则应付账款-待认证进项税额
            credit_account = "银行存款" if inv.certify == "current" else "应付账款-待认证进项税额"

            if d.amount and d.amount > 0:
                entries.append({
                    "account": debit_account,
                    "summary": f"{inv.seller_name} {d.item or ''}",
                    "debit": float(d.amount),
                    "credit": 0,
                })
            if d.tax and d.tax > 0:
                entries.append({
                    "account": tax_account,
                    "summary": f"{inv.seller_name} 进项税",
                    "debit": float(d.tax),
                    "credit": 0,
                })
            if d.total and d.total > 0:
                entries.append({
                    "account": credit_account,
                    "summary": f"{inv.seller_name} 应付",
                    "debit": 0,
                    "credit": float(d.total),
                })

    # 按科目合并（简单合并，保持借贷平衡）
    merged: dict = {}
    for e in entries:
        key = e["account"]
        if key not in merged:
            merged[key] = {"account": key, "summary": e["summary"], "debit": 0, "credit": 0}
        merged[key]["debit"] += e["debit"]
        merged[key]["credit"] += e["credit"]

    result = []
    for v in merged.values():
        v["debit"] = round(v["debit"], 2)
        v["credit"] = round(v["credit"], 2)
        result.append(v)

    return {"entries": result, "invoice_count": len(invoices)}


def _default_account(invoice_type: Optional[str], biz_type: Optional[str]) -> str:
    if invoice_type and ("火车" in invoice_type or "铁路" in invoice_type or "机票" in invoice_type or "航空" in invoice_type):
        return "管理费用-差旅费"
    if biz_type == "采购商品":
        return "库存商品"
    if biz_type == "采购固定资产":
        return "固定资产"
    if biz_type == "费用报销":
        return "管理费用"
    return "管理费用"
