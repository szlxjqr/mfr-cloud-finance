"""会计科目 API：科目列表 / 余额汇总 / 重置为标准科目。"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import subject as sm
from app.models import voucher as vm
from app.schemas import subject as s
from app.db.database import _seed_subjects

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.get("", response_model=list[s.AccountSubjectRead])
def list_subjects(db: Session = Depends(get_db)):
    """科目列表（按编码排序）。"""
    return db.scalars(select(sm.AccountSubject).order_by(sm.AccountSubject.code)).all()


@router.post("", response_model=s.AccountSubjectRead, status_code=201)
def create_subject(payload: s.AccountSubjectCreate, db: Session = Depends(get_db)):
    """新增科目。"""
    obj = sm.AccountSubject(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/balance", response_model=list[s.SubjectBalanceRead])
def subject_balance(
    period: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """科目余额表：由凭证分录汇总（本期=累计，暂不分期间）。

    - 资产/成本类（正常借）：期末借方余额 = 借合计 − 贷合计（负则转贷方）。
    - 负债/权益/损益类（正常贷）：期末贷方余额 = 贷合计 − 借合计（负则转借方）。
    """
    subs = db.scalars(select(sm.AccountSubject).order_by(sm.AccountSubject.code)).all()

    rows = db.execute(
        select(
            vm.VoucherEntry.subject_code,
            vm.VoucherEntry.direction,
            func.sum(vm.VoucherEntry.amount),
        ).group_by(vm.VoucherEntry.subject_code, vm.VoucherEntry.direction)
    ).all()

    agg: dict[str, dict] = {}
    for code, direction, amt in rows:
        agg.setdefault(code, {"借": 0.0, "贷": 0.0})
        agg[code][direction] = float(amt or 0)

    out: list[s.SubjectBalanceRead] = []
    for sub in subs:  # noqa: E501
        d = agg.get(sub.code, {"借": 0.0, "贷": 0.0})
        deb = d["借"]
        cre = d["贷"]
        if sub.direction == "借":
            bal = deb - cre
            ed = bal if bal > 0 else 0.0
            ec = -bal if bal < 0 else 0.0
        else:
            bal = cre - deb
            ec = bal if bal > 0 else 0.0
            ed = -bal if bal < 0 else 0.0
        out.append(
            s.SubjectBalanceRead(
                code=sub.code,
                name=sub.name,
                category=sub.category,
                direction=sub.direction,
                period_debit=deb,
                period_credit=cre,
                cum_debit=deb,
                cum_credit=cre,
                ending_debit=ed,
                ending_credit=ec,
            )
        )
    return out


@router.post("/reset", response_model=dict)
def reset_subjects(db: Session = Depends(get_db)):
    """清空凭证与科目，重置为标准会计科目表（开发/演示用）。"""
    db.execute(text("DELETE FROM voucher_entries"))
    db.execute(text("DELETE FROM vouchers"))
    db.execute(text("DELETE FROM account_subjects"))
    db.commit()
    _seed_subjects(db)
    return {"ok": True, "message": "已重置为标准会计科目"}
