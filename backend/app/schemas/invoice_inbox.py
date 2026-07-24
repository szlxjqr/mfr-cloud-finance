"""发票箱 Pydantic 模型：请求/响应结构。"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class InvoiceInboxBase(BaseModel):
    filename: str
    source: str = "upload"
    status: str = "pending"
    linked_doc_type: Optional[str] = None
    linked_doc_id: Optional[int] = None
    verify_result: Optional[str] = None
    verify_note: Optional[str] = None


class InvoiceInboxRead(InvoiceInboxBase):
    id: int
    storage_path: str
    extracted_json: Optional[str] = None
    created_at: datetime
    recognized_at: Optional[datetime] = None
    linked_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class InvoiceInboxUpdate(BaseModel):
    """人工校正：提交完整的 extracted_json（ParsedInvoice 的 JSON 字符串）。"""

    extracted_json: str


class InvoiceInboxLink(BaseModel):
    """挂接到业务单：reimburse(报销单) / purchase(采购申请)。"""

    doc_type: str  # reimburse | purchase
    doc_id: int


class InvoiceInboxVerify(BaseModel):
    """P1 查验结果登记。"""

    result: str  # real | fake | abnormal
    note: Optional[str] = None
