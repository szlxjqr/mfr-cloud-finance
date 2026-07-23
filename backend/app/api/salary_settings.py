"""工资设置 API：全局薪资计算参数（社保/公积金/个税口径）。

GET  /salary-settings          读取当前设置（无则建默认）
PUT  /salary-settings          保存设置
POST /salary-settings/calc-deductions
    依据当前设置，由应发组件（基本/绩效/加班/奖金）计算代扣与实发，
    供前端「按设置自动计算」回填工资单，落实「工资设置生效」。
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.services import salary_service as svc
from app.models import salary_setting as m

router = APIRouter(prefix="/salary-settings", tags=["salary-settings"])


class SalarySettingUpdate(BaseModel):
    social_personal_rate: Optional[float] = None
    fund_personal_rate: Optional[float] = None
    tax_threshold: Optional[float] = None
    tax_method: Optional[str] = None  # 月度税率表 | 固定比例
    tax_flat_rate: Optional[float] = None


class SalaryCalcRequest(BaseModel):
    base_salary: Optional[float] = 0
    performance: Optional[float] = 0
    overtime: Optional[float] = 0
    bonus: Optional[float] = 0


@router.get("", response_model=dict)
def get_setting(db: Session = Depends(get_db)):
    st = svc.get_settings(db)
    return {
        "social_personal_rate": float(st.social_personal_rate or 0),
        "fund_personal_rate": float(st.fund_personal_rate or 0),
        "tax_threshold": float(st.tax_threshold or 0),
        "tax_method": st.tax_method or "月度税率表",
        "tax_flat_rate": float(st.tax_flat_rate or 0),
    }


@router.put("", response_model=dict)
def save_setting(payload: SalarySettingUpdate, db: Session = Depends(get_db)):
    allowed_methods = {"月度税率表", "固定比例"}
    if payload.tax_method and payload.tax_method not in allowed_methods:
        raise HTTPException(status_code=422, detail="tax_method 仅支持：月度税率表 / 固定比例")
    st = svc.save_settings(db, payload.model_dump(exclude_unset=True))
    return {
        "social_personal_rate": float(st.social_personal_rate or 0),
        "fund_personal_rate": float(st.fund_personal_rate or 0),
        "tax_threshold": float(st.tax_threshold or 0),
        "tax_method": st.tax_method or "月度税率表",
        "tax_flat_rate": float(st.tax_flat_rate or 0),
    }


@router.post("/calc-deductions", response_model=dict)
def calc_deductions(payload: SalaryCalcRequest, db: Session = Depends(get_db)):
    """按当前设置计算代扣与实发（不落库，供前端回填）。"""
    return svc.compute_deductions(
        db,
        base_salary=payload.base_salary,
        performance=payload.performance,
        overtime=payload.overtime,
        bonus=payload.bonus,
    )
