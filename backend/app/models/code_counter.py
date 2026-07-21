"""编码计数器表：为并发安全的业务编码（发票编码 / 报销单号等）分配单调递增序号。

设计要点：
- 每个「编码命名空间」(key) 一行，value 即当前已分配的最大序号。
- 序号分配走乐观锁（UPDATE ... WHERE value=:cur），多人/多请求并发也不会分到同一序号。
- 业务表上对编码本身加 UNIQUE 约束，作为最终兜底，杜绝任何残余碰撞。
"""
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class CodeCounter(Base):
    __tablename__ = "code_counters"

    key: Mapped[str] = mapped_column(String(120), primary_key=True)
    value: Mapped[int] = mapped_column(Integer, default=0)
