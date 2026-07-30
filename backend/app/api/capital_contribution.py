"""股东入资 API：股东入资单 CRUD + 确认入账（联动凭证，自动审核）。"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.api.auth import get_current_user, require_admin_gm
from app.models import capital_contribution as m
from app.models import employee as emp
from app.schemas import capital_contribution as s
from app.utils.codegen import gen_capital_no
from app.services import voucher_service

router = APIRouter(prefix="/capital-contributions", tags=["capital-contributions"])


def _get_or_404(db: Session, pk: int):
    obj = db.get(m.CapitalContribution, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="股东入资单不存在")
    return obj


@router.get("", response_model=list[s.CapitalContributionRead])
def list_contributions(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    investor: Optional[str] = None,
    db: Session = Depends(get_db),
):
    stmt = select(m.CapitalContribution)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(
            (m.CapitalContribution.bill_no.like(like))
            | (m.CapitalContribution.investor.like(like))
            | (m.CapitalContribution.remark.like(like))
        )
    if status:
        stmt = stmt.where(m.CapitalContribution.status == status)
    if investor:
        stmt = stmt.where(m.CapitalContribution.investor == investor)
    return db.scalars(stmt).all()


@router.get("/next-bill-no", response_model=dict)
def next_bill_no(db: Session = Depends(get_db)):
    """新建前预占下一个单号（仅预览/预填，真正保存时以入库为准）。"""
    bill_no = gen_capital_no(db)
    db.commit()
    return {"bill_no": bill_no}


@router.post("", response_model=s.CapitalContributionRead, status_code=201)
def create_contribution(payload: s.CapitalContributionCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()
    if not data.get("bill_no"):
        data["bill_no"] = gen_capital_no(db)
    obj = m.CapitalContribution(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{cid}", response_model=s.CapitalContributionRead)
def get_contribution(cid: int, db: Session = Depends(get_db)):
    return _get_or_404(db, cid)


@router.put("/{cid}", response_model=s.CapitalContributionRead)
def update_contribution(cid: int, payload: s.CapitalContributionUpdate, db: Session = Depends(get_db)):
    obj = _get_or_404(db, cid)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{cid}")
def delete_contribution(cid: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, cid)
    db.delete(obj)
    db.commit()
    return {"ok": True}


@router.post("/{cid}/confirm", response_model=s.CapitalContributionRead)
def confirm_contribution(
    cid: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """确认入资 → 已确认：联动生成凭证并自动审核入账（借 收款科目 / 贷 实收资本）。

    幂等：若已存在来源凭证则跳过；重复确认不重复生成。已确认（已入账）不可改金额。
    """
    obj = _get_or_404(db, cid)
    if obj.status == "已确认":
        return obj
    if obj.status != "草稿":
        raise HTTPException(status_code=400, detail=f"当前状态「{obj.status}」不允许确认")
    obj.status = "已确认"
    # 联动：确认入资 → 自动生成并审核凭证（幂等）
    voc = voucher_service.generate_from_capital_contribution(db, obj, maker=current_user.username)
    if voc:
        obj.voucher_no = voc.voucher_no
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/{cid}/unarchive", response_model=s.CapitalContributionRead)
def unarchive_contribution(
    cid: int,
    current_user: emp.Account = Depends(require_admin_gm),
    db: Session = Depends(get_db),
):
    """反归档（撤销）：已确认 → 草稿，删除该入资单联动的凭证（级联删分录），回退待重新确认。限 admin/gm。

    入资无支付环节，故仅删除式反归档、无冲销。撤销后重确认将重新生成凭证（source_no 幂等）。
    """
    obj = _get_or_404(db, cid)
    if obj.status != "已确认":
        raise HTTPException(status_code=400, detail=f"当前状态「{obj.status}」不允许反归档（仅已确认可反归档）")
    obj.status = "草稿"
    obj.voucher_no = None  # 清空悬空凭证号（B3）
    db.add(obj)
    db.flush()
    voucher_service.void_vouchers_by_source_no(db, obj.bill_no)
    db.commit()
    db.refresh(obj)
    return obj
