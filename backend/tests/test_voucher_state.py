"""凭证记账状态机回归：未审核 → 已审核 → 已记账 流转 + 顺序约束。

此前 voucher.status 字段（未审核/已审核/已记账）是死字段，无任何代码翻转，
且 ledger 聚合不过滤状态（未审核凭证也进账簿）。本文件验证状态机
（audit_voucher / post_voucher）逻辑正确；ledger 是否按状态过滤是独立的产品决策，
不在本测试范围（避免改动年终演示数据）。
"""
import pytest

from app.services import voucher_service as vs


def test_make_voucher_default_status_unaudited(db, make_voucher):
    """新生成凭证默认状态=未审核。"""
    v = make_voucher(
        db, "2026-07",
        [("1002", "银行存款", "借", 100), ("2241", "其他应付款", "贷", 100)],
    )
    assert v.status == "未审核"


def test_audit_then_post_transition(db, make_voucher):
    """未审核 → 已审核 → 已记账 正常流转。"""
    v = make_voucher(
        db, "2026-07",
        [("1002", "银行存款", "借", 100), ("2241", "其他应付款", "贷", 100)],
    )
    a = vs.audit_voucher(db, v.id)
    assert a is not None and a.status == "已审核"
    p = vs.post_voucher(db, v.id)
    assert p is not None and p.status == "已记账"


def test_post_before_audit_rejected(db, make_voucher):
    """未审核直接记账应被拒绝（顺序约束）。"""
    v = make_voucher(
        db, "2026-07",
        [("1002", "银行存款", "借", 100), ("2241", "其他应付款", "贷", 100)],
    )
    with pytest.raises(ValueError):
        vs.post_voucher(db, v.id)


def test_audit_idempotent(db, make_voucher):
    """重复审核幂等，不报错、状态保持已审核。"""
    v = make_voucher(
        db, "2026-07",
        [("1002", "银行存款", "借", 100), ("2241", "其他应付款", "贷", 100)],
    )
    vs.audit_voucher(db, v.id)
    a2 = vs.audit_voucher(db, v.id)
    assert a2.status == "已审核"


def test_audit_unknown_returns_none(db):
    """审核不存在的凭证返回 None（由 API 层转 404）。"""
    assert vs.audit_voucher(db, 999999) is None
    assert vs.post_voucher(db, 999999) is None
