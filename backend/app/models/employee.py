"""人员管理 ORM 模型：员工档案 + 登录账号。

设计要点：
- Employee 存人事信息（员工编号 / 姓名 / 部门 / 职位 / 联系方式 / 状态）。
- Account 存登录凭据（账号 = 员工姓名全拼，密码 PBKDF2 哈希，关联员工编号）。
- 管理员 admin 固定绑定员工编号 00000000（见 db/database.py 种子）。
"""
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from app.db import Base


class Employee(Base):
    """员工档案：人员管理的核心锚点（采购申请人 / 差旅人 / 工资来源均关联此表）。"""

    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_no: Mapped[str] = mapped_column(String(8), unique=True, index=True)  # 8 位员工编号，admin = 00000000
    name: Mapped[str] = mapped_column(String(50), nullable=False)  # 姓名
    department: Mapped[Optional[str]] = mapped_column(String(50))  # 部门
    position: Mapped[Optional[str]] = mapped_column(String(50))  # 职位
    phone: Mapped[Optional[str]] = mapped_column(String(20))  # 手机号
    email: Mapped[Optional[str]] = mapped_column(String(100))  # 邮箱
    status: Mapped[str] = mapped_column(String(10), default="在职")  # 在职 / 离职
    hire_date: Mapped[Optional[date]] = mapped_column(Date)  # 入职日期
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    account: Mapped[Optional["Account"]] = relationship(
        "Account",
        back_populates="employee",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class Account(Base):
    """登录账号：账号为员工姓名全拼，密码哈希存储，不直接存明文。"""

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)  # 全拼账号
    password_hash: Mapped[str] = mapped_column(String(200))  # PBKDF2 哈希
    employee_no: Mapped[str] = mapped_column(
        ForeignKey("employees.employee_no", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(20), default="employee")  # admin / employee
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    employee: Mapped["Employee"] = relationship("Employee", back_populates="account")
