"""账簿查询 API：总账 / 明细账 / 科目汇总 / 序时账。

数据均由凭证分录实时汇总（见 ledger_service），无需额外参数存储。
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import ledger as sch
from app.services import ledger_service as svc

router = APIRouter(prefix="/ledger", tags=["ledger"])


@router.get("/summary", response_model=List[sch.LedgerSummaryRow])
def ledger_summary(
    period: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """科目汇总表：每个科目一行的期初/本期/累计/期末（期间感知）。"""
    return svc.summary(db, period)


@router.get("/general", response_model=sch.GeneralLedgerOut)
def general_ledger(
    subject_code: str,
    period: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """总账：某科目按期间汇总的期初/本期/期末。"""
    if not subject_code:
        raise HTTPException(status_code=400, detail="subject_code 必填")
    return svc.general_ledger(db, subject_code, period)


@router.get("/subsidiary", response_model=sch.SubsidiaryLedgerOut)
def subsidiary_ledger(
    subject_code: str,
    period: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """明细账：某科目逐笔分录流水 + 期初/合计/期末。"""
    if not subject_code:
        raise HTTPException(status_code=400, detail="subject_code 必填")
    return svc.subsidiary_ledger(db, subject_code, period)


@router.get("/journal", response_model=sch.JournalOut)
def journal_ledger(
    period: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """序时账：全部凭证分录按日期/凭证号/序号排序的流水。"""
    return svc.journal(db, period)
