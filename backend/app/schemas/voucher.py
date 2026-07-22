"""记账凭证 Pydantic 模型。"""
from typing import List, Optional

from pydantic import BaseModel


class VoucherEntryRead(BaseModel):
    seq: int
    subject_code: str
    subject_name: str
    summary: Optional[str] = None
    direction: str   # 借/贷
    amount: float


class VoucherRead(BaseModel):
    id: int
    voucher_no: str
    date: str           # ISO 日期字符串
    period: str          # 会计期间：2026-07
    voucher_word: str    # 凭证字：记/收/付/转
    seq: int             # 凭证序号（凭证号末段）
    attach_count: int
    maker: Optional[str] = None
    status: str          # 未审核/已审核/已记账
    source_type: Optional[str] = None
    source_no: Optional[str] = None
    summary: Optional[str] = None
    entries: List[VoucherEntryRead] = []


class VoucherGenerateResult(BaseModel):
    """批量从已通过业务单补生成凭证的结果。"""

    generated: int
    skipped: int
    detail: List[str] = []
