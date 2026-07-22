"""采购管理 ORM 模型：采购申请单。

前置审批流：申请人提交采购需求，经审批后执行采购。
字段与报销单保持同类命名习惯（applicant/department/status/审批字段），
便于后续统一流程看板。
"""
from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class PurchaseRequisition(Base):
    """采购申请单：采购前的前置审批单据。"""

    __tablename__ = "purchase_requisitions"

    id: Mapped[int] = mapped_column(primary_key=True)
    req_no: Mapped[Optional[str]] = mapped_column(String(50), unique=True)  # 单号：CG + 年 + 序号
    applicant: Mapped[str] = mapped_column(String(100), nullable=False)  # 申请人
    department: Mapped[Optional[str]] = mapped_column(String(100))  # 部门
    item_name: Mapped[str] = mapped_column(String(200), nullable=False)  # 采购物品 / 事项（首项，便于列表展示）
    spec: Mapped[Optional[str]] = mapped_column(String(200))  # 规格 / 型号
    quantity: Mapped[int] = mapped_column(Integer, default=1)  # 数量（首项，兼容旧单）
    expected_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))  # 预计总金额（元）= 明细金额合计
    supplier: Mapped[Optional[str]] = mapped_column(String(200))  # 建议供应商（首项）
    expected_date: Mapped[Optional[date]] = mapped_column(Date)  # 预计采购日期
    reason: Mapped[Optional[str]] = mapped_column(Text)  # 采购事由
    status: Mapped[str] = mapped_column(String(20), default="草稿")  # 草稿/待审批/已通过/已驳回
    submit_date: Mapped[Optional[date]] = mapped_column(Date)  # 提交日期
    approver: Mapped[Optional[str]] = mapped_column(String(100))  # 审批人
    approve_date: Mapped[Optional[date]] = mapped_column(Date)  # 审批日期
    approve_remark: Mapped[Optional[str]] = mapped_column(Text)  # 审批意见
    is_rd_project: Mapped[Optional[str]] = mapped_column(String(10))  # 是否归属研发项目：是/否
    rd_project_code: Mapped[Optional[str]] = mapped_column(String(100))  # 研发项目编码
    remark: Mapped[Optional[str]] = mapped_column(Text)  # 备注

    items: Mapped[List["PurchaseRequisitionItem"]] = relationship(
        "PurchaseRequisitionItem",
        back_populates="req",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class PurchaseRequisitionItem(Base):
    """采购申请明细：一条申请可包含多个物品 / 服务。"""

    __tablename__ = "purchase_requisition_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    req_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_requisitions.id", ondelete="CASCADE"), index=True
    )
    item_name: Mapped[str] = mapped_column(String(200), nullable=False)  # 物品 / 服务名称
    spec: Mapped[Optional[str]] = mapped_column(String(200))  # 规格 / 型号
    quantity: Mapped[int] = mapped_column(Integer, default=1)  # 数量
    unit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), default=0)  # 单价（元）
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), default=0)  # 金额 = 数量 × 单价
    supplier: Mapped[Optional[str]] = mapped_column(String(200))  # 建议供应商
    remark: Mapped[Optional[str]] = mapped_column(Text)  # 备注

    req: Mapped["PurchaseRequisition"] = relationship(
        "PurchaseRequisition", back_populates="items"
    )
