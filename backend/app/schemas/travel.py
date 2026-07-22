"""差旅管理 Pydantic 模型。"""
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TravelReqBase(BaseModel):
    req_no: Optional[str] = None
    applicant: str
    department: Optional[str] = None
    traveler: Optional[str] = None
    destination: Optional[str] = None
    travel_start: Optional[date] = None
    travel_end: Optional[date] = None
    expected_amount: Optional[Decimal] = None
    reason: Optional[str] = None
    status: str = "草稿"
    submit_date: Optional[date] = None
    approver: Optional[str] = None
    approve_date: Optional[date] = None
    approve_remark: Optional[str] = None
    remark: Optional[str] = None


class TravelReqCreate(TravelReqBase):
    pass


class TravelReqUpdate(BaseModel):
    req_no: Optional[str] = None
    applicant: Optional[str] = None
    department: Optional[str] = None
    traveler: Optional[str] = None
    destination: Optional[str] = None
    travel_start: Optional[date] = None
    travel_end: Optional[date] = None
    expected_amount: Optional[Decimal] = None
    reason: Optional[str] = None
    status: Optional[str] = None
    submit_date: Optional[date] = None
    approver: Optional[str] = None
    approve_date: Optional[date] = None
    approve_remark: Optional[str] = None
    remark: Optional[str] = None


class TravelReqRead(TravelReqBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ApprovalBody(BaseModel):
    approver: str
    remark: Optional[str] = None
