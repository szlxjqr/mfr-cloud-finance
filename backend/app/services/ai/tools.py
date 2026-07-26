"""ToolRegistry：把现有「采购 / 报销 / 发票」业务封装为可被 LLM 调用的工具。

v1 工具范围（决策 5）：采购 / 报销 / 发票 三域。
工具 handler 直接复用现有 API 路由函数（传入显式 db Session），不重写业务逻辑；
路由函数抛出的 HTTPException 在此转为友好结果回灌给 LLM。

安全分级：
- A 级（只读 / 报表）：直接执行，结果用 Markdown 表格呈现。
- B 级（创建草稿，可撤销）：说明后调用工具创建。
- C 级（付款 / 过账 / 审批通过，不可逆）：requires_confirm=True，Agent 循环须先取得用户确认。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api import invoice as invoice_api
from app.api import purchase as purchase_api
from app.api import reimburse as reimburse_api
from app.schemas import invoice as isc
from app.schemas import purchase as ps
from app.schemas import reimburse as rs


def _ok(data) -> dict:
    return {"ok": True, "data": data}


def _err(msg: str) -> dict:
    return {"ok": False, "error": msg}


# ───────────────────────── 采购域 ─────────────────────────
async def t_list_purchases(db: Session, user, **kw):
    rows = purchase_api.list_reqs(
        db=db,
        keyword=kw.get("keyword"),
        status=kw.get("status"),
        applicant=kw.get("applicant"),
        supplier=kw.get("supplier"),
    )
    return _ok([ps.PurchaseReqRead.model_validate(r).model_dump() for r in rows])


async def t_create_purchase(db: Session, user, **kw):
    payload = ps.PurchaseReqCreate(
        req_no=kw.get("req_no"),
        applicant=kw["applicant"],
        department=kw.get("department"),
        item_name=kw["item_name"],
        spec=kw.get("spec"),
        quantity=kw.get("quantity", 1),
        expected_amount=kw.get("expected_amount"),
        supplier=kw.get("supplier"),
        reason=kw.get("reason"),
        items=kw.get("items") or [],
    )
    obj = purchase_api.create_req(payload=payload, db=db)
    return _ok(ps.PurchaseReqRead.model_validate(obj).model_dump())


async def t_submit_purchase(db: Session, user, **kw):
    obj = purchase_api.submit_req(rid=int(kw["id"]), db=db)
    return _ok(ps.PurchaseReqRead.model_validate(obj).model_dump())


async def t_approve_purchase(db: Session, user, **kw):
    body = ps.ApprovalBody(approver=kw["approver"], remark=kw.get("remark"))
    obj = purchase_api.approve_req(rid=int(kw["id"]), body=body, db=db)
    return _ok(ps.PurchaseReqRead.model_validate(obj).model_dump())


async def t_pay_purchase(db: Session, user, **kw):
    obj = purchase_api.pay_req(rid=int(kw["id"]), db=db)
    return _ok(ps.PurchaseReqRead.model_validate(obj).model_dump())


# ───────────────────────── 报销域 ─────────────────────────
async def t_list_reimbursements(db: Session, user, **kw):
    rows = reimburse_api.list_bills(
        db=db,
        keyword=kw.get("keyword"),
        status=kw.get("status"),
        applicant=kw.get("applicant"),
    )
    return _ok([rs.ReimbursementBillRead.model_validate(r).model_dump() for r in rows])


async def t_create_reimbursement(db: Session, user, **kw):
    payload = rs.ReimbursementBillCreate(
        bill_no=kw.get("bill_no"),
        applicant=kw["applicant"],
        department=kw.get("department"),
        amount=kw.get("amount"),
        reason=kw.get("reason"),
        bill_type=kw.get("bill_type", "采购报销"),
        purchase_requisition_id=kw.get("purchase_requisition_id"),
        traveler=kw.get("traveler"),
    )
    obj = reimburse_api.create_bill(payload=payload, db=db)
    return _ok(rs.ReimbursementBillRead.model_validate(obj).model_dump())


async def t_convert_from_purchase(db: Session, user, **kw):
    obj = reimburse_api.convert_from_purchase(rid=int(kw["rid"]), db=db)
    return _ok(rs.ReimbursementBillRead.model_validate(obj).model_dump())


async def t_submit_reimbursement(db: Session, user, **kw):
    obj = reimburse_api.submit_bill(bid=int(kw["id"]), db=db)
    return _ok(rs.ReimbursementBillRead.model_validate(obj).model_dump())


async def t_approve_reimbursement(db: Session, user, **kw):
    body = rs.ApprovalBody(approver=kw["approver"], remark=kw.get("remark"))
    obj = reimburse_api.approve_bill(bid=int(kw["id"]), body=body, db=db)
    return _ok(rs.ReimbursementBillRead.model_validate(obj).model_dump())


async def t_pay_reimbursement(db: Session, user, **kw):
    obj = reimburse_api.pay_bill(bid=int(kw["id"]), db=db)
    return _ok(rs.ReimbursementBillRead.model_validate(obj).model_dump())


# ───────────────────────── 发票域 ─────────────────────────
async def t_list_invoices(db: Session, user, **kw):
    rows = invoice_api.list_invoices(
        db=db,
        keyword=kw.get("keyword"),
        reimbursement_bill_id=kw.get("reimbursement_bill_id"),
        unlinked=kw.get("unlinked"),
        start_date=kw.get("start_date"),
        end_date=kw.get("end_date"),
    )
    return _ok([isc.InvoiceRead.model_validate(r).model_dump() for r in rows])


async def t_create_invoice(db: Session, user, **kw):
    details = [isc.InvoiceDetailCreate(**d) for d in (kw.get("details") or [])]
    payload = isc.InvoiceCreate(
        invoice_type=kw.get("invoice_type", "增值税专用发票"),
        code=kw.get("code"),
        no=kw["no"],
        invoice_date=kw.get("invoice_date"),
        buyer_name=kw.get("buyer_name"),
        seller_name=kw["seller_name"],
        account=kw.get("account"),
        certify=kw.get("certify", "none"),
        remark=kw.get("remark"),
        details=details,
    )
    obj = invoice_api.create_invoice(payload=payload, db=db)
    return _ok(isc.InvoiceRead.model_validate(obj).model_dump())


async def t_link_invoice(db: Session, user, **kw):
    obj = invoice_api.link_invoice(
        iid=int(kw["iid"]),
        bid=int(kw["bid"]),
        purchase_requisition_item_id=kw.get("purchase_requisition_item_id"),
        db=db,
    )
    return _ok(isc.InvoiceRead.model_validate(obj).model_dump())


async def t_invoice_summary_by_bill(db: Session, user, **kw):
    result = invoice_api.invoice_summary_by_bill(bid=int(kw["bid"]), db=db)
    return _ok(dict(result))


async def t_voucher_draft(db: Session, user, **kw):
    result = invoice_api.generate_voucher_draft(invoice_ids=kw["invoice_ids"], db=db)
    return _ok(dict(result))


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict  # JSON Schema（object）
    handler: Callable
    safety_tier: str = "A"  # A=只读/报表 | B=创建草稿(可撤销) | C=付款/过账(需确认)
    requires_confirm: bool = False


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}
        _register_builtins(self)

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def requires_confirm(self, name: str) -> bool:
        t = self._tools.get(name)
        return bool(t and t.requires_confirm)

    def list_definitions(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in self._tools.values()
        ]

    async def execute(self, name: str, args: dict, db: Session, user) -> dict:
        tool = self._tools.get(name)
        if not tool:
            return _err(f"未知工具：{name}")
        try:
            return await tool.handler(db=db, user=user, **(args or {}))
        except HTTPException as e:
            return _err(e.detail)
        except Exception as e:  # 兜底，避免把异常栈直接丢给 LLM
            return _err(f"工具执行失败：{e}")


def _register_builtins(self: ToolRegistry) -> None:
    # ── 采购域 ──
    self.register(Tool(
        name="listPurchases",
        description="查询采购申请单列表，可按关键字/状态/申请人/供应商筛选。",
        parameters={
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "单号/申请人/品名/事由模糊匹配"},
                "status": {"type": "string", "description": "状态：草稿/待审批/已通过/已驳回/已支付"},
                "applicant": {"type": "string", "description": "申请人"},
                "supplier": {"type": "string", "description": "供应商"},
            },
            "required": [],
        },
        handler=t_list_purchases,
        safety_tier="A",
    ))
    self.register(Tool(
        name="createPurchase",
        description="新建采购申请单（草稿）。需提供申请人与采购品名；提交后会自动审批并生成应付凭证。",
        parameters={
            "type": "object",
            "properties": {
                "applicant": {"type": "string", "description": "申请人（必填）"},
                "item_name": {"type": "string", "description": "采购品名（必填）"},
                "department": {"type": "string", "description": "部门"},
                "expected_amount": {"type": "number", "description": "预计金额"},
                "supplier": {"type": "string", "description": "供应商"},
                "reason": {"type": "string", "description": "采购事由"},
                "quantity": {"type": "integer", "description": "数量，默认 1"},
                "spec": {"type": "string", "description": "规格"},
            },
            "required": ["applicant", "item_name"],
        },
        handler=t_create_purchase,
        safety_tier="B",
    ))
    self.register(Tool(
        name="submitPurchase",
        description="提交采购申请单（一人公司自动审批通过，并联动生成应付凭证）。C 级动作，需用户确认。",
        parameters={
            "type": "object",
            "properties": {"id": {"type": "integer", "description": "采购申请单 id"}},
            "required": ["id"],
        },
        handler=t_submit_purchase,
        safety_tier="C",
        requires_confirm=True,
    ))
    self.register(Tool(
        name="approvePurchase",
        description="审批通过采购申请单（联动生成应付凭证）。C 级动作，需用户确认。",
        parameters={
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "采购申请单 id"},
                "approver": {"type": "string", "description": "审批人（必填）"},
                "remark": {"type": "string", "description": "审批意见"},
            },
            "required": ["id", "approver"],
        },
        handler=t_approve_purchase,
        safety_tier="C",
        requires_confirm=True,
    ))
    self.register(Tool(
        name="payPurchase",
        description="采购付款（结算应付账款，联动生成付款凭证）。C 级动作，需用户确认。",
        parameters={
            "type": "object",
            "properties": {"id": {"type": "integer", "description": "采购申请单 id"}},
            "required": ["id"],
        },
        handler=t_pay_purchase,
        safety_tier="C",
        requires_confirm=True,
    ))

    # ── 报销域 ──
    self.register(Tool(
        name="listReimbursements",
        description="查询报销单列表，可按关键字/状态/申请人筛选。",
        parameters={
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "单号/申请人/事由模糊匹配"},
                "status": {"type": "string", "description": "状态：草稿/待审批/已通过/已驳回/已支付"},
                "applicant": {"type": "string", "description": "申请人"},
            },
            "required": [],
        },
        handler=t_list_reimbursements,
        safety_tier="A",
    ))
    self.register(Tool(
        name="createReimbursement",
        description="新建报销单（草稿）。需提供申请人。",
        parameters={
            "type": "object",
            "properties": {
                "applicant": {"type": "string", "description": "申请人（必填）"},
                "amount": {"type": "number", "description": "报销金额"},
                "reason": {"type": "string", "description": "报销事由"},
                "department": {"type": "string", "description": "部门"},
                "bill_type": {"type": "string", "description": "报销类型，默认 采购报销"},
                "purchase_requisition_id": {"type": "integer", "description": "关联采购申请单 id"},
                "traveler": {"type": "string", "description": "差旅人（差旅报销）"},
            },
            "required": ["applicant"],
        },
        handler=t_create_reimbursement,
        safety_tier="B",
    ))
    self.register(Tool(
        name="convertFromPurchase",
        description="将采购申请单转为报销单（幂等，同一采购单已转过则返回冲突）。",
        parameters={
            "type": "object",
            "properties": {"rid": {"type": "integer", "description": "采购申请单 id"}},
            "required": ["rid"],
        },
        handler=t_convert_from_purchase,
        safety_tier="B",
    ))
    self.register(Tool(
        name="submitReimbursement",
        description="提交报销单（一人公司自动审批通过，联动生成记账凭证）。C 级动作，需用户确认。",
        parameters={
            "type": "object",
            "properties": {"id": {"type": "integer", "description": "报销单 id"}},
            "required": ["id"],
        },
        handler=t_submit_reimbursement,
        safety_tier="C",
        requires_confirm=True,
    ))
    self.register(Tool(
        name="approveReimbursement",
        description="审批通过报销单（联动生成记账凭证）。C 级动作，需用户确认。",
        parameters={
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "报销单 id"},
                "approver": {"type": "string", "description": "审批人（必填）"},
                "remark": {"type": "string", "description": "审批意见"},
            },
            "required": ["id", "approver"],
        },
        handler=t_approve_reimbursement,
        safety_tier="C",
        requires_confirm=True,
    ))
    self.register(Tool(
        name="payReimbursement",
        description="报销付款（结算其他应付款，联动生成付款凭证）。C 级动作，需用户确认。",
        parameters={
            "type": "object",
            "properties": {"id": {"type": "integer", "description": "报销单 id"}},
            "required": ["id"],
        },
        handler=t_pay_reimbursement,
        safety_tier="C",
        requires_confirm=True,
    ))

    # ── 发票域 ──
    self.register(Tool(
        name="listInvoices",
        description="查询发票列表，可按关键字/关联报销单/未关联/日期区间筛选。",
        parameters={
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "发票号/销售方/购买方/账号模糊匹配"},
                "reimbursement_bill_id": {"type": "integer", "description": "仅查关联该报销单的发票"},
                "unlinked": {"type": "boolean", "description": "true=仅查未关联报销单的发票"},
                "start_date": {"type": "string", "description": "起始日期 YYYY-MM-DD"},
                "end_date": {"type": "string", "description": "结束日期 YYYY-MM-DD"},
            },
            "required": [],
        },
        handler=t_list_invoices,
        safety_tier="A",
    ))
    self.register(Tool(
        name="createInvoice",
        description="新建发票（含明细）。需提供发票号码与销售方名称。",
        parameters={
            "type": "object",
            "properties": {
                "no": {"type": "string", "description": "发票号码（必填）"},
                "seller_name": {"type": "string", "description": "销售方名称（必填）"},
                "invoice_type": {"type": "string", "description": "发票类型，默认 增值税专用发票"},
                "invoice_date": {"type": "string", "description": "开票日期 YYYY-MM-DD"},
                "buyer_name": {"type": "string", "description": "购买方名称"},
                "code": {"type": "string", "description": "发票代码（数电票可空）"},
                "account": {"type": "string", "description": "入账科目"},
                "certify": {"type": "string", "description": "认证状态：none/current"},
                "details": {
                    "type": "array",
                    "description": "发票明细行",
                    "items": {
                        "type": "object",
                        "properties": {
                            "item": {"type": "string", "description": "货物或应税劳务名称"},
                            "amount": {"type": "number", "description": "金额（不含税）"},
                            "tax": {"type": "number", "description": "税额"},
                            "total": {"type": "number", "description": "价税合计"},
                        },
                    },
                },
            },
            "required": ["no", "seller_name"],
        },
        handler=t_create_invoice,
        safety_tier="B",
    ))
    self.register(Tool(
        name="linkInvoice",
        description="将发票关联到报销单（建立报销与发票的勾稽关系）。",
        parameters={
            "type": "object",
            "properties": {
                "iid": {"type": "integer", "description": "发票 id"},
                "bid": {"type": "integer", "description": "报销单 id"},
                "purchase_requisition_item_id": {"type": "integer", "description": "关联采购明细 id（可选）"},
            },
            "required": ["iid", "bid"],
        },
        handler=t_link_invoice,
        safety_tier="B",
    ))
    self.register(Tool(
        name="invoiceSummaryByBill",
        description="按报销单汇总其关联发票的金额/税额/价税合计，用于核对报销金额。",
        parameters={
            "type": "object",
            "properties": {"bid": {"type": "integer", "description": "报销单 id"}},
            "required": ["bid"],
        },
        handler=t_invoice_summary_by_bill,
        safety_tier="A",
    ))
    self.register(Tool(
        name="voucherDraft",
        description="根据所选发票生成会计凭证分录草稿（仅计算，不落库）。用于预览入账方案。",
        parameters={
            "type": "object",
            "properties": {
                "invoice_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "发票 id 列表",
                }
            },
            "required": ["invoice_ids"],
        },
        handler=t_voucher_draft,
        safety_tier="A",
    ))


# 单例注册表（Agent 循环 / 路由直接复用）
registry = ToolRegistry()
