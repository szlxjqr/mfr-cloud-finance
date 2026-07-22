"""税务取数服务：从凭证分录实时汇总增值税相关数据。

数据来源：voucher_entries 关联 vouchers，按税务科目（2221.01.x）汇总。
- 进项税额：2221.01.01，正常方向为「贷」，进项抵扣记在「借」方 → 取 direction='借' 的合计
- 销项税额：2221.01.02，销售开票记在「贷」方 → 取 direction='贷' 的合计
- 应交增值税（简化）：销项税额 - 进项税额（未含进项转出/已交税金，后续可扩展）
期间以 voucher.period（YYYY-MM）为准，不冗余存储，保证与凭证始终一致。
"""
from datetime import date
from typing import Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import voucher as vm

INPUT_TAX_CODE = "2221.01.01"  # 应交税费—应交增值税—进项税额
OUTPUT_TAX_CODE = "2221.01.02"  # 应交税费—应交增值税—销项税额


def _sum(db: Session, subject_code: str, direction: str, period: Optional[str] = None) -> float:
    """某科目某方向在指定期间的金额合计。"""
    stmt = (
        select(func.coalesce(func.sum(vm.VoucherEntry.amount), 0.0))
        .select_from(vm.VoucherEntry)
        .join(vm.Voucher, vm.Voucher.id == vm.VoucherEntry.voucher_id)
        .where(
            vm.VoucherEntry.subject_code == subject_code,
            vm.VoucherEntry.direction == direction,
        )
    )
    if period:
        stmt = stmt.where(vm.Voucher.period == period)
    return float(db.scalar(stmt) or 0.0)


def input_tax(db: Session, period: Optional[str] = None) -> float:
    """进项税额（2221.01.01，借）。"""
    return _sum(db, INPUT_TAX_CODE, "借", period)


def output_tax(db: Session, period: Optional[str] = None) -> float:
    """销项税额（2221.01.02，贷）。"""
    return _sum(db, OUTPUT_TAX_CODE, "贷", period)


def vat_payable(db: Session, period: Optional[str] = None) -> float:
    """应交增值税（简化）= 销项税额 - 进项税额。负值表示留抵。"""
    return round(output_tax(db, period) - input_tax(db, period), 2)


def tax_summary(db: Session, period: Optional[str] = None) -> dict:
    """税务汇总 KPI。"""
    inp = round(input_tax(db, period), 2)
    out = round(output_tax(db, period), 2)
    vat = round(out - inp, 2)
    return {
        "period": period,
        "input_tax": inp,
        "output_tax": out,
        "vat_payable": vat,
        "carryforward": vat < 0,  # 负值=留抵（进项大于销项）
    }


def input_tax_detail(db: Session, period: Optional[str] = None) -> List[dict]:
    """进项税额明细：每笔抵扣凭证分录（关联来源业务单）。"""
    stmt = (
        select(
            vm.Voucher.voucher_no,
            vm.Voucher.voucher_date,
            vm.Voucher.period,
            vm.VoucherEntry.summary,
            vm.VoucherEntry.amount,
            vm.Voucher.source_type,
            vm.Voucher.source_no,
        )
        .select_from(vm.VoucherEntry)
        .join(vm.Voucher, vm.Voucher.id == vm.VoucherEntry.voucher_id)
        .where(
            vm.VoucherEntry.subject_code == INPUT_TAX_CODE,
            vm.VoucherEntry.direction == "借",
        )
        .order_by(vm.Voucher.voucher_date, vm.Voucher.voucher_no, vm.VoucherEntry.seq)
    )
    if period:
        stmt = stmt.where(vm.Voucher.period == period)
    rows = db.execute(stmt).all()
    return [
        {
            "voucher_no": r[0],
            "date": r[1].isoformat() if hasattr(r[1], "isoformat") else str(r[1]),
            "period": r[2],
            "summary": r[3],
            "amount": float(r[4] or 0),
            "source_type": r[5],
            "source_no": r[6],
        }
        for r in rows
    ]


def monthly_trend(db: Session, year: Optional[str] = None) -> List[dict]:
    """按期间（月份）汇总进项/销项税额，用于趋势图。返回该年 1-12 月。"""
    if not year:
        year = str(date.today().year)
    stmt = (
        select(
            vm.Voucher.period,
            vm.VoucherEntry.subject_code,
            vm.VoucherEntry.direction,
            func.sum(vm.VoucherEntry.amount),
        )
        .select_from(vm.VoucherEntry)
        .join(vm.Voucher, vm.Voucher.id == vm.VoucherEntry.voucher_id)
        .where(
            vm.VoucherEntry.subject_code.in_([INPUT_TAX_CODE, OUTPUT_TAX_CODE]),
            vm.Voucher.period.like(f"{year}-%"),
        )
        .group_by(
            vm.Voucher.period,
            vm.VoucherEntry.subject_code,
            vm.VoucherEntry.direction,
        )
    )
    rows = db.execute(stmt).all()

    agg: Dict[str, dict] = {}
    for period, code, direction, amt in rows:
        d = agg.setdefault(period, {"input": 0.0, "output": 0.0})
        if code == INPUT_TAX_CODE and direction == "借":
            d["input"] += float(amt or 0)
        elif code == OUTPUT_TAX_CODE and direction == "贷":
            d["output"] += float(amt or 0)

    out: List[dict] = []
    for m in range(1, 13):
        p = f"{year}-{m:02d}"
        d = agg.get(p, {"input": 0.0, "output": 0.0})
        out.append(
            {
                "period": p,
                "input_tax": round(d["input"], 2),
                "output_tax": round(d["output"], 2),
            }
        )
    return out
