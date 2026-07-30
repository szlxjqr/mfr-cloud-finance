"""报销管理 API：报销单的 CRUD 与状态流转。"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import invoice as im
from app.models import reimburse as m
from app.models import employee as emp  # 权限判定用的 Account 模型
from app.schemas import reimburse as s
from app.utils.codegen import gen_bill_no
from app.utils import approval
from app.services import voucher_service  # 联动：提交财务/归档 → 自动生成凭证
from app.api.auth import require_admin_gm  # 反归档/冲销限 admin/gm

router = APIRouter(prefix="/reimbursements", tags=["reimbursements"])

# 状态流转白名单：当前状态 -> 允许的动作 -> 目标状态
# 新流程：草稿→待审批→已通过→(提交财务)→已归档→(支付)→已支付
# 凭证生成时机在「提交财务(归档)」，审批通过只改状态不入账，可退回修改
# 反归档(限admin/gm)：已归档→已通过，删除计提凭证；冲销(限admin/gm)：已支付→已冲销，红冲计提+支付凭证
_STATUS_FLOW = {
    "草稿": {"submit": "待审批"},
    "待审批": {"approve": "已通过", "reject": "已驳回"},
    "已通过": {"submit_finance": "已归档", "revert": "草稿"},
    "已归档": {"pay": "已支付", "unarchive": "已通过"},    # 反归档(限admin/gm,删凭证)
    "已驳回": {"submit": "待审批"},                       # 重新提交
    "已支付": {"writeoff": "已冲销"},                     # 冲销(限admin/gm,红冲)
    "已冲销": {},                                          # 终态
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
    bill_type: Optional[str] = None,
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
    if bill_type:
        stmt = stmt.where(m.ReimbursementBill.bill_type == bill_type)
    return db.scalars(stmt).all()


@router.get("/next-bill-no", response_model=dict)
def next_bill_no(db: Session = Depends(get_db)):
    """新建报销单前预占下一个单号（仅预览/预填，真正保存时以入库为准）。"""
    bill_no = gen_bill_no(db)
    db.commit()  # 预占必须 commit；否则 session close 时 SQLAlchemy 会自动 rollback，计数器不递增
    return {"bill_no": bill_no}


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


@router.post("/from-purchase/{rid}", response_model=s.ReimbursementBillRead, status_code=201)
def convert_from_purchase(rid: int, db: Session = Depends(get_db)):
    """采购申请单 → 报销单：预填申请人/部门/金额/事由，状态置「草稿」待挂接发票后提交。

    幂等：同一采购单已生成过报销单则返回 409 并提示原单号，避免重复生成。
    生成的报销单进入草稿态，用户挂接发票后提交审批（自动审批通过），
    再提交财务归档形成待支付挂账，最后支付（仅账务调整，不触发真实银行付款）。
    """
    from app.models import purchase as pm

    req = db.get(pm.PurchaseRequisition, rid)
    if not req:
        raise HTTPException(status_code=404, detail="采购申请单不存在")

    existing = db.scalar(
        select(m.ReimbursementBill).where(
            m.ReimbursementBill.purchase_requisition_id == rid
        )
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"该采购申请单已生成报销单「{existing.bill_no}」，请勿重复操作",
        )

    reason = req.reason
    if not reason:
        reason = f"采购报销：{req.item_name or req.req_no or ''}".strip()

    obj = m.ReimbursementBill(
        bill_no=gen_bill_no(db),
        applicant=req.applicant,
        department=req.department,
        amount=req.expected_amount or 0,
        reason=reason,
        status="草稿",
        bill_type="采购报销",
        purchase_requisition_id=rid,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/from-travel/{rid}", response_model=s.ReimbursementBillRead, status_code=201)
def convert_from_travel(rid: int, db: Session = Depends(get_db)):
    """差旅申请单 → 报销单：预填申请人/部门/金额/事由/差旅字段，状态置「草稿」待挂接发票后提交。

    幂等：同一差旅单已生成过报销单则返回 409 并提示原单号，避免重复生成。
    """
    from app.models import travel as tm

    req = db.get(tm.TravelRequisition, rid)
    if not req:
        raise HTTPException(status_code=404, detail="差旅申请单不存在")

    existing = db.scalar(
        select(m.ReimbursementBill).where(
            m.ReimbursementBill.travel_requisition_id == rid
        )
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"该差旅申请单已生成报销单「{existing.bill_no}」，请勿重复操作",
        )

    reason = req.reason
    if not reason:
        reason = f"差旅报销：{req.traveler or req.req_no or ''}".strip()

    obj = m.ReimbursementBill(
        bill_no=gen_bill_no(db),
        applicant=req.applicant,
        department=req.department,
        amount=req.expected_amount or 0,
        reason=reason,
        status="草稿",
        bill_type="差旅报销",
        travel_requisition_id=rid,
        traveler=req.traveler,
        travel_destination=req.destination,
        travel_start=req.travel_start,
        travel_end=req.travel_end,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{bid}", response_model=s.ReimbursementBillRead)
def get_bill(bid: int, db: Session = Depends(get_db)):
    stmt = (
        select(m.ReimbursementBill)
        .options(
            selectinload(m.ReimbursementBill.invoices).selectinload(im.Invoice.details)
        )
        .where(m.ReimbursementBill.id == bid)
    )
    obj = db.scalars(stmt).first()
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
    """提交报销单 → 一人公司自动审批通过（不生成凭证，凭证在提交财务/归档时生成）。"""
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
    # 凭证生成已后移到 submit_finance（提交财务/归档），此处不再调用
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
    # 凭证生成已后移到 submit_finance（提交财务/归档），此处不再调用
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


@router.post("/{bid}/submit-finance", response_model=s.ReimbursementBillRead)
def submit_finance_bill(bid: int, db: Session = Depends(get_db)):
    """提交财务 → 已归档（不可逆）：此时自动生成费用凭证，形成待支付挂账。

    凭证规则（按来源采购单的 is_rd_project 区分借方科目）：
    - 研发项目 → 借 研发支出(4301) + 借 进项税额 + 贷 其他应付款(2241)
    - 非研发   → 借 管理费用(5602) + 借 进项税额 + 贷 其他应付款(2241)
    幂等：source_type='报销单', source_no=bill_no 已存在则跳过。
    """
    obj = _get_or_404(db, bid)
    if "submit_finance" not in _STATUS_FLOW.get(obj.status, {}):
        raise HTTPException(
            status_code=400,
            detail=f"当前状态「{obj.status}」不允许提交财务，仅「已通过」状态可提交",
        )
    obj.status = _STATUS_FLOW[obj.status]["submit_finance"]
    # 联动：提交财务/归档 → 自动生成记账凭证（幂等）
    voucher_service.generate_from_reimbursement(db, obj, maker=obj.approver or "system")
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/{bid}/revert", response_model=s.ReimbursementBillRead)
def revert_bill(bid: int, db: Session = Depends(get_db)):
    """退回：已通过 → 草稿（允许修改后重新提交）。归档后不可退回。"""
    obj = _get_or_404(db, bid)
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


@router.post("/{bid}/pay", response_model=s.ReimbursementBillRead)
def pay_bill(bid: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, bid)
    if "pay" not in _STATUS_FLOW.get(obj.status, {}):
        raise HTTPException(status_code=400, detail=f"当前状态「{obj.status}」不允许支付，仅「已归档」状态可支付")
    obj.status = _STATUS_FLOW[obj.status]["pay"]
    obj.pay_date = date.today()
    # 联动：支付报销款 → 自动生成付款凭证（借其他应付款 / 贷银行存款，幂等）
    voucher_service.generate_reimbursement_payment(db, obj, maker=obj.approver or "system")
    db.commit()
    db.refresh(obj)
    return obj


# ================= 反归档 / 冲销（限 admin/gm）=================
@router.post("/{bid}/unarchive", response_model=s.ReimbursementBillRead)
def unarchive_bill(
    bid: int,
    current_user: emp.Account = Depends(require_admin_gm),
    db: Session = Depends(get_db),
):
    """反归档（撤销）：已归档 → 已通过，删除该报销单联动的计提凭证（及支付凭证，若已存在），回退待重新归档。

    限 admin/gm。已支付不可反归档，须走冲销。报销单未存 voucher_no，直接按 source_no 删凭证。
    """
    obj = _get_or_404(db, bid)
    if "unarchive" not in _STATUS_FLOW.get(obj.status, {}):
        raise HTTPException(status_code=400, detail=f"当前状态「{obj.status}」不允许反归档（仅已归档可反归档）")
    obj.status = _STATUS_FLOW[obj.status]["unarchive"]
    db.add(obj)
    db.flush()
    voucher_service.void_vouchers_by_source_no(db, obj.bill_no)
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/{bid}/writeoff", response_model=s.ReimbursementBillRead)
def writeoff_bill(
    bid: int,
    current_user: emp.Account = Depends(require_admin_gm),
    db: Session = Depends(get_db),
):
    """冲销（红字冲销）：已支付 → 已冲销，对该报销单联动的计提+支付凭证做红字冲销（原凭证标记已冲销保留）。

    限 admin/gm。支付后不可反归档，故提供冲销：生成借贷反向、金额相同的红冲凭证（已审核）即时抵消，
    原+冲销+新 三套凭证共存、账务闭合。若已冲销则拒绝重复冲销。
    """
    obj = _get_or_404(db, bid)
    if "writeoff" not in _STATUS_FLOW.get(obj.status, {}):
        raise HTTPException(status_code=400, detail=f"当前状态「{obj.status}」不允许冲销（仅已支付可冲销）")
    obj.status = _STATUS_FLOW[obj.status]["writeoff"]
    db.add(obj)
    db.flush()
    try:
        red_no, cnt = voucher_service.reverse_vouchers_by_source_no(
            db, obj.bill_no, maker=current_user.username
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    db.commit()
    db.refresh(obj)
    return obj
