"""税务取数 Pydantic 模型。"""
from typing import List, Optional

from pydantic import BaseModel


class TaxSummaryOut(BaseModel):
    """税务汇总 KPI（期间感知）。"""

    period: Optional[str] = None
    input_tax: float = 0.0  # 进项税额
    output_tax: float = 0.0  # 销项税额
    vat_payable: float = 0.0  # 应交增值税（销项-进项，负值=留抵）
    carryforward: bool = False  # 是否留抵


class TaxInputDetail(BaseModel):
    """进项税额明细行（关联来源业务单）。"""

    voucher_no: str
    date: str
    period: str
    summary: Optional[str] = None
    amount: float = 0.0
    source_type: Optional[str] = None
    source_no: Optional[str] = None


class TaxMonthlyRow(BaseModel):
    """月度趋势行。"""

    period: str
    input_tax: float = 0.0
    output_tax: float = 0.0


class TaxSummaryDetailOut(BaseModel):
    """发票税务汇总：KPI + 进项税额明细 + 月度趋势（一次返回）。"""

    summary: TaxSummaryOut
    details: List[TaxInputDetail] = []
    monthly: List[TaxMonthlyRow] = []
