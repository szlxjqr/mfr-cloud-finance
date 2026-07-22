"""账簿数据服务：总账 / 明细账 / 科目汇总 / 序时账。

所有数据均由凭证分录（voucher_entries 关联 vouchers）**实时汇总**，
不冗余存储，保证与凭证始终一致。期间以 voucher.period（YYYY-MM）为准。
"""
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import subject as sm
from app.models import voucher as vm


def _normalize(normal_direction: str, cum_debit: float, cum_credit: float):
    """按科目正常方向，把累计借/贷归算为期末借/贷余额。

    返回 (ending_debit, ending_credit)，且两者仅一个非零。
    """
    if normal_direction == '借':
        bal = cum_debit - cum_credit
        if bal >= 0:
            return bal, 0.0
        return 0.0, -bal
    # 正常方向为贷（负债/权益/损益）
    bal = cum_credit - cum_debit
    if bal >= 0:
        return 0.0, bal
    return -bal, 0.0


def _subject_direction(db: Session, code: str) -> str:
    sub = db.scalars(
        select(sm.AccountSubject).where(sm.AccountSubject.code == code)
    ).first()
    return sub.direction if sub else '借'


def _aggregate(db: Session) -> Dict[str, dict]:
    """返回 {code: {'name':.., 'periods': {period: {'借':x, '贷':y}}}}。"""
    rows = db.execute(
        select(
            vm.VoucherEntry.subject_code,
            vm.VoucherEntry.subject_name,
            vm.Voucher.period,
            vm.VoucherEntry.direction,
            func.sum(vm.VoucherEntry.amount),
        )
        .join(vm.Voucher, vm.Voucher.id == vm.VoucherEntry.voucher_id)
        .group_by(
            vm.VoucherEntry.subject_code,
            vm.Voucher.period,
            vm.VoucherEntry.direction,
        )
    ).all()

    agg: Dict[str, dict] = {}
    for code, name, period, direction, amt in rows:
        d = agg.setdefault(code, {'name': name, 'periods': {}})
        d['periods'].setdefault(period, {'借': 0.0, '贷': 0.0})
        d['periods'][period][direction] = float(amt or 0)
    return agg


def _prior_cum(periods: Dict[str, dict], upto: Optional[str]) -> Tuple[float, float]:
    """取 upto 之前（不含）各期间的累计借/贷。upto 为 None 时返回 (0,0)。"""
    cd = cc = 0.0
    if not upto:
        return cd, cc
    for p, dv in periods.items():
        if p < upto:
            cd += dv.get('借', 0.0)
            cc += dv.get('贷', 0.0)
    return cd, cc


def general_ledger(
    db: Session, subject_code: str, period: Optional[str] = None
) -> dict:
    """总账：某科目按期间汇总的期初/本期/期末（期间感知）。"""
    agg = _aggregate(db)
    sub = agg.get(subject_code)
    normal = _subject_direction(db, subject_code)
    if not sub:
        return {
            'subject_code': subject_code,
            'subject_name': subject_code,
            'direction': normal,
            'rows': [],
        }

    periods = sorted(sub['periods'].keys())
    if period:
        periods = [p for p in periods if p <= period]

    cd, cc = _prior_cum(sub['periods'], period)
    rows: List[dict] = []
    for p in periods:
        deb = sub['periods'][p].get('借', 0.0)
        cre = sub['periods'][p].get('贷', 0.0)
        ed_prev, ec_prev = _normalize(normal, cd, cc)
        cd += deb
        cc += cre
        ed, ec = _normalize(normal, cd, cc)
        rows.append(
            {
                'period': p,
                'opening_debit': ed_prev,
                'opening_credit': ec_prev,
                'period_debit': deb,
                'period_credit': cre,
                'ending_debit': ed,
                'ending_credit': ec,
                'direction': normal,
                'balance': ed if ed > 0 else ec,
            }
        )
    return {
        'subject_code': subject_code,
        'subject_name': sub['name'],
        'direction': normal,
        'rows': rows,
    }


def subsidiary_ledger(
    db: Session, subject_code: str, period: Optional[str] = None
) -> dict:
    """明细账：某科目逐笔分录流水 + 期初/合计/期末（期间感知）。"""
    normal = _subject_direction(db, subject_code)
    sub = db.scalars(
        select(sm.AccountSubject).where(sm.AccountSubject.code == subject_code)
    ).first()
    subject_name = sub.name if sub else subject_code
    stmt = (
        select(
            vm.Voucher.voucher_date,
            vm.Voucher.voucher_no,
            vm.VoucherEntry.summary,
            vm.VoucherEntry.direction,
            vm.VoucherEntry.amount,
            vm.Voucher.period,
        )
        .join(vm.Voucher, vm.Voucher.id == vm.VoucherEntry.voucher_id)
        .where(vm.VoucherEntry.subject_code == subject_code)
        .order_by(vm.Voucher.voucher_date, vm.Voucher.voucher_no, vm.VoucherEntry.seq)
    )
    all_rows = db.execute(stmt).all()

    # 期初：所选期间之前（不含）的累计
    open_cd = open_cc = 0.0
    for _date, _vno, _sum, direction, amount, p in all_rows:
        if period and p < period:
            if direction == '借':
                open_cd += float(amount or 0)
            else:
                open_cc += float(amount or 0)
    opening_debit, opening_credit = _normalize(normal, open_cd, open_cc)

    lines: List[dict] = []
    cd, cc = open_cd, open_cc
    total_debit = total_credit = 0.0
    for vdate, vno, summary, direction, amount, p in all_rows:
        if period and p > period:
            continue
        if period and p < period:
            continue
        amt = float(amount or 0)
        if direction == '借':
            cd += amt
            total_debit += amt
        else:
            cc += amt
            total_credit += amt
        ed, ec = _normalize(normal, cd, cc)
        lines.append(
            {
                'date': vdate.isoformat() if hasattr(vdate, 'isoformat') else str(vdate),
                'voucher_no': vno,
                'summary': summary,
                'debit': amt if direction == '借' else 0.0,
                'credit': amt if direction == '贷' else 0.0,
                'direction': normal,
                'balance': ed if ed > 0 else ec,
            }
        )
    ending_debit, ending_credit = _normalize(normal, cd, cc)
    return {
        'subject_code': subject_code,
        'subject_name': subject_name,
        'direction': normal,
        'opening_debit': opening_debit,
        'opening_credit': opening_credit,
        'lines': lines,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'ending_debit': ending_debit,
        'ending_credit': ending_credit,
    }


def journal(db: Session, period: Optional[str] = None) -> dict:
    """序时账：全部凭证分录按日期/凭证号/序号排序的流水。"""
    stmt = (
        select(
            vm.Voucher.voucher_date,
            vm.Voucher.voucher_no,
            vm.Voucher.period,
            vm.VoucherEntry.summary,
            vm.VoucherEntry.subject_code,
            vm.VoucherEntry.subject_name,
            vm.VoucherEntry.direction,
            vm.VoucherEntry.amount,
        )
        .join(vm.Voucher, vm.Voucher.id == vm.VoucherEntry.voucher_id)
        .order_by(vm.Voucher.voucher_date, vm.Voucher.voucher_no, vm.VoucherEntry.seq)
    )
    if period:
        stmt = stmt.where(vm.Voucher.period == period)
    rows = db.execute(stmt).all()

    lines = [
        {
            'date': (r[0].isoformat() if hasattr(r[0], 'isoformat') else str(r[0])),
            'voucher_no': r[1],
            'period': r[2],
            'summary': r[3],
            'subject_code': r[4],
            'subject_name': r[5],
            'direction': r[6],
            'amount': float(r[7] or 0),
        }
        for r in rows
    ]
    return {'lines': lines}


def summary(db: Session, period: Optional[str] = None) -> List[dict]:
    """科目汇总表：每个科目一行（含期初/本期/累计/期末，期间感知）。"""
    subs = db.scalars(
        select(sm.AccountSubject).order_by(sm.AccountSubject.code)
    ).all()
    agg = _aggregate(db)

    out: List[dict] = []
    for sub in subs:
        periods = agg.get(sub.code, {}).get('periods', {})
        # 期初（所选期间之前）
        open_cd, open_cc = 0.0, 0.0
        if period:
            for p, dv in periods.items():
                if p < period:
                    open_cd += dv.get('借', 0.0)
                    open_cc += dv.get('贷', 0.0)
        # 本期
        if period:
            pd = periods.get(period, {}).get('借', 0.0)
            pc = periods.get(period, {}).get('贷', 0.0)
        else:
            pd = sum(dv.get('借', 0.0) for dv in periods.values())
            pc = sum(dv.get('贷', 0.0) for dv in periods.values())
        cd = open_cd + pd
        cc = open_cc + pc
        op_d, op_c = _normalize(sub.direction, open_cd, open_cc)
        ed, ec = _normalize(sub.direction, cd, cc)
        out.append(
            {
                'code': sub.code,
                'name': sub.name,
                'category': sub.category,
                'direction': sub.direction,
                'level': sub.level,
                'parent_code': sub.parent_code,
                'is_leaf': sub.is_leaf,
                'opening_debit': op_d,
                'opening_credit': op_c,
                'period_debit': pd,
                'period_credit': pc,
                'cum_debit': cd,
                'cum_credit': cc,
                'ending_debit': ed,
                'ending_credit': ec,
            }
        )
    return out
