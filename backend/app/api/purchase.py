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


def _build_items(db: Session, req: "m.PurchaseRequisition", items: list[s.PurchaseItemCreate]) -> None:
    """根据传入的明细列表（全量）为申请单构建采购明细。"""
    for it in items:
        data = it.model_dump()
        data.pop("id", None)
        data.pop("req_id", None)
        db.add(m.PurchaseRequisitionItem(req_id=req.id, **data))

router = APIRouter(prefix="/purchases", tags=["purchases"])

# 状态流转白名单：当前状态 -> 允许的动作 -> 目标状态
_STATUS_FLOW = {
    "草稿": {"submit": "待审批"},
    "待审批": {"approve": "已通过", "reject": "已驳回"},
    "已通过": {},
    "已驳回": {"submit": "待审批"},  # 重新提交
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
    return db.scalars(stmt).all()


@router.get("/next-req-no", response_model=dict)
def next_req_no(db: Session = Depends(get_db)):
    """新建采购申请前预占下一个单号。"""
    return {"req_no": gen_purchase_no(db)}


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
    obj = _get_or_404(db, rid)
    if "submit" not in _STATUS_FLOW.get(obj.status, {}):
        raise HTTPException(status_code=400, detail=f"当前状态「{obj.status}」不允许提交")
    obj.status = _STATUS_FLOW[obj.status]["submit"]
    obj.submit_date = date.today()
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
