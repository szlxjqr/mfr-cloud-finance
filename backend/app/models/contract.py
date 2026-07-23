"""合同管理相关 ORM 模型：往来单位 + 人事/销售/采购合同 + 合同模板。

人事合同（HRContract）字段按《深圳市劳动合同（适用全日制用工）》标准范本
（深圳市人力资源和社会保障局编制）所需信息补齐，并支持：
- employee_id 联动员工档案（姓名/身份证/部门/岗位自动带出）
- party_a 自动取系统公司设置（无需手填）
- 状态机 草稿 → 待审批 → 已生效 → 已到期/已终止
- 审批后生效，可按标准范本打印
"""
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
    """人事合同（劳动合同等）。状态机：草稿 → 待审批 → 已生效 → 已到期/已终止。"""

    __tablename__ = "hr_contracts"
    id: Mapped[int] = mapped_column(primary_key=True)
    # === 员工联动 ===
    employee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("employees.id"))  # 关联员工档案
    employee_no: Mapped[Optional[str]] = mapped_column(String(8))  # 工号（冗余便于打印）
    employee_name: Mapped[str] = mapped_column(String(100), nullable=False)
    id_number: Mapped[Optional[str]] = mapped_column(String(30))  # 身份证
    department: Mapped[Optional[str]] = mapped_column(String(50))  # 部门
    position: Mapped[Optional[str]] = mapped_column(String(50))  # 岗位
    phone: Mapped[Optional[str]] = mapped_column(String(20))  # 联系电话

    # === 合同类型 / 期限 ===
    contract_type: Mapped[str] = mapped_column(String(30), default="劳动合同")
    contract_term: Mapped[Optional[str]] = mapped_column(String(20))  # 有固定期限/无固定期限/以完成一定工作任务为期限
    sign_date: Mapped[Optional[date]] = mapped_column(Date)  # 签订日期
    start_date: Mapped[Optional[date]] = mapped_column(Date)  # 合同开始
    end_date: Mapped[Optional[date]] = mapped_column(Date)  # 合同结束

    # === 试用期 ===
    probation_months: Mapped[Optional[int]] = mapped_column(Integer)  # 试用期月数
    probation_start: Mapped[Optional[date]] = mapped_column(Date)
    probation_end: Mapped[Optional[date]] = mapped_column(Date)
    probation_salary: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))

    # === 工作内容/地点/时间 ===
    work_content: Mapped[Optional[str]] = mapped_column(String(200))  # 岗位或工种
    work_location: Mapped[Optional[str]] = mapped_column(String(200))
    work_hours_type: Mapped[Optional[str]] = mapped_column(String(30))  # 标准工时/综合计算/不定时

    # === 劳动报酬 ===
    salary: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))  # 转正后基本工资
    pay_method: Mapped[Optional[str]] = mapped_column(String(20))  # 计时/计件
    pay_day: Mapped[Optional[int]] = mapped_column(Integer)  # 每月发放日

    # === 保险/福利/其他 ===
    social_insurance: Mapped[Optional[str]] = mapped_column(String(255))  # 社保约定
    benefits: Mapped[Optional[str]] = mapped_column(Text)  # 福利待遇
    party_a: Mapped[Optional[str]] = mapped_column(String(200))  # 公司（自动取系统设置）
    party_b: Mapped[Optional[str]] = mapped_column(String(100))  # 员工（自动带出）

    # === 状态机 + 审批 ===
    status: Mapped[str] = mapped_column(String(20), default="草稿")  # 草稿/待审批/已生效/已到期/已终止
    approver: Mapped[Optional[str]] = mapped_column(String(50))
    approve_date: Mapped[Optional[date]] = mapped_column(Date)
    approve_remark: Mapped[Optional[str]] = mapped_column(Text)

    # === 模板 + 附件 ===
    template_id: Mapped[Optional[int]] = mapped_column(ForeignKey("contract_templates.id"))  # 使用的合同模板
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
