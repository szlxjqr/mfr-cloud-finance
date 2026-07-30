"""股东入资 ORM 模型：股东投入资本。"""
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class CapitalContribution(Base):
    """股东入资：股东投入资本，确认后联动生成凭证并自动审核入账。

    默认货币资金入资：借 银行存款(1002) / 贷 实收资本(3001)。
    receive_subject 可扩展为其他收款科目（如固定资产），但 v1 主路径为货币资金。
    """

    __tablename__ = "capital_contributions"
    id: Mapped[int] = mapped_column(primary_key=True)
    bill_no: Mapped[Optional[str]] = mapped_column(String(50), unique=True)  # 单号：RZ + 年 + 序号
    investor: Mapped[str] = mapped_column(String(100), nullable=False)  # 股东名称
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))  # 入资金额
    capital_type: Mapped[str] = mapped_column(String(20), default="货币资金")  # 货币资金/实物
    receive_subject: Mapped[str] = mapped_column(String(30), default="1002")  # 收款科目编码（默认银行存款）
    contribution_date: Mapped[Optional[date]] = mapped_column(Date)  # 入资日期
    status: Mapped[str] = mapped_column(String(20), default="草稿")  # 草稿/已确认
    remark: Mapped[Optional[str]] = mapped_column(Text)  # 备注
    voucher_no: Mapped[Optional[str]] = mapped_column(String(50))  # 联动生成的凭证号
