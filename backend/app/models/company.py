"""公司设置 ORM 模型（全局单例 id=1）。

为合同/工资/报表等所有单据的「甲方/公司名/法人/地址/联系方式」提供单一数据来源，
避免在每张单据里重复填写公司信息。变更后即刻影响所有联动单据。
"""
from typing import Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class CompanySettings(Base):
    """公司设置：全局唯一的甲方信息（单人公司对应一家公司）。"""

    __tablename__ = "company_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False, default=1)
    company_name: Mapped[Optional[str]] = mapped_column(String(200))  # 深圳市流形机器人科技有限公司
    legal_rep: Mapped[Optional[str]] = mapped_column(String(50))  # 法定代表人
    address: Mapped[Optional[str]] = mapped_column(String(255))  # 注册地址
    phone: Mapped[Optional[str]] = mapped_column(String(30))  # 联系电话
    tax_no: Mapped[Optional[str]] = mapped_column(String(50))  # 税号
    bank_name: Mapped[Optional[str]] = mapped_column(String(100))  # 开户行
    bank_account: Mapped[Optional[str]] = mapped_column(String(50))  # 账号
    contact: Mapped[Optional[str]] = mapped_column(String(50))  # 联系人
    email: Mapped[Optional[str]] = mapped_column(String(100))
    remark: Mapped[Optional[str]] = mapped_column(Text)
