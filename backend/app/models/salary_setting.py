"""工资设置 ORM 模型：全局唯一的薪资计算参数。

仅一条记录（id=1），保存社保/公积金个人缴纳比例与个税计算口径，
供工资单「按设置自动计算代扣」时作为单一数据来源，体现「业务→参数→派生」联动。
"""
from decimal import Decimal
from typing import Optional

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class SalarySetting(Base):
    """工资计算设置（全局单例，id 固定为 1）。"""

    __tablename__ = "salary_settings"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False, default=1)

    # 社保个人缴纳比例（%）：应发 × 比例 得社保个人部分
    social_personal_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), default=Decimal("10.5"))
    # 公积金个人缴纳比例（%）：应发 × 比例 得公积金个人部分
    fund_personal_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), default=Decimal("12"))
    # 个税基本减除费用（起征点），默认 5000
    tax_threshold: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), default=Decimal("5000"))
    # 个税计算方式：月度税率表 | 固定比例
    tax_method: Mapped[Optional[str]] = mapped_column(String(20), default="月度税率表")
    # 固定比例模式下的税率（%）
    tax_flat_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), default=Decimal("3"))
