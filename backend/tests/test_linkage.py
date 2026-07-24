"""联动核心冒烟测试：业务单审批→凭证、支付→付款凭证，借贷必平衡。

覆盖 P0 H1 修复的「支付/发放只改状态不生成凭证」问题，以及幂等联动地基。
"""
from datetime import date
from decimal import Decimal

from app.models import invoice as im
from app.models import purchase as pm
from app.models import reimburse as rm
from app.models import salary as slm
from app.services import voucher_service as vs


def test_purchase_approve_then_pay(db, make_voucher, voucher_sides):
    """采购申请通过 → 借原材料/贷应付；付款 → 借应付/贷银行存款。"""
    req = pm.PurchaseRequisition(
        req_no="CG2026TEST01",
        applicant="测试",
        department="测试部",
        item_name="测试物料",
        quantity=1,
        expected_amount=Decimal("1000.00"),
        supplier="测试供应商",
        expected_date=date(2026, 7, 1),
        status="已通过",
        approver="测试审批",
        approve_date=date(2026, 7, 1),
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    v = vs.generate_from_purchase(db, req, maker="测试")
    assert v is not None, "审批应通过联动生成凭证"
    d, c = voucher_sides(v)
    assert abs(d - c) < 0.005, "审批凭证借贷不平衡"
    codes = {(e.subject_code, e.direction): float(e.amount) for e in v.entries}
    assert codes.get(("1403", "借")) == 1000.0
    assert codes.get(("2202", "贷")) == 1000.0

    p = vs.generate_purchase_payment(db, req, maker="测试")
    assert p is not None, "付款应联动生成付款凭证"
    d, c = voucher_sides(p)
    assert abs(d - c) < 0.005, "付款凭证借贷不平衡"
    pc = {(e.subject_code, e.direction): float(e.amount) for e in p.entries}
    assert pc.get(("2202", "借")) == 1000.0
    assert pc.get(("1002", "贷")) == 1000.0


def test_reimbursement_approve_then_pay(db, make_voucher, voucher_sides):
    """报销审批 → 借管理费用+借进项税+贷其他应付；支付 → 借其他应付/贷银行存款。"""
    bill = rm.ReimbursementBill(
        bill_no="BXGL2026TEST01",
        applicant="测试",
        department="测试部",
        amount=Decimal("1160.00"),
        status="已通过",
        approver="测试审批",
        approve_date=date(2026, 7, 2),
        bill_type="采购报销",
    )
    db.add(bill)
    db.flush()
    inv = im.Invoice(no="TESTINV001", seller_name="测试销售方",
                     reimbursement_bill_id=bill.id)
    db.add(inv)
    db.flush()
    db.add(im.InvoiceDetail(
        invoice_id=inv.id, item="测试物料", qty=Decimal("1"),
        amount=Decimal("1000.00"), tax_rate=Decimal("16.00"),
        tax=Decimal("160.00"), total=Decimal("1160.00"),
    ))
    db.commit()

    v = vs.generate_from_reimbursement(db, bill, maker="测试")
    assert v is not None
    d, c = voucher_sides(v)
    assert abs(d - c) < 0.005, "报销审批凭证借贷不平衡"
    codes = {(e.subject_code, e.direction): float(e.amount) for e in v.entries}
    assert codes.get(("5602", "借")) == 1000.0
    assert codes.get(("2221.01.01", "借")) == 160.0
    assert codes.get(("2241", "贷")) == 1160.0

    p = vs.generate_reimbursement_payment(db, bill, maker="测试")
    assert p is not None
    d, c = voucher_sides(p)
    assert abs(d - c) < 0.005, "报销付款凭证借贷不平衡"
    pc = {(e.subject_code, e.direction): float(e.amount) for e in p.entries}
    assert pc.get(("2241", "借")) == 1160.0
    assert pc.get(("1002", "贷")) == 1160.0


def test_salary_accrual_then_pay(db, make_voucher, voucher_sides):
    """工资审核 → 借管理费用-工资/贷应付职工薪酬；发放 → 借应付/贷银行+贷其他应付(代扣)。"""
    bill = slm.SalaryBill(
        salary_no="GZ2026TEST01",
        employee_name="测试员工",
        department="测试部",
        period="2026-07",
        base_salary=Decimal("8000.00"),
        performance=Decimal("2000.00"),
        gross_pay=Decimal("10000.00"),
        social_personal=Decimal("1500.00"),
        fund_personal=Decimal("500.00"),
        tax_personal=Decimal("0.00"),
        deduct_total=Decimal("2000.00"),
        net_pay=Decimal("8000.00"),
        status="已通过",
        approver="测试审批",
        approve_date=date(2026, 7, 3),
    )
    db.add(bill)
    db.commit()
    db.refresh(bill)

    v = vs.generate_from_salary(db, bill, maker="测试")
    assert v is not None
    d, c = voucher_sides(v)
    assert abs(d - c) < 0.005, "工资计提凭证借贷不平衡"
    codes = {(e.subject_code, e.direction): float(e.amount) for e in v.entries}
    assert codes.get(("5602", "借")) == 10000.0
    assert codes.get(("2211", "贷")) == 10000.0

    p = vs.generate_salary_payment(db, bill, maker="测试")
    assert p is not None
    d, c = voucher_sides(p)
    assert abs(d - c) < 0.005, "工资发放凭证借贷不平衡"
    pc = {(e.subject_code, e.direction): float(e.amount) for e in p.entries}
    assert pc.get(("2211", "借")) == 10000.0
    assert pc.get(("1002", "贷")) == 8000.0
    assert pc.get(("2241", "贷")) == 2000.0


def test_idempotent_skip_on_repeat(db, make_voucher):
    """同一业务单重复触发联动只生成一张凭证（幂等）。"""
    req = pm.PurchaseRequisition(
        req_no="CG2026TEST02",
        applicant="测试",
        item_name="测试物料",
        quantity=1,
        expected_amount=Decimal("500.00"),
        status="已通过",
        approver="测试审批",
        approve_date=date(2026, 7, 1),
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    v1 = vs.generate_from_purchase(db, req, maker="测试")
    v2 = vs.generate_from_purchase(db, req, maker="测试")
    assert v1 is not None
    assert v2 is None, "重复调用不应生成第二张凭证（幂等失效）"
