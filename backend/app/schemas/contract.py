"""合同管理相关 Pydantic 模型。"""
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ---------------- 往来单位 ----------------
class PartyBase(BaseModel):
    name: str
    tax_no: Optional[str] = None
    ptype: str = "customer"  # customer / supplier
    contact: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    status: str = "enabled"
    remark: Optional[str] = None


class PartyCreate(PartyBase):
    pass


class PartyUpdate(BaseModel):
    name: Optional[str] = None
    tax_no: Optional[str] = None
    ptype: Optional[str] = None
    contact: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class PartyRead(PartyBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ---------------- 人事合同 ----------------
class HRContractBase(BaseModel):
    # 员工联动
    employee_id: Optional[int] = None
    employee_no: Optional[str] = None
    employee_name: str
    id_number: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    # 合同期限
    contract_type: str = "劳动合同"
    contract_term: Optional[str] = None  # 有固定期限/无固定期限/以完成一定工作任务为期限
    sign_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    # 试用期
    probation_months: Optional[int] = None
    probation_start: Optional[date] = None
    probation_end: Optional[date] = None
    probation_salary: Optional[Decimal] = None
    # 工作
    work_content: Optional[str] = None
    work_location: Optional[str] = None
    work_hours_type: Optional[str] = None
    # 报酬
    salary: Optional[Decimal] = None
    pay_method: Optional[str] = None
    pay_day: Optional[int] = None
    # 保险福利
    social_insurance: Optional[str] = None
    benefits: Optional[str] = None
    # 甲方乙方（甲方通常自动取系统设置，乙方自动从员工带出）
    party_a: Optional[str] = None
    party_b: Optional[str] = None
    # 状态/审批
    status: str = "草稿"  # 草稿/待审批/已生效/已到期/已终止
    approver: Optional[str] = None
    approve_date: Optional[date] = None
    approve_remark: Optional[str] = None
    # 模板
    template_id: Optional[int] = None
    attachment_path: Optional[str] = None
    remark: Optional[str] = None


class HRContractCreate(HRContractBase):
    # employee_name 在 _enrich_hr_data 中由 employee_id 自动带出，create 时允许省略
    employee_name: Optional[str] = None


class HRContractUpdate(BaseModel):
    employee_id: Optional[int] = None
    employee_no: Optional[str] = None
    employee_name: Optional[str] = None
    id_number: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    contract_type: Optional[str] = None
    contract_term: Optional[str] = None
    sign_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    probation_months: Optional[int] = None
    probation_start: Optional[date] = None
    probation_end: Optional[date] = None
    probation_salary: Optional[Decimal] = None
    work_content: Optional[str] = None
    work_location: Optional[str] = None
    work_hours_type: Optional[str] = None
    salary: Optional[Decimal] = None
    pay_method: Optional[str] = None
    pay_day: Optional[int] = None
    social_insurance: Optional[str] = None
    benefits: Optional[str] = None
    party_a: Optional[str] = None
    party_b: Optional[str] = None
    status: Optional[str] = None
    approver: Optional[str] = None
    approve_date: Optional[date] = None
    approve_remark: Optional[str] = None
    template_id: Optional[int] = None
    attachment_path: Optional[str] = None
    remark: Optional[str] = None


class HRContractRead(HRContractBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ---------------- 销售合同 ----------------
class SalesContractBase(BaseModel):
    contract_no: Optional[str] = None
    customer_id: Optional[int] = None
    sign_date: Optional[date] = None
    effective_date: Optional[date] = None
    expire_date: Optional[date] = None
    amount: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    status: str = "草稿"
    attachment_path: Optional[str] = None
    remark: Optional[str] = None


class SalesContractCreate(SalesContractBase):
    pass


class SalesContractUpdate(BaseModel):
    contract_no: Optional[str] = None
    customer_id: Optional[int] = None
    sign_date: Optional[date] = None
    effective_date: Optional[date] = None
    expire_date: Optional[date] = None
    amount: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    status: Optional[str] = None
    attachment_path: Optional[str] = None
    remark: Optional[str] = None


class SalesContractRead(SalesContractBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ---------------- 采购合同 ----------------
class PurchaseContractBase(BaseModel):
    contract_no: Optional[str] = None
    supplier_id: Optional[int] = None
    sign_date: Optional[date] = None
    effective_date: Optional[date] = None
    expire_date: Optional[date] = None
    amount: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    status: str = "草稿"
    attachment_path: Optional[str] = None
    remark: Optional[str] = None


class PurchaseContractCreate(PurchaseContractBase):
    pass


class PurchaseContractUpdate(BaseModel):
    contract_no: Optional[str] = None
    supplier_id: Optional[int] = None
    sign_date: Optional[date] = None
    effective_date: Optional[date] = None
    expire_date: Optional[date] = None
    amount: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    status: Optional[str] = None
    attachment_path: Optional[str] = None
    remark: Optional[str] = None


class PurchaseContractRead(PurchaseContractBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ---------------- 合同模板 ----------------
class ContractTemplateBase(BaseModel):
    name: str
    ctype: str = "hr"  # hr / sales / purchase
    content: Optional[str] = None
    remark: Optional[str] = None


class ContractTemplateCreate(ContractTemplateBase):
    pass


class ContractTemplateUpdate(BaseModel):
    name: Optional[str] = None
    ctype: Optional[str] = None
    content: Optional[str] = None
    remark: Optional[str] = None


class ContractTemplateRead(ContractTemplateBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
