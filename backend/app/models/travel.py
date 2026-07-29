"""差旅管理 ORM 模型：差旅申请单。

前置审批流：出差前提交差旅计划（出差人 / 地点 / 起止 / 预算），经审批后出行。
出差地点允许多地点，前端以顿号「、」、逗号「,」或空格之一分隔存储为单个字符串。

差旅细项（TravelRequisitionItem）镜像采购细项（PurchaseRequisitionItem），
新建差旅申请自动生成两个默认细项：交通费、住宿费，供发票挂接。
"""
from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
    is_rd_project: Mapped[Optional[str]] = mapped_column(String(10))  # 是否归属研发项目：是/否
    rd_project_code: Mapped[Optional[str]] = mapped_column(String(100))  # 研发项目编码
    remark: Mapped[Optional[str]] = mapped_column(Text)  # 备注

    items: Mapped[List["TravelRequisitionItem"]] = relationship(
        "TravelRequisitionItem",
        back_populates="req",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class TravelRequisitionItem(Base):
    """差旅申请明细：一条差旅申请包含多个费用细项（交通费/住宿费等）。

    镜像 PurchaseRequisitionItem，但字段更简洁——差旅细项无规格/数量/单价，
    只有费用名称 + 预算金额 + 备注，供发票挂接定位。
    """

    __tablename__ = "travel_requisition_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    req_id: Mapped[int] = mapped_column(
        ForeignKey("travel_requisitions.id", ondelete="CASCADE"), index=True
    )
    item_name: Mapped[str] = mapped_column(String(200), nullable=False)  # 费用名称（交通费/住宿费等）
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), default=0)  # 预算金额（元）
    sort_order: Mapped[int] = mapped_column(Integer, default=0)  # 排序序号
    remark: Mapped[Optional[str]] = mapped_column(Text)  # 备注

    req: Mapped["TravelRequisition"] = relationship(
        "TravelRequisition", back_populates="items"
    )
