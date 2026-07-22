"""会计核算核心：记账凭证（头 + 分录）。

设计要点：
- Voucher（凭证头）：一张凭证 = 一次会计分录，含凭证字/号/日期/期间/制单人/来源。
- VoucherEntry（凭证分录）：借贷方明细，借/贷 + 科目 + 金额；一张凭证多行。
- 来源（source_type/source_no）把凭证与其触发的业务单（报销单/采购申请）关联，
  既支撑「业务单审批通过 → 自动生成凭证」的联动，也用于幂等去重。
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, Date, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Voucher(Base):
    """记账凭证（头）。"""

    __tablename__ = "vouchers"

    id: Mapped[int] = mapped_column(primary_key=True)
    voucher_no: Mapped[str] = mapped_column(String(50), unique=True, index=True)  # 凭证号：记-2026-07-0001
    voucher_date: Mapped[Optional[date]] = mapped_column(Date, default=date.today)  # 凭证日期（避开 datetime.date 类型名，防注解名冲突）
    period: Mapped[str] = mapped_column(String(7), index=True)  # 会计期间：2026-07
    voucher_word: Mapped[str] = mapped_column(String(10), default="记")  # 凭证字：记/收/付/转
    seq: Mapped[int] = mapped_column(Integer, default=0)  # 凭证序号（凭证号末段）
    attach_count: Mapped[int] = mapped_column(Integer, default=0)  # 附单据数
    maker: Mapped[Optional[str]] = mapped_column(String(100))  # 制单人
    status: Mapped[str] = mapped_column(String(20), default="未审核")  # 未审核/已审核/已记账
    source_type: Mapped[Optional[str]] = mapped_column(String(30), index=True)  # 来源业务：报销单/采购申请
    source_no: Mapped[Optional[str]] = mapped_column(String(50), index=True)  # 来源单号
    summary: Mapped[Optional[str]] = mapped_column(Text)  # 凭证头摘要
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    entries: Mapped[List["VoucherEntry"]] = relationship(
        "VoucherEntry",
        back_populates="voucher",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class VoucherEntry(Base):
    """记账凭证分录（行）。"""

    __tablename__ = "voucher_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    voucher_id: Mapped[int] = mapped_column(ForeignKey("vouchers.id"), index=True)
    seq: Mapped[int] = mapped_column(Integer, default=1)  # 分录序号
    subject_code: Mapped[str] = mapped_column(String(20), index=True)
    subject_name: Mapped[str] = mapped_column(String(100))
    summary: Mapped[Optional[str]] = mapped_column(Text)  # 分录摘要
    direction: Mapped[str] = mapped_column(String(4))  # 借/贷
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))

    voucher: Mapped["Voucher"] = relationship(back_populates="entries")
