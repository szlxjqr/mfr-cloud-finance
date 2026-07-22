"""财务报表 API：三大报表 + 季报，全部由凭证分录实时派生。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.financial_statement import (
    BalanceSheetOut,
    CashFlowOut,
    IncomeStatementOut,
    QuarterOut,
)
from app.services import financial_statement_service as fs

router = APIRouter(prefix="/financial", tags=["financial"])


@router.get("/balance-sheet", response_model=BalanceSheetOut)
def get_balance_sheet(
    period: str = Query(None, description="YYYY-MM，不传则返回累计"),
    db: Session = Depends(get_db),
):
    """资产负债表：期末余额，损益按表结法自动结转至本年利润。"""
    return fs.balance_sheet(db, period=period)


@router.get("/income-statement", response_model=IncomeStatementOut)
def get_income_statement(
    period: str = Query(None, description="YYYY-MM，不传则返回累计"),
    db: Session = Depends(get_db),
):
    """利润表：本期金额 + 本年累计金额 双列。"""
    return fs.income_statement(db, period=period)


@router.get("/cash-flow", response_model=CashFlowOut)
def get_cash_flow(
    period: str = Query(None, description="YYYY-MM，不传则返回累计"),
    db: Session = Depends(get_db),
):
    """现金流量表：现金类科目按对方科目分类 经营/投资/筹资。"""
    return fs.cash_flow_statement(db, period=period)


@router.get("/quarterly", response_model=QuarterOut)
def get_quarterly(
    year: int = Query(..., description="年份，如 2026"),
    quarter: int = Query(..., ge=1, le=4, description="季度 1-4"),
    db: Session = Depends(get_db),
):
    """季报：季度内利润/现金流求和，资产负债表取季末月份快照。"""
    return fs.quarter_report(db, year=year, quarter=quarter)
