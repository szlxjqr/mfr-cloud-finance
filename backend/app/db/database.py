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
    from app.models import invoice as _invoice  # noqa: F401
    from app.models import reimburse as _reimburse  # noqa: F401
    from app.models import code_counter as _code_counter  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_invoice_code_column(engine)


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
