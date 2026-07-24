"""固定资产三类凭证回归测试：入账 / 计提折旧 / 处置，及幂等性。

覆盖「业务单→凭证」联动地基在固定资产场景的正确性：
- 入账：借 1601 原值 / 贷 1002（银行存款）原值
- 计提折旧：借 折旧费用科目(5602) / 贷 1602（累计折旧），按月折旧额
- 处置：借 1602（累计折旧）+ 借 5602（账面净值）/ 贷 1601（原值），借贷平衡
- 三类动作均幂等（重复调用不重复出凭证、不改累计折旧）
"""
import pytest
from datetime import date
from decimal import Decimal
from sqlalchemy import select, text

from sqlalchemy import func

from app.models import voucher as vm
from app.models import fixed_asset as fam
from app.services import asset_service as asset_svc


def _reset(db):
    """清空资产相关表（conftest 默认不清这两个表，需手动隔离）。"""
    db.execute(text("DELETE FROM dep_records"))
    db.execute(text("DELETE FROM fixed_assets"))
    db.commit()


def _make_asset(db, **kw):
    defaults = dict(
        asset_no="ZC2026TEST01",
        name="测试办公电脑",
        category="办公设备",
        department="行政部",
        acquisition_date=date(2026, 1, 15),
        original_value=Decimal("10000"),
        salvage_rate=Decimal("5.00"),
        useful_life=Decimal("5.0"),
        dep_subject_code="5602",
        status="未入账",
    )
    defaults.update(kw)
    a = fam.FixedAsset(**defaults)
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


def _voucher_of(db, source_type, source_no):
    return db.scalar(
        select(vm.Voucher).where(
            vm.Voucher.source_type == source_type,
            vm.Voucher.source_no == source_no,
        )
    )


def _count_vouchers(db, source_type):
    return db.scalar(
        select(func.count(vm.Voucher.id)).where(vm.Voucher.source_type == source_type)
    )


def _entry_map(voc):
    """返回 {科目编码: (方向, 金额(float))}。"""
    out = {}
    for e in voc.entries:
        out.setdefault(e.subject_code, []).append((e.direction, float(e.amount)))
    return out


def _debit_credit(voc):
    debit = sum(float(e.amount) for e in voc.entries if e.direction == "借")
    credit = sum(float(e.amount) for e in voc.entries if e.direction == "贷")
    return debit, credit


def test_asset_record_voucher(db):
    """入账生成购置凭证：借1601=原值，贷1002=原值；资产状态→在用。"""
    _reset(db)
    a = _make_asset(db)
    res = asset_svc.record(db, a.id, "测试")
    assert res["skipped"] is False
    assert res["voucher_no"]

    voc = _voucher_of(db, "固定资产", a.asset_no)
    assert voc is not None
    em = _entry_map(voc)
    assert em["1601"] == [("借", 10000.0)]
    assert em["1002"] == [("贷", 10000.0)]
    d, c = _debit_credit(voc)
    assert d == pytest.approx(c) == 10000.0

    db.refresh(a)
    assert a.status == "在用"


def test_asset_depreciate_voucher(db):
    """计提折旧：借5602=月折旧额，贷1602=月折旧额；累计折旧被累加。"""
    _reset(db)
    a = _make_asset(db)
    asset_svc.record(db, a.id, "测试")

    # 月折旧 = 10000*(1-5%)/(5*12) = 158.33
    res = asset_svc.depreciate(db, "2026-01", "测试")
    assert res["skipped"] is False
    assert res["count"] == 1
    assert res["total"] == pytest.approx(158.33)

    voc = _voucher_of(db, "固定资产折旧", f"ZCDEP|2026-01")
    assert voc is not None
    em = _entry_map(voc)
    assert em["5602"] == [("借", 158.33)]
    assert em["1602"] == [("贷", 158.33)]
    d, c = _debit_credit(voc)
    assert d == pytest.approx(c) == 158.33

    db.refresh(a)
    assert float(a.accum_dep) == pytest.approx(158.33)


def test_asset_dispose_voucher(db):
    """处置：借1602(累计)+借5602(净值)=贷方1601(原值)，借贷平衡。"""
    _reset(db)
    a = _make_asset(db)
    asset_svc.record(db, a.id, "测试")
    asset_svc.depreciate(db, "2026-01", "测试")

    res = asset_svc.dispose(db, a.id, "测试")
    assert res["skipped"] is False

    voc = _voucher_of(db, "固定资产处置", a.asset_no)
    assert voc is not None
    em = _entry_map(voc)
    # 累计折旧
    assert em["1602"] == [("借", 158.33)]
    # 账面净值 = 原值 - 累计 = 10000 - 158.33 = 9841.67
    assert em["5602"] == [("借", 9841.67)]
    # 原值
    assert em["1601"] == [("贷", 10000.0)]
    d, c = _debit_credit(voc)
    assert d == pytest.approx(c) == 10000.0

    db.refresh(a)
    assert a.status == "已处置"


def test_asset_record_idempotent(db):
    """已入账资产重复调用 record 不重复出凭证。"""
    _reset(db)
    a = _make_asset(db)
    r1 = asset_svc.record(db, a.id, "测试")
    r2 = asset_svc.record(db, a.id, "测试")
    assert r2["skipped"] is True
    assert r2["voucher_no"] == r1["voucher_no"]
    assert _count_vouchers(db, "固定资产") == 1


def test_asset_deprecate_idempotent(db):
    """同月重复计提折旧不重复出凭证、不动累计折旧。"""
    _reset(db)
    a = _make_asset(db)
    asset_svc.record(db, a.id, "测试")
    asset_svc.depreciate(db, "2026-01", "测试")
    r2 = asset_svc.depreciate(db, "2026-01", "测试")
    assert r2["skipped"] is True
    assert _count_vouchers(db, "固定资产折旧") == 1
    db.refresh(a)
    assert float(a.accum_dep) == pytest.approx(158.33)


def test_asset_dispose_idempotent(db):
    """已处置资产重复调用 dispose 不重复出凭证。"""
    _reset(db)
    a = _make_asset(db)
    asset_svc.record(db, a.id, "测试")
    asset_svc.depreciate(db, "2026-01", "测试")
    r1 = asset_svc.dispose(db, a.id, "测试")
    r2 = asset_svc.dispose(db, a.id, "测试")
    assert r2["skipped"] is True
    assert r2["voucher_no"] == r1["voucher_no"]
    assert _count_vouchers(db, "固定资产处置") == 1


def test_asset_dep_subject_rd(db):
    """研发设备的折旧应计入研发支出(4301)而非管理费用(5602)。"""
    _reset(db)
    a = _make_asset(db, asset_no="ZC2026TESTRD", dep_subject_code="4301")
    asset_svc.record(db, a.id, "测试")
    asset_svc.depreciate(db, "2026-01", "测试")
    voc = _voucher_of(db, "固定资产折旧", f"ZCDEP|2026-01")
    em = _entry_map(voc)
    assert em["4301"] == [("借", 158.33)]
    assert "5602" not in em
