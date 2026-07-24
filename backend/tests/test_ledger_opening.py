"""账簿期初余额推导回归：期初 = 所选期间之前（不含）的累计借/贷。

系统无独立「期初余额」存储表——期初由 ledger_service 按期间从凭证分录
实时累计推导。本文件验证「推导出的期初余额正确」，即 #3 要测的
「期初余额反映」真实落点。
"""
from app.services import ledger_service as ls


def test_general_ledger_opening_is_prior_cum(db, make_voucher):
    """2026-01 借银行存款 500；2026-02 再借 300。
    则 2026-02 期初=500（上月期末），期末=800。"""
    make_voucher(
        db, "2026-01",
        [("1002", "银行存款", "借", 500), ("2241", "其他应付款", "贷", 500)],
    )
    make_voucher(
        db, "2026-02",
        [("1002", "银行存款", "借", 300), ("2241", "其他应付款", "贷", 300)],
    )
    out = ls.general_ledger(db, "1002", "2026-02")
    rows = {r["period"]: r for r in out["rows"]}
    assert rows["2026-01"]["opening_debit"] == 0.0
    assert rows["2026-01"]["ending_debit"] == 500.0
    # 期初余额推导正确：= 之前期间累计
    assert rows["2026-02"]["opening_debit"] == 500.0, "期初应=上月期末 500"
    assert rows["2026-02"]["ending_debit"] == 800.0


def test_summary_opening_derivation(db, make_voucher):
    """科目汇总表期初/期末随跨期凭证正确推导。"""
    make_voucher(
        db, "2026-01",
        [("1002", "银行存款", "借", 1000), ("2241", "其他应付款", "贷", 1000)],
    )
    make_voucher(
        db, "2026-03",
        [("1002", "银行存款", "借", 500), ("2241", "其他应付款", "贷", 500)],
    )
    rows = {r["code"]: r for r in ls.summary(db, "2026-03")}
    assert rows["1002"]["opening_debit"] == 1000.0, "期初应=2026-01 累计 1000"
    assert rows["1002"]["ending_debit"] == 1500.0
