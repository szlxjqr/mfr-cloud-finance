"""差旅申请单 → 报销单 转换 + revert 状态机 + 凭证双来源冒烟测试。

直接调用路由函数（绕过 HTTP/鉴权层），覆盖：
- revert 状态机：已通过 → 草稿，清空审批信息；非白名单状态抛 400
- 转换：状态置「草稿」、预填申请人/部门/金额/事由/差旅字段、关联 travel_requisition_id
- 幂等：同一差旅单重复转换返回 409
- 凭证双来源：差旅单 is_rd_project=是 → 报销归档凭证借方 4301（研发支出）；
  非研发 → 借方 5602（管理费用）
"""
from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.api import reimburse as reimburse_api
from app.api import travel as travel_api
from app.models import travel as tm
from app.models import voucher as vm


def test_travel_revert_state_machine(db):
    """已通过 → 草稿，清空审批人/日期/意见；非白名单状态抛 400。"""
    req = tm.TravelRequisition(
        req_no="CL-TEST-001",
        applicant="沈雷",
        destination="北京",
        expected_amount=2000.00,
        reason="测试差旅",
        status="已通过",
        approver="老板",
        approve_date=date.today(),
        approve_remark="系统自动审批",
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    rid = req.id

    reverted = travel_api.revert_req(rid, db=db)
    assert reverted.status == "草稿"
    assert reverted.approver is None
    assert reverted.approve_date is None
    assert reverted.approve_remark is None

    # 已变草稿，白名单无 revert 动作 → 400
    with pytest.raises(HTTPException) as exc:
        travel_api.revert_req(rid, db=db)
    assert exc.value.status_code == 400


def test_from_travel_convert_and_idempotency(db):
    """转换预填 + 关联 + 幂等 409 + 研发差旅凭证借方 4301。"""
    req = tm.TravelRequisition(
        req_no="CL-TEST-002",
        applicant="沈雷",
        department="研发",
        traveler="沈雷",
        destination="上海",
        expected_amount=3000.00,
        reason="差旅测试",
        status="已通过",
        is_rd_project="是",
        rd_project_code="RD-001",
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    rid = req.id

    bill = reimburse_api.convert_from_travel(rid, db=db)
    assert bill.status == "草稿"
    assert bill.applicant == "沈雷"
    assert bill.bill_type == "差旅报销"
    assert bill.travel_requisition_id == rid
    assert abs(float(bill.amount) - 3000.00) < 0.001
    assert bill.traveler == "沈雷"
    assert bill.travel_destination == "上海"
    bid = bill.id

    # 幂等：重复转换应抛 409
    with pytest.raises(HTTPException) as exc:
        reimburse_api.convert_from_travel(rid, db=db)
    assert exc.value.status_code == 409

    # 提交 → 自动审批通过 → 提交财务 → 已归档（联动生成凭证）
    reimburse_api.submit_bill(bid, db=db)
    archived = reimburse_api.submit_finance_bill(bid, db=db)
    assert archived.status == "已归档"

    voc = db.scalar(
        select(vm.Voucher).where(
            vm.Voucher.source_type == "报销单",
            vm.Voucher.source_no == bill.bill_no,
        )
    )
    assert voc is not None
    debit_codes = [e.subject_code for e in voc.entries if e.direction == "借"]
    assert "4301" in debit_codes, "研发差旅应借 研发支出(4301)"


def test_from_travel_non_rd_uses_5602(db):
    """非研发差旅 → 报销归档凭证借方 5602（管理费用）。"""
    req = tm.TravelRequisition(
        req_no="CL-TEST-003",
        applicant="小李",
        expected_amount=1500.00,
        reason="销售拜访",
        status="已通过",
        is_rd_project="否",
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    rid = req.id

    bill = reimburse_api.convert_from_travel(rid, db=db)
    reimburse_api.submit_bill(bill.id, db=db)
    reimburse_api.submit_finance_bill(bill.id, db=db)

    voc = db.scalar(
        select(vm.Voucher).where(
            vm.Voucher.source_type == "报销单",
            vm.Voucher.source_no == bill.bill_no,
        )
    )
    assert voc is not None
    debit_codes = [e.subject_code for e in voc.entries if e.direction == "借"]
    assert "5602" in debit_codes, "非研发差旅应借 管理费用(5602)"
