"""税务取数 API：从凭证实时汇总增值税相关数据。"""
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import tax as sch
from app.services import tax_service as svc

router = APIRouter(prefix="/tax", tags=["税务取数"])


@router.get("/summary", response_model=sch.TaxSummaryDetailOut)
def tax_summary(
    period: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """发票税务汇总：本期 KPI + 进项税额明细 + 月度趋势。

    period 形如 2026-07；不传则返回全部期间的汇总、明细与当前年趋势。
    """
    summary = svc.tax_summary(db, period)
    details = svc.input_tax_detail(db, period)
    year = (period or "").split("-")[0] or None
    monthly = svc.monthly_trend(db, year)
    return sch.TaxSummaryDetailOut(
        summary=sch.TaxSummaryOut(**summary),
        details=[sch.TaxInputDetail(**d) for d in details],
        monthly=[sch.TaxMonthlyRow(**m) for m in monthly],
    )
