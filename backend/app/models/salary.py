"""工资管理 ORM 模型：工资单（薪资发放）。"""
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class SalaryBill(Base):
    """工资单：记录某员工某月工资明细，经审核后发放并联动生成凭证。

    派生字段（应发/代扣/实发）由组件字段实时计算后存储，
    作为凭证联动与报表取数的唯一来源，避免前后端口径不一致。
    """

    __tablename__ = "salary_bills"
    id: Mapped[int] = mapped_column(primary_key=True)
    salary_no: Mapped[Optional[str]] = mapped_column(String(50), unique=True)  # 单号：GZ + 年 + 4位序号
    employee_name: Mapped[str] = mapped_column(String(100), nullable=False)  # 员工姓名
    employee_no: Mapped[Optional[str]] = mapped_column(String(50))  # 关联员工工号（可选）
    department: Mapped[Optional[str]] = mapped_column(String(100))  # 部门
    period: Mapped[str] = mapped_column(String(7))  # 工资所属月份 YYYY-MM

    # 应发组件
    base_salary: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))  # 基本工资
    performance: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))  # 绩效
    overtime: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))  # 加班
    bonus: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))  # 奖金/补贴

    # 派生：应发 = 基本 + 绩效 + 加班 + 奖金
    gross_pay: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))

    # 代扣组件（个人部分）
    social_personal: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))  # 社保个人
    fund_personal: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))  # 公积金个人
    tax_personal: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))  # 个人所得税

    # 派生：代扣 = 社保 + 公积金 + 个税；实发 = 应发 - 代扣
    deduct_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    net_pay: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))

    status: Mapped[str] = mapped_column(String(20), default="草稿")  # 草稿/待审批/已通过/已驳回/已发放
    submit_date: Mapped[Optional[date]] = mapped_column(Date)
    approve_date: Mapped[Optional[date]] = mapped_column(Date)
    pay_date: Mapped[Optional[date]] = mapped_column(Date)
    approver: Mapped[Optional[str]] = mapped_column(String(100))
    payee: Mapped[Optional[str]] = mapped_column(String(100))
    approve_remark: Mapped[Optional[str]] = mapped_column(Text)
    pay_remark: Mapped[Optional[str]] = mapped_column(Text)
    remark: Mapped[Optional[str]] = mapped_column(Text)
