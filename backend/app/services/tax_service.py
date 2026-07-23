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
from app.models import salary as sm
from app.models import contract as cm

INPUT_TAX_CODE = "2221.01.01"  # 应交税费—应交增值税—进项税额
OUTPUT_TAX_CODE = "2221.01.02"  # 应交税费—应交增值税—销项税额

STAMP_RATE = 0.0003  # 买卖合同印花税税率 0.03%（2022-07-01 起，购销合同并入「买卖合同」）


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


# ---------------------------------------------------------------------------
# 个税申报 / 印花税 / 税务工作台 取数
# ---------------------------------------------------------------------------

def _party_name(db: Session, party_id: Optional[int]) -> Optional[str]:
    """往来单位名称（合同对方）。"""
    if not party_id:
        return None
    p = db.get(cm.Parties, party_id)
    return p.name if p else None


def individual_tax(db: Session, period: Optional[str] = None) -> dict:
    """个税申报：按员工 × 期间聚合工资单的个人所得税。

    数据来源：salary_bills（仅统计 已通过/已发放 的工资单，草稿/待审批不计）。
    每个员工每月一行，含应发/社保个人/公积金个人/个税。
    """
    stmt = (
        select(
            sm.SalaryBill.employee_name,
            sm.SalaryBill.employee_no,
            sm.SalaryBill.department,
            sm.SalaryBill.period,
            func.coalesce(func.sum(sm.SalaryBill.gross_pay), 0.0),
            func.coalesce(func.sum(sm.SalaryBill.social_personal), 0.0),
            func.coalesce(func.sum(sm.SalaryBill.fund_personal), 0.0),
            func.coalesce(func.sum(sm.SalaryBill.tax_personal), 0.0),
            func.count(sm.SalaryBill.id),
        )
        .where(sm.SalaryBill.status.in_(["已通过", "已发放"]))
    )
    if period:
        stmt = stmt.where(sm.SalaryBill.period == period)
    stmt = stmt.group_by(
        sm.SalaryBill.employee_name,
        sm.SalaryBill.employee_no,
        sm.SalaryBill.department,
        sm.SalaryBill.period,
    ).order_by(sm.SalaryBill.period, sm.SalaryBill.employee_name)
    rows = db.execute(stmt).all()

    out: List[dict] = []
    total_tax = 0.0
    total_gross = 0.0
    for r in rows:
        gross = float(r[4] or 0)
        tax = float(r[7] or 0)
        total_tax += tax
        total_gross += gross
        out.append(
            {
                "employee_name": r[0],
                "employee_no": r[1],
                "department": r[2],
                "period": r[3],
                "gross_pay": round(gross, 2),
                "social_personal": round(float(r[5] or 0), 2),
                "fund_personal": round(float(r[6] or 0), 2),
                "tax_personal": round(tax, 2),
            }
        )
    return {
        "period": period,
        "rows": out,
        "total_tax": round(total_tax, 2),
        "total_gross": round(total_gross, 2),
        "headcount": len(out),
    }


def stamp_tax(db: Session, year: Optional[str] = None) -> dict:
    """印花税：买卖合同（销售合同 + 采购合同）按金额 0.03% 计征。

    - 劳动合同（HRContract）依法免征印花税，已排除。
    - 仅统计 执行中/已完成 的合同。
    - 资金账簿（实收资本/资本公积）印花税暂未纳入，后续可扩展。
    """
    rows: List[dict] = []
    total_amount = 0.0
    total_tax = 0.0

    # 销售合同
    sales = (
        db.execute(
            select(cm.SalesContract).where(
                cm.SalesContract.status.in_(["执行中", "已完成"])
            )
        )
        .scalars()
        .all()
    )
    for c in sales:
        amt = float(c.amount or 0)
        tax = round(amt * STAMP_RATE, 2)
        total_amount += amt
        total_tax += tax
        rows.append(
            {
                "contract_no": c.contract_no or f"XS{c.id}",
                "party": _party_name(db, c.customer_id),
                "type": "销售合同",
                "sign_date": c.sign_date.isoformat() if c.sign_date else "",
                "amount": round(amt, 2),
                "rate": STAMP_RATE,
                "tax": tax,
            }
        )

    # 采购合同
    purchases = (
        db.execute(
            select(cm.PurchaseContract).where(
                cm.PurchaseContract.status.in_(["执行中", "已完成"])
            )
        )
        .scalars()
        .all()
    )
    for c in purchases:
        amt = float(c.amount or 0)
        tax = round(amt * STAMP_RATE, 2)
        total_amount += amt
        total_tax += tax
        rows.append(
            {
                "contract_no": c.contract_no or f"CG{c.id}",
                "party": _party_name(db, c.supplier_id),
                "type": "采购合同",
                "sign_date": c.sign_date.isoformat() if c.sign_date else "",
                "amount": round(amt, 2),
                "rate": STAMP_RATE,
                "tax": tax,
            }
        )

    # 按签约日期排序（空日期排末尾）
    rows.sort(key=lambda x: x["sign_date"] or "9999")

    # 年度过滤（仅前端想看某年时）
    if year:
        rows = [r for r in rows if r["sign_date"][:4] == year]

    return {
        "year": year,
        "rows": rows,
        "total_amount": round(total_amount, 2),
        "total_tax": round(total_tax, 2),
        "contract_count": len(rows),
    }


def tax_workbench(db: Session, period: Optional[str] = None) -> dict:
    """税务工作台：聚合增值税 + 个税 + 印花税 的当期/累计概览。"""
    vat = tax_summary(db, period)
    ind = individual_tax(db, period)
    stamp = stamp_tax(db)  # 印花税按全部有效合同累计
    return {
        "period": period,
        "vat": {
            "input_tax": vat["input_tax"],
            "output_tax": vat["output_tax"],
            "vat_payable": vat["vat_payable"],
            "carryforward": vat["carryforward"],
        },
        "individual": {
            "total_tax": ind["total_tax"],
            "total_gross": ind["total_gross"],
            "headcount": ind["headcount"],
        },
        "stamp": {
            "total_tax": stamp["total_tax"],
            "total_amount": stamp["total_amount"],
            "contract_count": stamp["contract_count"],
        },
    }
