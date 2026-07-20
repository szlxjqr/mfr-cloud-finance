"""报销管理 ORM 模型：报销单。"""
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

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
    attachment_path: Mapped[Optional[str]] = mapped_column(String(500))  # 附件路径
    remark: Mapped[Optional[str]] = mapped_column(Text)  # 备注
