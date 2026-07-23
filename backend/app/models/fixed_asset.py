"""固定资产 ORM 模型：资产卡片 + 折旧记录。

设计要点（延续「业务单 → 凭证」联动地基）：
- FixedAsset：资产卡片（原值 / 残值率 / 使用年限 / 累计折旧 / 状态）。
  派生量（月折旧额、净值）由 service 实时计算，不冗余存储，保证单一来源。
- DepRecord：每月计提折旧的明细（期间 / 金额 / 关联凭证号），用于回溯与幂等判定。
"""
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class FixedAsset(Base):
    """固定资产卡片：记录一项资产的入账价值与折旧进度。

    状态机：未入账 → 在用（入账后）/ 闲置 → 已处置。
    累计折旧随每月计提递增，净值 = 原值 − 累计折旧。
    """

    __tablename__ = "fixed_assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_no: Mapped[Optional[str]] = mapped_column(String(50), unique=True)  # 单号：ZC + 年 + 4位序号
    name: Mapped[str] = mapped_column(String(200), nullable=False)  # 资产名称
    category: Mapped[Optional[str]] = mapped_column(String(50), default="办公设备")  # 类别
    department: Mapped[Optional[str]] = mapped_column(String(100))  # 使用部门
    acquisition_date: Mapped[Optional[date]] = mapped_column(Date)  # 购入/入账日期

    original_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))  # 原值
    salvage_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2), default=Decimal("5.00")
    )  # 残值率（%）
    useful_life: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 1), default=Decimal("5.0")
    )  # 使用年限（年）

    # 折旧费用计入科目（默认 管理费用 5602；研发设备可改 研发支出 4301）
    dep_subject_code: Mapped[Optional[str]] = mapped_column(String(20), default="5602")

    accum_dep: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), default=Decimal("0")
    )  # 累计折旧

    status: Mapped[str] = mapped_column(String(20), default="未入账")  # 未入账/在用/闲置/已处置
    record_date: Mapped[Optional[date]] = mapped_column(Date)  # 入账日期
    record_voucher_no: Mapped[Optional[str]] = mapped_column(String(50))  # 入账凭证号
    dispose_date: Mapped[Optional[date]] = mapped_column(Date)  # 处置日期
    dispose_voucher_no: Mapped[Optional[str]] = mapped_column(String(50))  # 处置凭证号
    remark: Mapped[Optional[str]] = mapped_column(Text)


class DepRecord(Base):
    """折旧记录：某资产某月的计提明细，便于回溯与幂等判定。"""

    __tablename__ = "dep_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("fixed_assets.id"))
    period: Mapped[str] = mapped_column(String(7))  # YYYY-MM
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))  # 当月折旧额
    voucher_no: Mapped[Optional[str]] = mapped_column(String(50))  # 折旧汇总凭证号
