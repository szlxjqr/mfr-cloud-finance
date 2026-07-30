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
from app.models import employee as emp
from app.schemas import fixed_asset as s
from app.utils.codegen import gen_asset_no
from app.utils import approval
from app.services import asset_service as svc  # 月折旧计算 / 入账 / 计提 / 处置 / 汇总
from app.services import voucher_service  # 联动：自动生成凭证
from app.api.auth import require_admin_gm  # 反归档/冲销限 admin/gm

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
    asset_no = gen_asset_no(db)
    db.commit()  # 预占必须 commit；否则 session close 时 SQLAlchemy 会自动 rollback，计数器不递增
    return {"asset_no": asset_no}


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


# ================= 反归档 / 冲销（限 admin/gm）=================
@router.post("/{aid}/unarchive", response_model=dict)
def unarchive_asset(
    aid: int,
    current_user: emp.Account = Depends(require_admin_gm),
    db: Session = Depends(get_db),
):
    """反归档（撤销）：在用 → 未入账，删除该资产联动的入账凭证（级联删分录），回退待重新入账。限 admin/gm。

    仅「在用」可反归档；已处置须走冲销。清空 record_voucher_no/record_date 避免悬空引用（B3）。
    """
    obj = _get_or_404(db, aid)
    if obj.status != "在用":
        raise HTTPException(
            status_code=400,
            detail=f"当前状态「{obj.status}」不允许反归档（仅在用可反归档；已处置请走冲销）",
        )
    obj.status = "未入账"
    obj.record_voucher_no = None
    obj.record_date = None
    db.add(obj)
    db.flush()
    voucher_service.void_vouchers_by_source_no(db, obj.asset_no)
    db.commit()
    db.refresh(obj)
    return {"asset": _to_read(obj).model_dump(), "message": "已撤销入账，凭证已删除"}


@router.post("/{aid}/writeoff", response_model=dict)
def writeoff_asset(
    aid: int,
    current_user: emp.Account = Depends(require_admin_gm),
    db: Session = Depends(get_db),
):
    """冲销（红字冲销）：已处置 → 已冲销，对该资产联动的入账+处置凭证做红字冲销（原凭证标记已冲销保留）。限 admin/gm。

    支付/处置后不可反归档，故提供冲销：生成借贷反向、金额相同的红冲凭证（已审核）即时抵消，
    原+冲销+新 三套凭证共存、账务闭合。若已冲销则拒绝重复冲销。
    """
    obj = _get_or_404(db, aid)
    if obj.status != "已处置":
        raise HTTPException(status_code=400, detail=f"当前状态「{obj.status}」不允许冲销（仅已处置可冲销）")
    obj.status = "已冲销"
    db.add(obj)
    db.flush()
    try:
        red_no, cnt = voucher_service.reverse_vouchers_by_source_no(
            db, obj.asset_no, maker=current_user.username
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    db.commit()
    db.refresh(obj)
    return {"asset": _to_read(obj).model_dump(), "red_voucher_no": red_no, "reversed": cnt}
