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
    employee_name: str
    id_number: Optional[str] = None
    contract_type: str = "劳动合同"
    party_a: Optional[str] = None
    party_b: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str = "生效"
    salary: Optional[Decimal] = None
    attachment_path: Optional[str] = None
    remark: Optional[str] = None


class HRContractCreate(HRContractBase):
    pass


class HRContractUpdate(BaseModel):
    employee_name: Optional[str] = None
    id_number: Optional[str] = None
    contract_type: Optional[str] = None
    party_a: Optional[str] = None
    party_b: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None
    salary: Optional[Decimal] = None
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
