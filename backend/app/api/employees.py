"""人员管理 API：员工档案 CRUD + 新增时自动生成全拼登录账号。

业务规则（一人公司 · 2026-07-22 确认）：
- 部门限定为 总经办 / 综合办 / 研发部 / 市场部（见 employee.DEPARTMENTS）。
- 身份证号 18 位，可自动带出 性别 / 出生日期。
- 姓名全拼自动创建登录账号（如「沈雷」→ shenlei），冲突追加数字后缀。
- 工号 8 位自增，admin 固定 00000000，其余从 00000001 递增。
- 系统角色 role：admin（系统管理员）/ gm（总经理，与 admin 同级）/ employee（普通员工）。
  职位 position 为自由文本，仅作人事展示，不绑定权限。
- 初始密码统一为 123456，首次登录后建议修改。
"""
import re
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
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

# 身份证校验权重与校验码
_ID_WEIGHTS = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
_ID_CHECK_CODES = ["1", "0", "X", "9", "8", "7", "6", "5", "4", "3", "2"]


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


def parse_id_card(id_card: str):
    """解析 18 位身份证号 → (性别, 出生日期 date 对象)。

    返回 (gender, birthday: date) 或 None（格式/校验位不合法）。
    第 7-14 位为出生日期 YYYYMMDD；第 17 位奇男偶女；第 18 位校验码。
    """
    if not id_card or len(id_card) != 18:
        return None
    if not id_card[:17].isdigit() or id_card[17] not in "0123456789Xx":
        return None
    # 校验位
    try:
        total = sum(int(id_card[i]) * _ID_WEIGHTS[i] for i in range(17))
        if _ID_CHECK_CODES[total % 11].upper() != id_card[17].upper():
            return None
    except Exception:
        return None
    try:
        y, mo, d = int(id_card[6:10]), int(id_card[10:12]), int(id_card[12:14])
        birthday = date(y, mo, d)
    except ValueError:
        return None
    gender = "男" if int(id_card[16]) % 2 == 1 else "女"
    return gender, birthday


@router.get("/username-preview", summary="预览姓名对应的登录账号")
def username_preview(
    name: str = Query(..., min_length=1, description="员工姓名"),
    db: Session = Depends(get_db),
):
    """前端姓名输入时实时预览将生成的登录账号（含冲突后缀）。"""
    return {"username": _gen_username(db, name)}


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
        d.role = e.account.role if e.account else None  # 角色存在 Account
        result.append(d)
    return result


@router.post("", response_model=s.EmployeeRead, status_code=status.HTTP_201_CREATED)
def create_employee(payload: s.EmployeeCreate, current_user: m.Account = Depends(get_current_user), db: Session = Depends(get_db)):
    """新增员工，并自动创建全拼登录账号（初始密码 123456）。"""
    # 部门白名单校验
    if payload.department and payload.department not in m.DEPARTMENTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"部门必须是 {m.DEPARTMENTS} 之一",
        )
    # 角色校验
    if payload.role not in s.ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"角色必须是 {s.ROLES} 之一",
        )
    # 身份证解析
    gender = None
    birthday = None
    if payload.id_card:
        parsed = parse_id_card(payload.id_card)
        if not parsed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="身份证号不合法（应为 18 位且校验位正确）",
            )
        gender, birthday = parsed

    emp_no = _next_employee_no(db)
    emp = m.Employee(
        employee_no=emp_no,
        name=payload.name,
        department=payload.department,
        position=payload.position,
        id_card=payload.id_card,
        gender=gender,
        birthday=birthday,
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
        role=payload.role or "employee",
    )
    db.add(acc)
    db.commit()
    db.refresh(emp)
    out = s.EmployeeRead.model_validate(emp)
    out.username = username
    out.role = acc.role  # 角色存在 Account，回填响应
    return out


@router.put("/{employee_no}", response_model=s.EmployeeRead)
def update_employee(employee_no: str, payload: s.EmployeeUpdate, current_user: m.Account = Depends(get_current_user), db: Session = Depends(get_db)):
    """编辑员工档案（姓名 / 部门 / 职位 / 身份证等）。"""
    emp = db.scalar(select(m.Employee).where(m.Employee.employee_no == employee_no))
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="员工不存在")
    data = payload.model_dump(exclude_unset=True)
    # 部门白名单
    if data.get("department") is not None and data["department"] not in m.DEPARTMENTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"部门必须是 {m.DEPARTMENTS} 之一",
        )
    # 角色校验
    if data.get("role") is not None and data["role"] not in s.ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"角色必须是 {s.ROLES} 之一",
        )
    # 身份证变更时重新解析
    if "id_card" in data:
        gender = None
        birthday = None
        if data["id_card"]:
            parsed = parse_id_card(data["id_card"])
            if not parsed:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="身份证号不合法（应为 18 位且校验位正确）",
                )
            gender, birthday = parsed
        data["gender"] = gender
        data["birthday"] = birthday
    for k, v in data.items():
        if k == "role":
            # 角色存在 Account 表，写回关联账号而非 Employee
            if emp.account is not None:
                emp.account.role = v
            continue
        setattr(emp, k, v)
    db.commit()
    db.refresh(emp)
    out = s.EmployeeRead.model_validate(emp)
    out.username = emp.account.username if emp.account else None
    out.role = emp.account.role if emp.account else None
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
