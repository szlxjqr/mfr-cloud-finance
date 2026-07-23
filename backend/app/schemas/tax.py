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


class IndividualTaxRow(BaseModel):
    """个税申报明细行（按员工 × 期间聚合）。"""

    employee_name: str
    employee_no: Optional[str] = None
    department: Optional[str] = None
    period: str
    gross_pay: float = 0.0  # 应发合计
    social_personal: float = 0.0  # 社保(个人)
    fund_personal: float = 0.0  # 公积金(个人)
    tax_personal: float = 0.0  # 个人所得税


class IndividualTaxOut(BaseModel):
    """个税申报：按员工 × 期间聚合的工资个税。"""

    period: Optional[str] = None
    rows: List[IndividualTaxRow] = []
    total_tax: float = 0.0  # 本期/全部应申报个税合计
    total_gross: float = 0.0  # 应发合计
    headcount: int = 0  # 申报人数


class StampTaxRow(BaseModel):
    """印花税明细行（买卖合同）。"""

    contract_no: Optional[str] = None
    party: Optional[str] = None
    type: str  # 销售合同 / 采购合同
    sign_date: str = ""
    amount: float = 0.0  # 合同金额
    rate: float = 0.0003  # 印花税率
    tax: float = 0.0  # 应纳税额


class StampTaxOut(BaseModel):
    """印花税：销售 + 采购合同按 0.03% 计征（劳动合同免税已排除）。"""

    year: Optional[str] = None
    rows: List[StampTaxRow] = []
    total_amount: float = 0.0
    total_tax: float = 0.0
    contract_count: int = 0


class TaxWorkbenchOut(BaseModel):
    """税务工作台：增值税 + 个税 + 印花税 概览。"""

    period: Optional[str] = None
    vat: dict = {}
    individual: dict = {}
    stamp: dict = {}
