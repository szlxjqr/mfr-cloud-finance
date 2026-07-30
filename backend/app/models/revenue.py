"""收入 ORM 模型：销售收入。"""
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Revenue(Base):
    """收入：确认销售收入，确认后联动生成凭证并自动审核入账。

    默认银行收讫：借 银行存款(1002) / 贷 主营业务收入(5001) / 贷 销项税额(2221.01.02)。
    settle_method='应收账款' 时借方改为 应收账款(1122)。
    tax_rate=0 时不计销项税额，仅确认主营业务收入。
    """

    __tablename__ = "revenues"
    id: Mapped[int] = mapped_column(primary_key=True)
    bill_no: Mapped[Optional[str]] = mapped_column(String(50), unique=True)  # 单号：SR + 年 + 序号
    customer: Mapped[str] = mapped_column(String(100), nullable=False)  # 客户名称
    total_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))  # 价税合计（含税）
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=Decimal("0.13"))  # 增值税税率
    settle_method: Mapped[str] = mapped_column(String(20), default="银行收讫")  # 银行收讫/应收账款
    revenue_date: Mapped[Optional[date]] = mapped_column(Date)  # 收入确认日期
    status: Mapped[str] = mapped_column(String(20), default="草稿")  # 草稿/已确认
    remark: Mapped[Optional[str]] = mapped_column(Text)  # 备注
    voucher_no: Mapped[Optional[str]] = mapped_column(String(50))  # 联动生成的凭证号
