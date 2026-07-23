"""固定资产服务：月折旧计算、入账、计提折旧、处置、汇总。

全部由 fixed_assets / dep_records 实时统计与联动，延续「业务单→凭证」地基：
- 入账：购置凭证（借 1601 / 贷 1002 或 2202）
- 计提折旧：每月汇总一张凭证（借 折旧费用科目 / 贷 1602 累计折旧）
- 处置：清理凭证（借 1602 / 借 5602 净值 / 贷 1601）

派生量（月折旧额、净值）实时计算，不冗余存储，保证单一来源。
"""
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import fixed_asset as m
from app.services import voucher_service as vs


def _to_dec(v) -> Decimal:
    if v is None or v == "":
        return Decimal("0")
    try:
        return Decimal(str(v))
    except Exception:
        return Decimal("0")


def monthly_dep(asset: "m.FixedAsset") -> Decimal:
    """月折旧额 = 原值 × (1 − 残值率%) / (使用年限 × 12)。

    封顶：累计折旧 + 本月折旧 不超过 (原值 − 残值)，使净值永不低于残值。
    原值 / 使用年限 为 0 时返回 0。
    """
    original = _to_dec(asset.original_value)
    if original <= 0:
        return Decimal("0")
    salvage_rate = _to_dec(asset.salvage_rate) / Decimal("100")
    life = _to_dec(asset.useful_life)
    if life <= 0:
        return Decimal("0")
    salvage = (original * salvage_rate).quantize(Decimal("0.01"))
    depreciable = (original - salvage).quantize(Decimal("0.01"))
    per_month = (depreciable / (life * Decimal("12"))).quantize(Decimal("0.01"))
    accum = _to_dec(asset.accum_dep)
    remaining = (depreciable - accum).quantize(Decimal("0.01"))
    if remaining <= 0:
        return Decimal("0")
    return min(per_month, remaining).quantize(Decimal("0.01"))


def net_value(asset: "m.FixedAsset") -> Decimal:
    """净值 = 原值 − 累计折旧。"""
    original = _to_dec(asset.original_value)
    accum = _to_dec(asset.accum_dep)
    return (original - accum).quantize(Decimal("0.01"))


def record(db: Session, asset_id: int, maker: str, v_date: Optional[date] = None) -> dict:
    """入账：生成购置凭证（借1601 / 贷支付科目），状态→在用。幂等。

    已入账资产再次调用返回既有凭证号（skipped=True），不产生重复凭证。
    """
    asset = db.get(m.FixedAsset, asset_id)
    if not asset:
        raise ValueError("资产不存在")
    if asset.status != "未入账":
        return {
            "voucher_no": asset.record_voucher_no,
            "skipped": True,
            "message": "资产已入账，凭证号：" + (asset.record_voucher_no or "（无）"),
        }
    voc = vs.generate_from_asset_purchase(db, asset, maker, v_date=v_date)
    if voc is None:
        return {"voucher_no": asset.record_voucher_no, "skipped": True}
    asset.status = "在用"
    asset.record_date = v_date or asset.acquisition_date or date.today()
    db.commit()
    db.refresh(asset)
    return {"voucher_no": voc.voucher_no, "skipped": False}


def depreciate(db: Session, period: str, maker: str) -> dict:
    """计提某月折旧：聚合并生成一张折旧汇总凭证，写 DepRecord。幂等（按期间）。

    规则：仅对「在用」且已入账（record_date 不晚于计提期间）的资产计提；
    当月增加当月即提（小型公司简化口径）。
    """
    assets = db.scalars(select(m.FixedAsset).where(m.FixedAsset.status == "在用")).all()
    if not assets:
        return {"voucher_no": None, "count": 0, "total": 0.0, "message": "无在用资产，无需计提"}

    by_subject: Dict[str, Decimal] = {}
    total = Decimal("0")
    plan: List[Tuple["m.FixedAsset", Decimal, str]] = []  # (资产, 当月折旧, 费用科目)
    for a in assets:
        if not a.record_date:
            continue
        ry, rm = a.record_date.year, a.record_date.month
        py, pm = period.split("-")
        py, pm = int(py), int(pm)
        if (py, pm) < (ry, rm):
            # 入账月晚于计提月 → 不提
            continue
        amt = monthly_dep(a)
        if amt <= 0:
            continue
        subj = a.dep_subject_code or "5602"
        by_subject[subj] = by_subject.get(subj, Decimal("0")) + amt
        total += amt
        plan.append((a, amt, subj))  # 仅记录计划，暂不改动资产

    if total <= 0:
        return {"voucher_no": None, "count": 0, "total": 0.0, "message": "本期无可计提折旧"}

    lines = [(c, amt) for c, amt in by_subject.items()]
    voc = vs.generate_depreciation_voucher(db, period, maker, lines, total)
    if voc is None:
        # 幂等跳过：凭证已存在，绝不改动资产（避免内存里累计折旧被错误累加）
        return {
            "voucher_no": None, "count": 0, "total": 0.0,
            "skipped": True, "message": f"{period} 折旧凭证已存在（幂等跳过）",
        }
    # 凭证确认生成后，才落实折旧：累加累计折旧 + 写折旧记录
    for a, amt, _subj in plan:
        a.accum_dep = (_to_dec(a.accum_dep)) + amt
        db.add(m.DepRecord(asset_id=a.id, period=period, amount=amt, voucher_no=voc.voucher_no))
    db.commit()
    return {"voucher_no": voc.voucher_no, "count": len(plan), "total": float(total), "skipped": False}


def dispose(db: Session, asset_id: int, maker: str, dispose_date: Optional[date] = None) -> dict:
    """处置：生成清理凭证（借1602 / 借5602净值 / 贷1601），状态→已处置。幂等。"""
    asset = db.get(m.FixedAsset, asset_id)
    if not asset:
        raise ValueError("资产不存在")
    if asset.status == "已处置":
        return {
            "voucher_no": asset.dispose_voucher_no,
            "skipped": True,
            "message": "资产已处置，凭证号：" + (asset.dispose_voucher_no or "（无）"),
        }
    voc = vs.generate_disposal_voucher(db, asset, maker, v_date=dispose_date)
    if voc is None:
        return {"voucher_no": asset.dispose_voucher_no, "skipped": True}
    asset.status = "已处置"
    asset.dispose_date = dispose_date or date.today()
    db.commit()
    db.refresh(asset)
    return {"voucher_no": voc.voucher_no, "skipped": False}


def summary(db: Session) -> dict:
    """资产总览：总原值 / 累计折旧 / 净值 / 在用数 / 总数。"""
    row = db.execute(
        select(
            func.coalesce(func.sum(m.FixedAsset.original_value), 0),
            func.coalesce(func.sum(m.FixedAsset.accum_dep), 0),
            func.count().filter(m.FixedAsset.status == "在用"),
            func.count(),
        )
    ).one()
    original = _to_dec(row[0])
    accum = _to_dec(row[1])
    net = (original - accum).quantize(Decimal("0.01"))
    return {
        "total_original": float(original),
        "total_accum_dep": float(accum),
        "total_net": float(net),
        "in_use_count": int(row[2]),
        "total_count": int(row[3]),
    }


def depreciate_preview(db: Session, period: str) -> List[dict]:
    """折旧预览：列出每个在用资产当月应计提额与最新净值（不落库）。"""
    assets = db.scalars(select(m.FixedAsset).where(m.FixedAsset.status == "在用")).all()
    out: List[dict] = []
    for a in assets:
        if not a.record_date:
            continue
        ry, rm = a.record_date.year, a.record_date.month
        py, pm = period.split("-")
        py, pm = int(py), int(pm)
        if (py, pm) < (ry, rm):
            continue
        amt = monthly_dep(a)
        if amt <= 0:
            continue
        out.append({
            "id": a.id,
            "asset_no": a.asset_no,
            "name": a.name,
            "category": a.category,
            "department": a.department,
            "original_value": float(_to_dec(a.original_value)),
            "accum_dep": float(_to_dec(a.accum_dep)),
            "monthly_dep": float(amt),
            "net_value": float(net_value(a)),
            "dep_subject_code": a.dep_subject_code or "5602",
        })
    out.sort(key=lambda x: x["asset_no"] or "")
    return out
