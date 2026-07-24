"""回写期间 + 重排凭证号 + 补「资本实缴 100 万」凭证 + 标记已审核。

必须在后端「停止」时运行（直接改库）。

逻辑：
- 每张凭证按 source_type/source_no 回查业务单，取目标月份：
    工资单    -> salary_bills.period
    报销单    -> reimbursement_bills.remark（造数时写入 YYYY-MM）
    采购申请  -> purchase_requisitions.expected_date 的 YYYY-MM
    资本实缴  -> source_no 形如 CAP-2026-06-20
- 资本实缴无对应业务接口，本脚本直接插一张凭证：
    借 1002 银行存款 1,000,000 / 贷 3001 实收资本 1,000,000（2026-06-20）
- 全部凭证按 (期间, 凭证日期, id) 重排 记-YYYY-MM-NNNN，并置 status=已审核。
"""
import sqlite3
import os
import datetime

DB = os.path.join(os.path.dirname(__file__), "smart_finance.db")
CAP_AMT = 1000000  # 100 万


def main():
    c = sqlite3.connect(DB)
    c.execute("PRAGMA foreign_keys=OFF")

    # 1) 资本实缴凭证（如不存在）
    if not c.execute("SELECT 1 FROM vouchers WHERE source_no='CAP-2026-06-20'").fetchone():
        now = datetime.datetime.now()
        cur = c.execute(
            """INSERT INTO vouchers
               (voucher_no,voucher_date,period,voucher_word,seq,attach_count,maker,status,source_type,source_no,summary,created_at)
               VALUES ('记-2026-06-0000','2026-06-20','2026-06','记',0,1,'测试-系统','未审核','资本实缴','CAP-2026-06-20','实收资本注入（股东沈雷）',?)""",
            (now,),
        )
        vid = cur.lastrowid
        c.execute(
            """INSERT INTO voucher_entries (voucher_id,seq,subject_code,subject_name,summary,direction,amount)
               VALUES (?,1,'1002','银行存款','实收资本注入（股东沈雷）','借',?)""",
            (vid, CAP_AMT),
        )
        c.execute(
            """INSERT INTO voucher_entries (voucher_id,seq,subject_code,subject_name,summary,direction,amount)
               VALUES (?,2,'3001','实收资本','实收资本注入（股东沈雷）','贷',?)""",
            (vid, CAP_AMT),
        )
        print("  inserted 资本实缴 voucher")
    else:
        print("  资本实缴 voucher already exists")

    # 2) 回写每张凭证的期间与日期
    def target(vtype, sno):
        if vtype == "资本实缴":
            return ("2026-06", "2026-06-20")
        if vtype == "工资单":
            r = c.execute("SELECT period FROM salary_bills WHERE salary_no=?", (sno,)).fetchone()
            p = r[0] if r else "2026-07"
            return (p, f"{p}-10")
        if vtype == "报销单":
            r = c.execute("SELECT remark FROM reimbursement_bills WHERE bill_no=?", (sno,)).fetchone()
            p = (r[0] if (r and r[0]) else "2026-07")
            return (p, f"{p}-15")
        if vtype == "采购申请":
            r = c.execute("SELECT expected_date FROM purchase_requisitions WHERE req_no=?", (sno,)).fetchone()
            if r and r[0]:
                d = str(r[0])
                return (d[:7], d)
            return ("2026-07", "2026-07-01")
        return ("2026-07", "2026-07-01")

    upd = []
    for vid, vtype, sno in c.execute("SELECT id,source_type,source_no FROM vouchers"):
        p, d = target(vtype, sno)
        upd.append((p, d, vid))
    c.executemany("UPDATE vouchers SET period=?, voucher_date=? WHERE id=?", upd)
    print(f"  backdated {len(upd)} vouchers")

    # 3) 按 (期间, 日期, id) 重排凭证号并置已审核
    counters = {}
    for vid, vno in c.execute(
        "SELECT id,voucher_no FROM vouchers ORDER BY period, voucher_date, id"
    ):
        p = c.execute("SELECT period FROM vouchers WHERE id=?", (vid,)).fetchone()[0]
        counters[p] = counters.get(p, 0) + 1
        seq = counters[p]
        newno = f"记-{p}-{seq:04d}"
        c.execute(
            "UPDATE vouchers SET voucher_no=?, seq=?, status='已审核' WHERE id=?",
            (newno, seq, vid),
        )
    print(f"  renumbered vouchers across {len(counters)} periods")

    c.commit()
    c.close()
    print("PATCH DONE")


if __name__ == "__main__":
    main()
