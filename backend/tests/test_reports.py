"""三大财务报表冒烟：资产=负债+权益恒等、利润净额、现金流符号正确。

特别守护 P0 H2 修复：现金流量表以「现金方方向」定流入/流出，
股东注资 100 万必须记为筹资活动现金流入(+)，而非流出(-)。

注：账簿/报表只汇总「已审核/已记账」凭证（未审核草稿不进账簿），
故本文件每个用例在断言前先把凭证审核+记账，反映真实入账行为。
"""
from app.services import financial_statement_service as fs
from app.services import voucher_service as vs


def _book(db, v):
    """审核+记账，使凭证进入账簿/报表。"""
    vs.audit_voucher(db, v.id)
    vs.post_voucher(db, v.id)


def test_balance_sheet_balanced(db, make_voucher):
    """资产 = 负债 + 权益 恒等。"""
    v1 = make_voucher(db, "2026-07", [
        ("1002", "银行存款", "借", 1000000.0),
        ("3001", "实收资本", "贷", 1000000.0),
    ])
    _book(db, v1)
    v2 = make_voucher(db, "2026-07", [
        ("1403", "原材料", "借", 1000.0),
        ("2202", "应付账款", "贷", 1000.0),
    ])
    _book(db, v2)
    bs = fs.balance_sheet(db, "2026-07")
    assert bs["balanced"] is True, bs.get("note")
    assert abs(bs["total_assets"] - (bs["total_liabilities"] + bs["total_equity"])) < 0.005


def test_income_statement_expense(db, make_voucher):
    """仅发生管理费用 → 净利润为负。"""
    v = make_voucher(db, "2026-07", [
        ("5602", "管理费用", "借", 3000.0),
        ("1002", "银行存款", "贷", 3000.0),
    ])
    _book(db, v)
    inc = fs.income_statement(db, "2026-07")
    assert inc["total_revenue_cur"] == 0.0
    assert inc["total_expense_cur"] == 3000.0
    assert inc["net_profit_cur"] == -3000.0


def test_cash_flow_equity_injection_is_financing_inflow(db, make_voucher):
    """股东注资 100 万：借银行存款/贷实收资本 → 筹资活动现金流入 +100 万。"""
    v = make_voucher(db, "2026-07", [
        ("1002", "银行存款", "借", 1000000.0),
        ("3001", "实收资本", "贷", 1000000.0),
    ])
    _book(db, v)
    cf = fs.cash_flow_statement(db, "2026-07")
    assert cf["net_financing"] == 1000000.0, "股东注资应记为筹资活动现金流入(+)，而非流出(-)"
    assert cf["net_increase"] == 1000000.0


def test_cash_flow_purchase_pay_is_operating_outflow(db, make_voucher):
    """采购付款：借应付账款/贷银行存款 → 经营活动现金流出(-)。"""
    v = make_voucher(db, "2026-07", [
        ("2202", "应付账款", "借", 1000.0),
        ("1002", "银行存款", "贷", 1000.0),
    ])
    _book(db, v)
    cf = fs.cash_flow_statement(db, "2026-07")
    assert cf["net_operating"] == -1000.0, "采购付款应记为经营活动现金流出(-)"
