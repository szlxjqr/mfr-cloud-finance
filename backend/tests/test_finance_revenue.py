"""finance 模块回归测试：收入（revenue）。

覆盖任务要求的三个硬断言：
1. 确认收入（confirm）自动生成凭证并自动审核
   （借 银行存款/应收账款 / 贷 主营业务收入 / 贷 销项税额）。
2. source_no 幂等：重复确认 / 重复调用 generator 只生成一张凭证（不重复生成）。
3. 反归档（unarchive，限 admin/gm）级联删除该业务单联动的全部凭证。

业务规则来源：
- backend/app/api/revenue.py
- backend/app/services/voucher_service.py::generate_from_revenue / void_vouchers_by_source_no

金额关系：价税合计 total；不含税 net = total/(1+rate)；税额 tax = total-net。
settle_method='应收账款' 借方改 应收账款(1122)；tax_rate=0 不计销项税额。
"""
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select, text

from app.models import employee as emp_m
from app.models import revenue as revm
from app.models import voucher as vm
from app.services import voucher_service as vs

import app.api.revenue as rev_api


def _admin(db):
    """取测试库里已种子的 admin 账号，作为反归档/确认操作人。"""
    return db.scalar(select(emp_m.Account).where(emp_m.Account.employee_no == "00000000"))


def _vouchers_for(db, source_no):
    return db.scalars(select(vm.Voucher).where(vm.Voucher.source_no == source_no)).all()


@pytest.fixture(autouse=True)
def _clean_finance(db):
    """conftest 的 _clean 不含 capital_contributions / revenues，显式清空保证用例隔离。"""
    db.execute(text("DELETE FROM capital_contributions"))
    db.execute(text("DELETE FROM revenues"))
    db.commit()


def _make_draft(db, **kw):
    obj = revm.Revenue(
        bill_no=kw.get("bill_no", "SR-TEST-1"),
        customer=kw.get("customer", "测试客户"),
        total_amount=kw.get("total_amount", Decimal("11300")),
        tax_rate=kw.get("tax_rate", Decimal("0.13")),
        settle_method=kw.get("settle_method", "银行收讫"),
        revenue_date=kw.get("revenue_date", date(2026, 7, 1)),
        status="草稿",
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# ================= 1. 确认入账 → 自动生成凭证（自动审核）=================
def test_confirm_generates_audited_voucher(db):
    """确认收入应自动生成凭证并置「已审核」，业务单回写 voucher_no。"""
    obj = _make_draft(db, bill_no="SR-CFM-1", total_amount=Decimal("11300"), tax_rate=Decimal("0.13"))
    rev_api.confirm_revenue(obj.id, current_user=_admin(db), db=db)
    assert obj.status == "已确认"
    vs_ = _vouchers_for(db, "SR-CFM-1")
    assert len(vs_) == 1, "确认收入应生成一张凭证"
    assert vs_[0].status == "已审核", "收入凭证应自动审核入账"
    assert obj.voucher_no == vs_[0].voucher_no, "业务单应回写凭证号"


def test_confirm_voucher_entries_correct_bank(db):
    """银行收讫：借 银行存款(1002)=价税合计 / 贷 主营业务收入(5001)=不含税 / 贷 销项税额(2221.01.02)=税额。"""
    obj = _make_draft(db, bill_no="SR-ENT-1", total_amount=Decimal("11300"), tax_rate=Decimal("0.13"))
    rev_api.confirm_revenue(obj.id, current_user=_admin(db), db=db)
    v = _vouchers_for(db, "SR-ENT-1")[0]
    debit = sum(float(e.amount) for e in v.entries if e.direction == "借")
    credit = sum(float(e.amount) for e in v.entries if e.direction == "贷")
    assert abs(debit - credit) < 0.005, "凭证借贷不平衡"
    codes = {(e.subject_code, e.direction): float(e.amount) for e in v.entries}
    assert codes.get(("1002", "借")) == 11300.0
    assert codes.get(("5001", "贷")) == 10000.0
    assert codes.get(("2221.01.02", "贷")) == 1300.0


def test_confirm_settle_receivable_changes_debit(db):
    """settle_method='应收账款' 时借方改为 应收账款(1122)。"""
    obj = _make_draft(
        db, bill_no="SR-AR-1", total_amount=Decimal("11300"),
        tax_rate=Decimal("0.13"), settle_method="应收账款",
    )
    rev_api.confirm_revenue(obj.id, current_user=_admin(db), db=db)
    v = _vouchers_for(db, "SR-AR-1")[0]
    codes = {(e.subject_code, e.direction): float(e.amount) for e in v.entries}
    assert codes.get(("1122", "借")) == 11300.0, "应收账款结算时借方应为应收账款"
    assert codes.get(("1002", "借")) is None, "不应出现银行存款"


def test_confirm_zero_tax_no_output_tax(db):
    """tax_rate=0 时不计销项税额，仅 借 银行存款 / 贷 主营业务收入。"""
    obj = _make_draft(db, bill_no="SR-NTAX-1", total_amount=Decimal("10000"), tax_rate=Decimal("0"))
    rev_api.confirm_revenue(obj.id, current_user=_admin(db), db=db)
    v = _vouchers_for(db, "SR-NTAX-1")[0]
    codes = {(e.subject_code, e.direction): float(e.amount) for e in v.entries}
    assert codes.get(("1002", "借")) == 10000.0
    assert codes.get(("5001", "贷")) == 10000.0
    assert codes.get(("2221.01.02", "贷")) is None, "零税率不应出现销项税额"


# ================= 2. source_no 幂等 =================
def test_confirm_idempotent_at_api(db):
    """同一收入单重复确认只生成一张凭证（API 层幂等）。"""
    obj = _make_draft(db, bill_no="SR-IDEM-1", total_amount=Decimal("11300"), tax_rate=Decimal("0.13"))
    rev_api.confirm_revenue(obj.id, current_user=_admin(db), db=db)
    rev_api.confirm_revenue(obj.id, current_user=_admin(db), db=db)
    rev_api.confirm_revenue(obj.id, current_user=_admin(db), db=db)
    assert len(_vouchers_for(db, "SR-IDEM-1")) == 1, "重复确认不应生成多张凭证"


def test_generator_idempotent_returns_none(db):
    """直接重复调用 generator 第二次应返回 None（source_no 幂等）。"""
    obj = _make_draft(db, bill_no="SR-GIDEM-1", total_amount=Decimal("11300"), tax_rate=Decimal("0.13"))
    v1 = vs.generate_from_revenue(db, obj, maker="测试")
    v2 = vs.generate_from_revenue(db, obj, maker="测试")
    assert v1 is not None, "首次调用应生成凭证"
    assert v2 is None, "重复调用应跳过（幂等失效）"
    assert len(_vouchers_for(db, "SR-GIDEM-1")) == 1


def test_confirm_zero_amount_no_voucher(db):
    """收入价税合计 <= 0 不应生成凭证（generator 直接返回 None）。"""
    obj = _make_draft(db, bill_no="SR-ZERO-1", total_amount=Decimal("0"))
    v = vs.generate_from_revenue(db, obj, maker="测试")
    assert v is None, "零金额不应生成凭证"
    assert _vouchers_for(db, "SR-ZERO-1") == []


# ================= 3. 反归档级联删凭证 =================
def test_unarchive_cascades_deletes_voucher(db):
    """反归档（admin）删除该收入单联动的全部凭证，业务单回退草稿、清空 voucher_no。"""
    obj = _make_draft(db, bill_no="SR-UA-1", total_amount=Decimal("11300"), tax_rate=Decimal("0.13"))
    rev_api.confirm_revenue(obj.id, current_user=_admin(db), db=db)
    assert len(_vouchers_for(db, "SR-UA-1")) == 1
    rev_api.unarchive_revenue(obj.id, current_user=_admin(db), db=db)
    assert obj.status == "草稿", "反归档应回退到草稿"
    assert obj.voucher_no is None, "反归档应清空悬空凭证号"
    assert _vouchers_for(db, "SR-UA-1") == [], "反归档应级联删除联动凭证"
    ent = db.scalars(
        select(vm.VoucherEntry).where(
            vm.VoucherEntry.voucher_id.in_(
                select(vm.Voucher.id).where(vm.Voucher.source_no == "SR-UA-1")
            )
        )
    ).all()
    assert ent == [], "级联删除不应残留分录"


def test_unarchive_only_admin_allowed(db):
    """反归档要求 admin/gm；非管理员应被拒绝。"""
    from types import SimpleNamespace
    from app.api.auth import require_admin_gm
    import asyncio

    obj = _make_draft(db, bill_no="SR-UA-AUTH-1", total_amount=Decimal("11300"), tax_rate=Decimal("0.13"))
    rev_api.confirm_revenue(obj.id, current_user=_admin(db), db=db)
    emp_user = SimpleNamespace(role="employee", username="emp")
    with pytest.raises(Exception):
        asyncio.run(require_admin_gm(emp_user))


def test_unarchive_then_reconfirm_regenerates(db):
    """反归档后重确认应重新生成凭证（source_no 幂等重建），仍为一张。"""
    obj = _make_draft(db, bill_no="SR-REBUILD-1", total_amount=Decimal("11300"), tax_rate=Decimal("0.13"))
    rev_api.confirm_revenue(obj.id, current_user=_admin(db), db=db)
    rev_api.unarchive_revenue(obj.id, current_user=_admin(db), db=db)
    assert _vouchers_for(db, "SR-REBUILD-1") == []
    rev_api.confirm_revenue(obj.id, current_user=_admin(db), db=db)
    assert obj.status == "已确认"
    assert len(_vouchers_for(db, "SR-REBUILD-1")) == 1, "重确认应重建一张凭证"
