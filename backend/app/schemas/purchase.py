"""采购管理 Pydantic 模型。"""
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PurchaseItemBase(BaseModel):
    item_name: str
    spec: Optional[str] = None
    quantity: int = 1
    unit_price: Optional[Decimal] = None
    amount: Optional[Decimal] = None
    supplier: Optional[str] = None
    remark: Optional[str] = None


class PurchaseItemCreate(PurchaseItemBase):
    pass


class PurchaseItemRead(PurchaseItemBase):
    id: int
    req_id: int
    model_config = ConfigDict(from_attributes=True)


class PurchaseReqBase(BaseModel):
    req_no: Optional[str] = None
    applicant: str
    department: Optional[str] = None
    item_name: str
    spec: Optional[str] = None
    quantity: int = 1
    expected_amount: Optional[Decimal] = None
    supplier: Optional[str] = None
    expected_date: Optional[date] = None
    reason: Optional[str] = None
    status: str = "草稿"
    submit_date: Optional[date] = None
    approver: Optional[str] = None
    approve_date: Optional[date] = None
    approve_remark: Optional[str] = None
    is_rd_project: Optional[str] = None  # 是否归属研发项目：是/否
    rd_project_code: Optional[str] = None  # 研发项目编码
    remark: Optional[str] = None
    items: list[PurchaseItemCreate] = []


class PurchaseReqCreate(PurchaseReqBase):
    pass


class PurchaseReqUpdate(BaseModel):
    req_no: Optional[str] = None
    applicant: Optional[str] = None
    department: Optional[str] = None
    item_name: Optional[str] = None
    spec: Optional[str] = None
    quantity: Optional[int] = None
    expected_amount: Optional[Decimal] = None
    supplier: Optional[str] = None
    expected_date: Optional[date] = None
    reason: Optional[str] = None
    status: Optional[str] = None
    submit_date: Optional[date] = None
    approver: Optional[str] = None
    approve_date: Optional[date] = None
    approve_remark: Optional[str] = None
    is_rd_project: Optional[str] = None
    rd_project_code: Optional[str] = None
    remark: Optional[str] = None
    items: Optional[list[PurchaseItemCreate]] = None


class PurchaseReqRead(PurchaseReqBase):
    id: int
    items: list[PurchaseItemRead] = []
    model_config = ConfigDict(from_attributes=True)


class ApprovalBody(BaseModel):
    approver: str
    remark: Optional[str] = None
