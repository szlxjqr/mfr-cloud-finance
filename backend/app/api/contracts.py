"""合同管理 API：往来单位 + 人事/销售/采购合同 + 合同模板的 CRUD。

人事合同（HRContract）特别支持：
- employee_id 联动员工档案（姓名/身份证/部门/岗位/电话自动带出）
- 甲方（公司）自动取系统公司设置，前端无需手填
- 状态机 草稿 → 待审批 → 已生效 → 已到期/已终止
- 提交/审批/终止/打印
"""
from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import company as cm
from app.models import contract as m
from app.models import employee as em
from app.schemas import contract as s
from app.utils import approval

router = APIRouter(prefix="/contracts", tags=["contracts"])


def _compute_tax(data: dict) -> None:
    """有金额与税率时，服务端统一计算税额，保证数据一致。"""
    amount = data.get("amount")
    rate = data.get("tax_rate")
    if amount is not None and rate is not None:
        data["tax_amount"] = round(Decimal(str(amount)) * Decimal(str(rate)), 2)


def _get_or_404(db: Session, model, pk: int):
    obj = db.get(model, pk)
    if not obj:
        raise HTTPException(status_code=404, detail=f"{model.__name__} 不存在")
    return obj


def _enrich_hr_data(db: Session, data: dict) -> None:
    """新建/编辑人事合同时的自动联动：

    1) employee_id → 自动带出员工档案的姓名/身份证/部门/岗位/电话（缺失时补齐）。
    2) party_a → 自动取系统公司设置（公司名），前端无需手填（若已显式传则保留）。
    3) party_b → 自动取员工姓名（若未传）。

    注意：不能用 setdefault——Pydantic dump 后字段值是 None（而非缺失），
    setdefault 不会覆盖 None，会导致 employee_name 仍为 None 而触发 NOT NULL 约束。
    """
    # 1) 员工联动
    emp_id = data.get("employee_id")
    if emp_id:
        emp = db.get(em.Employee, emp_id)
        if not emp:
            raise HTTPException(status_code=400, detail=f"员工ID {emp_id} 不存在")
        # 显式 None/空值检查，确保覆盖 Pydantic 的 None 默认值
        if not data.get("employee_name"):
            data["employee_name"] = emp.name
        if not data.get("employee_no"):
            data["employee_no"] = emp.employee_no
        if not data.get("id_number"):
            data["id_number"] = emp.id_card
        if not data.get("department"):
            data["department"] = emp.department
        if not data.get("position"):
            data["position"] = emp.position
        if not data.get("phone"):
            data["phone"] = emp.phone
        if not data.get("party_b"):
            data["party_b"] = emp.name

    # 2) 甲方自动取公司设置（除非前端显式传了非空值）
    if not data.get("party_a"):
        cs = db.get(cm.CompanySettings, 1)
        if cs and cs.company_name:
            data["party_a"] = cs.company_name

    # 3) 新签默认 草稿 状态
    if not data.get("status"):
        data["status"] = "草稿"


# ================= 往来单位 =================
@router.get("/parties", response_model=list[s.PartyRead])
def list_parties(
    ptype: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
):
    stmt = select(m.Parties)
    if ptype:
        stmt = stmt.where(m.Parties.ptype == ptype)
    if keyword:
        stmt = stmt.where(m.Parties.name.like(f"%{keyword}%"))
    return db.scalars(stmt).all()


@router.post("/parties", response_model=s.PartyRead, status_code=201)
def create_party(payload: s.PartyCreate, db: Session = Depends(get_db)):
    obj = m.Parties(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/parties/{pid}", response_model=s.PartyRead)
def get_party(pid: int, db: Session = Depends(get_db)):
    return _get_or_404(db, m.Parties, pid)


@router.put("/parties/{pid}", response_model=s.PartyRead)
def update_party(pid: int, payload: s.PartyUpdate, db: Session = Depends(get_db)):
    obj = _get_or_404(db, m.Parties, pid)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/parties/{pid}")
def delete_party(pid: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, m.Parties, pid)
    db.delete(obj)
    db.commit()
    return {"ok": True}


# ================= 人事合同 =================
@router.get("/hr-contracts", response_model=list[s.HRContractRead])
def list_hr(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    stmt = select(m.HRContract)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(
            m.HRContract.employee_name.like(like)
            | (m.HRContract.party_a.is_not(None) & m.HRContract.party_a.like(like))
            | (m.HRContract.id_number.is_not(None) & m.HRContract.id_number.like(like))
        )
    if status:
        stmt = stmt.where(m.HRContract.status == status)
    if employee_id is not None:
        stmt = stmt.where(m.HRContract.employee_id == employee_id)
    stmt = stmt.order_by(m.HRContract.id.desc())
    return db.scalars(stmt).all()


@router.post("/hr-contracts", response_model=s.HRContractRead, status_code=201)
def create_hr(payload: s.HRContractCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()
    _enrich_hr_data(db, data)
    obj = m.HRContract(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/hr-contracts/{cid}", response_model=s.HRContractRead)
def get_hr(cid: int, db: Session = Depends(get_db)):
    return _get_or_404(db, m.HRContract, cid)


@router.put("/hr-contracts/{cid}", response_model=s.HRContractRead)
def update_hr(cid: int, payload: s.HRContractUpdate, db: Session = Depends(get_db)):
    obj = _get_or_404(db, m.HRContract, cid)
    if obj.status in ("已生效", "已到期", "已终止"):
        # 终态/生效后允许编辑基础信息，但不允许改状态（避免误操作）
        data = payload.model_dump(exclude_unset=True)
        data.pop("status", None)
    else:
        data = payload.model_dump(exclude_unset=True)
    _enrich_hr_data(db, data)  # 员工/公司设置仍会重新联动
    for k, v in data.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/hr-contracts/{cid}")
def delete_hr(cid: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, m.HRContract, cid)
    if obj.status == "已生效":
        raise HTTPException(status_code=400, detail="已生效合同不可删除，请先终止")
    db.delete(obj)
    db.commit()
    return {"ok": True}


# ---------------- 状态流：提交 / 审批 / 终止 / 打印 ----------------
@router.post("/hr-contracts/{cid}/submit", response_model=s.HRContractRead)
def submit_hr(cid: int, db: Session = Depends(get_db)):
    """草稿 → 待审批（并自动审批，一人公司）。"""
    obj = _get_or_404(db, m.HRContract, cid)
    if obj.status != "草稿":
        raise HTTPException(status_code=400, detail=f"当前状态「{obj.status}」不允许提交")
    obj.status = "待审批"
    # 一人公司：提交即自动审批
    approver = approval.resolve_auto_approver(db, obj.employee_name)
    obj.status = "已生效"
    obj.approver = approver
    obj.approve_date = date.today()
    obj.approve_remark = "系统自动审批（一人公司）"
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/hr-contracts/{cid}/approve", response_model=s.HRContractRead)
def approve_hr(cid: int, body: dict, db: Session = Depends(get_db)):
    """待审批 → 已生效。body: {approver: str, remark?: str}。"""
    obj = _get_or_404(db, m.HRContract, cid)
    if obj.status != "待审批":
        raise HTTPException(status_code=400, detail=f"当前状态「{obj.status}」不允许审批")
    approver = (body.get("approver") or "").strip()
    if not approver:
        raise HTTPException(status_code=422, detail="审批人不能为空")
    obj.status = "已生效"
    obj.approver = approver
    obj.approve_date = date.today()
    obj.approve_remark = (body.get("remark") or "").strip() or None
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/hr-contracts/{cid}/terminate", response_model=s.HRContractRead)
def terminate_hr(cid: int, body: Optional[dict] = None, db: Session = Depends(get_db)):
    """已生效/已到期 → 已终止。body: {remark?: str}。"""
    obj = _get_or_404(db, m.HRContract, cid)
    if obj.status not in ("已生效", "已到期"):
        raise HTTPException(status_code=400, detail=f"当前状态「{obj.status}」不允许终止")
    obj.status = "已终止"
    if body and body.get("remark"):
        obj.approve_remark = f"{obj.approve_remark or ''}\n[终止] {body['remark']}".strip()
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/hr-contracts/{cid}/print")
def print_hr(cid: int, db: Session = Depends(get_db)):
    """获取打印视图所需的合同 + 模板 + 公司信息（前端用这些数据渲染 A4 打印页）。"""
    obj = _get_or_404(db, m.HRContract, cid)
    if obj.status not in ("已生效", "已到期", "已终止"):
        raise HTTPException(
            status_code=400,
            detail=f"当前状态「{obj.status}」尚未生效，不可打印。请先提交审批。",
        )
    company = db.get(cm.CompanySettings, 1)
    template = None
    if obj.template_id:
        template = db.get(m.ContractTemplate, obj.template_id)
    elif obj.contract_type == "劳动合同":
        # 默认取深圳市劳动合同模板（ctype=hr 且 name 含"深圳"或"标准"）
        template = db.scalar(
            select(m.ContractTemplate)
            .where(m.ContractTemplate.ctype == "hr")
            .order_by(m.ContractTemplate.id)
        )
    return {
        "contract": s.HRContractRead.model_validate(obj).model_dump(),
        "company": {
            "company_name": company.company_name if company else None,
            "legal_rep": company.legal_rep if company else None,
            "address": company.address if company else None,
            "phone": company.phone if company else None,
            "tax_no": company.tax_no if company else None,
        } if company else None,
        "template": {
            "name": template.name if template else None,
            "content": template.content if template else None,
        } if template else None,
    }


# ================= 销售合同 =================
@router.get("/sales-contracts", response_model=list[s.SalesContractRead])
def list_sales(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    customer_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    stmt = select(m.SalesContract)
    if keyword:
        stmt = stmt.where(m.SalesContract.contract_no.like(f"%{keyword}%"))
    if status:
        stmt = stmt.where(m.SalesContract.status == status)
    if customer_id is not None:
        stmt = stmt.where(m.SalesContract.customer_id == customer_id)
    return db.scalars(stmt).all()


@router.post("/sales-contracts", response_model=s.SalesContractRead, status_code=201)
def create_sales(payload: s.SalesContractCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()
    _compute_tax(data)
    obj = m.SalesContract(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/sales-contracts/{cid}", response_model=s.SalesContractRead)
def get_sales(cid: int, db: Session = Depends(get_db)):
    return _get_or_404(db, m.SalesContract, cid)


@router.put("/sales-contracts/{cid}", response_model=s.SalesContractRead)
def update_sales(cid: int, payload: s.SalesContractUpdate, db: Session = Depends(get_db)):
    obj = _get_or_404(db, m.SalesContract, cid)
    data = payload.model_dump(exclude_unset=True)
    _compute_tax(data)
    for k, v in data.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/sales-contracts/{cid}")
def delete_sales(cid: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, m.SalesContract, cid)
    db.delete(obj)
    db.commit()
    return {"ok": True}


# ================= 采购合同 =================
@router.get("/purchase-contracts", response_model=list[s.PurchaseContractRead])
def list_purchase(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    supplier_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    stmt = select(m.PurchaseContract)
    if keyword:
        stmt = stmt.where(m.PurchaseContract.contract_no.like(f"%{keyword}%"))
    if status:
        stmt = stmt.where(m.PurchaseContract.status == status)
    if supplier_id is not None:
        stmt = stmt.where(m.PurchaseContract.supplier_id == supplier_id)
    return db.scalars(stmt).all()


@router.post("/purchase-contracts", response_model=s.PurchaseContractRead, status_code=201)
def create_purchase(payload: s.PurchaseContractCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()
    _compute_tax(data)
    obj = m.PurchaseContract(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/purchase-contracts/{cid}", response_model=s.PurchaseContractRead)
def get_purchase(cid: int, db: Session = Depends(get_db)):
    return _get_or_404(db, m.PurchaseContract, cid)


@router.put("/purchase-contracts/{cid}", response_model=s.PurchaseContractRead)
def update_purchase(cid: int, payload: s.PurchaseContractUpdate, db: Session = Depends(get_db)):
    obj = _get_or_404(db, m.PurchaseContract, cid)
    data = payload.model_dump(exclude_unset=True)
    _compute_tax(data)
    for k, v in data.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/purchase-contracts/{cid}")
def delete_purchase(cid: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, m.PurchaseContract, cid)
    db.delete(obj)
    db.commit()
    return {"ok": True}


# ================= 合同模板 =================
@router.get("/templates", response_model=list[s.ContractTemplateRead])
def list_templates(ctype: Optional[str] = None, keyword: Optional[str] = None, db: Session = Depends(get_db)):
    stmt = select(m.ContractTemplate)
    if ctype:
        stmt = stmt.where(m.ContractTemplate.ctype == ctype)
    if keyword:
        stmt = stmt.where(m.ContractTemplate.name.like(f"%{keyword}%"))
    return db.scalars(stmt).all()


@router.post("/templates", response_model=s.ContractTemplateRead, status_code=201)
def create_template(payload: s.ContractTemplateCreate, db: Session = Depends(get_db)):
    obj = m.ContractTemplate(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/templates/{tid}", response_model=s.ContractTemplateRead)
def get_template(tid: int, db: Session = Depends(get_db)):
    return _get_or_404(db, m.ContractTemplate, tid)


@router.put("/templates/{tid}", response_model=s.ContractTemplateRead)
def update_template(tid: int, payload: s.ContractTemplateUpdate, db: Session = Depends(get_db)):
    obj = _get_or_404(db, m.ContractTemplate, tid)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/templates/{tid}")
def delete_template(tid: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, m.ContractTemplate, tid)
    db.delete(obj)
    db.commit()
    return {"ok": True}
