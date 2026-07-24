"""清空本库的「模拟测试数据」，保留科目表/员工/管理员账号/公司设置/合同模板。

用于按老板新口径（研发30万/差旅5万/房租1300/工资5000+4000/实缴100万/无营收）
从 2026-05 干净重造到 2026-12 的全年决算场景。

纪律：所有模拟记录均带「测试」标记；本脚本仅删测试造数，不动科目/员工/管理员。
"""
import sqlite3
import os

DB = os.path.join(os.path.dirname(__file__), "smart_finance.db")


def main():
    c = sqlite3.connect(DB)
    c.execute("PRAGMA foreign_keys=OFF")
    # 先删子表，再删主表，避免外键约束报错
    children = [
        "voucher_entries",
        "purchase_requisition_items",
    ]
    parents = [
        "vouchers",
        "salary_bills",
        "reimbursement_bills",
        "purchase_requisitions",
        "travel_requisitions",
        "invoices",
    ]
    for t in children + parents:
        try:
            n = c.execute(f"DELETE FROM {t}").rowcount
            print(f"  cleared {t}: {n} rows")
        except Exception as e:
            print(f"  skip {t}: {e}")
    # 重置编码计数器（后续按现有单据 MAX 自动续号；此处单据已清空，故从 0 起）
    try:
        c.execute("DELETE FROM code_counters")
        print("  cleared code_counters")
    except Exception as e:
        print(f"  skip code_counters: {e}")
    c.commit()
    # 校验保留项
    for t in ["account_subjects", "employees", "accounts", "company_settings"]:
        n = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  keep {t}: {n} rows")
    c.close()
    print("RESET DONE")


if __name__ == "__main__":
    main()
