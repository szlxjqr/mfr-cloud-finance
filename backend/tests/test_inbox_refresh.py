"""发票箱识别结果更新后，正式发票明细自动同步（防折扣行负数残留）。

两个场景：
1. 内部函数 `_refresh_linked_invoices`：用最新识别（含负数折扣）重建同号正式发票明细，负号不丢。
2. `update_inbox`：人工校正识别结果时，级联刷新同号正式发票明细。
"""
import json

from app.api import invoice_inbox as ib_mod
from app.models import invoice as inv_m
from app.models import invoice_inbox as ib_m
from app.schemas import invoice_inbox as s


def _seed_invoice_dirty(db, no="26447000001453308870"):
    """构造一张正式发票，明细为脏数据：折扣行被存成正数。"""
    inv = inv_m.Invoice(
        no=no,
        invoice_type="增值税专用发票",
        seller_name="广州晶东贸易有限公司",
    )
    db.add(inv)
    db.flush()
    db.add(
        inv_m.InvoiceDetail(
            invoice_id=inv.id, biz_type="采购商品", item="行1",
            amount=777.88, tax_rate=13, tax=101.12, total=879,
        )
    )
    db.add(
        inv_m.InvoiceDetail(
            invoice_id=inv.id, biz_type="采购商品", item="行2折扣",
            amount=2.7, tax_rate=13, tax=0.35, total=3.05,  # 脏：应为 -2.7 / -0.35
        )
    )
    db.commit()
    return inv


def test_refresh_linked_invoices_keeps_negative(db):
    inv = _seed_invoice_dirty(db)
    extracted = {
        "no": "26447000001453308870",
        "items": [
            {"name": "行1", "amount": 777.88, "tax": 101.12, "taxRate": 13},
            {"name": "行2折扣", "amount": -2.7, "tax": -0.35, "taxRate": 13},
        ],
    }
    n = ib_mod._refresh_linked_invoices(db, "26447000001453308870", extracted)
    assert n == 1, n

    db.refresh(inv)
    amts = sorted(float(d.amount) for d in inv.details)
    assert amts == [-2.7, 777.88], amts
    tot = sum(float(d.total) for d in inv.details)
    assert abs(tot - 875.95) < 0.005, tot


def test_update_inbox_refreshes_linked(db):
    inv = _seed_invoice_dirty(db)
    ib = ib_m.InvoiceInbox(
        filename="f.pdf", storage_path="/tmp/f.pdf", source="upload",
        status="recognized",
        extracted_json=json.dumps({
            "no": "26447000001453308870",
            "items": [{"name": "x", "amount": 2.7, "tax": 0.35, "taxRate": 13}],
        }),
    )
    db.add(ib)
    db.commit()
    db.refresh(ib)

    new_ej = json.dumps({
        "no": "26447000001453308870",
        "items": [
            {"name": "行1", "amount": 777.88, "tax": 101.12, "taxRate": 13},
            {"name": "行2折扣", "amount": -2.7, "tax": -0.35, "taxRate": 13},
        ],
    })
    ib_mod.update_inbox(ib.id, s.InvoiceInboxUpdate(extracted_json=new_ej), db)

    db.refresh(inv)
    amts = sorted(float(d.amount) for d in inv.details)
    assert amts == [-2.7, 777.88], amts
    tot = sum(float(d.total) for d in inv.details)
    assert abs(tot - 875.95) < 0.005, tot
