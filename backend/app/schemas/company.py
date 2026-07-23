"""公司设置 Pydantic 模型（全局单例）。"""
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CompanySettingsBase(BaseModel):
    company_name: Optional[str] = None  # 深圳市流形机器人科技有限公司
    legal_rep: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    tax_no: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    contact: Optional[str] = None
    email: Optional[str] = None
    remark: Optional[str] = None


class CompanySettingsUpdate(CompanySettingsBase):
    """全部字段可选（PUT 表示更新任意子集）。"""
    pass


class CompanySettingsRead(CompanySettingsBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
