"""税务取数冒烟：进项/销项/应交增值税汇总。

数据全部来自 voucher_entries，与凭证实时一致（不冗余存储）。
"""
from app.services import tax_service as ts


def test_tax_summary_input_output_vat(db, make_voucher):
    """进项 100（借2221.01.01）+ 销项 200（贷2221.01.02）→ 应交增值税 100。"""
    make_voucher(db, "2026-07", [
        ("2221.01.01", "进项税额", "借", 100.0),
        ("1002", "银行存款", "贷", 100.0),
    ])
    make_voucher(db, "2026-07", [
        ("1122", "应收账款", "借", 200.0),
        ("2221.01.02", "销项税额", "贷", 200.0),
    ])
    s = ts.tax_summary(db, "2026-07")
    assert s["input_tax"] == 100.0
    assert s["output_tax"] == 200.0
    assert s["vat_payable"] == 100.0  # 销项 - 进项
