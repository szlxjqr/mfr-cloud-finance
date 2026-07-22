"""记账凭证 API：凭证列表 / 详情 / 一键从已通过业务单补生成。"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import voucher as vm
from app.schemas import voucher as s
from app.services import voucher_service
from app.api.auth import get_current_user

router = APIRouter(prefix="/vouchers", tags=["vouchers"])


def _to_read(v: "vm.Voucher") -> s.VoucherRead:
    """把 ORM 凭证对象映射为 Pydantic 读模型（Decimal→float，日期→字符串）。"""
    entries = [
        s.VoucherEntryRead(
            seq=e.seq,
            subject_code=e.subject_code,
            subject_name=e.subject_name,
            summary=e.summary,
            direction=e.direction,
            amount=float(e.amount),
        )
        for e in sorted(v.entries, key=lambda x: x.seq)
    ]
    return s.VoucherRead(
        id=v.id,
        voucher_no=v.voucher_no,
        date=v.voucher_date.isoformat(),
        period=v.period,
        voucher_word=v.voucher_word,
        seq=v.seq,
        attach_count=v.attach_count,
        maker=v.maker,
        status=v.status,
        source_type=v.source_type,
        source_no=v.source_no,
        summary=v.summary,
        entries=entries,
    )


@router.get("", response_model=list[s.VoucherRead])
def list_vouchers(db: Session = Depends(get_db)):
    """凭证列表（按日期、序号倒序）。"""
    vocs = db.scalars(
        select(vm.Voucher).order_by(vm.Voucher.voucher_date.desc(), vm.Voucher.seq.desc())
    ).all()
    return [_to_read(v) for v in vocs]


@router.get("/{vid}", response_model=s.VoucherRead)
def get_voucher(vid: int, db: Session = Depends(get_db)):
    """凭证详情（含分录）。"""
    v = db.get(vm.Voucher, vid)
    if not v:
        raise HTTPException(status_code=404, detail="凭证不存在")
    return _to_read(v)


@router.delete("/{vid}")
def delete_voucher(
    vid: int,
    db: Session = Depends(get_db),
    current_user: object = Depends(get_current_user),
):
    """删除凭证（联动记录一并清除）。"""
    v = db.get(vm.Voucher, vid)
    if not v:
        raise HTTPException(status_code=404, detail="凭证不存在")
    db.delete(v)
    db.commit()
    return {"ok": True}


@router.post("/sync", response_model=s.VoucherGenerateResult)
def sync_from_approved(
    db: Session = Depends(get_db),
    current_user: object = Depends(get_current_user),
):
    """一键把「已通过」的报销单/采购申请补生成凭证（历史回填 + 联动铺开）。"""
    generated, skipped, logs = voucher_service.sync_from_approved(
        db, getattr(current_user, "username", "system")
    )
    return s.VoucherGenerateResult(
        generated=generated, skipped=skipped, detail=logs
    )
