"""财务报表引擎：由 ledger_service.summary 实时派生三大报表 + 季报。

所有数据均来自凭证分录汇总，**不冗余存储**：
- 资产负债表：期末余额（资产/负债/权益分段）；损益类科目按「表结法」自动结转到
  「本年利润」权益项，使 资产 = 负债 + 权益 恒等。
- 利润表：损益类科目「本期发生额」与「本年累计发生额」双列。
- 现金流量表：以现金类科目（1001 库存现金 / 1002 银行存款）的凭证分录为入口，
  按对方科目类别归类 经营 / 投资 / 筹资 活动。
- 季报：选定季度内各月利润/现金流求和，资产负债表取季末月份快照。

期间以 voucher.period（YYYY-MM）为准。
"""

from typing import Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import voucher as vm
from app.models import subject as sm
from app.services import ledger_service

# ── 资产负债表项目映射（小企业会计准则简化）──
_BALANCE_ASSETS_CURRENT = ("流动资产", [
    ("1001", "库存现金"),
    ("1002", "银行存款"),
    ("1122", "应收账款"),
    ("1123", "预付账款"),
    ("1403", "原材料"),
    ("1405", "库存商品"),
    ("4001", "生产成本"),
])
_BALANCE_ASSETS_NONCURRENT = ("非流动资产", [
    ("1601", "固定资产"),
    ("4301", "研发支出"),
])
_BALANCE_LIAB_CURRENT = ("流动负债", [
    ("2202", "应付账款"),
    ("2211", "应付职工薪酬"),
    ("2221", "应交税费"),
    ("2241", "其他应付款"),
])
_BALANCE_EQUITY = ("所有者权益", [
    ("3001", "实收资本"),
    ("3103", "本年利润"),
    ("3104", "利润分配"),
])

# 损益类科目（利润表取数源）
_INCOME_REVENUE = [("5001", "主营业务收入"), ("5051", "其他业务收入")]
_INCOME_COST = [("5401", "主营业务成本")]
_INCOME_EXPENSE = [
    ("5601", "销售费用"),
    ("5602", "管理费用"),
    ("5603", "财务费用"),
    ("5801", "所得税费用"),
]
_INCOME_ALL = (
    [c for c, _ in _INCOME_REVENUE]
    + [c for c, _ in _INCOME_COST]
    + [c for c, _ in _INCOME_EXPENSE]
)

# 现金类科目（现金流量表入口）
_CASH_CODES = ("1001", "1002")


def _signed(sub: dict, f_debit: str, f_credit: str) -> float:
    """按科目正常方向，返回带符号的发生额/余额。"""
    if not sub:
        return 0.0
    d = float(sub.get(f_debit) or 0)
    c = float(sub.get(f_credit) or 0)
    if sub.get("direction") == "借":
        return d - c
    return c - d


def _ending(sub: dict) -> float:
    return _signed(sub, "ending_debit", "ending_credit")


def _period_amt(sub: dict) -> float:
    return _signed(sub, "period_debit", "period_credit")


def _cum_amt(sub: dict) -> float:
    return _signed(sub, "cum_debit", "cum_credit")


def _code_balance(subs: Dict[str, dict], code: str) -> float:
    """某科目余额：含其自身及所有子孙叶子科目（父科目常无直接分录）。"""
    total = 0.0
    for c, s in subs.items():
        if c == code or c.startswith(code + "."):
            total += _ending(s)
    return total


def _balance_items(subs: Dict[str, dict], mapping: Tuple[str, List[Tuple[str, str]]]):
    name, rows = mapping
    items = [{"code": code, "name": label, "amount": round(_code_balance(subs, code), 2)} for code, label in rows]
    total = round(sum(it["amount"] for it in items), 2)
    return {"name": name, "items": items, "total": total}


def balance_sheet(db: Session, period: Optional[str] = None) -> dict:
    """资产负债表（表结法：损益自动结转到本年利润）。"""
    subs = {r["code"]: r for r in ledger_service.summary(db, period=period)}

    assets_cur = _balance_items(subs, _BALANCE_ASSETS_CURRENT)
    assets_non = _balance_items(subs, _BALANCE_ASSETS_NONCURRENT)
    liab_cur = _balance_items(subs, _BALANCE_LIAB_CURRENT)
    equity = _balance_items(subs, _BALANCE_EQUITY)

    # 固定资产净值 = 固定资产(1601) − 累计折旧(1602)（1602 为贷方备抵）
    _accum_dep = _code_balance(subs, "1602")
    for it in assets_non["items"]:
        if it["code"] == "1601":
            it["amount"] = round(it["amount"] - _accum_dep, 2)
    assets_non["total"] = round(sum(it["amount"] for it in assets_non["items"]), 2)

    total_assets = round(assets_cur["total"] + assets_non["total"], 2)
    total_liab = liab_cur["total"]

    # 本年利润 = 权益项 3103 自身余额 + 损益类科目本年累计净额
    # （未结账时 3103=0、损益承载 YTD；已结账时相反，两者相加恒成立）
    # 注意：收入（贷正常向）累计为正、费用（借正常向）累计为正，
    # 净利润 = 收入 - 费用，故费用项需取负。
    revenue_cum = sum(_cum_amt(subs.get(c, {})) for c, _ in _INCOME_REVENUE)
    expense_cum = sum(_cum_amt(subs.get(c, {})) for c, _ in _INCOME_COST + _INCOME_EXPENSE)
    ytd_profit = round(_ending(subs.get("3103", {})) + revenue_cum - expense_cum, 2)
    # 覆盖「本年利润」行
    for it in equity["items"]:
        if it["code"] == "3103":
            it["amount"] = ytd_profit
    equity["total"] = round(sum(it["amount"] for it in equity["items"]), 2)

    total_equity = equity["total"]
    balanced = abs(total_assets - (total_liab + total_equity)) < 0.005
    note = "" if balanced else "⚠ 资产与负债+权益不平衡，请检查凭证"

    return {
        "as_of": period or "累计",
        "sections": [assets_cur, assets_non, liab_cur, equity],
        "total_assets": total_assets,
        "total_liabilities": total_liab,
        "total_equity": total_equity,
        "balanced": balanced,
        "note": note,
    }


def income_statement(db: Session, period: Optional[str] = None) -> dict:
    """利润表：本期金额 + 本年累计金额 双列。"""
    subs = {r["code"]: r for r in ledger_service.summary(db, period=period)}

    def lines(mapping):
        out = []
        for code, label in mapping:
            s = subs.get(code, {})
            out.append({
                "code": code,
                "name": label,
                "current": round(_period_amt(s), 2),
                "cumulative": round(_cum_amt(s), 2),
            })
        return out

    revenue = lines(_INCOME_REVENUE)
    cost = lines(_INCOME_COST)
    expense = lines(_INCOME_EXPENSE)

    total_rev_cur = round(sum(r["current"] for r in revenue), 2)
    total_rev_cum = round(sum(r["cumulative"] for r in revenue), 2)
    total_exp_cur = round(sum(x["current"] for x in cost + expense), 2)
    total_exp_cum = round(sum(x["cumulative"] for x in cost + expense), 2)

    op_profit_cur = round(total_rev_cur - total_exp_cur, 2)
    op_profit_cum = round(total_rev_cum - total_exp_cum, 2)
    total_profit_cur = op_profit_cur  # 无营业外收支
    total_profit_cum = op_profit_cum
    net_cur = round(total_profit_cur - _period_amt(subs.get("5801", {})), 2)
    net_cum = round(total_profit_cum - _cum_amt(subs.get("5801", {})), 2)

    return {
        "period": period or "累计",
        "revenue": revenue,
        "cost": cost,
        "expense": expense,
        "total_revenue_cur": total_rev_cur,
        "total_revenue_cum": total_rev_cum,
        "total_expense_cur": total_exp_cur,
        "total_expense_cum": total_exp_cum,
        "operating_profit_cur": op_profit_cur,
        "operating_profit_cum": op_profit_cum,
        "total_profit_cur": total_profit_cur,
        "total_profit_cum": total_profit_cum,
        "net_profit_cur": net_cur,
        "net_profit_cum": net_cum,
    }


# 流动资产（应收/预付/存货等）对应的现金收支属经营活动；
# 长期资产（固定资产等）购建属投资活动。
_CASH_FLOW_OPERATING_ASSET_CODES = {"1122", "1123", "1403", "1405"}


def _classify(category: Optional[str], code: Optional[str] = None) -> str:
    """按对方科目类别归类现金流量活动。

    - 损益 / 负债（应付、应交税费等）→ 经营
    - 权益（实收资本等）→ 筹资
    - 资产：流动资产（应收/预付/存货）→ 经营；长期资产（固定资产等）→ 投资
    - 成本（研发支出等长期资产）→ 投资
    """
    if category in ("损益", "负债"):
        return "operating"
    if category in ("权益",):
        return "financing"
    if category == "资产":
        # 固定资产等长期资产购建属投资活动；流动资产（应收/预付/存货）属经营
        return "investing" if code not in _CASH_FLOW_OPERATING_ASSET_CODES else "operating"
    if category == "成本":
        return "investing"
    return "operating"


def cash_flow_statement(db: Session, period: Optional[str] = None) -> dict:
    """现金流量表：现金类科目分录按对方科目分类。"""
    q = (
        select(
            vm.VoucherEntry.voucher_id,
            vm.VoucherEntry.subject_code,
            vm.VoucherEntry.direction,
            vm.VoucherEntry.amount,
        )
        .join(vm.Voucher, vm.Voucher.id == vm.VoucherEntry.voucher_id)
        .where(vm.VoucherEntry.subject_code.in_(_CASH_CODES))
    )
    if period:
        q = q.where(vm.Voucher.period == period)
    cash_rows = db.execute(q).all()

    cash_voucher_ids = {r[0] for r in cash_rows}
    # 取这些凭证的全部分录，用于确定「对方科目」类别
    all_rows = db.execute(
        select(
            vm.VoucherEntry.voucher_id,
            vm.VoucherEntry.subject_code,
            vm.VoucherEntry.subject_name,
            vm.VoucherEntry.direction,
            vm.VoucherEntry.amount,
            sm.AccountSubject.category,
        )
        .join(vm.Voucher, vm.Voucher.id == vm.VoucherEntry.voucher_id)
        .join(sm.AccountSubject, sm.AccountSubject.code == vm.VoucherEntry.subject_code)
        .where(vm.VoucherEntry.voucher_id.in_(cash_voucher_ids) if cash_voucher_ids else False)
    ).all() if cash_voucher_ids else []

    # 归类：逐凭证，以「现金方方向」定流入/流出，以「对方科目类别」定活动。
    # 现金方 借=流入(+)、贷=流出(-)；对方科目仅决定 经营/投资/筹资。
    by_vouch: dict = {}
    for vid, code, name, direction, amount, category in all_rows:
        by_vouch.setdefault(vid, []).append((code, name, direction, amount, category))
    buckets = {"operating": {}, "investing": {}, "financing": {}}
    has_data = False
    for vid, lines in by_vouch.items():
        cash_dir = None
        for code, name, direction, amount, category in lines:
            if code in _CASH_CODES:
                cash_dir = direction  # 取现金方方向
                break
        if cash_dir is None:
            continue
        cash_sign = 1.0 if cash_dir == "借" else -1.0
        for code, name, direction, amount, category in lines:
            if code in _CASH_CODES:
                continue  # 现金方本身，跳过
            has_data = True
            act = _classify(category, code)
            sign = cash_sign * float(amount)
            buckets[act][name] = round(buckets[act].get(name, 0.0) + sign, 2)

    def section(items: dict, label: str):
        lines_ = [{"name": k, "amount": v} for k, v in items.items()]
        return {"name": label, "items": lines_, "total": round(sum(items.values()), 2)}

    op = section(buckets["operating"], "经营活动产生的现金流量")
    inv = section(buckets["investing"], "投资活动产生的现金流量")
    fin = section(buckets["financing"], "筹资活动产生的现金流量")
    net = round(op["total"] + inv["total"] + fin["total"], 2)
    note = "" if has_data else "本期无现金类（库存现金/银行存款）凭证，现金流量表为空"

    return {
        "period": period or "累计",
        "operating": op,
        "investing": inv,
        "financing": fin,
        "net_operating": op["total"],
        "net_investing": inv["total"],
        "net_financing": fin["total"],
        "net_increase": net,
        "note": note,
    }


def _quarter_months(db: Session, year: int, quarter: int) -> List[str]:
    """返回该季度内的所有业务期间（YYYY-MM），按升序。"""
    rows = db.execute(select(vm.Voucher.period).distinct()).all()
    months = [r[0] for r in rows if r[0]]
    q_months = []
    for m in months:
        try:
            y, mo = m.split("-")
            if int(y) == year and (int(mo) - 1) // 3 + 1 == quarter:
                q_months.append(m)
        except Exception:
            continue
    return sorted(q_months)


def quarter_report(db: Session, year: int, quarter: int) -> dict:
    """季报：季度内利润/现金流求和，资产负债表取季末月份快照。"""
    months = _quarter_months(db, year, quarter)
    if not months:
        # 无数据：返回空季报（诚实占位）
        empty_bs = balance_sheet(db, None)
        empty_bs["as_of"] = f"{year}Q{quarter}（无数据）"
        return {
            "year": year,
            "quarter": quarter,
            "as_of": f"{year}Q{quarter}",
            "months": [],
            "balance_sheet": empty_bs,
            "income": income_statement(db, None),
            "cash_flow": cash_flow_statement(db, None),
            "note": "该季度无业务凭证数据",
        }

    end_month = months[-1]
    bs = balance_sheet(db, end_month)
    bs["as_of"] = f"{year}Q{quarter}（季末 {end_month}）"

    # 利润表：季度内各月本期发生额求和
    inc = income_statement(db, end_month)
    rev_acc, cost_acc, exp_acc = {}, {}, {}
    for m in months:
        s = income_statement(db, m)
        for r in s["revenue"]:
            rev_acc[r["code"]] = rev_acc.get(r["code"], {"code": r["code"], "name": r["name"], "current": 0.0, "cumulative": 0.0})
            rev_acc[r["code"]]["current"] += r["current"]
        for r in s["cost"]:
            cost_acc[r["code"]] = cost_acc.get(r["code"], {"code": r["code"], "name": r["name"], "current": 0.0, "cumulative": 0.0})
            cost_acc[r["code"]]["current"] += r["current"]
        for r in s["expense"]:
            exp_acc[r["code"]] = exp_acc.get(r["code"], {"code": r["code"], "name": r["name"], "current": 0.0, "cumulative": 0.0})
            exp_acc[r["code"]]["current"] += r["current"]
    inc["revenue"] = list(rev_acc.values())
    inc["cost"] = list(cost_acc.values())
    inc["expense"] = list(exp_acc.values())
    inc["period"] = f"{year}Q{quarter}"
    inc["total_revenue_cur"] = round(sum(r["current"] for r in inc["revenue"]), 2)
    inc["total_expense_cur"] = round(sum(x["current"] for x in inc["cost"] + inc["expense"]), 2)
    inc["operating_profit_cur"] = round(inc["total_revenue_cur"] - inc["total_expense_cur"], 2)
    inc["total_profit_cur"] = inc["operating_profit_cur"]
    inc["net_profit_cur"] = inc["total_profit_cur"]

    # 现金流量：季度内各月求和
    cf = cash_flow_statement(db, end_month)
    cf["period"] = f"{year}Q{quarter}"
    cf["note"] = "本期无现金类凭证" if cf["net_increase"] == 0 else ""

    return {
        "year": year,
        "quarter": quarter,
        "as_of": f"{year}Q{quarter}",
        "months": months,
        "balance_sheet": bs,
        "income": inc,
        "cash_flow": cf,
    }
