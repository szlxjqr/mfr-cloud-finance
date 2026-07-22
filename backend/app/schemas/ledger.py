"""账簿查询 Pydantic 模型：总账 / 明细账 / 科目汇总 / 序时账。"""
from typing import List, Optional

from pydantic import BaseModel


class LedgerSummaryRow(BaseModel):
    """科目汇总表行（含期初/本期/累计/期末，期间感知）。"""

    code: str
    name: str
    category: str
    direction: str
    level: int
    parent_code: Optional[str] = None
    is_leaf: bool
    opening_debit: float = 0.0
    opening_credit: float = 0.0
    period_debit: float = 0.0
    period_credit: float = 0.0
    cum_debit: float = 0.0
    cum_credit: float = 0.0
    ending_debit: float = 0.0
    ending_credit: float = 0.0


class GeneralLedgerRow(BaseModel):
    period: str
    opening_debit: float = 0.0
    opening_credit: float = 0.0
    period_debit: float = 0.0
    period_credit: float = 0.0
    ending_debit: float = 0.0
    ending_credit: float = 0.0
    direction: str
    balance: float


class GeneralLedgerOut(BaseModel):
    subject_code: str
    subject_name: str
    direction: str
    rows: List[GeneralLedgerRow] = []


class SubsidiaryLine(BaseModel):
    date: str
    voucher_no: str
    summary: Optional[str] = None
    debit: float = 0.0
    credit: float = 0.0
    direction: str
    balance: float


class SubsidiaryLedgerOut(BaseModel):
    subject_code: str
    subject_name: str
    direction: str
    opening_debit: float = 0.0
    opening_credit: float = 0.0
    lines: List[SubsidiaryLine] = []
    total_debit: float = 0.0
    total_credit: float = 0.0
    ending_debit: float = 0.0
    ending_credit: float = 0.0


class JournalLine(BaseModel):
    date: str
    voucher_no: str
    period: str
    summary: Optional[str] = None
    subject_code: str
    subject_name: str
    direction: str
    amount: float


class JournalOut(BaseModel):
    lines: List[JournalLine] = []
