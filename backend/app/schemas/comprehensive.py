"""综合报表相关 Pydantic 模型定义"""

from typing import Dict, List, Optional

from pydantic import BaseModel

from app.schemas.tax import TaxSummaryOut


class FundItem(BaseModel):
    code: str
    name: str
    amount: float


class RevenuePoint(BaseModel):
    period: str
    revenue: float


class BusinessSummary(BaseModel):
    reimburse: Dict[str, int]
    purchase: Dict[str, int]
    travel: Dict[str, int]
    pending_total: int


class VoucherSummary(BaseModel):
    total: int
    period: Optional[str] = None
    period_count: int


class ComprehensiveOverview(BaseModel):
    """综合报表看板一次性聚合响应。"""

    period: Optional[str] = None
    funds: List[FundItem]
    revenue_trend: List[RevenuePoint]
    tax: TaxSummaryOut
    business: BusinessSummary
    voucher: VoucherSummary
