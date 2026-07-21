"""发票管理 ORM 模型：发票（头）与发票明细（行）。

设计要点：
- 一张发票（Invoice）对应 0~N 条明细（InvoiceDetail），1:N。
- 发票头存销售方/购买方/结算科目/认证状态/关联报销单等；
- 明细行存业务类型/项目/数量/金额/税率/税额/价税合计。
- reimbursement_bill_id 外键指向报销单：一张发票可被挂到某张报销单上（P1 打通报销）。
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Invoice(Base):
    """发票（进项）：企业收到的增值税专用发票/普通发票等。"""

    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_type: Mapped[str] = mapped_column(String(50), default="增值税专用发票")  # 专票/普票/数电票/火车票/机票等
    code: Mapped[Optional[str]] = mapped_column(String(50))  # 发票代码（数电票已取消，可空）
    no: Mapped[str] = mapped_column(String(50), index=True)  # 发票号码
    invoice_date: Mapped[Optional[date]] = mapped_column(Date)  # 开票日期
    buyer_name: Mapped[Optional[str]] = mapped_column(String(200))  # 购买方名称
    buyer_tax_no: Mapped[Optional[str]] = mapped_column(String(30))  # 购买方纳税人识别号
    seller_name: Mapped[str] = mapped_column(String(200), index=True)  # 销售方名称
    seller_tax_no: Mapped[Optional[str]] = mapped_column(String(30))  # 销售方识别号
    seller_address_phone: Mapped[Optional[str]] = mapped_column(String(200))  # 地址、电话
    seller_bank_account: Mapped[Optional[str]] = mapped_column(String(200))  # 开户行及账号
    account: Mapped[Optional[str]] = mapped_column(String(50))  # 结算科目（入账科目）
    certify: Mapped[str] = mapped_column(String(10), default="none")  # 是否认证：current=本期认证 / none=暂不认证
    remark: Mapped[Optional[str]] = mapped_column(Text)  # 备注
    reimbursement_bill_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("reimbursement_bills.id"), nullable=True, index=True
    )  # 关联报销单（未报销为 NULL）
    attachment_path: Mapped[Optional[str]] = mapped_column(String(500))  # 归档附件路径（PDF/OFD）
    route_info: Mapped[Optional[str]] = mapped_column(String(100))  # 路线（火车票/机票用）
    traveler: Mapped[Optional[str]] = mapped_column(String(100))  # 旅客姓名（火车票/机票用）
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    details: Mapped[List["InvoiceDetail"]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class InvoiceDetail(Base):
    """发票明细行：一张发票可有多条商品/服务明细。"""

    __tablename__ = "invoice_details"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"))
    biz_type: Mapped[Optional[str]] = mapped_column(String(50))  # 业务类型：采购商品/接受服务/费用报销
    item: Mapped[Optional[str]] = mapped_column(String(200))  # 开票项目
    qty: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=1)  # 数量
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)  # 金额（不含税）
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)  # 税率(%)
    tax: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)  # 税额
    total: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)  # 价税合计

    invoice: Mapped["Invoice"] = relationship(back_populates="details")
