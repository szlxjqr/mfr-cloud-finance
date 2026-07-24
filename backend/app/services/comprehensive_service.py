"""综合报表服务：跨模块实时聚合（业务 / 财务 / 税务 / 凭证）。

所有数据均由各模块既有数据**实时汇总**，不冗余存储：
- 资金/科目余额：复用 ledger_service.summary（由 voucher_entries 实时归算）
- 税务：复用 tax_service.tax_summary（由 2221.01.01/2221.01.02 实时汇总）
- 业务概况：直接统计 报销/采购/差旅 单据状态
- 凭证概况：统计 vouchers 表

期间以 voucher.period（YYYY-MM）为准；聚合类接口默认取全部期间（累计）。
"""

from typing import Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import reimburse as rm
from app.models import purchase as pm
from app.models import travel as tm
from app.models import voucher as vm
from app.services import ledger_service, tax_service

# 资金看板关注的关键科目（code, 显示名）
_FUND_SUBJECTS = [
    ("1001", "库存现金"),
    ("1002", "银行存款"),
    ("1122", "应收账款"),
    ("2202", "应付账款"),
    ("2211", "应付职工薪酬"),
    ("2221", "应交税费"),
]


def _ending_value(row: Optional[dict]) -> float:
    """取某科目期末余额（期末借/贷仅一个非零）。"""
    if not row:
        return 0.0
    return float(row.get("ending_debit") or 0) + float(row.get("ending_credit") or 0)


def funds(db: Session) -> List[dict]:
    """资金情况：关键科目真实期末余额。

    注：应交税费(2221)为父科目，实际税额记在子科目
    （2221.01.01 进项税额/借、2221.01.02 销项税额/贷），
    故按「销项 - 进项」净额归算，负值即留抵。
    """
    subs = {r["code"]: r for r in ledger_service.summary(db)}
    out: List[dict] = []
    for code, name in _FUND_SUBJECTS:
        if code == "2221":
            inp = _ending_value(subs.get("2221.01.01"))  # 进项税额（借）
            out_ = _ending_value(subs.get("2221.01.02"))  # 销项税额（贷）
            amt = out_ - inp  # 应交增值税净额，负值=留抵
        else:
            amt = _ending_value(subs.get(code))
        out.append({"code": code, "name": name, "amount": round(amt, 2)})
    return out


def revenue_trend(db: Session) -> List[dict]:
    """主营业务收入（5001，贷）按月趋势。"""
    rows = db.execute(
        select(vm.Voucher.period, func.sum(vm.VoucherEntry.amount))
        .join(vm.VoucherEntry, vm.VoucherEntry.voucher_id == vm.Voucher.id)
        .where(vm.VoucherEntry.subject_code == "5001", vm.VoucherEntry.direction == "贷")
        .group_by(vm.Voucher.period)
        .order_by(vm.Voucher.period)
    ).all()
    return [{"period": p, "revenue": round(float(v or 0), 2)} for p, v in rows]


def _status_counts(db: Session, model) -> Dict[str, int]:
    res = db.execute(select(model.status, func.count()).group_by(model.status)).all()
    return {s: int(c) for s, c in res}


def business_summary(db: Session) -> dict:
    """报销 / 采购 / 差旅 各状态计数 + 待审批合计。"""
    r = _status_counts(db, rm.ReimbursementBill)
    p = _status_counts(db, pm.PurchaseRequisition)
    t = _status_counts(db, tm.TravelRequisition)
    pending = r.get("待审批", 0) + p.get("待审批", 0) + t.get("待审批", 0)
    return {
        "reimburse": r,
        "purchase": p,
        "travel": t,
        "pending_total": pending,
    }


def voucher_summary(db: Session, period: Optional[str] = None) -> dict:
    total = db.scalar(select(func.count()).select_from(vm.Voucher)) or 0
    period_count = 0
    if period:
        period_count = (
            db.scalar(
                select(func.count())
                .select_from(vm.Voucher)
                .where(vm.Voucher.period == period)
            )
            or 0
        )
    return {"total": total, "period": period, "period_count": period_count}


def overview(db: Session, period: Optional[str] = None) -> dict:
    """综合看板一次性聚合。"""
    tax = tax_service.tax_summary(db, period=period)
    return {
        "period": period,
        "funds": funds(db),
        "revenue_trend": revenue_trend(db),
        "tax": tax,
        "business": business_summary(db),
        "voucher": voucher_summary(db, period),
    }
