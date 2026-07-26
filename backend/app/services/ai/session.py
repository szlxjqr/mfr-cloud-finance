"""会话 / 消息 落库 CRUD（按 user_id 隔离，不跨设备）。"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_session import AiMessage, AiSession


def create_session(db: Session, user_id: int, title: str = "新对话") -> AiSession:
    obj = AiSession(user_id=user_id, title=title)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_session(db: Session, session_id: int, user_id: int) -> Optional[AiSession]:
    obj = db.get(AiSession, session_id)
    if not obj or obj.user_id != user_id:
        return None
    return obj


def list_sessions(db: Session, user_id: int) -> list[AiSession]:
    return list(
        db.scalars(
            select(AiSession)
            .where(AiSession.user_id == user_id)
            .order_by(AiSession.updated_at.desc())
        ).all()
    )


def delete_session(db: Session, session_id: int, user_id: int) -> bool:
    obj = get_session(db, session_id, user_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


def add_message(
    db: Session,
    session_id: int,
    role: str,
    content: str,
    parts_json: Optional[str] = None,
) -> AiMessage:
    obj = AiMessage(
        session_id=session_id, role=role, content=content, parts_json=parts_json
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    # 触碰会话的 updated_at（级联更新）
    sess = db.get(AiSession, session_id)
    if sess:
        sess.updated_at = datetime.now()
        db.commit()
    return obj


def get_messages(db: Session, session_id: int) -> list[AiMessage]:
    return list(
        db.scalars(
            select(AiMessage)
            .where(AiMessage.session_id == session_id)
            .order_by(AiMessage.created_at.asc())
        ).all()
    )


def build_openai_messages(db: Session, session_id: int, system_prompt: str) -> list[dict]:
    """将会话历史拼成 OpenAI 格式 messages（system + 历史），供 Provider 调用。"""
    msgs = [{"role": "system", "content": system_prompt}]
    for m in get_messages(db, session_id):
        msgs.append({"role": m.role, "content": m.content or ""})
    return msgs
