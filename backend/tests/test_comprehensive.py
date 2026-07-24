"""综合看板 overview 聚合回归：资金/业务/凭证计数实时正确。

不冗余存储，全部由 ledger_service / tax_service / 业务表实时汇总，
故重点验证「插一张凭证 / 插一张单据」后 overview 聚合数随动。
"""
from datetime import date
from decimal import Decimal

from app.models import reimburse as rm
from app.services import comprehensive_service as cs
from app.services import voucher_service as vs


def test_overview_funds_reflect_voucher(db, make_voucher):
    """插一张借银行存款(1002)/贷其他应付(2241) 的凭证，期初资金看板应反映。

    账簿只汇总「已审核/已记账」凭证，故先审核+记账。
    """
    v = make_voucher(
        db, "2026-05",
        [("1002", "银行存款", "借", 1000), ("2241", "其他应付款", "贷", 1000)],
    )
    vs.audit_voucher(db, v.id)
    vs.post_voucher(db, v.id)
    ov = cs.overview(db)
    assert ov["period"] is None
    funds = {f["code"]: f["amount"] for f in ov["funds"]}
    assert funds["1002"] == 1000.0, "资金看板银行存款应=凭证借方 1000"
    assert ov["voucher"]["total"] == 1, "凭证计数应=1"
    # 业务表在 conftest 中已清空，待审批合计应为 0
    assert ov["business"]["pending_total"] == 0


def test_overview_business_counts(db):
    """报销单不同状态计数应正确汇总到 business 段。"""
    db.add(rm.ReimbursementBill(
        bill_no="BXT01", applicant="测试", department="测试部",
        amount=Decimal("100.00"), bill_type="差旅", status="待审批",
    ))
    db.add(rm.ReimbursementBill(
        bill_no="BXT02", applicant="测试", department="测试部",
        amount=Decimal("200.00"), bill_type="差旅", status="已通过",
    ))
    db.commit()
    ov = cs.overview(db)
    assert ov["business"]["reimburse"]["待审批"] == 1
    assert ov["business"]["reimburse"]["已通过"] == 1
    assert ov["business"]["pending_total"] == 1, "待审批合计应跨单据类型累加"


def test_overview_revenue_trend_empty(db):
    """无主营业务收入凭证时 revenue_trend 应为空列表（不报错）。"""
    ov = cs.overview(db)
    assert ov["revenue_trend"] == []
