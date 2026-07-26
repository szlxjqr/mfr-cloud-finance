"""AI 会话（Copilot）ORM 模型：会话 + 消息落库（按 user_id 隔离，不跨设备）。

设计要点：
- AiSession 归属某个登录用户（accounts.id），跨用户不可见。
- AiMessage 存纯文本 content（用于回显/检索）+ parts_json（SSE 部件 JSON：token/table/confirm/done）。
- 删除会话级联删除其消息（cascade）。
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class AiSession(Base):
    """一个 Copilot 对话会话，归属某个用户。"""

    __tablename__ = "ai_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)  # 对应 accounts.id
    title: Mapped[str] = mapped_column(String(200), default="新对话")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

    messages: Mapped[list["AiMessage"]] = relationship(
        "AiMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="AiMessage.created_at",
    )


class AiMessage(Base):
    """会话中的一条消息（user / assistant / system）。"""

    __tablename__ = "ai_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("ai_sessions.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(20))  # user / assistant / system
    content: Mapped[str] = mapped_column(Text, default="")  # 纯文本（回显/检索）
    parts_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # SSE 部件 JSON
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    session: Mapped["AiSession"] = relationship("AiSession", back_populates="messages")
