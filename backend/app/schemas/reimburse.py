"""报销管理 Pydantic 模型。"""
from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.invoice import InvoiceRead


class ReimbursementBillBase(BaseModel):
    bill_no: Optional[str] = None
    applicant: str
    department: Optional[str] = None
    amount: Optional[Decimal] = None
    reason: Optional[str] = None
    status: str = "草稿"
    submit_date: Optional[date] = None
    approve_date: Optional[date] = None
    approver: Optional[str] = None
    approve_remark: Optional[str] = None
    attachment_path: Optional[str] = None
    remark: Optional[str] = None
    bill_type: str = "采购报销"
    traveler: Optional[str] = None
    travel_destination: Optional[str] = None
    travel_start: Optional[date] = None
    travel_end: Optional[date] = None


class ReimbursementBillCreate(ReimbursementBillBase):
    pass


class ReimbursementBillUpdate(BaseModel):
    bill_no: Optional[str] = None
    applicant: Optional[str] = None
    department: Optional[str] = None
    amount: Optional[Decimal] = None
    reason: Optional[str] = None
    status: Optional[str] = None
    submit_date: Optional[date] = None
    approve_date: Optional[date] = None
    approver: Optional[str] = None
    approve_remark: Optional[str] = None
    attachment_path: Optional[str] = None
    remark: Optional[str] = None
    bill_type: Optional[str] = None
    traveler: Optional[str] = None
    travel_destination: Optional[str] = None
    travel_start: Optional[date] = None
    travel_end: Optional[date] = None


class ReimbursementBillRead(ReimbursementBillBase):
    id: int
    invoices: List[InvoiceRead] = []
    model_config = ConfigDict(from_attributes=True)


class ApprovalBody(BaseModel):
    approver: str
    remark: Optional[str] = None
