"""工资分摊回归测试：部门占比 + 研发人力成本占比（rd_ratio）。

覆盖 salary_allocation：
- total_gross / total_headcount（按员工姓名去重）/ avg_gross
- 各部门 ratio = 部门应发 / 工资总额
- rd_ratio = 含「研发」部门应发合计 / 工资总额
- period 过滤：指定期间返回对应数据，无关期间返回空
"""
import pytest
from decimal import Decimal

from app.models import salary as sm
from app.services import salary_service as salary_svc


def _make_bill(db, **kw):
    defaults = dict(
        salary_no="GZ2026T01",
        employee_name="张三",
        department="研发部",
        period="2026-01",
        base_salary=Decimal("20000"),
        gross_pay=Decimal("20000"),
        status="已通过",
    )
    defaults.update(kw)
    b = sm.SalaryBill(**defaults)
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


def test_salary_allocation_ratio_and_rd(db):
    """5 名员工跨 2 部门：占比与研发占比正确。"""
    _make_bill(db, employee_name="张三", department="研发部", gross_pay=Decimal("20000"))
    _make_bill(db, salary_no="GZ2026T02", employee_name="李四", department="研发部", gross_pay=Decimal("10000"))
    _make_bill(db, salary_no="GZ2026T03", employee_name="王五", department="行政部", gross_pay=Decimal("8000"))
    _make_bill(db, salary_no="GZ2026T04", employee_name="赵六", department="研发部", gross_pay=Decimal("5000"))
    _make_bill(db, salary_no="GZ2026T05", employee_name="钱七", department="行政部", gross_pay=Decimal("2000"))

    res = salary_svc.salary_allocation(db)
    assert res["total_gross"] == pytest.approx(45000.0)
    assert res["total_headcount"] == 5
    assert res["avg_gross"] == pytest.approx(9000.0)

    by_dept = {r["department"]: r for r in res["rows"]}
    assert set(by_dept) == {"研发部", "行政部"}

    # 研发部 35000 / 45000 = 0.7778；行政部 10000 / 45000 = 0.2222
    assert by_dept["研发部"]["gross_total"] == pytest.approx(35000.0)
    assert by_dept["研发部"]["ratio"] == pytest.approx(0.7778, abs=1e-4)
    assert by_dept["行政部"]["ratio"] == pytest.approx(0.2222, abs=1e-4)

    # rd_ratio = (20000+10000+5000)/45000 = 0.7778
    assert res["rd_ratio"] == pytest.approx(0.7778, abs=1e-4)


def test_salary_allocation_rd_label_match(db):
    """「研发中心」等含「研发」字样的部门被计入研发占比。"""
    _make_bill(db, employee_name="张三", department="研发中心", gross_pay=Decimal("30000"))
    _make_bill(db, salary_no="GZ2026T02", employee_name="李四", department="行政部", gross_pay=Decimal("10000"))

    res = salary_svc.salary_allocation(db)
    assert res["total_gross"] == pytest.approx(40000.0)
    assert res["rd_ratio"] == pytest.approx(0.75, abs=1e-4)


def test_salary_allocation_period_filter(db):
    """period 过滤：无关期间返回空统计。"""
    _make_bill(db, employee_name="张三", department="研发部", period="2026-01", gross_pay=Decimal("10000"))
    res = salary_svc.salary_allocation(db, period="2026-02")
    assert res["total_gross"] == 0.0
    assert res["total_headcount"] == 0
    assert res["rd_ratio"] == 0.0
    assert res["rows"] == []

    # 指定有数据的期间则正常返回
    res2 = salary_svc.salary_allocation(db, period="2026-01")
    assert res2["total_gross"] == pytest.approx(10000.0)
    assert res2["rd_ratio"] == pytest.approx(1.0, abs=1e-4)
