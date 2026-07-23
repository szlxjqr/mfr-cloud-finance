"""固定资产 Pydantic 模型。

派生字段（累计折旧/月折旧额/净值）由 service 实时计算后随读返回，
此处仅声明；计算逻辑集中在 services/asset_service.py。
"""
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class FixedAssetBase(BaseModel):
    asset_no: Optional[str] = None
    name: str
    category: Optional[str] = "办公设备"  # 房屋建筑物/机器设备/办公设备/运输工具/电子设备/其他
    department: Optional[str] = None
    acquisition_date: Optional[date] = None
    original_value: Optional[Decimal] = None
    salvage_rate: Optional[Decimal] = None  # 残值率（%）
    useful_life: Optional[Decimal] = None  # 使用年限（年）
    dep_subject_code: Optional[str] = "5602"  # 折旧费用计入科目
    remark: Optional[str] = None


class FixedAssetCreate(FixedAssetBase):
    pass


class FixedAssetUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    department: Optional[str] = None
    acquisition_date: Optional[date] = None
    original_value: Optional[Decimal] = None
    salvage_rate: Optional[Decimal] = None
    useful_life: Optional[Decimal] = None
    dep_subject_code: Optional[str] = None
    remark: Optional[str] = None
    status: Optional[str] = None  # 允许手动改 在用/闲置


class FixedAssetRead(FixedAssetBase):
    id: int
    accum_dep: Optional[Decimal] = None
    status: str
    record_date: Optional[date] = None
    record_voucher_no: Optional[str] = None
    dispose_date: Optional[date] = None
    dispose_voucher_no: Optional[str] = None
    monthly_dep: Optional[Decimal] = None  # 当月折旧额（派生）
    net_value: Optional[Decimal] = None  # 净值 = 原值 − 累计折旧（派生）
    model_config = ConfigDict(from_attributes=True)


class DepRecordRead(BaseModel):
    id: int
    asset_id: int
    period: str
    amount: Optional[Decimal] = None
    voucher_no: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class AssetSummary(BaseModel):
    total_original: float
    total_accum_dep: float
    total_net: float
    in_use_count: int
    total_count: int


class DepPreviewItem(BaseModel):
    id: int
    asset_no: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    department: Optional[str] = None
    original_value: float = 0.0
    accum_dep: float = 0.0
    monthly_dep: float = 0.0
    net_value: float = 0.0
    dep_subject_code: str = "5602"


class ActionBody(BaseModel):
    """入账 / 处置 / 计提 等动作的请求体（审批人 + 可选日期）。"""
    maker: Optional[str] = None
    action_date: Optional[date] = None


class DepreciateBody(BaseModel):
    period: str  # YYYY-MM
    maker: Optional[str] = None
