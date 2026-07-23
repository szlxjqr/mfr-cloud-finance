"""工资管理 Pydantic 模型。

派生字段（gross_pay / deduct_total / net_pay）由组件字段计算后存储，
此处仅声明，计算逻辑集中在 api/salary.py 的 _derive() 中统一处理。
"""
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SalaryBillBase(BaseModel):
    salary_no: Optional[str] = None
    employee_name: str
    employee_no: Optional[str] = None
    department: Optional[str] = None
    period: str  # YYYY-MM
    base_salary: Optional[Decimal] = None
    performance: Optional[Decimal] = None
    overtime: Optional[Decimal] = None
    bonus: Optional[Decimal] = None
    social_personal: Optional[Decimal] = None
    fund_personal: Optional[Decimal] = None
    tax_personal: Optional[Decimal] = None
    # 派生字段允许前端传入（后端会以组件重算覆盖，保证单一来源）
    gross_pay: Optional[Decimal] = None
    deduct_total: Optional[Decimal] = None
    net_pay: Optional[Decimal] = None
    status: str = "草稿"
    submit_date: Optional[date] = None
    approve_date: Optional[date] = None
    pay_date: Optional[date] = None
    approver: Optional[str] = None
    payee: Optional[str] = None
    approve_remark: Optional[str] = None
    pay_remark: Optional[str] = None
    remark: Optional[str] = None


class SalaryBillCreate(SalaryBillBase):
    pass


class SalaryBillUpdate(BaseModel):
    salary_no: Optional[str] = None
    employee_name: Optional[str] = None
    employee_no: Optional[str] = None
    department: Optional[str] = None
    period: Optional[str] = None
    base_salary: Optional[Decimal] = None
    performance: Optional[Decimal] = None
    overtime: Optional[Decimal] = None
    bonus: Optional[Decimal] = None
    social_personal: Optional[Decimal] = None
    fund_personal: Optional[Decimal] = None
    tax_personal: Optional[Decimal] = None
    gross_pay: Optional[Decimal] = None
    deduct_total: Optional[Decimal] = None
    net_pay: Optional[Decimal] = None
    status: Optional[str] = None
    submit_date: Optional[date] = None
    approve_date: Optional[date] = None
    pay_date: Optional[date] = None
    approver: Optional[str] = None
    payee: Optional[str] = None
    approve_remark: Optional[str] = None
    pay_remark: Optional[str] = None
    remark: Optional[str] = None


class SalaryBillRead(SalaryBillBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ApprovalBody(BaseModel):
    approver: str
    remark: Optional[str] = None
