"""差旅管理 Pydantic 模型。"""
from datetime import date
from decimal import Decimal
from typing import List, Optional

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
    is_rd_project: Optional[str] = None  # 是否归属研发项目：是/否
    rd_project_code: Optional[str] = None  # 研发项目编码
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
    is_rd_project: Optional[str] = None
    rd_project_code: Optional[str] = None
    remark: Optional[str] = None


class TravelItemRead(BaseModel):
    """差旅费用细项（只读）：镜像 PurchaseItemRead。"""
    id: int
    req_id: int
    item_name: str
    amount: Optional[Decimal] = None
    sort_order: int = 0
    remark: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class TravelReqRead(TravelReqBase):
    id: int
    items: List[TravelItemRead] = []
    model_config = ConfigDict(from_attributes=True)


class ApprovalBody(BaseModel):
    approver: str
    remark: Optional[str] = None
