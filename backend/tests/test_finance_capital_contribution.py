"""finance 模块回归测试：股东入资（capital_contribution）。

覆盖任务要求的三个硬断言：
1. 确认入账（confirm）自动生成凭证并自动审核（借 收款科目 / 贷 实收资本）。
2. source_no 幂等：重复确认 / 重复调用 generator 只生成一张凭证（不重复生成）。
3. 反归档（unarchive，限 admin/gm）级联删除该业务单联动的全部凭证。

业务规则来源：
- backend/app/api/capital_contribution.py
- backend/app/services/voucher_service.py::generate_from_capital_contribution / void_vouchers_by_source_no

测试数据均带「测试」标记，且依赖 conftest 的临时 SQLite（永不触碰真实库）。
"""
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select, text

from app.models import capital_contribution as ccm
from app.models import employee as emp_m
from app.models import voucher as vm
from app.services import voucher_service as vs

import app.api.capital_contribution as cap_api


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
    obj = ccm.CapitalContribution(
        bill_no=kw.get("bill_no", "RZ-TEST-1"),
        investor=kw.get("investor", "测试股东"),
        amount=kw.get("amount", Decimal("50000")),
        capital_type=kw.get("capital_type", "货币资金"),
        receive_subject=kw.get("receive_subject", "1002"),
        contribution_date=kw.get("contribution_date", date(2026, 7, 1)),
        status="草稿",
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# ================= 1. 确认入账 → 自动生成凭证（自动审核）=================
def test_confirm_generates_audited_voucher(db):
    """确认入资应自动生成凭证并置「已审核」，业务单回写 voucher_no。"""
    obj = _make_draft(db, bill_no="RZ-CFM-1", amount=Decimal("50000"))
    cap_api.confirm_contribution(obj.id, current_user=_admin(db), db=db)
    assert obj.status == "已确认"
    vs_ = _vouchers_for(db, "RZ-CFM-1")
    assert len(vs_) == 1, "确认入资应生成一张凭证"
    assert vs_[0].status == "已审核", "入资凭证应自动审核入账"
    assert obj.voucher_no == vs_[0].voucher_no, "业务单应回写凭证号"


def test_confirm_voucher_entries_correct(db):
    """凭证分录正确：借 银行存款(1002) / 贷 实收资本(3001)，金额=入资金额，借贷平衡。"""
    obj = _make_draft(db, bill_no="RZ-ENT-1", amount=Decimal("80000"))
    cap_api.confirm_contribution(obj.id, current_user=_admin(db), db=db)
    v = _vouchers_for(db, "RZ-ENT-1")[0]
    debit = sum(float(e.amount) for e in v.entries if e.direction == "借")
    credit = sum(float(e.amount) for e in v.entries if e.direction == "贷")
    assert abs(debit - credit) < 0.005, "凭证借贷不平衡"
    codes = {(e.subject_code, e.direction): float(e.amount) for e in v.entries}
    assert codes.get(("1002", "借")) == 80000.0
    assert codes.get(("3001", "贷")) == 80000.0


def test_confirm_uses_receive_subject(db):
    """receive_subject 可指定收款科目；借方跟随该科目而非默认银行存款。"""
    obj = _make_draft(db, bill_no="RZ-SUB-1", amount=Decimal("30000"), receive_subject="1122")
    cap_api.confirm_contribution(obj.id, current_user=_admin(db), db=db)
    v = _vouchers_for(db, "RZ-SUB-1")[0]
    codes = {(e.subject_code, e.direction): float(e.amount) for e in v.entries}
    assert codes.get(("1122", "借")) == 30000.0, "借方应使用指定的收款科目"
    assert codes.get(("3001", "贷")) == 30000.0


# ================= 2. source_no 幂等 =================
def test_confirm_idempotent_at_api(db):
    """同一入资单重复确认只生成一张凭证（API 层幂等）。"""
    obj = _make_draft(db, bill_no="RZ-IDEM-1", amount=Decimal("50000"))
    cap_api.confirm_contribution(obj.id, current_user=_admin(db), db=db)
    cap_api.confirm_contribution(obj.id, current_user=_admin(db), db=db)
    cap_api.confirm_contribution(obj.id, current_user=_admin(db), db=db)
    assert len(_vouchers_for(db, "RZ-IDEM-1")) == 1, "重复确认不应生成多张凭证"


def test_generator_idempotent_returns_none(db):
    """直接重复调用 generator 第二次应返回 None（source_no 幂等）。"""
    obj = _make_draft(db, bill_no="RZ-GIDEM-1", amount=Decimal("50000"))
    v1 = vs.generate_from_capital_contribution(db, obj, maker="测试")
    v2 = vs.generate_from_capital_contribution(db, obj, maker="测试")
    assert v1 is not None, "首次调用应生成凭证"
    assert v2 is None, "重复调用应跳过（幂等失效）"
    assert len(_vouchers_for(db, "RZ-GIDEM-1")) == 1


def test_confirm_zero_amount_no_voucher(db):
    """入资金额 <= 0 不应生成凭证（generator 直接返回 None）。"""
    obj = _make_draft(db, bill_no="RZ-ZERO-1", amount=Decimal("0"))
    v = vs.generate_from_capital_contribution(db, obj, maker="测试")
    assert v is None, "零金额不应生成凭证"
    assert _vouchers_for(db, "RZ-ZERO-1") == []


# ================= 3. 反归档级联删凭证 =================
def test_unarchive_cascades_deletes_voucher(db):
    """反归档（admin）删除该入资单联动的全部凭证，业务单回退草稿、清空 voucher_no。"""
    obj = _make_draft(db, bill_no="RZ-UA-1", amount=Decimal("50000"))
    cap_api.confirm_contribution(obj.id, current_user=_admin(db), db=db)
    assert len(_vouchers_for(db, "RZ-UA-1")) == 1
    cap_api.unarchive_contribution(obj.id, current_user=_admin(db), db=db)
    assert obj.status == "草稿", "反归档应回退到草稿"
    assert obj.voucher_no is None, "反归档应清空悬空凭证号"
    assert _vouchers_for(db, "RZ-UA-1") == [], "反归档应级联删除联动凭证"
    # 级联删分录：无孤儿分录残留
    ent = db.scalars(
        select(vm.VoucherEntry).where(
            vm.VoucherEntry.voucher_id.in_(
                select(vm.Voucher.id).where(vm.Voucher.source_no == "RZ-UA-1")
            )
        )
    ).all()
    assert ent == []


def test_unarchive_only_admin_allowed(db):
    """反归档要求 admin/gm；非管理员应被拒绝。"""
    from types import SimpleNamespace
    from app.api.auth import require_admin_gm
    import asyncio

    obj = _make_draft(db, bill_no="RZ-UA-AUTH-1", amount=Decimal("50000"))
    cap_api.confirm_contribution(obj.id, current_user=_admin(db), db=db)
    emp_user = SimpleNamespace(role="employee", username="emp")
    with pytest.raises(Exception):
        asyncio.run(require_admin_gm(emp_user))


def test_unarchive_then_reconfirm_regenerates(db):
    """反归档后重确认应重新生成凭证（source_no 幂等重建），仍为一张。"""
    obj = _make_draft(db, bill_no="RZ-REBUILD-1", amount=Decimal("50000"))
    cap_api.confirm_contribution(obj.id, current_user=_admin(db), db=db)
    cap_api.unarchive_contribution(obj.id, current_user=_admin(db), db=db)
    assert _vouchers_for(db, "RZ-REBUILD-1") == []
    cap_api.confirm_contribution(obj.id, current_user=_admin(db), db=db)
    assert obj.status == "已确认"
    assert len(_vouchers_for(db, "RZ-REBUILD-1")) == 1, "重确认应重建一张凭证"
