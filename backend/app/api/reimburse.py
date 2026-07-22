"""报销管理 API：报销单的 CRUD 与状态流转。"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import invoice as im
from app.models import reimburse as m
from app.schemas import reimburse as s
from app.utils.codegen import gen_bill_no
from app.utils import approval
from app.services import voucher_service  # 联动：审批通过 → 自动生成凭证

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


# 报销单号生成已统一收口到 app/utils/codegen.py:gen_bill_no
# （并发安全：乐观锁分配序号 + 从历史 BXGL{year} 最大编号继承 seed，避免碰撞）
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


@router.get("/next-bill-no", response_model=dict)
def next_bill_no(db: Session = Depends(get_db)):
    """新建报销单前预占下一个单号（仅预览/预填，真正保存时以入库为准）。"""
    return {"bill_no": gen_bill_no(db)}


@router.post("", response_model=s.ReimbursementBillRead, status_code=201)
def create_bill(payload: s.ReimbursementBillCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()
    # 单号留空时自动生成；前端也可预占单号后传入，确保新建弹窗预览与入库一致
    if not data.get("bill_no"):
        data["bill_no"] = gen_bill_no(db)
    obj = m.ReimbursementBill(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{bid}", response_model=s.ReimbursementBillRead)
def get_bill(bid: int, db: Session = Depends(get_db)):
    obj = (
        db.query(m.ReimbursementBill)
        .options(
            selectinload(m.ReimbursementBill.invoices).selectinload(im.Invoice.details)
        )
        .get(bid)
    )
    if not obj:
        raise HTTPException(status_code=404, detail="报销单不存在")
    return obj


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
    """提交报销单 → 一人公司自动审批通过（并联动生成凭证）。"""
    obj = _get_or_404(db, bid)
    if "submit" not in _STATUS_FLOW.get(obj.status, {}):
        raise HTTPException(status_code=400, detail=f"当前状态「{obj.status}」不允许提交")
    obj.status = _STATUS_FLOW[obj.status]["submit"]
    obj.submit_date = date.today()
    # 一人公司：提交即自动审批完成（总经理的审批由 admin、其他由总经理）
    approver = approval.resolve_auto_approver(db, obj.applicant)
    obj.status = _STATUS_FLOW.get("待审批", {}).get("approve", "已通过")
    obj.approve_date = date.today()
    obj.approver = approver
    obj.approve_remark = "系统自动审批（一人公司）"
    # 联动：报销单审批通过 → 自动生成记账凭证（幂等）
    voucher_service.generate_from_reimbursement(db, obj, maker=approver)
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/{bid}/approve", response_model=s.ReimbursementBillRead)
def approve_bill(bid: int, body: s.ApprovalBody, db: Session = Depends(get_db)):
    obj = _get_or_404(db, bid)
    if "approve" not in _STATUS_FLOW.get(obj.status, {}):
        raise HTTPException(status_code=400, detail=f"当前状态「{obj.status}」不允许审批通过")
    if not body.approver or not body.approver.strip():
        raise HTTPException(status_code=422, detail="审批人不能为空")
    obj.status = _STATUS_FLOW[obj.status]["approve"]
    obj.approve_date = date.today()
    obj.approver = body.approver.strip()
    obj.approve_remark = body.remark.strip() if body.remark else None
    # 联动：报销单审批通过 → 自动生成记账凭证（幂等，已生成则跳过）
    voucher_service.generate_from_reimbursement(db, obj, maker=obj.approver)
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/{bid}/reject", response_model=s.ReimbursementBillRead)
def reject_bill(bid: int, body: s.ApprovalBody, db: Session = Depends(get_db)):
    obj = _get_or_404(db, bid)
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


@router.post("/{bid}/pay", response_model=s.ReimbursementBillRead)
def pay_bill(bid: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, bid)
    if "pay" not in _STATUS_FLOW.get(obj.status, {}):
        raise HTTPException(status_code=400, detail=f"当前状态「{obj.status}」不允许支付")
    obj.status = _STATUS_FLOW[obj.status]["pay"]
    db.commit()
    db.refresh(obj)
    return obj
