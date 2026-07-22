"""登录鉴权 API：登录获取 Token、获取当前登录用户。

前端在请求拦截器中携带 `Authorization: Bearer <token>`；
业务接口通过 get_current_user 依赖校验身份。
"""
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Optional

from app.db import get_db
from app.models import employee as m
from app.schemas import employee as s
from app.utils import security

router = APIRouter(prefix="/auth", tags=["auth"])


async def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> m.Account:
    """鉴权依赖：从 Authorization 头解析 Bearer Token，返回当前账号（无效则 401）。

    供 /auth/me 与业务接口（如人员管理）复用，确保登录态真实有效。
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录或登录已过期")
    token = authorization.split(" ", 1)[1]
    payload = security.verify_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已过期，请重新登录")
    acc = db.scalar(select(m.Account).where(m.Account.username == payload["sub"]))
    if not acc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号不存在")
    return acc


@router.post("/login", response_model=s.LoginResponse)
def login(payload: s.LoginRequest, db: Session = Depends(get_db)):
    """用户名 + 密码登录，成功返回自签名 Token。"""
    acc = db.scalar(select(m.Account).where(m.Account.username == payload.username.strip()))
    if not acc or not security.verify_password(payload.password, acc.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    emp = acc.employee
    token = security.generate_token(acc.username, acc.role, acc.employee_no)
    return s.LoginResponse(
        token=token,
        username=acc.username,
        role=acc.role,
        employee_no=acc.employee_no,
        name=emp.name if emp else None,
    )


@router.get("/me", response_model=s.CurrentUser)
def get_me(current: m.Account = Depends(get_current_user)):
    """返回当前登录用户。"""
    emp = current.employee
    return s.CurrentUser(
        username=current.username,
        role=current.role,
        employee_no=current.employee_no,
        name=emp.name if emp else None,
    )
