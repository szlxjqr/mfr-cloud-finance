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

# SQLite 单文件库需关闭同线程检查；云端数据库无需该参数
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

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

    当前尚无业务模型；后续模块（合同 / 税务 / 报销等）模型继承 Base 并导入后，
    应用启动时调用本函数即可自动建表。
    """
    # 未来在此导入模型以注册到 Base.metadata，例如：
    #   from app.models import contract, tax, reimbursement  # noqa: F401
    Base.metadata.create_all(bind=engine)
