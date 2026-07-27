"""采购管理 API：采购申请单的 CRUD 与状态流转。"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import purchase as m
from app.schemas import purchase as s
from app.utils.codegen import gen_purchase_no
from app.utils import approval
from app.services import voucher_service  # 联动：审批通过 → 自动确认应付凭证


def _build_items(db: Session, req: "m.PurchaseRequisition", items: list[s.PurchaseItemCreate]) -> None:
    """根据传入的明细列表（全量）为申请单构建采购明细。"""
    for it in items:
        # 丢弃没有实际内容的细项（名称为空即视为无效）
        if not it.item_name or not it.item_name.strip():
            continue
        data = it.model_dump()
        data.pop("id", None)
        data.pop("req_id", None)
        db.add(m.PurchaseRequisitionItem(req_id=req.id, **data))

router = APIRouter(prefix="/purchases", tags=["purchases"])

# 状态流转白名单：当前状态 -> 允许的动作 -> 目标状态
# 采购申请不再生成凭证（确认应付凭证已废弃），费用在报销单提交财务时入账
# 已通过可退回草稿修改后重新提交
_STATUS_FLOW = {
    "草稿": {"submit": "待审批"},
    "待审批": {"approve": "已通过", "reject": "已驳回"},
    "已通过": {"revert": "草稿"},
    "已驳回": {"submit": "待审批"},  # 重新提交
    "已支付": {},  # 终态（兼容旧数据）
}


def _get_or_404(db: Session, pk: int):
    obj = db.get(m.PurchaseRequisition, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="采购申请单不存在")
    return obj


# ================= CRUD =================
@router.get("", response_model=list[s.PurchaseReqRead])
def list_reqs(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    applicant: Optional[str] = None,
    supplier: Optional[str] = None,
    db: Session = Depends(get_db),
):
    stmt = select(m.PurchaseRequisition)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(
            (m.PurchaseRequisition.req_no.like(like))
            | (m.PurchaseRequisition.applicant.like(like))
            | (m.PurchaseRequisition.item_name.like(like))
            | (m.PurchaseRequisition.reason.like(like))
        )
    if status:
        stmt = stmt.where(m.PurchaseRequisition.status == status)
    if applicant:
        stmt = stmt.where(m.PurchaseRequisition.applicant == applicant)
    if supplier:
        stmt = stmt.where(m.PurchaseRequisition.supplier == supplier)
    return db.scalars(stmt).all()


@router.get("/next-req-no", response_model=dict)
def next_req_no(db: Session = Depends(get_db)):
    """新建采购申请前预占下一个单号。"""
    req_no = gen_purchase_no(db)
    db.commit()  # 预占必须 commit；否则 session close 时 SQLAlchemy 会自动 rollback，计数器不递增
    return {"req_no": req_no}


@router.post("", response_model=s.PurchaseReqRead, status_code=201)
def create_req(payload: s.PurchaseReqCreate, db: Session = Depends(get_db)):
    data = payload.model_dump(exclude={"items"})
    if not data.get("req_no"):
        data["req_no"] = gen_purchase_no(db)
    obj = m.PurchaseRequisition(**data)
    db.add(obj)
    db.flush()  # 先写主表拿到 id，再写明细
    _build_items(db, obj, payload.items or [])
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{rid}", response_model=s.PurchaseReqRead)
def get_req(rid: int, db: Session = Depends(get_db)):
    return _get_or_404(db, rid)


@router.put("/{rid}", response_model=s.PurchaseReqRead)
def update_req(rid: int, payload: s.PurchaseReqUpdate, db: Session = Depends(get_db)):
    obj = _get_or_404(db, rid)
    for k, v in payload.model_dump(exclude_unset=True, exclude={"items"}).items():
        setattr(obj, k, v)
    if payload.items is not None:
        # 全量替换明细：删除旧行，写入新行
        for old in list(obj.items):
            db.delete(old)
        db.flush()
        _build_items(db, obj, payload.items)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{rid}")
def delete_req(rid: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, rid)
    db.delete(obj)
    db.commit()
    return {"ok": True}


# ================= 状态流转 =================
@router.post("/{rid}/submit", response_model=s.PurchaseReqRead)
def submit_req(rid: int, db: Session = Depends(get_db)):
    """提交采购申请 → 一人公司自动审批通过（不再生成凭证，费用在报销单归档时入账）。"""
    obj = _get_or_404(db, rid)
    if "submit" not in _STATUS_FLOW.get(obj.status, {}):
        raise HTTPException(status_code=400, detail=f"当前状态「{obj.status}」不允许提交")
    obj.status = _STATUS_FLOW[obj.status]["submit"]
    obj.submit_date = date.today()
    # 一人公司：提交即自动审批完成
    approver = approval.resolve_auto_approver(db, obj.applicant)
    obj.status = _STATUS_FLOW.get("待审批", {}).get("approve", "已通过")
    obj.approve_date = date.today()
    obj.approver = approver
    obj.approve_remark = "系统自动审批（一人公司）"
    # 采购申请不再生成凭证；费用在报销单提交财务/归档时入账
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/{rid}/approve", response_model=s.PurchaseReqRead)
def approve_req(rid: int, body: s.ApprovalBody, db: Session = Depends(get_db)):
    obj = _get_or_404(db, rid)
    if "approve" not in _STATUS_FLOW.get(obj.status, {}):
        raise HTTPException(status_code=400, detail=f"当前状态「{obj.status}」不允许审批通过")
    if not body.approver or not body.approver.strip():
        raise HTTPException(status_code=422, detail="审批人不能为空")
    obj.status = _STATUS_FLOW[obj.status]["approve"]
    obj.approve_date = date.today()
    obj.approver = body.approver.strip()
    obj.approve_remark = body.remark.strip() if body.remark else None
    # 采购申请不再生成凭证；费用在报销单提交财务/归档时入账
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/{rid}/reject", response_model=s.PurchaseReqRead)
def reject_req(rid: int, body: s.ApprovalBody, db: Session = Depends(get_db)):
    obj = _get_or_404(db, rid)
    if "reject" not in _STATUS_FLOW.get(obj.status, {}):
        raise HTTPException(status_code=400, detail=f"当前状态「{obj.status}」不允许驳回")
    if not body.approver or not body.approver.strip():
        raise HTTPException(status_code=422, detail="审批人不能为空")
    obj.status = _STATUS_FLOW[obj.status]["reject"]
    obj.approve_date = date.today()
    obj.approver = body.approver.strip()
    obj.approve_remark = body.remark.strip() if body.remark else None
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/{rid}/revert", response_model=s.PurchaseReqRead)
def revert_req(rid: int, db: Session = Depends(get_db)):
    """退回：已通过 → 草稿（允许修改后重新提交）。"""
    obj = _get_or_404(db, rid)
    if "revert" not in _STATUS_FLOW.get(obj.status, {}):
        raise HTTPException(
            status_code=400,
            detail=f"当前状态「{obj.status}」不允许退回，仅「已通过」状态可退回",
        )
    obj.status = _STATUS_FLOW[obj.status]["revert"]
    obj.approve_date = None
    obj.approver = None
    obj.approve_remark = None
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/{rid}/pay", response_model=s.PurchaseReqRead)
def pay_req(rid: int, db: Session = Depends(get_db)):
    """采购付款：结算应付账款 → 自动生成付款凭证（借应付账款 / 贷银行存款）。"""
    obj = _get_or_404(db, rid)
    if "pay" not in _STATUS_FLOW.get(obj.status, {}):
        raise HTTPException(status_code=400, detail=f"当前状态「{obj.status}」不允许付款")
    obj.status = _STATUS_FLOW[obj.status]["pay"]
    obj.pay_date = date.today()
    # 联动：采购付款 → 自动生成付款凭证（借应付账款 / 贷银行存款，幂等）
    voucher_service.generate_purchase_payment(db, obj, maker=obj.approver or "system")
    db.commit()
    db.refresh(obj)
    return obj
