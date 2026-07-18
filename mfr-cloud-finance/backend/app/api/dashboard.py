"""仪表盘 API 路由：返回模拟（Mock）业务数据"""

from fastapi import APIRouter

from app.schemas.dashboard import (
    DashboardSummaryResponse,
    FundItem,
    FundOverviewResponse,
    RevenueDataPoint,
    RevenueTrendResponse,
    TaxItem,
    TaxOverviewResponse,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_summary():
    """仪表盘汇总信息：凭证总数、当前月份"""
    return DashboardSummaryResponse(voucher_count=128, current_month="2026-05")


@router.get("/funds", response_model=FundOverviewResponse)
def get_funds():
    """资金情况：6 个资金指标"""
    return FundOverviewResponse(
        month="2026-05",
        funds=[
            FundItem(name="现金", amount=156820.50, color="#E6A23C", unit="元"),
            FundItem(name="银行存款", amount=2856740.30, color="#67C23A", unit="元"),
            FundItem(name="应收账款", amount=456230.00, color="#409EFF", unit="元"),
            FundItem(name="应付账款", amount=198560.80, color="#909399", unit="元"),
            FundItem(name="主营业务收入", amount=3567890.00, color="#F56C6C", unit="元"),
            FundItem(name="管理费用", amount=428650.00, color="#00CED1", unit="元"),
        ],
    )


@router.get("/revenue", response_model=RevenueTrendResponse)
def get_revenue():
    """经营数据：近 12 个月营收趋势（折线图用）"""
    return RevenueTrendResponse(
        month="2026-05",
        data=[
            RevenueDataPoint(month="2025-06", value=245.6),
            RevenueDataPoint(month="2025-07", value=312.8),
            RevenueDataPoint(month="2025-08", value=298.4),
            RevenueDataPoint(month="2025-09", value=356.2),
            RevenueDataPoint(month="2025-10", value=389.1),
            RevenueDataPoint(month="2025-11", value=425.7),
            RevenueDataPoint(month="2025-12", value=512.3),
            RevenueDataPoint(month="2026-01", value=478.9),
            RevenueDataPoint(month="2026-02", value=398.2),
            RevenueDataPoint(month="2026-03", value=534.6),
            RevenueDataPoint(month="2026-04", value=589.3),
            RevenueDataPoint(month="2026-05", value=623.8),
        ],
    )


@router.get("/taxes", response_model=TaxOverviewResponse)
def get_taxes():
    """应交税费：环形图数据"""
    return TaxOverviewResponse(
        total_tax=186450.00,
        taxes=[
            TaxItem(name="应交增值税", value=85600.00, color="#409EFF"),
            TaxItem(name="未交增值税", value=32400.00, color="#67C23A"),
            TaxItem(name="应交所得税", value=52300.00, color="#E6A23C"),
            TaxItem(name="其他", value=16150.00, color="#909399"),
        ],
    )
