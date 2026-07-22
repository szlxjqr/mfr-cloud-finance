"""会计科目 Pydantic 模型。"""
from typing import Optional

from pydantic import BaseModel


class AccountSubjectBase(BaseModel):
    code: str
    name: str
    category: str = "资产"   # 资产/负债/权益/成本/损益
    direction: str = "借"    # 正常余额方向：借/贷
    level: int = 1
    parent_code: Optional[str] = None
    is_leaf: bool = True
    status: str = "启用"      # 启用/封存


class AccountSubjectCreate(AccountSubjectBase):
    pass


class AccountSubjectUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    direction: Optional[str] = None
    level: Optional[int] = None
    parent_code: Optional[str] = None
    is_leaf: Optional[bool] = None
    status: Optional[str] = None


class AccountSubjectRead(AccountSubjectBase):
    id: int


class SubjectBalanceRead(BaseModel):
    """科目余额（由凭证分录汇总得出）。"""

    code: str
    name: str
    category: str
    direction: str
    period_debit: float = 0.0     # 本期借方发生额
    period_credit: float = 0.0    # 本期贷方发生额
    cum_debit: float = 0.0       # 本年累计借方
    cum_credit: float = 0.0      # 本年累计贷方
    ending_debit: float = 0.0      # 期末借方余额
    ending_credit: float = 0.0     # 期末贷方余额
