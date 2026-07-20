"""仪表盘相关 Pydantic 模型定义"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# 快捷功能项
class QuickActionItem(BaseModel):
    icon: str
    label: str
    path: str
    color: Optional[str] = None


# 资金指标项
class FundItem(BaseModel):
    name: str
    amount: float
    color: str  # 颜色代码如 #E6A23C
    unit: str = "元"


# 税费项
class TaxItem(BaseModel):
    name: str
    value: float
    color: str


# 经营业绩数据点
class RevenueDataPoint(BaseModel):
    month: str
    value: float


# 仪表盘汇总响应
class DashboardSummaryResponse(BaseModel):
    voucher_count: int  # 凭证总数
    current_month: str  # 当前月份


# 资金情况响应
class FundOverviewResponse(BaseModel):
    month: str
    funds: list[FundItem]  # 6个资金指标


# 经营数据响应
class RevenueTrendResponse(BaseModel):
    month: str
    data: list[RevenueDataPoint]  # 月度数据点列表


# 应交税费响应
class TaxOverviewResponse(BaseModel):
    total_tax: float  # 合计税额
    taxes: list[TaxItem]  # 4项税费
