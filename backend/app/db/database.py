"""数据库基础设置：引擎 / 会话 / 基类 / 依赖注入。

设计要点：
- 开发默认 SQLite（本地文件库 smart_finance.db），零配置即可跑起来。
- 生产部署通过环境变量 DATABASE_URL 切换为云 PostgreSQL（如云厂商 RDS），
  满足「可连数据库、可上云」的硬性要求，且连接串不硬编码。
- 业务模块模型统一继承 Base；应用启动时调用 init_db() 自动建表。
"""
import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# 生产环境示例：DATABASE_URL=postgresql://user:pass@host:5432/smart_finance
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./smart_finance.db")

# SQLite 单文件库需关闭同线程检查；云端数据库无需该参数。
# busy_timeout：并发写时等待（毫秒）而非立即报 "database is locked"，
# 这是并发安全编码生成器（乐观锁）能成立的底层前提。
_connect_args = (
    {"check_same_thread": False, "timeout": 30}
    if DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(DATABASE_URL, connect_args=_connect_args, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    """所有 ORM 模型的声明基类。"""


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：每个请求一个独立 Session，结束时自动关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """初始化数据库表。

    业务模型统一继承 Base 并在此导入注册，create_all 自动建表；
    对「已存在的旧库」额外处理：补加新列 / 唯一索引 / 计数器表。
    """
    # 导入模型以注册到 Base.metadata（create_all 才能建出对应表）
    from app.models import contract  # noqa: F401
    from app.models import employee as _employee  # noqa: F401
    from app.models import invoice as _invoice  # noqa: F401
    from app.models import reimburse as _reimburse  # noqa: F401
    from app.models import purchase as _purchase  # noqa: F401
    from app.models import travel as _travel  # noqa: F401
    from app.models import subject as _subject  # noqa: F401
    from app.models import voucher as _voucher  # noqa: F401
    from app.models import salary as _salary  # noqa: F401
    from app.models import code_counter as _code_counter  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_invoice_code_column(engine)
    _ensure_reimbursement_bills_columns(engine)
    _ensure_purchase_columns(engine)
    _ensure_employees_columns(engine)
    _seed_admin(engine)
    _seed_subjects(engine)


def _ensure_invoice_code_column(engine) -> None:
    """为已存在的 invoices 表补加 invoice_code 列 + 唯一索引。

    SQLite 的 create_all 只会建缺失的表、不会给已存在的表加列，
    故单独处理；新库由模型 unique 约束建好，跳过即可。
    """
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    cols = [c["name"] for c in inspector.get_columns("invoices")]
    if "invoice_code" in cols:
        return
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE invoices ADD COLUMN invoice_code VARCHAR(16)"))
        conn.execute(
            text("CREATE UNIQUE INDEX IF NOT EXISTS uq_invoice_code ON invoices(invoice_code)")
        )


def _ensure_reimbursement_bills_columns(engine) -> None:
    """为已存在的 reimbursement_bills 表补加审批相关字段与报销类型/差旅字段。

    - bill_type：报销类型（采购报销 / 差旅报销），旧行回填 '采购报销'
    - traveler / travel_destination / travel_start / travel_end：差旅报销专属字段
    """
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    cols = [c["name"] for c in inspector.get_columns("reimbursement_bills")]
    with engine.begin() as conn:
        if "approver" not in cols:
            conn.execute(text("ALTER TABLE reimbursement_bills ADD COLUMN approver VARCHAR(100)"))
        if "approve_remark" not in cols:
            conn.execute(text("ALTER TABLE reimbursement_bills ADD COLUMN approve_remark TEXT"))
        # 报销类型与差旅专属字段
        if "bill_type" not in cols:
            conn.execute(text("ALTER TABLE reimbursement_bills ADD COLUMN bill_type VARCHAR(20)"))
            conn.execute(text("UPDATE reimbursement_bills SET bill_type = '采购报销' WHERE bill_type IS NULL"))
        if "traveler" not in cols:
            conn.execute(text("ALTER TABLE reimbursement_bills ADD COLUMN traveler VARCHAR(100)"))
        if "travel_destination" not in cols:
            conn.execute(text("ALTER TABLE reimbursement_bills ADD COLUMN travel_destination VARCHAR(200)"))
        if "travel_start" not in cols:
            conn.execute(text("ALTER TABLE reimbursement_bills ADD COLUMN travel_start DATE"))
        if "travel_end" not in cols:
            conn.execute(text("ALTER TABLE reimbursement_bills ADD COLUMN travel_end DATE"))


def _ensure_purchase_columns(engine) -> None:
    """为已存在的 purchase_requisitions 表补加「研发项目」相关字段。"""
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    cols = [c["name"] for c in inspector.get_columns("purchase_requisitions")]
    with engine.begin() as conn:
        if "is_rd_project" not in cols:
            conn.execute(text("ALTER TABLE purchase_requisitions ADD COLUMN is_rd_project VARCHAR(10)"))
            conn.execute(text("UPDATE purchase_requisitions SET is_rd_project = '否' WHERE is_rd_project IS NULL"))
        if "rd_project_code" not in cols:
            conn.execute(text("ALTER TABLE purchase_requisitions ADD COLUMN rd_project_code VARCHAR(100)"))


def _ensure_employees_columns(engine) -> None:
    """为已存在的 employees 表补加身份证 / 性别 / 生日字段。

    SQLite 的 create_all 只会建缺失的表、不会给已存在的表加列，故单独处理。
    """
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    cols = [c["name"] for c in inspector.get_columns("employees")]
    with engine.begin() as conn:
        if "id_card" not in cols:
            conn.execute(text("ALTER TABLE employees ADD COLUMN id_card VARCHAR(18)"))
        if "gender" not in cols:
            conn.execute(text("ALTER TABLE employees ADD COLUMN gender VARCHAR(4)"))
        if "birthday" not in cols:
            conn.execute(text("ALTER TABLE employees ADD COLUMN birthday DATE"))


def _seed_admin(engine) -> None:
    """初始化管理员：固定员工编号 00000000 + 账号 admin（密码 admin123，role=admin）。

    仅在 accounts 表为空时执行，避免重复写入覆盖线上数据。
    账号 admin / 密码 admin123 仅为初始凭据，上线前应通过环境变量或后台修改。
    """
    from sqlalchemy import select, text

    from app.models import employee as _models
    from app.utils import security

    with SessionLocal() as db:
        exists = db.scalar(select(_models.Account).limit(1))
        if exists:
            return

        # 管理员员工档案
        admin_emp = _models.Employee(
            employee_no="00000000",
            name="管理员",
            department="管理层",
            position="系统管理员",
            status="在职",
        )
        db.add(admin_emp)
        db.flush()

        admin_acc = _models.Account(
            username="admin",
            password_hash=security.hash_password("admin123"),
            employee_no="00000000",
            role="admin",
        )
        db.add(admin_acc)
        db.commit()


# 标准会计科目（小企业会计准则风格）。code 即层级表达；direction 为正常余额方向。
# voucher_service 的科目映射全部引用这里的 code，新增/调整科目在此维护。
_SUBJECT_SEED: list[dict] = [
    # ── 资产类（借）──
    {"code": "1001", "name": "库存现金", "category": "资产", "direction": "借"},
    {"code": "1002", "name": "银行存款", "category": "资产", "direction": "借"},
    {"code": "1122", "name": "应收账款", "category": "资产", "direction": "借"},
    {"code": "1123", "name": "预付账款", "category": "资产", "direction": "借"},
    {"code": "1403", "name": "原材料", "category": "资产", "direction": "借"},
    {"code": "1405", "name": "库存商品", "category": "资产", "direction": "借"},
    {"code": "1601", "name": "固定资产", "category": "资产", "direction": "借"},
    # ── 负债类（贷）──
    {"code": "2202", "name": "应付账款", "category": "负债", "direction": "贷"},
    {"code": "2211", "name": "应付职工薪酬", "category": "负债", "direction": "贷"},
    {"code": "2221", "name": "应交税费", "category": "负债", "direction": "贷", "level": 1},
    {"code": "2221.01", "name": "应交增值税", "category": "负债", "direction": "贷", "level": 2, "parent_code": "2221"},
    {"code": "2221.01.01", "name": "进项税额", "category": "负债", "direction": "贷", "level": 3, "parent_code": "2221.01"},
    {"code": "2221.01.02", "name": "销项税额", "category": "负债", "direction": "贷", "level": 3, "parent_code": "2221.01"},
    {"code": "2241", "name": "其他应付款", "category": "负债", "direction": "贷"},
    # ── 权益类（贷）──
    {"code": "3001", "name": "实收资本", "category": "权益", "direction": "贷"},
    {"code": "3103", "name": "本年利润", "category": "权益", "direction": "贷"},
    {"code": "3104", "name": "利润分配", "category": "权益", "direction": "贷"},
    # ── 成本类（借）──
    {"code": "4001", "name": "生产成本", "category": "成本", "direction": "借"},
    {"code": "4101", "name": "制造费用", "category": "成本", "direction": "借"},
    {"code": "4301", "name": "研发支出", "category": "成本", "direction": "借"},
    # ── 损益类 ──
    {"code": "5001", "name": "主营业务收入", "category": "损益", "direction": "贷"},
    {"code": "5051", "name": "其他业务收入", "category": "损益", "direction": "贷"},
    {"code": "5401", "name": "主营业务成本", "category": "损益", "direction": "借"},
    {"code": "5601", "name": "销售费用", "category": "损益", "direction": "借"},
    {"code": "5602", "name": "管理费用", "category": "损益", "direction": "借"},
    {"code": "5603", "name": "财务费用", "category": "损益", "direction": "借"},
    {"code": "5801", "name": "所得税费用", "category": "损益", "direction": "借"},
]


def _seed_subjects(engine) -> None:
    """初始化标准会计科目：account_subjects 为空时写入（不清空已有数据）。"""
    from sqlalchemy import select, text

    from app.models import subject as _models

    with SessionLocal() as db:
        exists = db.scalar(select(_models.AccountSubject).limit(1))
        if exists:
            return
        for item in _SUBJECT_SEED:
            db.add(
                _models.AccountSubject(
                    code=item["code"],
                    name=item["name"],
                    category=item["category"],
                    direction=item["direction"],
                    level=item.get("level", 1),
                    parent_code=item.get("parent_code"),
                    is_leaf=item.get("is_leaf", True),
                    status=item.get("status", "启用"),
                )
            )
        db.commit()
