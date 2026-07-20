"""报销管理 API：报销单的 CRUD 与状态流转。"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import reimburse as m
from app.schemas import reimburse as s

router = APIRouter(prefix="/reimbursements", tags=["reimbursements"])

# 状态流转白名单：当前状态 -> 允许的动作 -> 目标状态
_STATUS_FLOW = {
    "草稿": {"submit": "待审批"},
    "待审批": {"approve": "已通过", "reject": "已驳回"},
    "已通过": {"pay": "已支付"},
    "已驳回": {"submit": "待审批"},  # 重新提交
    "已支付": {},  # 终态
}


def _get_or_404(db: Session, pk: int):
    obj = db.get(m.ReimbursementBill, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="报销单不存在")
    return obj


def _gen_bill_no(obj_id: int) -> str:
    """单号：BX + 提交日期(YYYYMMDD) + 自增序号(4位)。"""
    return f"BX{date.today():%Y%m%d}{obj_id:04d}"


# ================= CRUD =================
@router.get("", response_model=list[s.ReimbursementBillRead])
def list_bills(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    applicant: Optional[str] = None,
    db: Session = Depends(get_db),
):
    stmt = select(m.ReimbursementBill)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(
            (m.ReimbursementBill.bill_no.like(like))
            | (m.ReimbursementBill.applicant.like(like))
            | (m.ReimbursementBill.reason.like(like))
        )
    if status:
        stmt = stmt.where(m.ReimbursementBill.status == status)
    if applicant:
        stmt = stmt.where(m.ReimbursementBill.applicant == applicant)
    return db.scalars(stmt).all()


@router.post("", response_model=s.ReimbursementBillRead, status_code=201)
def create_bill(payload: s.ReimbursementBillCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()
    # 单号留空时，先入库取 id，再生成 BX+日期+序号 的唯一单号
    data["bill_no"] = None
    obj = m.ReimbursementBill(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    obj.bill_no = _gen_bill_no(obj.id)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{bid}", response_model=s.ReimbursementBillRead)
def get_bill(bid: int, db: Session = Depends(get_db)):
    return _get_or_404(db, bid)


@router.put("/{bid}", response_model=s.ReimbursementBillRead)
def update_bill(bid: int, payload: s.ReimbursementBillUpdate, db: Session = Depends(get_db)):
    obj = _get_or_404(db, bid)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{bid}")
def delete_bill(bid: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, bid)
    db.delete(obj)
    db.commit()
    return {"ok": True}


# ================= 状态流转 =================
@router.post("/{bid}/submit", response_model=s.ReimbursementBillRead)
def submit_bill(bid: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, bid)
    if "submit" not in _STATUS_FLOW.get(obj.status, {}):
        raise HTTPException(status_code=400, detail=f"当前状态「{obj.status}」不允许提交")
    obj.status = _STATUS_FLOW[obj.status]["submit"]
    obj.submit_date = date.today()
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/{bid}/approve", response_model=s.ReimbursementBillRead)
def approve_bill(bid: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, bid)
    if "approve" not in _STATUS_FLOW.get(obj.status, {}):
        raise HTTPException(status_code=400, detail=f"当前状态「{obj.status}」不允许审批通过")
    obj.status = _STATUS_FLOW[obj.status]["approve"]
    obj.approve_date = date.today()
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/{bid}/reject", response_model=s.ReimbursementBillRead)
def reject_bill(bid: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, bid)
    if "reject" not in _STATUS_FLOW.get(obj.status, {}):
        raise HTTPException(status_code=400, detail=f"当前状态「{obj.status}」不允许驳回")
    obj.status = _STATUS_FLOW[obj.status]["reject"]
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/{bid}/pay", response_model=s.ReimbursementBillRead)
def pay_bill(bid: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, bid)
    if "pay" not in _STATUS_FLOW.get(obj.status, {}):
        raise HTTPException(status_code=400, detail=f"当前状态「{obj.status}」不允许支付")
    obj.status = _STATUS_FLOW[obj.status]["pay"]
    db.commit()
    db.refresh(obj)
    return obj
