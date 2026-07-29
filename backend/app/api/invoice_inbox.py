"""发票箱 API：上传（浏览器已解析，随文件带 extracted_json）/列表/详情/校正/挂接业务单/查验。

约定：
- 浏览器端 invoiceParser.parseInvoiceFile 已完成 OCR/PDF 解析，上传时把 ParsedInvoice 序列化
  为 extracted_json 一并传来；后端只存盘 + 落库，不跑 OCR（零后端 OCR 依赖）。
- 挂接（link）：用 extracted_json 生成正式 invoices 表的 Invoice 记录（带报销单/采购申请外键），
  发票箱记录置 linked；正式凭证由业务单（报销/采购）既有审批→凭证流程驱动（业务驱动账务灵魂）。
"""
import base64
import io
import json
import os
import re
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import invoice as inv_m
from app.models import invoice_inbox as m
from app.models import purchase as pm
from app.models import reimburse as rm
from app.schemas import invoice_inbox as s
from app.utils.codegen import gen_invoice_code
from pypdf import PdfReader

router = APIRouter(prefix="/invoice-inbox", tags=["invoice-inbox"])

# 发票箱原文件存档目录（与 invoices 归档 uploads/invoices 分开，确认挂接后正式发票指向同一文件）
INBOX_DIR = Path(os.getenv("INVOICE_INBOX_DIR", "./uploads/inbox"))


def _get_or_404(db: Session, pk: int) -> m.InvoiceInbox:
    obj = db.get(m.InvoiceInbox, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="发票箱记录不存在")
    return obj


def _dup_of(db: Session, seller_tax_no: Optional[str], no: Optional[str]) -> Optional["m.InvoiceInbox"]:
    """P1 去重：按发票号码（可选叠加税号）查箱中是否已存在同票。"""
    if not no:
        return None
    for r in db.scalars(select(m.InvoiceInbox)).all():
        if not r.extracted_json:
            continue
        try:
            d = json.loads(r.extracted_json)
        except Exception:
            continue
        if d.get("no") != no:
            continue
        if seller_tax_no and d.get("sellerTaxNo") and d.get("sellerTaxNo") != seller_tax_no:
            continue
        return r
    return None


# 入库拦截：购买方为自然人姓名（非企业）的发票不能报销入库；火车票（铁路电子客票）豁免。
SELF_NAME = '深圳市流形机器人科技有限公司'
ORG_SUFFIX = '股份有限公司|有限责任公司|有限公司|总公司|分公司|子公司|集团|酒店|旅行社|中心|局|厂|店|超市|商场|医院|学校|大学|银行|证券|保险|商行|商厦|企业|研究院|学院'


def is_personal_name(buyer_name: Optional[str], invoice_type: Optional[str] = None) -> bool:
    """购买方为自然人姓名（纯中文 2-4 字、无企业后缀）→ True（应彻底拒绝入库）。

    仅对「发票」类凭证生效：类型含「发票」（增值税专用发票/普通发票/电子发票/数电票等）。
    火车票、机票行程单、酒店/订单账单（其他票据）及未识别类型一律豁免——
    这些票据的票面常出现旅客/入住人姓名，不应被误判为个人购买方而拒收。
    """
    if not buyer_name:
        return False
    # 仅发票类凭证做个人购买方拦截；非发票类（火车票/机票/其他票据）及未识别类型豁免
    if not invoice_type or '发票' not in invoice_type:
        return False
    n = re.sub(r'\s+', '', buyer_name)
    if not n or n == SELF_NAME:
        return False
    if re.search(r'(?:' + ORG_SUFFIX + r')$', n):
        return False
    if re.match(r'^[一-鿿]{2,4}$', n):
        return True
    return False


def _refresh_linked_invoices(db: Session, no: Optional[str], extracted: dict) -> int:
    """发票箱识别结果更新后，级联刷新同号正式发票的头字段与明细（防折扣行负数等残留旧值）。

    头字段：销方/购方/日期/号码；明细用 extracted.items 重建，逻辑与 link_inbox 一致；
    负数经 `it.get("amount") or 0` 仍为 truthy，不会被转正。返回刷新的正式发票张数。
    """
    if not no or not extracted:
        return 0
    items = extracted.get("items") or []
    invs = db.scalars(select(inv_m.Invoice).where(inv_m.Invoice.no == no)).all()
    refreshed = 0
    for inv in invs:
        # 刷新头字段（人工复核可能修正了销方/日期/号码）
        if extracted.get("sellerName"):
            inv.seller_name = extracted["sellerName"]
        if extracted.get("buyerName"):
            inv.buyer_name = extracted["buyerName"]
        if extracted.get("sellerTaxNo"):
            inv.seller_tax_no = extracted["sellerTaxNo"]
        if extracted.get("buyerTaxNo"):
            inv.buyer_tax_no = extracted["buyerTaxNo"]
        if extracted.get("date"):
            inv.invoice_date = _parse_date(extracted["date"])
        if extracted.get("no"):
            inv.no = extracted["no"]
        # 刷新明细行
        for d in list(inv.details):
            db.delete(d)
        for it in items:
            amt = it.get("amount") or 0
            tax = it.get("tax") or 0
            name = it.get("name") or ""
            inv.details.append(
                inv_m.InvoiceDetail(
                    biz_type=name,
                    item=name,
                    qty=it.get("qty") or 1,
                    amount=amt,
                    tax_rate=it.get("taxRate") or 0,
                    tax=tax,
                    total=round(amt + tax, 2),
                )
            )
        refreshed += 1
    if refreshed:
        db.commit()
    return refreshed


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


# 客户端无副作用：仅抽 PDF 文字层返回（前端 PDF.js 在某些数电票上 leading-1 脏数据，
# 走后端 pypdf 抽的更干净）。前端 parsePdf 调这个端点拿 text 再走 r1/r2 解析。
@router.post("/extract-text")
async def extract_text(body: dict = Body(...)):
    import sys
    import base64
    import io
    filename = body.get("filename", "")
    content_b64 = body.get("content_base64", "")
    print(f"[extract-text] 收到请求: file={filename}, base64_len={len(content_b64)}", flush=True, file=sys.stderr)
    if not content_b64:
        raise HTTPException(status_code=400, detail="content_base64 为空")
    try:
        raw = base64.b64decode(content_b64)
        reader = PdfReader(io.BytesIO(raw))
        text = "\n".join((pg.extract_text() or "") for pg in reader.pages)
        return {"text": text, "pages": len(reader.pages)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF 文字层抽取失败: {e}")


@router.post("/upload", response_model=s.InvoiceInboxRead, status_code=201)
async def upload(
    file: UploadFile = File(...),
    extracted_json: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    content = await file.read()
    # ── P1 去重：同发票号码（可选税号）已在箱中存在，更新原记录，不重复落盘 ──
    _seller = None
    _no = None
    _consistent = True  # 双识别闸门结论：一致(可信) / 不一致(隔离待复核)
    _validation_passed = True  # 公式核对权威判定
    _ej: Optional[dict] = None
    if extracted_json:
        try:
            _ej = json.loads(extracted_json)
            _seller = _ej.get("sellerTaxNo")
            _no = _ej.get("no")
            _consistent = bool((_ej.get("recognition") or {}).get("consistent", True))
            _validation_passed = bool((_ej.get("validation") or {}).get("passed", True))
            _is_manual = (_ej.get("recognition") or {}).get("method") == "manual"
        except Exception:
            pass
    _buyer = _ej.get("buyerName") if _ej else None
    _itype = _ej.get("type") if _ej else None
    _personal = is_personal_name(_buyer, _itype)
    dup = _dup_of(db, _seller, _no)
    if dup:
        # 重复上传：用本次识别结果更新发票箱记录，并级联刷新同号正式发票明细
        if extracted_json:
            dup.extracted_json = extracted_json
            dup.recognized_at = datetime.now()
            # 个人姓名购买方 → 彻底拒绝（不入库、不隔离待复核、不可人工放行）
            if _personal:
                dup.status = "rejected"
            # 双识别一致 → recognized；不一致 → needs_review（人工修正过 → reviewed）
            elif not _consistent:
                dup.status = "needs_review"
            elif _is_manual:
                dup.status = "reviewed"
            elif dup.status == "needs_review":
                dup.status = "recognized"
            if _ej:
                _refresh_linked_invoices(db, _no, _ej)
        resp = s.InvoiceInboxRead.model_validate(dup)
        resp.duplicated = True
        db.commit()
        db.refresh(dup)
        return resp
    # 先建记录拿 id，再按 id 命名文件（避免重名覆盖）
    if extracted_json:
        # 个人姓名购买方 → 彻底拒绝（最高优先级，不入库）
        if _personal:
            _status = "rejected"
        # 双识别一致 → recognized；不一致 → needs_review（人工修正过 → reviewed）
        elif not _consistent:
            _status = "needs_review"
        elif _is_manual:
            _status = "reviewed"
        else:
            _status = "recognized"
    else:
        _status = "pending"
    rec = m.InvoiceInbox(
        filename=file.filename or "unknown",
        storage_path="",
        source="upload",
        extracted_json=extracted_json,
        status=_status,
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
    # 双识别闸门 + 公式核对：
    # - 手工修正（method='manual' 且 consistent=true）→ reviewed（已复核）
    # - 自动一致且公式通过 → recognized（已识别）
    # - 不一致 / 公式未过 → needs_review（隔离待复核）
    try:
        _rj = json.loads(payload.extracted_json) or {}
        _recognition = _rj.get("recognition") or {}
        _consistent = bool(_recognition.get("consistent", True))
        _validation = _rj.get("validation") or {}
        _validation_passed = bool(_validation.get("passed", True))
        _is_manual = _recognition.get("method") == "manual"
        # 个人姓名购买方 → 彻底拒绝（重新基于提交内容判定，防止人工误放行）
        _personal = is_personal_name(_rj.get("buyerName"), _rj.get("type"))
    except Exception:
        _consistent = True
        _validation_passed = True
        _is_manual = False
        _personal = False
    # 个人姓名购买方 → 彻底拒绝（最高优先级，不入库、不可人工放行）
    if _personal:
        obj.status = "rejected"
    elif not _consistent:
        obj.status = "needs_review"
    elif _is_manual:
        obj.status = "reviewed"
    else:
        obj.status = "recognized"
    obj.recognized_at = datetime.now()
    db.commit()
    db.refresh(obj)
    # 识别结果变更后，级联刷新同号正式发票明细（自动同步，防复发）
    try:
        _rj = json.loads(payload.extracted_json) or {}
        _refresh_linked_invoices(db, _rj.get("no"), _rj)
    except Exception:
        pass
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
        # 取报销单关联的采购单（若有），给正式发票也挂上采购单关联
        if bill.purchase_requisition_id:
            inv.purchase_requisition_id = bill.purchase_requisition_id
    elif payload.doc_type == "purchase":
        pr = db.get(pm.PurchaseRequisition, payload.doc_id)
        if not pr:
            raise HTTPException(status_code=404, detail="采购申请不存在")
        inv.purchase_requisition_id = payload.doc_id
    else:
        raise HTTPException(status_code=400, detail="doc_type 仅支持 reimburse / purchase")

    # 绑定采购细项（可选）
    if payload.purchase_requisition_item_id is not None:
        inv.purchase_requisition_item_id = payload.purchase_requisition_item_id

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
