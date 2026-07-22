"""差旅管理 ORM 模型：差旅申请单。

前置审批流：出差前提交差旅计划（出差人 / 地点 / 起止 / 预算），经审批后出行。
出差地点允许多地点，前端以顿号「、」、逗号「,」或空格之一分隔存储为单个字符串。
"""
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class TravelRequisition(Base):
    """差旅申请单：出差前的前置审批单据。"""

    __tablename__ = "travel_requisitions"

    id: Mapped[int] = mapped_column(primary_key=True)
    req_no: Mapped[Optional[str]] = mapped_column(String(50), unique=True)  # 单号：CL + 年 + 序号
    applicant: Mapped[str] = mapped_column(String(100), nullable=False)  # 申请人
    department: Mapped[Optional[str]] = mapped_column(String(100))  # 部门
    traveler: Mapped[Optional[str]] = mapped_column(String(100))  # 出差人（可与申请人不同）
    destination: Mapped[Optional[str]] = mapped_column(String(200))  # 出差地点（多地点用、/,/空格分隔）
    travel_start: Mapped[Optional[date]] = mapped_column(Date)  # 出差起始日期
    travel_end: Mapped[Optional[date]] = mapped_column(Date)  # 出差结束日期
    expected_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))  # 差旅预算（元）
    reason: Mapped[Optional[str]] = mapped_column(Text)  # 出差事由
    status: Mapped[str] = mapped_column(String(20), default="草稿")  # 草稿/待审批/已通过/已驳回
    submit_date: Mapped[Optional[date]] = mapped_column(Date)  # 提交日期
    approver: Mapped[Optional[str]] = mapped_column(String(100))  # 审批人
    approve_date: Mapped[Optional[date]] = mapped_column(Date)  # 审批日期
    approve_remark: Mapped[Optional[str]] = mapped_column(Text)  # 审批意见
    remark: Mapped[Optional[str]] = mapped_column(Text)  # 备注
