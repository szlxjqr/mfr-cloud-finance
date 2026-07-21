"""发票管理 Pydantic 模型：请求/响应结构。"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class InvoiceDetailBase(BaseModel):
    biz_type: Optional[str] = None
    item: Optional[str] = None
    qty: Decimal = Decimal(1)
    amount: Decimal = Decimal(0)
    tax_rate: Decimal = Decimal(0)
    tax: Decimal = Decimal(0)
    total: Decimal = Decimal(0)


class InvoiceDetailCreate(InvoiceDetailBase):
    pass


class InvoiceDetailRead(InvoiceDetailBase):
    id: int
    invoice_id: int
    model_config = ConfigDict(from_attributes=True)


class InvoiceBase(BaseModel):
    invoice_type: str = "增值税专用发票"
    code: Optional[str] = None
    no: str
    invoice_date: Optional[date] = None
    buyer_name: Optional[str] = None
    buyer_tax_no: Optional[str] = None
    seller_name: str
    seller_tax_no: Optional[str] = None
    seller_address_phone: Optional[str] = None
    seller_bank_account: Optional[str] = None
    account: Optional[str] = None
    certify: str = "none"
    remark: Optional[str] = None
    reimbursement_bill_id: Optional[int] = None
    attachment_path: Optional[str] = None
    route_info: Optional[str] = None
    traveler: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    details: List[InvoiceDetailCreate] = []


class InvoiceUpdate(BaseModel):
    invoice_type: Optional[str] = None
    code: Optional[str] = None
    no: Optional[str] = None
    invoice_date: Optional[date] = None
    buyer_name: Optional[str] = None
    buyer_tax_no: Optional[str] = None
    seller_name: Optional[str] = None
    seller_tax_no: Optional[str] = None
    seller_address_phone: Optional[str] = None
    seller_bank_account: Optional[str] = None
    account: Optional[str] = None
    certify: Optional[str] = None
    remark: Optional[str] = None
    reimbursement_bill_id: Optional[int] = None
    attachment_path: Optional[str] = None
    route_info: Optional[str] = None
    traveler: Optional[str] = None
    details: Optional[List[InvoiceDetailCreate]] = None


class InvoiceRead(InvoiceBase):
    id: int
    created_at: datetime
    details: List[InvoiceDetailRead] = []
    model_config = ConfigDict(from_attributes=True)
