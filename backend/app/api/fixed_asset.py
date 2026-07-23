"""固定资产管理 API：资产卡片 CRUD + 入账 / 计提折旧 / 处置 联动凭证。

联动地基（B）：
- 入账：借 固定资产(1601) / 贷 银行存款(1002) [赊购则 应付账款(2202)] → 自动凭证
- 计提折旧：每月汇总一张凭证 借 折旧费用科目 / 贷 累计折旧(1602) → 自动凭证
- 处置：借 累计折旧(1602) + 借 管理费用(5602) 净值 / 贷 固定资产(1601) → 自动凭证
全部幂等，重复操作不重复生成凭证。
"""
from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import fixed_asset as m
from app.schemas import fixed_asset as s
from app.utils.codegen import gen_asset_no
from app.utils import approval
from app.services import asset_service as svc  # 月折旧计算 / 入账 / 计提 / 处置 / 汇总
from app.services import voucher_service  # 联动：自动生成凭证

router = APIRouter(prefix="/fixed-assets", tags=["fixed-assets"])


def _get_or_404(db: Session, pk: int) -> m.FixedAsset:
    obj = db.get(m.FixedAsset, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="资产不存在")
    return obj


def _to_dec(v) -> Decimal:
    if v is None or v == "":
        return Decimal("0")
    try:
        return Decimal(str(v))
    except Exception:
        return Decimal("0")


def _to_read(obj: m.FixedAsset) -> s.FixedAssetRead:
    """构造读模型，并注入派生量（月折旧额 / 净值）。"""
    r = s.FixedAssetRead.model_validate(obj)
    r.monthly_dep = float(svc.monthly_dep(obj))
    r.net_value = float(svc.net_value(obj))
    return r


def _resolve_maker(db: Session, maker: Optional[str]) -> str:
    if maker and maker.strip():
        return maker.strip()
    return approval.resolve_auto_approver(db, None)


# ================= 汇总 / 预览 =================
@router.get("/summary", response_model=s.AssetSummary)
def asset_summary(db: Session = Depends(get_db)):
    """资产总览：总原值 / 累计折旧 / 净值 / 在用数。"""
    return svc.summary(db)


@router.get("/depreciate-preview", response_model=list[s.DepPreviewItem])
def depreciate_preview(period: str, db: Session = Depends(get_db)):
    """折旧预览：列出每个在用资产在指定期间的应计提额与净值（不落库）。"""
    return svc.depreciate_preview(db, period)


# ================= CRUD =================
@router.get("", response_model=list[s.FixedAssetRead])
def list_assets(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    department: Optional[str] = None,
    db: Session = Depends(get_db),
):
    stmt = select(m.FixedAsset)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(
            (m.FixedAsset.asset_no.like(like))
            | (m.FixedAsset.name.like(like))
            | (m.FixedAsset.department.like(like))
        )
    if status:
        stmt = stmt.where(m.FixedAsset.status == status)
    if category:
        stmt = stmt.where(m.FixedAsset.category == category)
    if department:
        stmt = stmt.where(m.FixedAsset.department == department)
    stmt = stmt.order_by(m.FixedAsset.id.desc())
    return [_to_read(o) for o in db.scalars(stmt).all()]


@router.get("/next-no", response_model=dict)
def next_asset_no(db: Session = Depends(get_db)):
    """新建资产前预占下一个单号（仅预览/预填）。"""
    return {"asset_no": gen_asset_no(db)}


@router.post("", response_model=s.FixedAssetRead, status_code=201)
def create_asset(payload: s.FixedAssetCreate, db: Session = Depends(get_db)):
    data = payload.model_dump(exclude_unset=True)
    if not data.get("asset_no"):
        data["asset_no"] = gen_asset_no(db)
    obj = m.FixedAsset(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return _to_read(obj)


@router.get("/{aid}", response_model=s.FixedAssetRead)
def get_asset(aid: int, db: Session = Depends(get_db)):
    return _to_read(_get_or_404(db, aid))


@router.put("/{aid}", response_model=s.FixedAssetRead)
def update_asset(aid: int, payload: s.FixedAssetUpdate, db: Session = Depends(get_db)):
    obj = _get_or_404(db, aid)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return _to_read(obj)


@router.delete("/{aid}")
def delete_asset(aid: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, aid)
    db.delete(obj)
    db.commit()
    return {"ok": True}


@router.get("/{aid}/dep-records", response_model=list[s.DepRecordRead])
def dep_records(aid: int, db: Session = Depends(get_db)):
    """某资产的折旧记录列表（按期间升序）。"""
    _get_or_404(db, aid)
    rows = db.scalars(
        select(m.DepRecord)
        .where(m.DepRecord.asset_id == aid)
        .order_by(m.DepRecord.period)
    ).all()
    return rows


# ================= 联动动作 =================
@router.post("/{aid}/record", response_model=dict)
def record_asset(aid: int, body: s.ActionBody, db: Session = Depends(get_db)):
    """资产入账：生成购置凭证，状态→在用。幂等。"""
    maker = _resolve_maker(db, body.maker)
    obj = _get_or_404(db, aid)
    result = svc.record(db, aid, maker, v_date=body.action_date)
    return {"asset": _to_read(obj).model_dump(), **result}


@router.post("/depreciate", response_model=dict)
def depreciate_assets(body: s.DepreciateBody, db: Session = Depends(get_db)):
    """计提折旧：按指定期间汇总生成一张折旧凭证，并写折旧记录。幂等（按期间）。"""
    maker = _resolve_maker(db, body.maker)
    return svc.depreciate(db, body.period, maker)


@router.post("/{aid}/dispose", response_model=dict)
def dispose_asset(aid: int, body: s.ActionBody, db: Session = Depends(get_db)):
    """资产处置：生成清理凭证，状态→已处置。幂等。"""
    maker = _resolve_maker(db, body.maker)
    obj = _get_or_404(db, aid)
    result = svc.dispose(db, aid, maker, dispose_date=body.action_date)
    return {"asset": _to_read(obj).model_dump(), **result}
