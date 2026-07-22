"""会计核算主数据：会计科目表（联动地基的锚点）。

设计要点：
- 科目编码采用「小企业会计准则」风格（如 1001 / 2221.01.01），层级用 code 表达。
- category：资产/负债/权益/成本/损益；direction：正常余额方向（借/贷）。
- 这是「业务单 → 凭证 → 科目余额」链路的总锚点；业务映射、余额汇总都依赖它。
"""
from typing import Optional

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class AccountSubject(Base):
    """会计科目：企业会计核算的分类账户。"""

    __tablename__ = "account_subjects"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)  # 科目编码，如 2221.01.01
    name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(20), default="资产")  # 资产/负债/权益/成本/损益
    direction: Mapped[str] = mapped_column(String(4), default="借")  # 正常余额方向：借/贷
    level: Mapped[int] = mapped_column(default=1)  # 层级（1 级科目）
    parent_code: Mapped[Optional[str]] = mapped_column(String(20), index=True)  # 上级科目编码
    is_leaf: Mapped[bool] = mapped_column(Boolean, default=True)  # 是否末级（可记账）
    status: Mapped[str] = mapped_column(String(10), default="启用")  # 启用/封存
