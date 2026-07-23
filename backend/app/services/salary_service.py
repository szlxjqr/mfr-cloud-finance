"""工资服务：计算派生（代扣/实发）、参数设置、汇总聚合。

所有聚合均由 salary_bills 实时统计，不冗余存储，延续「业务单→派生数据」联动地基。
个税计算默认采用月度税率表（按年度综合所得税率表换算的月度速算扣除），
亦支持「固定比例」简化模式，口径由工资设置统一控制。
"""
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import salary as m
from app.models import salary_setting as sm


# ── 个税月度税率表（按年度综合所得税率表 ÷12 换算）──
# (应纳税所得额上限, 税率, 速算扣除数)
_TAX_BRACKETS = [
    (Decimal("3000"), Decimal("0.03"), Decimal("0")),
    (Decimal("12000"), Decimal("0.10"), Decimal("210")),
    (Decimal("25000"), Decimal("0.20"), Decimal("1410")),
    (Decimal("35000"), Decimal("0.25"), Decimal("2660")),
    (Decimal("55000"), Decimal("0.30"), Decimal("4410")),
    (Decimal("80000"), Decimal("0.35"), Decimal("7160")),
    (Decimal("999999999"), Decimal("0.45"), Decimal("15160")),
]


def _to_decimal(v) -> Decimal:
    if v is None or v == "":
        return Decimal("0")
    try:
        return Decimal(str(v))
    except Exception:
        return Decimal("0")


def get_settings(db: Session) -> sm.SalarySetting:
    """读取全局工资设置；不存在则写入默认单例（id=1）。"""
    obj = db.get(sm.SalarySetting, 1)
    if not obj:
        obj = sm.SalarySetting(id=1)
        db.add(obj)
        db.commit()
        db.refresh(obj)
    return obj


def save_settings(db: Session, data: dict) -> sm.SalarySetting:
    """保存（创建或更新）全局工资设置。"""
    obj = db.get(sm.SalarySetting, 1)
    if not obj:
        obj = sm.SalarySetting(id=1)
        db.add(obj)
        db.flush()
    for k in ("social_personal_rate", "fund_personal_rate", "tax_threshold", "tax_method", "tax_flat_rate"):
        if k in data:
            obj.__setattr__(k, _to_decimal(data[k]) if k != "tax_method" else data[k])
    db.commit()
    db.refresh(obj)
    return obj


def _monthly_tax(taxable: Decimal) -> Decimal:
    """按月度税率表计算个税。taxable ≤ 0 时为 0。"""
    if taxable <= 0:
        return Decimal("0")
    for upper, rate, quick in _TAX_BRACKETS:
        if taxable <= upper:
            return (taxable * rate - quick).quantize(Decimal("0.01"))
    return (taxable * _TAX_BRACKETS[-1][1] - _TAX_BRACKETS[-1][2]).quantize(Decimal("0.01"))


def compute_deductions(
    db: Session,
    base_salary: object = 0,
    performance: object = 0,
    overtime: object = 0,
    bonus: object = 0,
) -> dict:
    """依据当前工资设置，由应发组件计算社保/公积金个人部分与个税。

    返回：应发、社保个人、公积金个人、个税、代扣合计、实发。
    口径：社保/公积金个人 = 应发 × 设置比例%；个税基数 = 应发 − 社保 − 公积金 − 起征点。
    """
    st = get_settings(db)
    gross = (
        _to_decimal(base_salary)
        + _to_decimal(performance)
        + _to_decimal(overtime)
        + _to_decimal(bonus)
    ).quantize(Decimal("0.01"))

    social_rate = _to_decimal(st.social_personal_rate) / Decimal("100")
    fund_rate = _to_decimal(st.fund_personal_rate) / Decimal("100")
    social = (gross * social_rate).quantize(Decimal("0.01"))
    fund = (gross * fund_rate).quantize(Decimal("0.01"))

    threshold = _to_decimal(st.tax_threshold)
    taxable = (gross - social - fund - threshold).quantize(Decimal("0.01"))

    if st.tax_method == "固定比例":
        rate = _to_decimal(st.tax_flat_rate) / Decimal("100")
        tax = (taxable * rate).quantize(Decimal("0.01")) if taxable > 0 else Decimal("0")
    else:
        tax = _monthly_tax(taxable)

    deduct = (social + fund + tax).quantize(Decimal("0.01"))
    net = (gross - deduct).quantize(Decimal("0.01"))
    return {
        "gross_pay": float(gross),
        "social_personal": float(social),
        "fund_personal": float(fund),
        "tax_personal": float(tax),
        "deduct_total": float(deduct),
        "net_pay": float(net),
    }


# ================= 汇总聚合 =================
def dept_summary(db: Session, period: Optional[str] = None, status: Optional[str] = None) -> List[dict]:
    """按 (部门, 工资月份) 聚合应发/代扣/实发/人数。

    部门为空记为「未分配」。期以 period（YYYY-MM）为准。
    """
    stmt = select(
        func.coalesce(m.SalaryBill.department, "未分配").label("department"),
        m.SalaryBill.period,
        func.count().label("headcount"),
        func.coalesce(func.sum(m.SalaryBill.gross_pay), 0).label("gross_total"),
        func.coalesce(func.sum(m.SalaryBill.social_personal), 0).label("social_total"),
        func.coalesce(func.sum(m.SalaryBill.fund_personal), 0).label("fund_total"),
        func.coalesce(func.sum(m.SalaryBill.tax_personal), 0).label("tax_total"),
        func.coalesce(func.sum(m.SalaryBill.deduct_total), 0).label("deduct_total"),
        func.coalesce(func.sum(m.SalaryBill.net_pay), 0).label("net_total"),
    ).group_by(
        func.coalesce(m.SalaryBill.department, "未分配"),
        m.SalaryBill.period,
    )
    if period:
        stmt = stmt.where(m.SalaryBill.period == period)
    if status:
        stmt = stmt.where(m.SalaryBill.status == status)
    stmt = stmt.order_by(
        func.coalesce(m.SalaryBill.department, "未分配"),
        m.SalaryBill.period,
    )
    rows = db.execute(stmt).all()
    return [
        {
            "department": r.department,
            "period": r.period,
            "headcount": int(r.headcount),
            "gross_total": round(float(r.gross_total), 2),
            "social_total": round(float(r.social_total), 2),
            "fund_total": round(float(r.fund_total), 2),
            "tax_total": round(float(r.tax_total), 2),
            "deduct_total": round(float(r.deduct_total), 2),
            "net_total": round(float(r.net_total), 2),
        }
        for r in rows
    ]


def tax_report(db: Session, period: Optional[str] = None, employee_name: Optional[str] = None) -> List[dict]:
    """按 (员工, 部门, 工资月份) 聚合个税与应发，便于个税申报核对。

    排序：个税降序。
    """
    stmt = select(
        m.SalaryBill.employee_name,
        func.coalesce(m.SalaryBill.department, "未分配").label("department"),
        m.SalaryBill.period,
        func.count().label("headcount"),
        func.coalesce(func.sum(m.SalaryBill.gross_pay), 0).label("gross_total"),
        func.coalesce(func.sum(m.SalaryBill.social_personal), 0).label("social_total"),
        func.coalesce(func.sum(m.SalaryBill.fund_personal), 0).label("fund_total"),
        func.coalesce(func.sum(m.SalaryBill.tax_personal), 0).label("tax_total"),
        func.coalesce(func.sum(m.SalaryBill.deduct_total), 0).label("deduct_total"),
        func.coalesce(func.sum(m.SalaryBill.net_pay), 0).label("net_total"),
    ).group_by(
        m.SalaryBill.employee_name,
        func.coalesce(m.SalaryBill.department, "未分配"),
        m.SalaryBill.period,
    )
    if period:
        stmt = stmt.where(m.SalaryBill.period == period)
    if employee_name:
        stmt = stmt.where(m.SalaryBill.employee_name == employee_name)
    rows = db.execute(stmt).all()
    out = [
        {
            "employee_name": r.employee_name,
            "department": r.department,
            "period": r.period,
            "headcount": int(r.headcount),
            "gross_total": round(float(r.gross_total), 2),
            "social_total": round(float(r.social_total), 2),
            "fund_total": round(float(r.fund_total), 2),
            "tax_total": round(float(r.tax_total), 2),
            "deduct_total": round(float(r.deduct_total), 2),
            "net_total": round(float(r.net_total), 2),
        }
        for r in rows
    ]
    out.sort(key=lambda x: x["tax_total"], reverse=True)
    return out
