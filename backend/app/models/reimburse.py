"""报销管理 ORM 模型：报销单。"""
from datetime import date
from decimal import Decimal
from typing import Optional

from typing import List

from sqlalchemy import Date, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ReimbursementBill(Base):
    """报销单：申请人提交费用，经审批后支付。"""

    __tablename__ = "reimbursement_bills"
    id: Mapped[int] = mapped_column(primary_key=True)
    bill_no: Mapped[Optional[str]] = mapped_column(String(50), unique=True)  # 单号：BX + 日期 + 自增序号
    applicant: Mapped[str] = mapped_column(String(100), nullable=False)  # 申请人
    department: Mapped[Optional[str]] = mapped_column(String(100))  # 部门
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))  # 报销金额
    reason: Mapped[Optional[str]] = mapped_column(Text)  # 事由
    status: Mapped[str] = mapped_column(String(20), default="草稿")  # 草稿/待审批/已通过/已驳回/已支付
    submit_date: Mapped[Optional[date]] = mapped_column(Date)  # 提交日期
    approve_date: Mapped[Optional[date]] = mapped_column(Date)  # 审批日期
    approver: Mapped[Optional[str]] = mapped_column(String(100))  # 审批人
    approve_remark: Mapped[Optional[str]] = mapped_column(Text)  # 审批意见
    attachment_path: Mapped[Optional[str]] = mapped_column(String(500))  # 附件路径
    remark: Mapped[Optional[str]] = mapped_column(Text)  # 备注

    # 报销类型与差旅专属字段：采购报销无需填写差旅字段，差旅报销填写出差人/地点/起止
    bill_type: Mapped[str] = mapped_column(
        String(20), default="采购报销"
    )  # 报销类型：采购报销 / 差旅报销
    traveler: Mapped[Optional[str]] = mapped_column(String(100))  # 出差人
    travel_destination: Mapped[Optional[str]] = mapped_column(String(200))  # 出差地点
    travel_start: Mapped[Optional[date]] = mapped_column(Date)  # 出差起始日期
    travel_end: Mapped[Optional[date]] = mapped_column(Date)  # 出差结束日期

    invoices: Mapped[List["Invoice"]] = relationship(
        "Invoice",
        back_populates="bill",
        lazy="selectin",
    )
