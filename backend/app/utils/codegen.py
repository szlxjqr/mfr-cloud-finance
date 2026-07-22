"""并发安全的业务编码生成器（统一原则：适用于所有业务编码，不止发票）。

── 编码结构 ──
- 发票编码：FP + YYYYMMDD + 类型码(2) + 当日序号(4) = 16 位，人可读。
- 报销单号：BXGL + 4位年 + 4位序号（沿用既有规则）。

── 唯一性 / 防碰撞原则（通用，适用于所有编码生成）──
1. 序号由 code_counters 表「乐观锁」原子分配：
       UPDATE code_counters SET value=:v WHERE key=:k AND value=:cur
   仅当当前值仍等于读取时的值才更新成功（rowcount==1）；
   并发竞争者读取到的旧值已失效，UPDATE 影响 0 行 → 自动重试，永不分到同一序号。
2. 连接层已设 busy_timeout（见 app/db/database.py），并发写会等待而非报 "database is locked"。
3. 业务表对编码列加 UNIQUE 约束，作为最终兜底，即便逻辑异常也绝不入库重复编码。
4. 新命名空间的序号从 0 起；报销单号等需"继承历史最大编号"的场景，
   通过 seed 参数从已有数据中取最大序号作为起点，避免与历史编号碰撞。
"""
from datetime import date
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


# 发票类型 -> 2 位类型码（人可读）
INVOICE_TYPE_CODE: dict[str, str] = {
    "增值税专用发票": "ZP",
    "增值税普通发票": "PP",
    "电子专用发票": "SD",
    "电子普通发票": "SP",
    "数电专票": "SD",
    "数电普票": "SP",
    "火车票": "HP",
    "机票": "JP",
    "机动车销售统一发票": "JD",
    "其他": "QT",
}
DEFAULT_TYPE_CODE = "QT"


def invoice_type_code(inv_type: Optional[str]) -> str:
    """发票类型 -> 2 位类型码；未知类型回落默认 QT。"""
    return INVOICE_TYPE_CODE.get((inv_type or "").strip(), DEFAULT_TYPE_CODE)


def _ensure_counter(db: Session, key: str, seed: int = 0) -> None:
    """确保计数器行存在；不存在则以 seed 初始化（用于继承历史最大编号）。"""
    db.execute(
        text("INSERT OR IGNORE INTO code_counters(key, value) VALUES(:k, :v)"),
        {"k": key, "v": int(seed)},
    )
    db.flush()


def _alloc_seq(db: Session, key: str, retries: int = 100) -> int:
    """乐观锁分配下一个序号，并发安全、单调递增、全局唯一。"""
    for _ in range(retries):
        row = db.execute(
            text("SELECT value FROM code_counters WHERE key=:k"), {"k": key}
        ).fetchone()
        if row is None:
            # 兜底：理论上 _ensure_counter 已建行
            db.execute(
                text("INSERT OR IGNORE INTO code_counters(key, value) VALUES(:k, 0)"),
                {"k": key},
            )
            db.flush()
            continue
        nxt = int(row[0]) + 1
        res = db.execute(
            text("UPDATE code_counters SET value=:v WHERE key=:k AND value=:cur"),
            {"v": nxt, "k": key, "cur": int(row[0])},
        )
        if getattr(res, "rowcount", 0) == 1:
            db.flush()
            return nxt
        # 竞争失败，重试
    raise RuntimeError(f"分配编码序号失败（key={key}）")


def gen_invoice_code(
    db: Session,
    invoice_type: Optional[str],
    invoice_date: Optional[date] = None,
    today: Optional[date] = None,
) -> str:
    """生成 16 位可读发票编码：FP + YYYYMMDD + 类型码(2) + 当日序号(4)。"""
    d = invoice_date or today or date.today()
    ymd = d.strftime("%Y%m%d")
    tt = invoice_type_code(invoice_type)
    key = f"INV|{ymd}|{tt}"
    _ensure_counter(db, key, seed=0)
    seq = _alloc_seq(db, key)
    return f"FP{ymd}{tt}{seq:04d}"


def gen_bill_no(db: Session, year: Optional[int] = None) -> str:
    """生成报销单号：BXGL + 4位年 + 4位序号。

    首次使用该年份时，从已有 BXGL{year} 编号里取最大序号作为起点（seed），
    避免与历史编号碰撞；之后走同一并发安全分配器。
    """
    y = year or date.today().year
    key = f"BILL|{y}"
    mx = db.execute(
        text(
            "SELECT COALESCE(MAX(CAST(SUBSTR(bill_no, -4) AS INTEGER)), 0) "
            "FROM reimbursement_bills WHERE bill_no LIKE :p"
        ),
        {"p": f"BXGL{y}%"},
    ).fetchone()[0]
    _ensure_counter(db, key, seed=int(mx or 0))
    seq = _alloc_seq(db, key)
    return f"BXGL{y}{seq:04d}"


def _seed_from_req_no(db: Session, table: str, prefix: str, year: int) -> int:
    """从已有 {prefix}{year} 单号里取末尾 4 位最大序号作为 seed（防碰撞）。"""
    mx = db.execute(
        text(
            "SELECT COALESCE(MAX(CAST(SUBSTR(req_no, -4) AS INTEGER)), 0) "
            f"FROM {table} WHERE req_no LIKE :p"
        ),
        {"p": f"{prefix}{year}%"},
    ).fetchone()[0]
    return int(mx or 0)


def gen_purchase_no(db: Session, year: Optional[int] = None) -> str:
    """生成采购申请单号：CG + 4位年 + 4位序号。"""
    y = year or date.today().year
    key = f"PUR|{y}"
    seed = _seed_from_req_no(db, "purchase_requisitions", "CG", y)
    _ensure_counter(db, key, seed=seed)
    seq = _alloc_seq(db, key)
    return f"CG{y}{seq:04d}"


def gen_travel_no(db: Session, year: Optional[int] = None) -> str:
    """生成差旅申请单号：CL + 4位年 + 4位序号。"""
    y = year or date.today().year
    key = f"TRV|{y}"
    seed = _seed_from_req_no(db, "travel_requisitions", "CL", y)
    _ensure_counter(db, key, seed=seed)
    seq = _alloc_seq(db, key)
    return f"CL{y}{seq:04d}"


def gen_voucher_no(db: Session, year: Optional[int] = None, month: Optional[int] = None) -> "tuple[str, int]":
    """生成记账凭证号：记-YYYY-MM-NNNN（返回 (凭证号, 序号)）。

    按月计序、并发安全（复用乐观锁分配器）。凭证字固定「记」。
    """
    from datetime import date as _date

    now = _date.today()
    y = year or now.year
    m = month or now.month
    key = f"VCH|{y}{m:02d}"
    _ensure_counter(db, key, seed=0)
    seq = _alloc_seq(db, key)
    return (f"记-{y}-{m:02d}-{seq:04d}", seq)
