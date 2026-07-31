"""工资自动扣减回归防线（HTTP 接口级，路线 A）。

针对缺陷：新建/修改工资单时，代扣项（社保个人 / 公积金个人 / 个税）不采信前端传值，
必须由后端依据「全局工资设置」(salary_settings 单例) 强制重算后覆盖，
避免前端漏传导致代扣落 0（汇总页社保/公积金/个税全为 ¥0）。

口径（默认设置：社保 10.5% / 公积金 12% / 起征点 5000 / 月度税率表）：
    应发   = 基本 + 绩效 + 加班 + 奖金
    社保   = 应发 × 10.5%
    公积金 = 应发 × 12%
    应纳税所得额 = 应发 − 社保 − 公积金 − 5000
    个税   = 按月度税率表（≤0 记 0）
    代扣合计 = 社保 + 公积金 + 个税；实发 = 应发 − 代扣合计

真实库纪律：全部经根 conftest 重定向至临时 SQLite，绝不触碰 backend/smart_finance.db。
测试数据统一带「测试」标记。
"""
import pytest

# 默认工资设置（与 app/models/salary_setting.py 的默认值一致）
_DEFAULT_SETTINGS = {
    "social_personal_rate": 10.5,
    "fund_personal_rate": 12,
    "tax_threshold": 5000,
    "tax_method": "月度税率表",
    "tax_flat_rate": 3,
}


def _f(v):
    """派生字段可能被序列化为字符串（Decimal）或数字，统一转 float 后比较。"""
    return float(v) if v is not None else None


def _assert_deductions(body, *, gross, social, fund, tax):
    """断言一张工资单的应发 / 代扣三项 / 代扣合计 / 实发。"""
    deduct = round(social + fund + tax, 2)
    net = round(gross - deduct, 2)
    assert _f(body["gross_pay"]) == pytest.approx(gross, abs=0.01), "应发不符"
    assert _f(body["social_personal"]) == pytest.approx(social, abs=0.01), "社保个人不符"
    assert _f(body["fund_personal"]) == pytest.approx(fund, abs=0.01), "公积金个人不符"
    assert _f(body["tax_personal"]) == pytest.approx(tax, abs=0.01), "个税不符"
    assert _f(body["deduct_total"]) == pytest.approx(deduct, abs=0.01), "代扣合计不符"
    assert _f(body["net_pay"]) == pytest.approx(net, abs=0.01), "实发不符"


@pytest.fixture
def restore_settings(client):
    """用例可自由修改工资设置，退出时恢复默认，避免污染其它测试。"""
    yield
    resp = client.put("/api/salary-settings", json=_DEFAULT_SETTINGS)
    assert resp.status_code == 200


def _create(client, **overrides):
    payload = {
        "employee_name": "测试员工甲",
        "department": "测试部门",
        "period": "2099-01",
        "base_salary": 4000,
        "remark": "自动扣减测试",
    }
    payload.update(overrides)
    resp = client.post("/api/salaries", json=payload)
    assert resp.status_code == 201, f"新建工资单失败：{resp.status_code} {resp.text}"
    return resp.json()


# ── 1. 核心回归防线：不传代扣项，后端必须按全局设置自动算出 ──
def test_create_bill_auto_deduct(db, client):
    """应发 4000、前端完全不传代扣项 → 社保 420 / 公积金 480 / 个税 0 / 代扣 900 / 实发 3100。"""
    body = _create(client)

    # 应纳税所得额 = 4000 - 420 - 480 - 5000 < 0 → 个税 0
    _assert_deductions(body, gross=4000, social=420, fund=480, tax=0)

    # 落库校验：不是只在响应里算对，数据库里也必须存对（汇总页读的是库）
    from app.models import salary as sm

    obj = db.get(sm.SalaryBill, body["id"])
    assert obj is not None
    assert float(obj.social_personal) == pytest.approx(420, abs=0.01)
    assert float(obj.fund_personal) == pytest.approx(480, abs=0.01)
    assert float(obj.deduct_total) == pytest.approx(900, abs=0.01)
    assert float(obj.net_pay) == pytest.approx(3100, abs=0.01)


# ── 2. X 强制口径：前端传错的代扣值必须被覆盖 ──
def test_create_bill_overrides_frontend_values(db, client):
    """应发 20000 且前端传入错误代扣值 → 一律被后端计算结果覆盖。"""
    body = _create(
        client,
        employee_name="测试员工乙",
        base_salary=20000,
        social_personal=1,
        fund_personal=2,
        tax_personal=3,
        deduct_total=6,
        net_pay=19994,
    )

    # 社保 2100 / 公积金 2400；taxable = 20000-2100-2400-5000 = 10500
    # 10500 ≤ 12000 → 10500×10% − 210 = 840
    _assert_deductions(body, gross=20000, social=2100, fund=2400, tax=840)
    assert _f(body["deduct_total"]) == pytest.approx(5340, abs=0.01)
    assert _f(body["net_pay"]) == pytest.approx(14660, abs=0.01)


# ── 3. 修改工资单：改应发 + 传错代扣值 → 强制重算覆盖 ──
def test_update_bill_recompute(db, client):
    """update 时应发变化、且前端传入错误代扣值 → 按设置重算覆盖。"""
    created = _create(client, employee_name="测试员工丙", base_salary=4000)
    _assert_deductions(created, gross=4000, social=420, fund=480, tax=0)

    resp = client.put(
        f"/api/salaries/{created['id']}",
        json={
            "base_salary": 12000,
            "performance": 5000,
            "bonus": 3000,
            "social_personal": 0,      # 前端漏传/传 0，必须被覆盖
            "fund_personal": 0,
            "tax_personal": 0,
            "deduct_total": 0,
            "net_pay": 20000,
        },
    )
    assert resp.status_code == 200, f"修改工资单失败：{resp.status_code} {resp.text}"
    body = resp.json()

    # 应发 = 12000+5000+3000 = 20000 → 与用例 2 同口径
    _assert_deductions(body, gross=20000, social=2100, fund=2400, tax=840)

    # 落库校验
    from app.models import salary as sm

    obj = db.get(sm.SalaryBill, created["id"])
    assert float(obj.deduct_total) == pytest.approx(5340, abs=0.01)
    assert float(obj.net_pay) == pytest.approx(14660, abs=0.01)


def test_update_bill_only_component_change(db, client):
    """只改应发组件、完全不传代扣字段 → 代扣项仍随之重算（不会残留旧值）。"""
    created = _create(client, employee_name="测试员工丁", base_salary=20000)
    _assert_deductions(created, gross=20000, social=2100, fund=2400, tax=840)

    resp = client.put(f"/api/salaries/{created['id']}", json={"base_salary": 4000})
    assert resp.status_code == 200
    # 应发降为 4000 → 代扣必须同步降为 420/480/0，而不是残留 2100/2400/840
    _assert_deductions(resp.json(), gross=4000, social=420, fund=480, tax=0)


# ── 4. 设置变更后新建单据，代扣随之变化 ──
def test_settings_change_reflected(db, client, restore_settings):
    """改 salary_settings 的社保/公积金比例 → 新建工资单的代扣项随之变化。"""
    # 先按默认设置建一张，作为基线
    base = _create(client, employee_name="测试员工戊", base_salary=20000)
    _assert_deductions(base, gross=20000, social=2100, fund=2400, tax=840)

    # 调整设置：社保 8% / 公积金 5%
    resp = client.put(
        "/api/salary-settings",
        json={"social_personal_rate": 8, "fund_personal_rate": 5},
    )
    assert resp.status_code == 200, f"保存工资设置失败：{resp.status_code} {resp.text}"
    assert resp.json()["social_personal_rate"] == pytest.approx(8, abs=0.01)
    assert resp.json()["fund_personal_rate"] == pytest.approx(5, abs=0.01)

    # 新建单据应采用新比例：社保 1600 / 公积金 1000
    # taxable = 20000-1600-1000-5000 = 12400 → 12400×20% − 1410 = 1070
    after = _create(client, employee_name="测试员工己", base_salary=20000)
    _assert_deductions(after, gross=20000, social=1600, fund=1000, tax=1070)

    # 同一张旧单据触发 update 时，也应按新设置重算
    resp = client.put(f"/api/salaries/{base['id']}", json={"remark": "设置变更后重算"})
    assert resp.status_code == 200
    _assert_deductions(resp.json(), gross=20000, social=1600, fund=1000, tax=1070)


def test_settings_flat_rate_method(db, client, restore_settings):
    """个税切「固定比例」模式 → 个税按固定税率计算，同样强制覆盖前端传值。"""
    resp = client.put(
        "/api/salary-settings",
        json={"tax_method": "固定比例", "tax_flat_rate": 10},
    )
    assert resp.status_code == 200

    # 应发 20000：社保 2100 / 公积金 2400 / taxable 10500 → 固定 10% = 1050
    body = _create(
        client,
        employee_name="测试员工庚",
        base_salary=20000,
        social_personal=999,
        fund_personal=999,
        tax_personal=999,
    )
    _assert_deductions(body, gross=20000, social=2100, fund=2400, tax=1050)
