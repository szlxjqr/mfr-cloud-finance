"""人员管理 Pydantic 模型。"""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class EmployeeBase(BaseModel):
    name: str
    department: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    status: str = "在职"
    hire_date: Optional[date] = None


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = None
    hire_date: Optional[date] = None


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
