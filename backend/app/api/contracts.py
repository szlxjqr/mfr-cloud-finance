"""合同管理 API：往来单位 + 人事/销售/采购合同 + 合同模板的 CRUD。"""
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import contract as m
from app.schemas import contract as s

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
def list_hr(keyword: Optional[str] = None, status: Optional[str] = None, db: Session = Depends(get_db)):
    stmt = select(m.HRContract)
    if keyword:
        stmt = stmt.where(m.HRContract.employee_name.like(f"%{keyword}%"))
    if status:
        stmt = stmt.where(m.HRContract.status == status)
    return db.scalars(stmt).all()


@router.post("/hr-contracts", response_model=s.HRContractRead, status_code=201)
def create_hr(payload: s.HRContractCreate, db: Session = Depends(get_db)):
    obj = m.HRContract(**payload.model_dump())
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
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/hr-contracts/{cid}")
def delete_hr(cid: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, m.HRContract, cid)
    db.delete(obj)
    db.commit()
    return {"ok": True}


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
