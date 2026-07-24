"""发票箱 API：上传（浏览器已解析，随文件带 extracted_json）/列表/详情/校正/挂接业务单/查验。

约定：
- 浏览器端 invoiceParser.parseInvoiceFile 已完成 OCR/PDF 解析，上传时把 ParsedInvoice 序列化
  为 extracted_json 一并传来；后端只存盘 + 落库，不跑 OCR（零后端 OCR 依赖）。
- 挂接（link）：用 extracted_json 生成正式 invoices 表的 Invoice 记录（带报销单/采购申请外键），
  发票箱记录置 linked；正式凭证由业务单（报销/采购）既有审批→凭证流程驱动（业务驱动账务灵魂）。
"""
import json
import os
import re
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import invoice as inv_m
from app.models import invoice_inbox as m
from app.models import purchase as pm
from app.models import reimburse as rm
from app.schemas import invoice_inbox as s
from app.utils.codegen import gen_invoice_code

router = APIRouter(prefix="/invoice-inbox", tags=["invoice-inbox"])

# 发票箱原文件存档目录（与 invoices 归档 uploads/invoices 分开，确认挂接后正式发票指向同一文件）
INBOX_DIR = Path(os.getenv("INVOICE_INBOX_DIR", "./uploads/inbox"))


def _get_or_404(db: Session, pk: int) -> m.InvoiceInbox:
    obj = db.get(m.InvoiceInbox, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="发票箱记录不存在")
    return obj


def _safe_filename(name: str) -> str:
    return re.sub(r"[^\w\-_.\u4e00-\u9fff]", "_", name or "unknown")


def _parse_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            continue
    return None


def _ensure_dir() -> None:
    INBOX_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload", response_model=s.InvoiceInboxRead, status_code=201)
async def upload(
    file: UploadFile = File(...),
    extracted_json: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    content = await file.read()
    # 先建记录拿 id，再按 id 命名文件（避免重名覆盖）
    rec = m.InvoiceInbox(
        filename=file.filename or "unknown",
        storage_path="",
        source="upload",
        extracted_json=extracted_json,
        status="recognized" if extracted_json else "pending",
        recognized_at=datetime.now() if extracted_json else None,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    _ensure_dir()
    fname = f"{rec.id}_{_safe_filename(file.filename or 'unknown')}"
    low = fname.lower()
    if not low.endswith((".pdf", ".ofd", ".png", ".jpg", ".jpeg")):
        fname += ".pdf"
    path = INBOX_DIR / fname
    with open(path, "wb") as f:
        f.write(content)
    rec.storage_path = str(path)
    db.commit()
    db.refresh(rec)
    return rec


@router.get("", response_model=List[s.InvoiceInboxRead])
def list_inbox(
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
):
    stmt = select(m.InvoiceInbox)
    if status:
        stmt = stmt.where(m.InvoiceInbox.status == status)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(
            (m.InvoiceInbox.filename.like(like))
            | (m.InvoiceInbox.extracted_json.like(like))
        )
    stmt = stmt.order_by(m.InvoiceInbox.created_at.desc())
    return db.scalars(stmt).all()


@router.get("/{iid}", response_model=s.InvoiceInboxRead)
def get_inbox(iid: int, db: Session = Depends(get_db)):
    return _get_or_404(db, iid)


@router.put("/{iid}", response_model=s.InvoiceInboxRead)
def update_inbox(iid: int, payload: s.InvoiceInboxUpdate, db: Session = Depends(get_db)):
    obj = _get_or_404(db, iid)
    # 校验合法 JSON
    try:
        json.loads(payload.extracted_json)
    except Exception:
        raise HTTPException(status_code=400, detail="extracted_json 不是合法 JSON")
    obj.extracted_json = payload.extracted_json
    obj.status = "recognized"
    obj.recognized_at = datetime.now()
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/{iid}/link", response_model=s.InvoiceInboxRead)
def link_inbox(iid: int, payload: s.InvoiceInboxLink, db: Session = Depends(get_db)):
    """把发票箱记录挂接到业务单：生成正式 invoices 表记录，发票箱置 linked。"""
    obj = _get_or_404(db, iid)
    if not obj.extracted_json:
        raise HTTPException(status_code=400, detail="该记录尚未识别，无法挂接")
    data = json.loads(obj.extracted_json)

    inv = inv_m.Invoice(
        invoice_type=data.get("type") or "增值税专用发票",
        code=data.get("code"),
        no=data.get("no") or "",
        invoice_date=_parse_date(data.get("date")),
        buyer_name=data.get("buyerName"),
        buyer_tax_no=data.get("buyerTaxNo"),
        seller_name=data.get("sellerName") or "未知销售方",
        seller_tax_no=data.get("sellerTaxNo"),
        certify="none",
        remark="来自发票箱自动生成",
        attachment_path=obj.storage_path,  # 直接指向发票箱原文件（同一文件，不重复存）
    )

    if payload.doc_type == "reimburse":
        bill = db.get(rm.ReimbursementBill, payload.doc_id)
        if not bill:
            raise HTTPException(status_code=404, detail="报销单不存在")
        inv.reimbursement_bill_id = payload.doc_id
    elif payload.doc_type == "purchase":
        pr = db.get(pm.PurchaseRequisition, payload.doc_id)
        if not pr:
            raise HTTPException(status_code=404, detail="采购申请不存在")
        inv.purchase_requisition_id = payload.doc_id
    else:
        raise HTTPException(status_code=400, detail="doc_type 仅支持 reimburse / purchase")

    # 明细行（来自 ParsedInvoice.items）
    for it in (data.get("items") or []):
        amt = it.get("amount") or 0
        tax = it.get("tax") or 0
        inv.details.append(
            inv_m.InvoiceDetail(
                biz_type=it.get("name"),
                item=it.get("name"),
                qty=it.get("qty") or 1,
                amount=amt,
                tax_rate=it.get("taxRate") or 0,
                tax=tax,
                total=amt + tax,
            )
        )

    inv.invoice_code = gen_invoice_code(db, inv.invoice_type, inv.invoice_date)
    db.add(inv)
    db.commit()
    db.refresh(inv)

    obj.linked_doc_type = payload.doc_type
    obj.linked_doc_id = inv.id
    obj.status = "linked"
    obj.linked_at = datetime.now()
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/{iid}/verify", response_model=s.InvoiceInboxRead)
def verify_inbox(iid: int, payload: s.InvoiceInboxVerify, db: Session = Depends(get_db)):
    """P1 查验结果登记（前端跳税务局查验平台人工核对后回填）。"""
    obj = _get_or_404(db, iid)
    if payload.result not in ("real", "fake", "abnormal"):
        raise HTTPException(status_code=400, detail="result 仅支持 real / fake / abnormal")
    obj.verify_result = payload.result
    obj.verify_note = payload.note
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{iid}")
def delete_inbox(iid: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, iid)
    try:
        if obj.storage_path and os.path.exists(obj.storage_path):
            os.remove(obj.storage_path)
    except Exception:
        pass
    db.delete(obj)
    db.commit()
    return {"ok": True}
