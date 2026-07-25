#!/usr/bin/env python3
"""数据补传脚本：扫描 invoices 表中 attachment_path 为空的历史发票，
通过发票号码匹配 invoice_inbox 中的记录（extracted_json 含 no），
将 inbox 的 storage_path 补到 invoices.attachment_path。

用法：
    cd backend
    .venv/bin/python scripts/backfill_invoice_attachments.py          # 正式执行
    .venv/bin/python scripts/backfill_invoice_attachments.py --dry-run  # 仅预览不修改
"""
import json
import sys
from pathlib import Path

# 确保能找到 backend 包
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.db.database import engine, init_db
from sqlalchemy import text


def main():
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("🧪 DRY-RUN 模式：仅预览，不修改数据库\n")
    else:
        print("🚀 正式执行模式\n")

    # 确保表存在
    init_db()

    with engine.connect() as conn:
        # 1. 查 invoices 中 attachment_path 为空的记录
        inv_rows = conn.execute(
            text("""
                SELECT i.id, i.no, i.seller_name, i.invoice_date, i.attachment_path
                FROM invoices i
                WHERE i.attachment_path IS NULL
                ORDER BY i.id
            """)
        ).fetchall()
        print(f"📋 invoices 表 attachment_path 为空的记录共 {len(inv_rows)} 条\n")

        # 2. 查 invoice_inbox 中已识别+有文件的记录
        inbox_rows = conn.execute(
            text("""
                SELECT ib.id, ib.storage_path, ib.extracted_json, ib.filename
                FROM invoice_inbox ib
                WHERE ib.status IN ('recognized', 'linked')
                  AND ib.storage_path != ''
                  AND ib.extracted_json IS NOT NULL
                ORDER BY ib.id
            """)
        ).fetchall()
        print(f"📋 invoice_inbox 中已识别且有文件的记录共 {len(inbox_rows)} 条\n")

        # 构建 inbox 映射：发票号码 → storage_path
        inbox_map: dict[str, str] = {}
        inbox_id_map: dict[str, int] = {}
        for r in inbox_rows:
            try:
                ej = json.loads(r.extracted_json)
            except Exception:
                continue
            no = (ej.get("no") or "").strip()
            if not no:
                continue
            # 重复取最新的
            inbox_map[no] = r.storage_path
            inbox_id_map[no] = r.id

        # 3. 匹配补传
        matched = 0
        skipped_no_inbox = 0
        for row in inv_rows:
            inv_no = (row.no or "").strip()
            if not inv_no:
                print(f"   ⚠️  ID={row.id} 发票号码为空，跳过")
                skipped_no_inbox += 1
                continue

            storage = inbox_map.get(inv_no)
            if not storage:
                print(f"   ⚠️  ID={row.id} 发票号码「{inv_no}」在发票箱中未找到匹配记录")
                skipped_no_inbox += 1
                continue

            # 检查文件是否存在
            if not Path(storage).is_file():
                print(f"   ⚠️  ID={row.id} 匹配到 inbox ID={inbox_id_map.get(inv_no)} 但文件「{storage}」不存在，跳过")
                skipped_no_inbox += 1
                continue

            # 补传
            print(f"   ✅ ID={row.id} 发票「{inv_no}」({row.seller_name or '?'}) → 补 attachment_path = {storage}")
            if not dry_run:
                conn.execute(
                    text("UPDATE invoices SET attachment_path = :p WHERE id = :id"),
                    {"p": storage, "id": row.id},
                )
            matched += 1

        if not dry_run:
            conn.commit()

        print(f"\n{'='*50}")
        print(f"结果汇总（{'DRY-RUN' if dry_run else '正式执行'}）:")
        print(f"  总处理: {len(inv_rows)} 条")
        print(f"  已补传: {matched} 条")
        print(f"  未匹配: {skipped_no_inbox} 条")
        print(f"{'='*50}")


if __name__ == "__main__":
    main()
