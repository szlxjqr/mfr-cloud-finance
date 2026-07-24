"""三大财务报表冒烟：资产=负债+权益恒等、利润净额、现金流符号正确。

特别守护 P0 H2 修复：现金流量表以「现金方方向」定流入/流出，
股东注资 100 万必须记为筹资活动现金流入(+)，而非流出(-)。
"""
from app.services import financial_statement_service as fs


def test_balance_sheet_balanced(db, make_voucher):
    """资产 = 负债 + 权益 恒等。"""
    make_voucher(db, "2026-07", [
        ("1002", "银行存款", "借", 1000000.0),
        ("3001", "实收资本", "贷", 1000000.0),
    ])
    make_voucher(db, "2026-07", [
        ("1403", "原材料", "借", 1000.0),
        ("2202", "应付账款", "贷", 1000.0),
    ])
    bs = fs.balance_sheet(db, "2026-07")
    assert bs["balanced"] is True, bs.get("note")
    assert abs(bs["total_assets"] - (bs["total_liabilities"] + bs["total_equity"])) < 0.005


def test_income_statement_expense(db, make_voucher):
    """仅发生管理费用 → 净利润为负。"""
    make_voucher(db, "2026-07", [
        ("5602", "管理费用", "借", 3000.0),
        ("1002", "银行存款", "贷", 3000.0),
    ])
    inc = fs.income_statement(db, "2026-07")
    assert inc["total_revenue_cur"] == 0.0
    assert inc["total_expense_cur"] == 3000.0
    assert inc["net_profit_cur"] == -3000.0


def test_cash_flow_equity_injection_is_financing_inflow(db, make_voucher):
    """股东注资 100 万：借银行存款/贷实收资本 → 筹资活动现金流入 +100 万。"""
    make_voucher(db, "2026-07", [
        ("1002", "银行存款", "借", 1000000.0),
        ("3001", "实收资本", "贷", 1000000.0),
    ])
    cf = fs.cash_flow_statement(db, "2026-07")
    assert cf["net_financing"] == 1000000.0, "股东注资应记为筹资活动现金流入(+)，而非流出(-)"
    assert cf["net_increase"] == 1000000.0


def test_cash_flow_purchase_pay_is_operating_outflow(db, make_voucher):
    """采购付款：借应付账款/贷银行存款 → 经营活动现金流出(-)。"""
    make_voucher(db, "2026-07", [
        ("2202", "应付账款", "借", 1000.0),
        ("1002", "银行存款", "贷", 1000.0),
    ])
    cf = fs.cash_flow_statement(db, "2026-07")
    assert cf["net_operating"] == -1000.0, "采购付款应记为经营活动现金流出(-)"
