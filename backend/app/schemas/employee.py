"""人员管理 Pydantic 模型。"""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

# 部门白名单（与模型 DEPARTMENTS 保持一致）
DEPARTMENTS = ["总经办", "综合办", "研发部", "市场部"]
# 账号角色
ROLES = ["admin", "gm", "employee"]


class EmployeeBase(BaseModel):
    name: str
    department: Optional[str] = Field(default=None, description="部门（见 DEPARTMENTS）")
    position: Optional[str] = None  # 职位（自由文本，不含权限含义）
    id_card: Optional[str] = Field(default=None, description="身份证号（18 位，可解析性别/生日）")
    gender: Optional[str] = None  # 男 / 女（由身份证号解析）
    birthday: Optional[date] = None  # 出生日期（由身份证号解析）
    phone: Optional[str] = None
    email: Optional[str] = None
    status: str = "在职"
    hire_date: Optional[date] = None
    role: str = "employee"  # 账号角色：admin / gm / employee


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    id_card: Optional[str] = None
    gender: Optional[str] = None
    birthday: Optional[date] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = None
    hire_date: Optional[date] = None
    role: Optional[str] = None


class EmployeeRead(EmployeeBase):
    id: int
    employee_no: str
    created_at: Optional[datetime] = None
    username: Optional[str] = None  # 关联账号（全拼）
    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    username: str
    role: str
    employee_no: str
    name: Optional[str] = None


class CurrentUser(BaseModel):
    username: str
    role: str
    employee_no: str
    name: Optional[str] = None
