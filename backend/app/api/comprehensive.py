"""综合报表 API 路由：跨模块实时聚合看板数据。"""

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.comprehensive import ComprehensiveOverview
from app.services import comprehensive_service

router = APIRouter(prefix="/comprehensive", tags=["comprehensive"])


@router.get("/overview", response_model=ComprehensiveOverview)
def get_overview(
    period: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """综合报表看板：资金 / 经营趋势 / 税务 / 业务概况 / 凭证概况 一次性聚合。"""
    return comprehensive_service.overview(db, period=period)
