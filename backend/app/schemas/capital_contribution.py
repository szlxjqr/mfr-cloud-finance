"""股东入资 Pydantic 模型。"""
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CapitalContributionBase(BaseModel):
    bill_no: Optional[str] = None
    investor: str
    amount: Optional[Decimal] = None
    capital_type: str = "货币资金"
    receive_subject: str = "1002"
    contribution_date: Optional[date] = None
    status: str = "草稿"
    remark: Optional[str] = None


class CapitalContributionCreate(CapitalContributionBase):
    pass


class CapitalContributionUpdate(BaseModel):
    bill_no: Optional[str] = None
    investor: Optional[str] = None
    amount: Optional[Decimal] = None
    capital_type: Optional[str] = None
    receive_subject: Optional[str] = None
    contribution_date: Optional[date] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class CapitalContributionRead(CapitalContributionBase):
    id: int
    voucher_no: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
