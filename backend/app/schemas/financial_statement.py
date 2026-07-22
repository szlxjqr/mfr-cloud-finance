"""财务报表 schemas：资产负债表 / 利润表 / 现金流量表 / 季报。"""

from typing import List, Optional

from pydantic import BaseModel


# ── 资产负债表 ──
class BalanceSheetItem(BaseModel):
    code: str
    name: str
    amount: float


class BalanceSheetSection(BaseModel):
    name: str
    items: List[BalanceSheetItem]
    total: float


class BalanceSheetOut(BaseModel):
    as_of: str
    sections: List[BalanceSheetSection]
    total_assets: float
    total_liabilities: float
    total_equity: float
    balanced: bool
    note: str = ""


# ── 利润表 ──
class IncomeLine(BaseModel):
    code: str
    name: str
    current: float       # 本期金额
    cumulative: float     # 本年累计金额


class IncomeStatementOut(BaseModel):
    period: str
    revenue: List[IncomeLine]
    cost: List[IncomeLine]
    expense: List[IncomeLine]
    total_revenue_cur: float
    total_revenue_cum: float
    total_expense_cur: float
    total_expense_cum: float
    operating_profit_cur: float
    operating_profit_cum: float
    total_profit_cur: float
    total_profit_cum: float
    net_profit_cur: float
    net_profit_cum: float


# ── 现金流量表 ──
class CashFlowLine(BaseModel):
    name: str
    amount: float


class CashFlowSection(BaseModel):
    name: str
    items: List[CashFlowLine]
    total: float


class CashFlowOut(BaseModel):
    period: str
    operating: CashFlowSection
    investing: CashFlowSection
    financing: CashFlowSection
    net_operating: float
    net_investing: float
    net_financing: float
    net_increase: float
    note: str = ""


# ── 季报（合并）──
class QuarterOut(BaseModel):
    year: int
    quarter: int
    as_of: str
    months: List[str]
    balance_sheet: BalanceSheetOut
    income: IncomeStatementOut
    cash_flow: CashFlowOut
    note: Optional[str] = None
