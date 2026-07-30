"""收入 API：销售收入单 CRUD + 确认入账（联动凭证，自动审核）。"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.api.auth import get_current_user, require_admin_gm
from app.models import revenue as m
from app.models import employee as emp
from app.schemas import revenue as s
from app.utils.codegen import gen_revenue_no
from app.services import voucher_service

router = APIRouter(prefix="/revenues", tags=["revenues"])


def _get_or_404(db: Session, pk: int):
    obj = db.get(m.Revenue, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="收入单不存在")
    return obj


@router.get("", response_model=list[s.RevenueRead])
def list_revenues(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    customer: Optional[str] = None,
    db: Session = Depends(get_db),
):
    stmt = select(m.Revenue)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(
            (m.Revenue.bill_no.like(like))
            | (m.Revenue.customer.like(like))
            | (m.Revenue.remark.like(like))
        )
    if status:
        stmt = stmt.where(m.Revenue.status == status)
    if customer:
        stmt = stmt.where(m.Revenue.customer == customer)
    return db.scalars(stmt).all()


@router.get("/next-bill-no", response_model=dict)
def next_bill_no(db: Session = Depends(get_db)):
    """新建前预占下一个单号（仅预览/预填，真正保存时以入库为准）。"""
    bill_no = gen_revenue_no(db)
    db.commit()
    return {"bill_no": bill_no}


@router.post("", response_model=s.RevenueRead, status_code=201)
def create_revenue(payload: s.RevenueCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()
    if not data.get("bill_no"):
        data["bill_no"] = gen_revenue_no(db)
    obj = m.Revenue(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{rid}", response_model=s.RevenueRead)
def get_revenue(rid: int, db: Session = Depends(get_db)):
    return _get_or_404(db, rid)


@router.put("/{rid}", response_model=s.RevenueRead)
def update_revenue(rid: int, payload: s.RevenueUpdate, db: Session = Depends(get_db)):
    obj = _get_or_404(db, rid)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{rid}")
def delete_revenue(rid: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, rid)
    db.delete(obj)
    db.commit()
    return {"ok": True}


@router.post("/{rid}/confirm", response_model=s.RevenueRead)
def confirm_revenue(
    rid: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """确认收入 → 已确认：联动生成凭证并自动审核入账（借 银行存款/应收账款，贷 主营业务收入/销项税额）。

    幂等：若已存在来源凭证则跳过；重复确认不重复生成。已确认（已入账）不可改金额。
    """
    obj = _get_or_404(db, rid)
    if obj.status == "已确认":
        return obj
    if obj.status != "草稿":
        raise HTTPException(status_code=400, detail=f"当前状态「{obj.status}」不允许确认")
    obj.status = "已确认"
    # 联动：确认收入 → 自动生成并审核凭证（幂等）
    voc = voucher_service.generate_from_revenue(db, obj, maker=current_user.username)
    if voc:
        obj.voucher_no = voc.voucher_no
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/{rid}/unarchive", response_model=s.RevenueRead)
def unarchive_revenue(
    rid: int,
    current_user: emp.Account = Depends(require_admin_gm),
    db: Session = Depends(get_db),
):
    """反归档（撤销）：已确认 → 草稿，删除该收入单联动的凭证（级联删分录），回退待重新确认。限 admin/gm。

    收入无支付环节，故仅删除式反归档、无冲销。撤销后重确认将重新生成凭证（source_no 幂等）。
    """
    obj = _get_or_404(db, rid)
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
