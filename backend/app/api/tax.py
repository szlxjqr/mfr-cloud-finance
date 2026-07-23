"""税务取数 API：从凭证/工资/合同实时汇总增值税、个税、印花税。"""
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


@router.get("/individual", response_model=sch.IndividualTaxOut)
def tax_individual(
    period: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """个税申报：按员工 × 期间聚合工资单的个人所得税。

    period 形如 2026-07；不传则返回全部期间汇总。
    仅统计 已通过/已发放 的工资单。
    """
    return svc.individual_tax(db, period)


@router.get("/stamp", response_model=sch.StampTaxOut)
def tax_stamp(
    year: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """印花税：销售合同 + 采购合同按金额 0.03% 计征（劳动合同免税已排除）。

    year 形如 2026；不传则返回全部有效合同累计。
    """
    return svc.stamp_tax(db, year)


@router.get("/workbench", response_model=sch.TaxWorkbenchOut)
def tax_workbench(
    period: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """税务工作台：聚合增值税 + 个税 + 印花税 的概览。

    period 形如 2026-07；不传则返回全部期间汇总。
    """
    return svc.tax_workbench(db, period)
