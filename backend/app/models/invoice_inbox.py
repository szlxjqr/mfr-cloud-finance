"""发票箱 ORM 模型：发票收口/暂存区（与正式 invoices 表分离）。

设计要点：
- 发票箱是"入口/暂存"：上传即浏览器解析（OCR/PDF 已在前端 invoiceParser 完成），
  原文件存盘、提取字段以 JSON 存本表；确认挂接后才生成正式 Invoice 记录（落入 invoices 表）。
- status：pending(待识别) / recognized(已识别) / reviewed(已复核) / needs_review(待复核) / linked(已挂接) / error。
- linked_doc_type：reimburse(报销单) / purchase(采购申请) / null。
- verify_result（P1 查验）：none / real / fake / abnormal。
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class InvoiceInbox(Base):
    """发票箱：一张上传/收集到的发票（暂存态）。"""

    __tablename__ = "invoice_inbox"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))  # 原始文件名
    storage_path: Mapped[str] = mapped_column(String(500))  # 原文件存盘路径
    source: Mapped[str] = mapped_column(String(10), default="upload")  # upload(直接上传) / box(箱收集)
    extracted_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # ParsedInvoice 的 JSON 字符串
    status: Mapped[str] = mapped_column(String(10), default="pending")  # pending/recognized/linked/error
    linked_doc_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # reimburse/purchase
    linked_doc_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    verify_result: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # none/real/fake/abnormal（P1）
    verify_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    recognized_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    linked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
