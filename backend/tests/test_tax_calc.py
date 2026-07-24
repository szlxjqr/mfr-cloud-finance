"""税务计算回归测试：个税（计算 + 取数）与印花税（按合同计征）。

覆盖：
- compute_deductions：月度税率表算个税（社保/公积金/起征点口径）
- individual_tax：仅统计 已通过/已发放 工资单（草稿/待审批排除）
- stamp_tax：销售/采购合同按金额 0.03% 计征，草稿合同排除
"""
import pytest
from datetime import date
from decimal import Decimal
from sqlalchemy import select, text

from app.models import salary as sm
from app.models import contract as cm
from app.services import salary_service as salary_svc
from app.services import tax_service as tax_svc

STAMP_RATE = 0.0003  # tax_service.STAMP_RATE


def _make_salary_bill(db, **kw):
    defaults = dict(
        salary_no="GZ2026TEST01",
        employee_name="张三",
        employee_no="E001",
        department="研发部",
        period="2026-01",
        base_salary=Decimal("20000"),
        gross_pay=Decimal("20000"),
        social_personal=Decimal("2000"),
        fund_personal=Decimal("2400"),
        tax_personal=Decimal("850"),
        deduct_total=Decimal("5250"),
        net_pay=Decimal("14750"),
        status="已通过",
    )
    defaults.update(kw)
    b = sm.SalaryBill(**defaults)
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


def test_compute_deductions_monthly_tax(db):
    """月薪 20000：社保10%/公积金12%/起征点5000 → 个税 850。"""
    salary_svc.save_settings(
        db,
        {
            "social_personal_rate": "10",
            "fund_personal_rate": "12",
            "tax_threshold": "5000",
            "tax_method": "月度税率表",
        },
    )
    r = salary_svc.compute_deductions(db, base_salary=20000)
    assert r["gross_pay"] == pytest.approx(20000.0)
    assert r["social_personal"] == pytest.approx(2000.0)
    assert r["fund_personal"] == pytest.approx(2400.0)
    # taxable = 20000 - 2000 - 2400 - 5000 = 10600 → 10600*10% - 210 = 850
    assert r["tax_personal"] == pytest.approx(850.0)
    assert r["deduct_total"] == pytest.approx(5250.0)
    assert r["net_pay"] == pytest.approx(14750.0)


def test_individual_tax_excludes_draft(db):
    """个税申报仅含 已通过/已发放；草稿被排除。"""
    _make_salary_bill(db, employee_name="张三", gross_pay=Decimal("20000"), tax_personal=Decimal("1000"), status="已通过")
    _make_salary_bill(db, salary_no="GZ2026TEST02", employee_name="李四", department="行政部",
                      gross_pay=Decimal("8000"), social_personal=Decimal("800"), fund_personal=Decimal("960"),
                      tax_personal=Decimal("200"), deduct_total=Decimal("1960"), net_pay=Decimal("6040"), status="已发放")
    # 草稿不应计入
    _make_salary_bill(db, salary_no="GZ2026TEST03", employee_name="王五", department="行政部",
                      gross_pay=Decimal("5000"), tax_personal=Decimal("50"), status="草稿")

    res = tax_svc.individual_tax(db, "2026-01")
    assert res["headcount"] == 2
    assert res["total_gross"] == pytest.approx(28000.0)
    assert res["total_tax"] == pytest.approx(1200.0)
    names = {r["employee_name"] for r in res["rows"]}
    assert names == {"张三", "李四"}


def test_stamp_tax_by_contract(db):
    """销售+采购合同按金额 0.03% 计征；草稿合同排除。"""
    db.execute(text("DELETE FROM sales_contracts"))
    db.execute(text("DELETE FROM purchase_contracts"))
    db.commit()

    db.add(cm.SalesContract(contract_no="XS-T1", amount=Decimal("1000000"),
                            sign_date=date(2026, 3, 1), status="执行中"))
    db.add(cm.PurchaseContract(contract_no="CG-T1", amount=Decimal("500000"),
                               sign_date=date(2026, 5, 1), status="已完成"))
    # 草稿不应计征
    db.add(cm.SalesContract(contract_no="XS-T2", amount=Decimal("9999999"),
                            sign_date=date(2026, 6, 1), status="草稿"))
    db.commit()

    res = tax_svc.stamp_tax(db)
    assert res["contract_count"] == 2
    assert res["total_amount"] == pytest.approx(1500000.0)
    # 1000000*0.03% + 500000*0.03% = 300 + 150 = 450
    assert res["total_tax"] == pytest.approx(450.0)
    types = {r["type"] for r in res["rows"]}
    assert types == {"销售合同", "采购合同"}


def test_stamp_tax_rate_value(db):
    """单合同印花税税率 0.03%，金额 200000 → 60。"""
    db.execute(text("DELETE FROM sales_contracts"))
    db.execute(text("DELETE FROM purchase_contracts"))
    db.commit()
    db.add(cm.SalesContract(contract_no="XS-R", amount=Decimal("200000"),
                            sign_date=date(2026, 1, 10), status="执行中"))
    db.commit()
    res = tax_svc.stamp_tax(db)
    assert res["total_amount"] == pytest.approx(200000.0)
    assert res["total_tax"] == pytest.approx(200000.0 * STAMP_RATE)
