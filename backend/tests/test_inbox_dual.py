"""双识别闸门（A 方案）后端测试。

验证 invoice_inbox 的「两张识别结果不一致 → 隔离待复核」逻辑：
- upload 新记录：recognition.consistent=false → needs_review；true → recognized；无识别 → pending
- upload 重复：不一致 → 已存在记录置 needs_review，且返回 duplicated=True
- update_inbox：consistent=false → needs_review；true（手工修正）→ recognized（解除隔离）

说明：upload 是 async + UploadFile，这里用 FakeUpload 直接 await 调用，
绕过 HTTP 层。INBOX_DIR 用 tmp_path 重定向，避免落盘污染。
"""
import asyncio
import json
from datetime import datetime

import pytest

from app.api import invoice_inbox as ib_mod
from app.models import invoice_inbox as ib_m
from app.schemas import invoice_inbox as s
from sqlalchemy import text


class FakeUpload:
    """模拟 fastapi.UploadFile：只实现 upload() 用到的 .filename / await .read()。"""

    def __init__(self, filename, content=b"%PDF-1.4 test"):
        self.filename = filename
        self._content = content

    async def read(self):
        return self._content


def _clean_inbox(db):
    """invoice_inbox 不在 conftest 的 _BUSINESS_TABLES 清理列表，需自清防跨测试污染。"""
    db.execute(text("DELETE FROM invoice_inbox"))
    db.commit()


def _ej(no, consistent, **extra):
    """构造携带双识别结论的 extracted_json 字符串。"""
    data = {
        "no": no,
        "sellerTaxNo": "91110000MA01XXXX2K",
        "date": "2026-07-25",
        "sellerName": "深圳市流形机器人科技有限公司",
        "recognition": {
            "consistent": consistent,
            "diffs": [] if consistent else ["total 不一致"],
            "method": "dual",
        },
    }
    data.update(extra)
    return json.dumps(data)


@pytest.fixture
def inbox_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(ib_mod, "INBOX_DIR", tmp_path)
    return tmp_path


def test_upload_new_inconsistent_is_needs_review(db, inbox_dir):
    _clean_inbox(db)
    rec = asyncio.run(
        ib_mod.upload(
            FakeUpload("a.pdf"), extracted_json=_ej("8811700000000000001", False), db=db
        )
    )
    assert rec.status == "needs_review", rec.status
    assert rec.id is not None  # 新建记录已落库


def test_upload_new_consistent_is_recognized(db, inbox_dir):
    _clean_inbox(db)
    rec = asyncio.run(
        ib_mod.upload(
            FakeUpload("b.pdf"), extracted_json=_ej("8811700000000000002", True), db=db
        )
    )
    assert rec.status == "recognized", rec.status


def test_upload_no_extracted_is_pending(db, inbox_dir):
    _clean_inbox(db)
    rec = asyncio.run(ib_mod.upload(FakeUpload("c.pdf"), extracted_json=None, db=db))
    assert rec.status == "pending", rec.status


def test_upload_duplicate_inconsistent_sets_needs_review(db, inbox_dir):
    _clean_inbox(db)
    # 先传一张一致（recognized）的票
    first = asyncio.run(
        ib_mod.upload(
            FakeUpload("d.pdf"), extracted_json=_ej("8811700000000000003", True), db=db
        )
    )
    assert first.status == "recognized"
    # 再传同号票，但本次识别不一致 → 旧记录应被置 needs_review
    second = asyncio.run(
        ib_mod.upload(
            FakeUpload("d2.pdf"), extracted_json=_ej("8811700000000000003", False), db=db
        )
    )
    assert second.duplicated is True
    db.refresh(first)
    assert first.status == "needs_review", first.status


def test_update_consistent_false_sets_needs_review(db, inbox_dir):
    _clean_inbox(db)
    ib = ib_m.InvoiceInbox(
        filename="e.pdf", storage_path="/tmp/e.pdf", source="upload",
        status="recognized", extracted_json=_ej("8811700000000000004", True),
    )
    db.add(ib)
    db.commit()
    db.refresh(ib)

    obj = ib_mod.update_inbox(
        ib.id, s.InvoiceInboxUpdate(extracted_json=_ej("8811700000000000004", False)), db
    )
    assert obj.status == "needs_review", obj.status


def test_update_consistent_true_releases_isolation(db, inbox_dir):
    _clean_inbox(db)
    # 模拟一张被双识别隔离的记录
    ib = ib_m.InvoiceInbox(
        filename="f.pdf", storage_path="/tmp/f.pdf", source="upload",
        status="needs_review", extracted_json=_ej("8811700000000000005", False),
    )
    db.add(ib)
    db.commit()
    db.refresh(ib)

    # 手工修正：前端把 recognition.consistent 置 true（method=manual）后提交
    payload = _ej("8811700000000000005", True, method="manual")
    obj = ib_mod.update_inbox(
        ib.id, s.InvoiceInboxUpdate(extracted_json=payload), db
    )
    assert obj.status == "recognized", obj.status
