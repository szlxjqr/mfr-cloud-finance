"""采购申请单 → 报销单 转换逻辑冒烟测试（含 pay_date 修复验证）。

直接调用路由函数（绕过 HTTP/鉴权层），覆盖：
- 转换：状态置「待审批」、预填申请人/部门/金额/事由、关联 purchase_requisition_id
- 幂等：同一采购单重复转换返回 409
- 全流程：审批通过 → 已通过（联动凭证）→ 付款 → 已支付（验证 pay_date 列存在）
"""
import pytest
from fastapi import HTTPException

from app.api import reimburse as reimburse_api
from app.models import purchase as pm
from app.schemas import reimburse as rs


def test_from_purchase_convert_and_idempotency(db):
    # 1) 插入一条已通过的采购申请单
    req = pm.PurchaseRequisition(
        req_no="CG-TEST-001",
        applicant="沈雷",
        department="研发",
        item_name="测试采购物",
        expected_amount=1234.56,
        reason="测试采购事由",
        status="已通过",
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    rid = req.id

    # 2) 转换：状态「待审批」，字段正确
    bill = reimburse_api.convert_from_purchase(rid, db=db)
    assert bill.status == "待审批"
    assert bill.applicant == "沈雷"
    assert abs(float(bill.amount) - 1234.56) < 0.001
    assert bill.purchase_requisition_id == rid
    assert bill.bill_no
    bid = bill.id

    # 3) 幂等：重复转换应抛 409
    with pytest.raises(HTTPException) as exc:
        reimburse_api.convert_from_purchase(rid, db=db)
    assert exc.value.status_code == 409

    # 4) 审批通过 → 已通过（联动生成凭证）
    approved = reimburse_api.approve_bill(
        bid, rs.ApprovalBody(approver="沈雷", remark="测试"), db=db
    )
    assert approved.status == "已通过"

    # 5) 付款：验证 pay_date 修复（修复前该列不存在会 AttributeError/500）
    paid = reimburse_api.pay_bill(bid, db=db)
    assert paid.status == "已支付"
    assert paid.pay_date is not None
