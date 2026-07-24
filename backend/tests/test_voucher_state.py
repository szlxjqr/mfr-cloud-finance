"""凭证记账状态机回归：未审核 → 已审核 → 已记账 → 反记账 → 反审核 全流转 + 顺序约束。

此前 voucher.status 字段（未审核/已审核/已记账）是死字段，无任何代码翻转，
且 ledger 聚合不过滤状态（未审核凭证也进账簿）。本文件验证状态机
（audit_voucher / post_voucher / unpost_voucher / unaudit_voucher）逻辑正确，
并守护「账簿只汇总 已审核/已记账 凭证、未审核草稿不进账簿」的产品决策
（反审核把凭证拉回未审核即移出账簿）。
"""
import types
from datetime import date

import pytest

from app.services import ledger_service as ls
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


def test_unpost_then_unaudit_transition(db, make_voucher):
    """已记账 → 反记账(已审核) → 反审核(未审核) 正常反向流转。"""
    v = make_voucher(
        db, "2026-07",
        [("1002", "银行存款", "借", 100), ("2241", "其他应付款", "贷", 100)],
    )
    vs.audit_voucher(db, v.id)
    vs.post_voucher(db, v.id)
    assert vs.post_voucher(db, v.id).status == "已记账"  # 幂等
    up = vs.unpost_voucher(db, v.id)
    assert up is not None and up.status == "已审核", "反记账应回到已审核"
    ua = vs.unaudit_voucher(db, v.id)
    assert ua is not None and ua.status == "未审核", "反审核应回到未审核"


def test_unaudit_before_unpost_rejected(db, make_voucher):
    """已记账凭证直接反审核应被拒绝（须先反记账）。"""
    v = make_voucher(
        db, "2026-07",
        [("1002", "银行存款", "借", 100), ("2241", "其他应付款", "贷", 100)],
    )
    vs.audit_voucher(db, v.id)
    vs.post_voucher(db, v.id)
    with pytest.raises(ValueError):
        vs.unaudit_voucher(db, v.id)


def test_ledger_excludes_unaudited_draft(db, make_voucher):
    """未审核草稿不进账簿；审核+记账后才出现在总账。"""
    v = make_voucher(
        db, "2026-07",
        [("1002", "银行存款", "借", 100), ("2241", "其他应付款", "贷", 100)],
    )
    # 未审核：总账该科目无数据
    out = ls.general_ledger(db, "1002", "2026-07")
    assert out["rows"] == [], "未审核凭证不应进入总账"
    # 审核+记账：进入总账
    vs.audit_voucher(db, v.id)
    vs.post_voucher(db, v.id)
    out2 = ls.general_ledger(db, "1002", "2026-07")
    assert out2["rows"], "已记账凭证应进入总账"
    assert out2["rows"][0]["ending_debit"] == 100.0
    # 反审核拉回未审核：再次移出总账（验证 L4 缓存随状态翻转失效）
    vs.unpost_voucher(db, v.id)
    vs.unaudit_voucher(db, v.id)
    out3 = ls.general_ledger(db, "1002", "2026-07")
    assert out3["rows"] == [], "反审核后凭证应移出总账（缓存须失效）"


def _fake_payload(**kw):
    return types.SimpleNamespace(**kw)


def test_create_manual_voucher_ok(db):
    """手工录入借贷平衡凭证：默认未审核、来源=手工、不污染业务联动。"""
    p = _fake_payload(
        voucher_date="2026-07-15",
        voucher_word="记",
        attach_count=1,
        maker="会计",
        summary="手工测试凭证",
        entries=[
            types.SimpleNamespace(subject_code="1002", direction="借", summary="存现", amount=500.0),
            types.SimpleNamespace(subject_code="2241", direction="贷", summary="其他应付", amount=500.0),
        ],
    )
    v = vs.create_manual_voucher(db, p, "会计")
    assert v is not None
    assert v.status == "未审核"
    assert v.source_type == "手工" and v.source_no is None
    assert len(v.entries) == 2


def test_create_manual_voucher_imbalance_rejected(db):
    """借贷不平衡的手工凭证应被拒绝（ValueError → API 400）。"""
    p = _fake_payload(
        voucher_date="2026-07-15",
        entries=[
            types.SimpleNamespace(subject_code="1002", direction="借", summary="存现", amount=500.0),
            types.SimpleNamespace(subject_code="2241", direction="贷", summary="其他应付", amount=300.0),
        ],
    )
    with pytest.raises(ValueError):
        vs.create_manual_voucher(db, p, "会计")


def test_create_manual_voucher_single_entry_rejected(db):
    """少于 2 条分录的手工凭证应被拒绝。"""
    p = _fake_payload(
        voucher_date="2026-07-15",
        entries=[
            types.SimpleNamespace(subject_code="1002", direction="借", summary="存现", amount=500.0),
        ],
    )
    with pytest.raises(ValueError):
        vs.create_manual_voucher(db, p, "会计")
