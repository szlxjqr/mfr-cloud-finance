"""仪表盘 API 路由：返回**真实**跨模块聚合数据（不再使用 Mock）。

前端 src/api/dashboard.ts 约定的契约（必须严格对齐，否则前端会走 fallback 假数据）：
- GET /summary        -> DashboardSummary { voucher_count, current_month }
- GET /funds         -> FundItem[]            （资金情况，取真实科目余额）
- GET /revenue-trend -> RevenueDataPoint[]    （主营业务收入按月，取真实凭证）
- GET /tax            -> TaxItem[]             （应交税费，复用 tax_service）
- GET /voucher-count -> int                   （指定月份凭证数，默认全部）
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import voucher as vm
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    FundItem,
    RevenueDataPoint,
    TaxItem,
)
from app.services import comprehensive_service, tax_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# 资金卡片配色（与前端历史样式保持一致）
_FUND_COLORS = {
    "1001": "#E6A23C",
    "1002": "#67C23A",
    "1122": "#409EFF",
    "2202": "#909399",
    "2211": "#F56C6C",
    "2221": "#00CED1",
}


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_summary(db: Session = Depends(get_db)):
    """仪表盘汇总：凭证总数 + 最近业务期间。"""
    total = db.query(vm.Voucher).count()
    current_month = db.query(func.max(vm.Voucher.period)).scalar() or ""
    return DashboardSummaryResponse(voucher_count=total, current_month=current_month)


@router.get("/funds", response_model=list[FundItem])
def get_funds(db: Session = Depends(get_db)):
    """资金情况：关键科目真实期末余额。"""
    return [
        FundItem(
            name=f["name"],
            amount=f["amount"],
            color=_FUND_COLORS.get(f["code"], "#909399"),
            unit="元",
        )
        for f in comprehensive_service.funds(db)
    ]


@router.get("/revenue-trend", response_model=list[RevenueDataPoint])
def get_revenue_trend(db: Session = Depends(get_db)):
    """经营数据：主营业务收入（6001）按月真实趋势。"""
    return [
        RevenueDataPoint(month=r["period"], value=r["revenue"])
        for r in comprehensive_service.revenue_trend(db)
    ]


@router.get("/tax", response_model=list[TaxItem])
def get_tax(db: Session = Depends(get_db)):
    """应交税费：环形图数据（复用税务取数）。"""
    s = tax_service.tax_summary(db)
    inp = s["input_tax"]
    out = s["output_tax"]
    vat = s["vat_payable"]  # 负值=留抵
    carry = -vat if vat < 0 else 0.0
    return [
        TaxItem(name="进项税额", value=round(inp, 2), color="#409EFF"),
        TaxItem(name="销项税额", value=round(out, 2), color="#67C23A"),
        TaxItem(name="应交增值税", value=round(max(vat, 0.0), 2), color="#E6A23C"),
        TaxItem(name="留抵税额", value=round(carry, 2), color="#909399"),
    ]


@router.get("/voucher-count", response_model=int)
def get_voucher_count(
    month: str = Query(None, description="YYYY-MM，不传则返回全部"),
    db: Session = Depends(get_db),
):
    """指定月份的凭证总数（默认全部期间）。"""
    q = db.query(vm.Voucher)
    if month:
        q = q.filter(vm.Voucher.period == month)
    return q.count()
