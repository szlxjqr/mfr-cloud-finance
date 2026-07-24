"""pytest 公共夹具：把 DATABASE_URL 重定向到临时 SQLite，确保测试永不触碰老板真实库。

关键：必须在 import app.db 之前设置 DATABASE_URL，否则引擎已绑定 smart_finance.db。
测试数据库是全新临时文件，init_db() 会建表 + 种入 28 个标准科目 / admin / 公司设置。
"""
import atexit
import os
import tempfile
from datetime import date
from decimal import Decimal

# 1) 先设置临时数据库，再 import app.db（引擎在 import 时按 DATABASE_URL 建连）
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"
atexit.register(lambda: os.path.exists(_tmp.name) and os.unlink(_tmp.name))

from app.db import database as dbmod  # noqa: E402

dbmod.init_db()  # 建表 + 种子（28 科目 / admin / 公司设置）

from sqlalchemy import text  # noqa: E402

from app.models import voucher as vm  # noqa: E402
from app.utils.codegen import gen_voucher_no  # noqa: E402

# 测试开始前清空业务表，保留种子（科目/admin/公司），保证用例间隔离
_BUSINESS_TABLES = [
    "voucher_entries",
    "vouchers",
    "invoice_details",
    "invoices",
    "purchase_requisition_items",
    "purchase_requisitions",
    "salary_bills",
    "reimbursement_bills",
]


def _clean(db):
    for t in _BUSINESS_TABLES:
        db.execute(text(f"DELETE FROM {t}"))
    db.commit()


import pytest  # noqa: E402


@pytest.fixture
def db():
    """每个测试一个会话，并先清空业务表（保留种子）。"""
    session = dbmod.SessionLocal()
    _clean(session)
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def make_voucher():
    """手动写一张凭证 + 分录，返回 Voucher 对象。

    entries: [(科目编码, 科目名, 方向'借'/'贷', 金额), ...]
    """
    def _make(db, period, entries, source_type=None, source_no=None, summary="测试凭证"):
        y, m = period.split("-")
        vno, seq = gen_voucher_no(db, int(y), int(m))
        voc = vm.Voucher(
            voucher_no=vno,
            seq=seq,
            voucher_date=date(int(y), int(m), 5),
            period=period,
            voucher_word="记",
            maker="测试",
            source_type=source_type,
            source_no=source_no,
            summary=summary,
        )
        db.add(voc)
        db.flush()
        for i, (code, name, direction, amount) in enumerate(entries, start=1):
            db.add(
                vm.VoucherEntry(
                    voucher_id=voc.id,
                    seq=i,
                    subject_code=code,
                    subject_name=name,
                    summary=summary,
                    direction=direction,
                    amount=Decimal(str(amount)),
                )
            )
        db.commit()
        db.refresh(voc)
        return voc

    return _make


@pytest.fixture
def voucher_sides():
    """返回 (借方合计, 贷方合计)。"""
    def _sides(voc):
        debit = sum(float(e.amount) for e in voc.entries if e.direction == "借")
        credit = sum(float(e.amount) for e in voc.entries if e.direction == "贷")
        return debit, credit

    return _sides
