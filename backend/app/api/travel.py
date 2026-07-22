"""差旅管理 API：差旅申请单的 CRUD 与状态流转。"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import travel as m
from app.schemas import travel as s
from app.utils.codegen import gen_travel_no
from app.utils import approval

router = APIRouter(prefix="/travels", tags=["travels"])

# 状态流转白名单：当前状态 -> 允许的动作 -> 目标状态
_STATUS_FLOW = {
    "草稿": {"submit": "待审批"},
    "待审批": {"approve": "已通过", "reject": "已驳回"},
    "已通过": {},
    "已驳回": {"submit": "待审批"},  # 重新提交
}


def _get_or_404(db: Session, pk: int):
    obj = db.get(m.TravelRequisition, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="差旅申请单不存在")
    return obj


# ================= CRUD =================
@router.get("", response_model=list[s.TravelReqRead])
def list_reqs(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    applicant: Optional[str] = None,
    db: Session = Depends(get_db),
):
    stmt = select(m.TravelRequisition)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(
            (m.TravelRequisition.req_no.like(like))
            | (m.TravelRequisition.applicant.like(like))
            | (m.TravelRequisition.traveler.like(like))
            | (m.TravelRequisition.destination.like(like))
            | (m.TravelRequisition.reason.like(like))
        )
    if status:
        stmt = stmt.where(m.TravelRequisition.status == status)
    if applicant:
        stmt = stmt.where(m.TravelRequisition.applicant == applicant)
    return db.scalars(stmt).all()


@router.get("/next-req-no", response_model=dict)
def next_req_no(db: Session = Depends(get_db)):
    """新建差旅申请前预占下一个单号。"""
    return {"req_no": gen_travel_no(db)}


@router.post("", response_model=s.TravelReqRead, status_code=201)
def create_req(payload: s.TravelReqCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()
    if not data.get("req_no"):
        data["req_no"] = gen_travel_no(db)
    obj = m.TravelRequisition(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{rid}", response_model=s.TravelReqRead)
def get_req(rid: int, db: Session = Depends(get_db)):
    return _get_or_404(db, rid)


@router.put("/{rid}", response_model=s.TravelReqRead)
def update_req(rid: int, payload: s.TravelReqUpdate, db: Session = Depends(get_db)):
    obj = _get_or_404(db, rid)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
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
@router.post("/{rid}/submit", response_model=s.TravelReqRead)
def submit_req(rid: int, db: Session = Depends(get_db)):
    """提交差旅申请 → 一人公司自动审批通过。"""
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
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/{rid}/approve", response_model=s.TravelReqRead)
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


@router.post("/{rid}/reject", response_model=s.TravelReqRead)
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
