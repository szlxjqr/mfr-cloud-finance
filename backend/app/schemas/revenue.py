"""收入 Pydantic 模型。"""
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class RevenueBase(BaseModel):
    bill_no: Optional[str] = None
    customer: str
    total_amount: Optional[Decimal] = None
    tax_rate: Decimal = Decimal("0.13")
    settle_method: str = "银行收讫"
    revenue_date: Optional[date] = None
    status: str = "草稿"
    remark: Optional[str] = None


class RevenueCreate(RevenueBase):
    pass


class RevenueUpdate(BaseModel):
    bill_no: Optional[str] = None
    customer: Optional[str] = None
    total_amount: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    settle_method: Optional[str] = None
    revenue_date: Optional[date] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class RevenueRead(RevenueBase):
    id: int
    voucher_no: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
