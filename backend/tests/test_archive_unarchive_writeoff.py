"""业财联动「归档闸门 + 反归档(删除) + 冲销(红字)」闭环测试。

覆盖 2026-07-30 老板拍板的两条硬约束与自洽性结论：
1. 归档闸门：未归档不联动账务（工资/报销在归档/提交财务前不出凭证）。
2. 反归档(限admin/gm)：删除该业务单联动的全部凭证，业务回退，重提交新走一遍。
3. 支付/处置后禁反归档：提供红字冲销——借贷反向、金额相同的红冲凭证(已审核)即时抵消，
   原凭证标记「已冲销」保留，账务闭合。重复冲销拒绝。
"""
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models import employee as emp_m
from app.models import fixed_asset as fam
from app.models import invoice as im
from app.models import reimburse as rm
from app.models import salary as slm
from app.models import capital_contribution as ccm
from app.models import revenue as revm
from app.models import voucher as vm
from app.services import voucher_service as vs

import app.api.salary as salary_api
import app.api.reimburse as reimburse_api
import app.api.fixed_asset as fixed_api
import app.api.capital_contribution as cap_api
import app.api.revenue as rev_api
from app.schemas.fixed_asset import ActionBody


def _admin(db):
    """取测试库里已种子的 admin 账号，作为反归档/冲销操作人。"""
    return db.scalar(select(emp_m.Account).where(emp_m.Account.employee_no == "00000000"))


def _vouchers_for(db, source_no):
    return db.scalars(select(vm.Voucher).where(vm.Voucher.source_no == source_no)).all()


# ================= 核心助手：void / reverse =================
def test_void_deletes_all_by_source_no_and_cascades(db, make_voucher):
    """void_vouchers_by_source_no 按 source_no 删除全部凭证（含不同 source_type）并级联删分录。"""
    make_voucher(db, "2026-07", [("5602", "管理费用", "借", 100), ("2241", "其他应付", "贷", 100)],
                 source_type="报销单", source_no="BX-VOID-1")
    make_voucher(db, "2026-07", [("2241", "其他应付", "借", 100), ("1002", "银行存款", "贷", 100)],
                 source_type="报销支付", source_no="BX-VOID-1")
    assert len(_vouchers_for(db, "BX-VOID-1")) == 2

    n = vs.void_vouchers_by_source_no(db, "BX-VOID-1")
    assert n == 2
    assert _vouchers_for(db, "BX-VOID-1") == []
    # 分录级联删除：该 source_no 关联的凭证已无分录残留
    ent = db.scalars(
        select(vm.VoucherEntry).where(
            vm.VoucherEntry.voucher_id.in_(
                select(vm.Voucher.id).where(vm.Voucher.source_no == "BX-VOID-1")
            )
        )
    ).all()
    assert ent == []


def test_reverse_creates_red_and_marks_originals(db, make_voucher, voucher_sides):
    """reverse：对 source_no 下已审核凭证生成红冲凭证(已审核)，原凭证标记已冲销。"""
    make_voucher(db, "2026-07", [("5602", "管理费用", "借", 100), ("2241", "其他应付", "贷", 100)],
                 source_type="报销单", source_no="BX-REV-1", summary="计提")
    make_voucher(db, "2026-07", [("2241", "其他应付", "借", 100), ("1002", "银行存款", "贷", 100)],
                 source_type="报销支付", source_no="BX-REV-1", summary="支付")
    # 业务联动凭证在归档/支付后均为「已审核」，这里模拟该状态
    for v in _vouchers_for(db, "BX-REV-1"):
        v.status = "已审核"
        db.add(v)
    db.commit()

    originals = _vouchers_for(db, "BX-REV-1")
    assert len(originals) == 2 and all(v.status == "已审核" for v in originals)

    red_no, cnt = vs.reverse_vouchers_by_source_no(db, "BX-REV-1", maker="admin")
    assert cnt == 2
    assert red_no is not None

    reds = [v for v in _vouchers_for(db, "BX-REV-1") if v.source_type == vs.RED_SOURCE_TYPE]
    assert len(reds) == 1
    red = reds[0]
    assert red.status == "已审核", "红冲凭证应自动审核入账"
    d, c = voucher_sides(red)
    assert abs(d - c) < 0.005, "红冲凭证借贷必须平衡"
    # 原凭证标记已冲销
    for v in _vouchers_for(db, "BX-REV-1"):
        if v.source_type != vs.RED_SOURCE_TYPE:
            assert v.status == "已冲销", "原凭证应保留并标记已冲销"


def test_reverse_rejects_double(db, make_voucher):
    """重复冲销应被拒绝（已存在红冲凭证）。"""
    make_voucher(db, "2026-07", [("5602", "管理费用", "借", 100), ("2241", "其他应付", "贷", 100)],
                 source_type="报销单", source_no="BX-DBL-1")
    for v in _vouchers_for(db, "BX-DBL-1"):
        v.status = "已审核"
        db.add(v)
    db.commit()
    vs.reverse_vouchers_by_source_no(db, "BX-DBL-1", maker="admin")
    with pytest.raises(ValueError):
        vs.reverse_vouchers_by_source_no(db, "BX-DBL-1", maker="admin")


def test_reverse_rejects_no_booked(db, make_voucher):
    """无可冲销的已入账凭证（如未审核）应被拒绝。"""
    # 手工造一张未审核凭证（make_voucher 默认未审核）
    make_voucher(db, "2026-07", [("5602", "管理费用", "借", 100), ("2241", "其他应付", "贷", 100)],
                 source_type="报销单", source_no="BX-NB-1")
    with pytest.raises(ValueError):
        vs.reverse_vouchers_by_source_no(db, "BX-NB-1", maker="admin")


# ================= 权限闸门 =================
def test_require_admin_gm_allows_admin_rejects_employee():
    import asyncio
    from types import SimpleNamespace
    from app.api.auth import require_admin_gm
    admin = SimpleNamespace(role="admin", username="admin")
    emp = SimpleNamespace(role="employee", username="emp")
    # require_admin_gm 是 async 依赖，测试时显式 await
    assert asyncio.run(require_admin_gm(admin)) is admin
    with pytest.raises(Exception):  # HTTPException 403
        asyncio.run(require_admin_gm(emp))


# ================= 工资：归档闸门 + 反归档 + 冲销 =================
def test_salary_archive_gate(db):
    """工资：提交/审批通过不出凭证（归档闸门），归档才出计提凭证(已审核)。"""
    bill = slm.SalaryBill(
        salary_no="GZ-GATE-1", employee_name="测试员工", department="测试部", period="2026-07",
        base_salary=Decimal("8000"), performance=Decimal("2000"), gross_pay=Decimal("10000"),
        social_personal=Decimal("1500"), fund_personal=Decimal("500"), deduct_total=Decimal("2000"),
        net_pay=Decimal("8000"), status="草稿",
    )
    db.add(bill); db.commit(); db.refresh(bill)
    # 提交（一人公司自动审批通过）
    salary_api.submit_bill(bill.id, db)
    assert bill.status == "已通过"
    # B1：审批通过不得生成凭证
    assert _vouchers_for(db, "GZ-GATE-1") == [], "归档闸门失效：审批通过即出凭证"
    # 归档才出计提凭证
    salary_api.archive_bill(bill.id, db)
    assert bill.status == "已归档"
    vs_ = _vouchers_for(db, "GZ-GATE-1")
    assert len(vs_) == 1 and vs_[0].status == "已审核", "归档应生成已审核计提凭证"
    # 发放（支付凭证）
    salary_api.pay_bill(bill.id, db=db)
    assert bill.status == "已发放"
    assert len(_vouchers_for(db, "GZ-GATE-1")) == 2


def test_salary_unarchive_deletes_and_reverts(db):
    """工资反归档(admin)：删除计提+支付凭证，回退已通过，可重新归档。"""
    bill = slm.SalaryBill(
        salary_no="GZ-UA-1", employee_name="测试员工", department="测试部", period="2026-07",
        base_salary=Decimal("8000"), gross_pay=Decimal("10000"), deduct_total=Decimal("0"),
        net_pay=Decimal("10000"), status="草稿",
    )
    db.add(bill); db.commit(); db.refresh(bill)
    salary_api.submit_bill(bill.id, db)
    salary_api.archive_bill(bill.id, db)
    assert len(_vouchers_for(db, "GZ-UA-1")) == 1
    # 反归档（admin）必须在支付前（已归档态）
    salary_api.unarchive_bill(bill.id, current_user=_admin(db), db=db)
    assert bill.status == "已通过", "反归档应回退到已通过"
    assert _vouchers_for(db, "GZ-UA-1") == [], "反归档应删除全部联动凭证"
    # 重新归档 + 支付（幂等重建）
    salary_api.archive_bill(bill.id, db)
    assert len(_vouchers_for(db, "GZ-UA-1")) == 1
    salary_api.pay_bill(bill.id, db=db)
    assert len(_vouchers_for(db, "GZ-UA-1")) == 2


def test_salary_writeoff_red_reverses(db):
    """工资冲销(admin)：已发放→已冲销，红冲计提+支付凭证，拒绝重复冲销。"""
    bill = slm.SalaryBill(
        salary_no="GZ-WO-1", employee_name="测试员工", department="测试部", period="2026-07",
        base_salary=Decimal("8000"), gross_pay=Decimal("10000"), deduct_total=Decimal("0"),
        net_pay=Decimal("10000"), status="草稿",
    )
    db.add(bill); db.commit(); db.refresh(bill)
    salary_api.submit_bill(bill.id, db)
    salary_api.archive_bill(bill.id, db)
    salary_api.pay_bill(bill.id, db=db)

    salary_api.writeoff_bill(bill.id, current_user=_admin(db), db=db)
    assert bill.status == "已冲销"
    originals = [v for v in _vouchers_for(db, "GZ-WO-1") if v.source_type != vs.RED_SOURCE_TYPE]
    assert all(v.status == "已冲销" for v in originals)
    reds = [v for v in _vouchers_for(db, "GZ-WO-1") if v.source_type == vs.RED_SOURCE_TYPE]
    assert len(reds) == 1 and reds[0].status == "已审核"
    # 重复冲销拒绝
    with pytest.raises(Exception):
        salary_api.writeoff_bill(bill.id, current_user=_admin(db), db=db)


# ================= 报销：反归档 + 冲销 =================
def test_reimburse_unarchive_writeoff(db):
    """报销：提交财务(归档)出凭证、支付出付款凭证；反归档删除、冲销红冲。"""
    bill = rm.ReimbursementBill(
        bill_no="BX-UW-1", applicant="测试", department="测试部",
        amount=Decimal("1160"), status="草稿", approver="测试审批", bill_type="采购报销",
    )
    db.add(bill); db.commit(); db.refresh(bill)
    reimburse_api.submit_bill(bill.id, db)
    reimburse_api.submit_finance_bill(bill.id, db)  # 归档
    assert bill.status == "已归档"
    assert len(_vouchers_for(db, "BX-UW-1")) == 1  # 计提

    # 反归档（admin）必须在支付前（已归档态）
    reimburse_api.unarchive_bill(bill.id, current_user=_admin(db), db=db)
    assert bill.status == "已通过"
    assert _vouchers_for(db, "BX-UW-1") == []

    # 重新走一遍：归档 → 支付 → 冲销
    reimburse_api.submit_finance_bill(bill.id, db)
    reimburse_api.pay_bill(bill.id, db)
    assert bill.status == "已支付"
    assert len(_vouchers_for(db, "BX-UW-1")) == 2
    reimburse_api.writeoff_bill(bill.id, current_user=_admin(db), db=db)
    assert bill.status == "已冲销"
    originals = [v for v in _vouchers_for(db, "BX-UW-1") if v.source_type != vs.RED_SOURCE_TYPE]
    assert all(v.status == "已冲销" for v in originals)


# ================= 固定资产：反归档 + 冲销 =================
def _make_asset(db, asset_no):
    a = fam.FixedAsset(
        asset_no=asset_no, name="测试设备", category="办公设备", department="测试部",
        acquisition_date=date(2026, 7, 1), original_value=Decimal("12000"),
        salvage_rate=Decimal("5"), useful_life=Decimal("5"), status="未入账",
    )
    db.add(a); db.commit(); db.refresh(a)
    return a


def test_fixed_asset_unarchive(db):
    """固定资产反归档(admin)：在用→未入账，删入账凭证。"""
    a = _make_asset(db, "ZC-UA-1")
    fixed_api.record_asset(a.id, ActionBody(maker="admin"), db)
    assert a.status == "在用"
    assert len(_vouchers_for(db, "ZC-UA-1")) == 1
    fixed_api.unarchive_asset(a.id, current_user=_admin(db), db=db)
    assert a.status == "未入账"
    assert _vouchers_for(db, "ZC-UA-1") == []
    assert a.record_voucher_no is None


def test_fixed_asset_writeoff(db):
    """固定资产冲销(admin)：已处置→已冲销，红冲入账+处置凭证。"""
    a = _make_asset(db, "ZC-WO-1")
    fixed_api.record_asset(a.id, ActionBody(maker="admin"), db)
    fixed_api.dispose_asset(a.id, ActionBody(maker="admin"), db)
    assert a.status == "已处置"
    assert len(_vouchers_for(db, "ZC-WO-1")) == 2  # 入账 + 处置，均应为已审核
    assert all(v.status == "已审核" for v in _vouchers_for(db, "ZC-WO-1"))

    fixed_api.writeoff_asset(a.id, current_user=_admin(db), db=db)
    assert a.status == "已冲销"
    originals = [v for v in _vouchers_for(db, "ZC-WO-1") if v.source_type != vs.RED_SOURCE_TYPE]
    assert all(v.status == "已冲销" for v in originals)
    reds = [v for v in _vouchers_for(db, "ZC-WO-1") if v.source_type == vs.RED_SOURCE_TYPE]
    assert len(reds) == 1 and reds[0].status == "已审核"


# ================= 股东入资 / 收入：反归档（删除式）=================
def test_capital_unarchive(db):
    """股东入资反归档(admin)：已确认→草稿，删凭证。"""
    obj = ccm.CapitalContribution(
        bill_no="RZ-UA-1", investor="测试股东", amount=Decimal("50000"),
        capital_type="货币资金", contribution_date=date(2026, 7, 1), status="草稿",
    )
    db.add(obj); db.commit(); db.refresh(obj)
    cap_api.confirm_contribution(obj.id, current_user=_admin(db), db=db)
    assert obj.status == "已确认"
    assert len(_vouchers_for(db, "RZ-UA-1")) == 1
    cap_api.unarchive_contribution(obj.id, current_user=_admin(db), db=db)
    assert obj.status == "草稿"
    assert obj.voucher_no is None
    assert _vouchers_for(db, "RZ-UA-1") == []


def test_revenue_unarchive(db):
    """收入反归档(admin)：已确认→草稿，删凭证。"""
    obj = revm.Revenue(
        bill_no="SR-UA-1", customer="测试客户", total_amount=Decimal("11300"),
        tax_rate=Decimal("0.13"), settle_method="银行收讫", revenue_date=date(2026, 7, 1),
        status="草稿",
    )
    db.add(obj); db.commit(); db.refresh(obj)
    rev_api.confirm_revenue(obj.id, current_user=_admin(db), db=db)
    assert obj.status == "已确认"
    assert len(_vouchers_for(db, "SR-UA-1")) == 1
    rev_api.unarchive_revenue(obj.id, current_user=_admin(db), db=db)
    assert obj.status == "草稿"
    assert obj.voucher_no is None
    assert _vouchers_for(db, "SR-UA-1") == []
