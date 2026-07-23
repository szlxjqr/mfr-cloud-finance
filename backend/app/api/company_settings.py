"""公司设置 API：全局单例（id=1），为合同/工资/报表的甲方信息提供单一数据来源。

首次访问时自动种入默认值（深圳市流形机器人科技有限公司占位），
后续 PUT 修改后即影响所有联动单据。
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import company as m
from app.schemas import company as s

router = APIRouter(prefix="/company-settings", tags=["company-settings"])


def _get_or_seed(db: Session) -> m.CompanySettings:
    """读取单例；不存在则写入空记录（id=1），保证前端 PUT 永远更新。"""
    obj = db.get(m.CompanySettings, 1)
    if not obj:
        obj = m.CompanySettings(
            id=1,
            company_name="深圳市流形机器人科技有限公司",  # 默认值，老板在「公司设置」页可改
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
    return obj


@router.get("", response_model=s.CompanySettingsRead)
def get_settings(db: Session = Depends(get_db)):
    """获取公司设置（单例）。首次访问自动种入默认值。"""
    return _get_or_seed(db)


@router.put("", response_model=s.CompanySettingsRead)
def update_settings(payload: s.CompanySettingsUpdate, db: Session = Depends(get_db)):
    """更新公司设置（任意字段子集）。"""
    obj = _get_or_seed(db)
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
