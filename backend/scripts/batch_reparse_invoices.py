#!/usr/bin/env python3
"""批量重新解析发票箱中所有发票的 extracted_json——用前端的 extractInvoiceFields 新版本（负号+合计行）。

1. 从 DB 读出所有 invoice_inbox 的 id + extracted_json 中的 rawText
2. 写入临时文件
3. 调用 Node 脚本（前端 scripts/reparse_invoices.mjs）重新解析
4. 更新 DB 中每条记录的 extracted_json

用法：
    cd backend && .venv/bin/python scripts/batch_reparse_invoices.py
"""
import json
import subprocess
import sys
from pathlib import Path

# 项目根
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # backend/
FRONTEND_ROOT = PROJECT_ROOT / "frontend"
NODE_SCRIPT = FRONTEND_ROOT / "scripts" / "reparse_invoices.mjs"


def main():
    # 1. 从 DB 读出数据
    sys.path.insert(0, str(PROJECT_ROOT))
    from app.db.database import engine
    from sqlalchemy import text

    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, extracted_json FROM invoice_inbox WHERE extracted_json IS NOT NULL")
        ).fetchall()

    records = []
    for r in rows:
        try:
            d = json.loads(r.extracted_json)
        except Exception:
            continue
        raw_text = d.get("rawText", "")
        if not raw_text:
            continue
        records.append({"id": r.id, "rawText": raw_text})

    print(f"📋 共 {len(records)} 条发票需要重新解析")

    # 2. 写入临时文件（直接用 pipe 交给 Node，不需要写文件）
    print(f"🔄 调用 Node 解析器（{len(records)} 条）...")
    result = subprocess.run(
        [
            "/Users/szlxjqr/.workbuddy/binaries/node/versions/22.22.2/bin/node",
            NODE_SCRIPT,
        ],
        cwd=FRONTEND_ROOT,
        input=json.dumps(records),
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode != 0:
        print(f"❌ Node 脚本错误:\n{result.stderr}")
        sys.exit(1)

    # 4. 解析输出
    try:
        results = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"❌ 解析 Node 输出失败: {e}")
        print(f"Node stdout:\n{result.stdout[:2000]}")
        sys.exit(1)

    # 5. 更新 DB
    ok = 0
    err = 0
    skipped = 0
    with engine.begin() as conn:
        for item in results:
            rid = item["id"]
            if item.get("error"):
                print(f"   ❌ ID={rid}: {item['error']}")
                err += 1
                continue
            # 检查新旧是否相同（避免无意义写入）
            new_json = item["newJson"]
            old_row = [r for r in rows if r.id == rid]
            if old_row:
                old_json = old_row[0].extracted_json
                try:
                    old_parsed = json.loads(old_json)
                    new_parsed = json.loads(new_json)
                    # 只比较账务字段（不比较 rawText、items 等）
                    old_amt = old_parsed.get("amount")
                    new_amt = new_parsed.get("amount")
                    old_tax = old_parsed.get("tax")
                    new_tax = new_parsed.get("tax")
                    old_total = old_parsed.get("total")
                    new_total = new_parsed.get("total")
                    if old_amt == new_amt and old_tax == new_tax and old_total == new_total:
                        skipped += 1
                        # 打印无变化，不更新
                        continue
                except Exception:
                    pass

            # 有变化 → 更新
            conn.execute(
                text("UPDATE invoice_inbox SET extracted_json = :j WHERE id = :id"),
                {"j": new_json, "id": rid},
            )
            ok += 1
            print(f"   ✅ ID={rid}: 已更新")
            try:
                np = json.loads(new_json)
                print(f"      金额={np.get('amount')} 税额={np.get('tax')} 总金额={np.get('total')}")
            except Exception:
                pass

    print(f"\n{'='*50}")
    print(f"批量重新解析完成:")
    print(f"  总处理: {len(results)} 条")
    print(f"  已更新: {ok} 条")
    print(f"  无变化: {skipped} 条")
    print(f"  错误:   {err} 条")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
