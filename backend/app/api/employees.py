"""人员管理 API：员工档案 CRUD + 新增时自动生成全拼登录账号。

业务规则：
- 新增员工时，按其姓名全拼自动创建登录账号（如「沈雷」→shenlei）。
- 全拼账号若存在冲突，追加数字后缀（shenlei1 / shenlei2 ...）。
- 初始密码统一为 123456，首次登录后建议修改（改密功能后续补充）。
"""
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pypinyin import Style, lazy_pinyin
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import employee as m
from app.schemas import employee as s
from app.api.auth import get_current_user
from app.utils import security

router = APIRouter(prefix="/employees", tags=["employees"])

_INITIAL_PASSWORD = "123456"


def _to_pinyin_full(name: str) -> str:
    """姓名转全拼小写，如「沈雷」→ shenlei。"""
    return "".join(lazy_pinyin(name, style=Style.NORMAL)).lower()


def _gen_username(db: Session, name: str) -> str:
    """生成不重复的全拼账号：冲突时追加数字后缀。"""
    base = _to_pinyin_full(name) or "user"
    base = "".join(ch for ch in base if ch.isalnum())
    if not base:
        base = "user"
    username = base
    suffix = 1
    while db.scalar(select(m.Account).where(m.Account.username == username)):
        username = f"{base}{suffix}"
        suffix += 1
    return username


def _next_employee_no(db: Session) -> str:
    """生成下一个 8 位员工编号（不含 admin 的 00000000）。"""
    max_no = db.scalar(
        select(func.max(m.Employee.employee_no)).where(m.Employee.employee_no != "00000000")
    )
    if not max_no:
        return "00000001"
    try:
        num = int(max_no) + 1
    except ValueError:
        num = 1
    return f"{num:08d}"


@router.get("", response_model=list[s.EmployeeRead])
def list_employees(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    current_user: m.Account = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """员工列表，支持按姓名 / 部门 / 编号关键字、在职状态筛选。"""
    stmt = select(m.Employee)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(
            m.Employee.name.like(like)
            | m.Employee.department.like(like)
            | m.Employee.employee_no.like(like)
        )
    if status:
        stmt = stmt.where(m.Employee.status == status)
    stmt = stmt.order_by(m.Employee.employee_no)
    emps = db.scalars(stmt).all()
    result = []
    for e in emps:
        d = s.EmployeeRead.model_validate(e)
        d.username = e.account.username if e.account else None
        result.append(d)
    return result


@router.post("", response_model=s.EmployeeRead, status_code=status.HTTP_201_CREATED)
def create_employee(payload: s.EmployeeCreate, current_user: m.Account = Depends(get_current_user), db: Session = Depends(get_db)):
    """新增员工，并自动创建全拼登录账号（初始密码 123456）。"""
    emp_no = _next_employee_no(db)
    emp = m.Employee(
        employee_no=emp_no,
        name=payload.name,
        department=payload.department,
        position=payload.position,
        phone=payload.phone,
        email=payload.email,
        status=payload.status or "在职",
        hire_date=payload.hire_date,
    )
    db.add(emp)
    db.flush()
    username = _gen_username(db, payload.name)
    acc = m.Account(
        username=username,
        password_hash=security.hash_password(_INITIAL_PASSWORD),
        employee_no=emp_no,
        role="employee",
    )
    db.add(acc)
    db.commit()
    db.refresh(emp)
    out = s.EmployeeRead.model_validate(emp)
    out.username = username
    return out


@router.put("/{employee_no}", response_model=s.EmployeeRead)
def update_employee(employee_no: str, payload: s.EmployeeUpdate, current_user: m.Account = Depends(get_current_user), db: Session = Depends(get_db)):
    """编辑员工档案（姓名 / 部门 / 职位等）。"""
    emp = db.scalar(select(m.Employee).where(m.Employee.employee_no == employee_no))
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="员工不存在")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(emp, k, v)
    db.commit()
    db.refresh(emp)
    out = s.EmployeeRead.model_validate(emp)
    out.username = emp.account.username if emp.account else None
    return out


@router.delete("/{employee_no}")
def delete_employee(employee_no: str, current_user: m.Account = Depends(get_current_user), db: Session = Depends(get_db)):
    """删除员工（级联删除其登录账号）。admin(00000000) 受保护。"""
    if employee_no == "00000000":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="管理员账号不可删除")
    emp = db.scalar(select(m.Employee).where(m.Employee.employee_no == employee_no))
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="员工不存在")
    db.delete(emp)
    db.commit()
    return {"ok": True, "deleted": employee_no}
