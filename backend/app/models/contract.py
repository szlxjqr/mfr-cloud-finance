"""合同管理相关 ORM 模型：往来单位 + 人事/销售/采购合同 + 合同模板。"""
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Parties(Base):
    """往来单位：客户 / 供应商。"""

    __tablename__ = "parties"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    tax_no: Mapped[Optional[str]] = mapped_column(String(50))
    ptype: Mapped[str] = mapped_column(String(20), default="customer")  # customer / supplier
    contact: Mapped[Optional[str]] = mapped_column(String(50))
    phone: Mapped[Optional[str]] = mapped_column(String(30))
    address: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default="enabled")  # enabled / disabled
    remark: Mapped[Optional[str]] = mapped_column(Text)


class HRContract(Base):
    """人事合同。"""

    __tablename__ = "hr_contracts"
    id: Mapped[int] = mapped_column(primary_key=True)
    employee_name: Mapped[str] = mapped_column(String(100), nullable=False)
    id_number: Mapped[Optional[str]] = mapped_column(String(30))  # 身份证，脱敏 * 原样保留
    contract_type: Mapped[str] = mapped_column(String(30), default="劳动合同")
    party_a: Mapped[Optional[str]] = mapped_column(String(200))  # 公司
    party_b: Mapped[Optional[str]] = mapped_column(String(100))  # 员工
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="生效")  # 生效/到期/终止/续签中
    salary: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    attachment_path: Mapped[Optional[str]] = mapped_column(String(500))
    remark: Mapped[Optional[str]] = mapped_column(Text)


class SalesContract(Base):
    """销售合同。"""

    __tablename__ = "sales_contracts"
    id: Mapped[int] = mapped_column(primary_key=True)
    contract_no: Mapped[Optional[str]] = mapped_column(String(50))
    customer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("parties.id"))
    sign_date: Mapped[Optional[date]] = mapped_column(Date)
    effective_date: Mapped[Optional[date]] = mapped_column(Date)
    expire_date: Mapped[Optional[date]] = mapped_column(Date)
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    tax_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4))
    tax_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    status: Mapped[str] = mapped_column(String(20), default="草稿")  # 草稿/执行中/已完成/终止/纠纷
    attachment_path: Mapped[Optional[str]] = mapped_column(String(500))
    remark: Mapped[Optional[str]] = mapped_column(Text)


class PurchaseContract(Base):
    """采购合同。"""

    __tablename__ = "purchase_contracts"
    id: Mapped[int] = mapped_column(primary_key=True)
    contract_no: Mapped[Optional[str]] = mapped_column(String(50))
    supplier_id: Mapped[Optional[int]] = mapped_column(ForeignKey("parties.id"))
    sign_date: Mapped[Optional[date]] = mapped_column(Date)
    effective_date: Mapped[Optional[date]] = mapped_column(Date)
    expire_date: Mapped[Optional[date]] = mapped_column(Date)
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    tax_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4))
    tax_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    status: Mapped[str] = mapped_column(String(20), default="草稿")
    attachment_path: Mapped[Optional[str]] = mapped_column(String(500))
    remark: Mapped[Optional[str]] = mapped_column(Text)


class ContractTemplate(Base):
    """合同模板（按类型维护模板内容）。"""

    __tablename__ = "contract_templates"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    ctype: Mapped[str] = mapped_column(String(20), default="hr")  # hr / sales / purchase
    content: Mapped[Optional[str]] = mapped_column(Text)
    remark: Mapped[Optional[str]] = mapped_column(Text)
