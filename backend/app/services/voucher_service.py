"""联动核心：业务单审批通过 → 自动生成记账凭证。

这是「以业务为入口、联动账务」的发动机：
- 报销单（采购报销/差旅报销）审批通过 → 借 费用 + 借 进项税额 + 贷 其他应付款（员工）
- 采购申请审批通过 → 借 存货/研发支出 + 贷 应付账款（供应商）

科目编码采用「小企业会计准则」风格，全部来自 account_subjects 种子表；
生成时按 code 查 name，找不到则回退用 code 本身（不应发生，因为已种子）。

幂等：同一 (source_type, source_no) 仅生成一张凭证，重复调用自动跳过，
避免审批流重试/编辑重提交产生重复凭证。
"""
from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import fixed_asset as fam
from app.models import invoice as im
from app.models import purchase as pm
from app.models import reimburse as rm
from app.models import salary as slm
from app.models import subject as sm
from app.models import voucher as vm
from app.utils.codegen import gen_asset_no, gen_voucher_no


# ── 业务 → 科目映射（集中维护，便于审阅/调整）──
SUB_MANAGE = "5602"          # 管理费用
SUB_RDCOST = "4301"          # 研发支出
SUB_RAWMAT = "1403"          # 原材料
SUB_INPUT_TAX = "2221.01.01"  # 应交税费—应交增值税—进项税额
SUB_OTHER_PAY = "2241"        # 其他应付款
SUB_AP = "2202"               # 应付账款
SUB_WAGE = "5602"            # 管理费用—工资（计提/发放工资费用）
SUB_PAYROLL_PAY = "2211"     # 应付职工薪酬
SUB_FIXED_ASSET = "1601"      # 固定资产
SUB_ACCUM_DEP = "1602"        # 累计折旧（固定资产备抵，贷方余额）
SUB_BANK = "1002"             # 银行存款


def _subject_name(db: Session, code: str) -> str:
    """按科目编码取名称；找不到回退为编码本身。"""
    obj = db.scalar(select(sm.AccountSubject).where(sm.AccountSubject.code == code))
    return obj.name if obj else code


def _period_of(d: date) -> str:
    return f"{d.year}-{d.month:02d}"


def _exists(db: Session, source_type: str, source_no: str) -> Optional[vm.Voucher]:
    return db.scalar(
        select(vm.Voucher).where(
            vm.Voucher.source_type == source_type,
            vm.Voucher.source_no == source_no,
        )
    )


def _make_voucher(
    db: Session,
    source_type: str,
    source_no: str,
    v_date: date,
    maker: str,
    summary: str,
    entries: List[Tuple[str, str, str, Decimal]],  # (subject_code, direction, summary, amount)
    attach_count: int = 0,
) -> vm.Voucher:
    """写入一张凭证 + 多行分录，返回凭证对象。"""
    voucher_no, seq = gen_voucher_no(db, year=v_date.year, month=v_date.month)
    voc = vm.Voucher(
        voucher_no=voucher_no,
        seq=seq,
        voucher_date=v_date,
        period=_period_of(v_date),
        voucher_word="记",
        attach_count=attach_count,
        maker=maker,
        status="未审核",
        source_type=source_type,
        source_no=source_no,
        summary=summary,
    )
    db.add(voc)
    db.flush()
    for i, (code, direction, line_summary, amount) in enumerate(entries, start=1):
        db.add(
            vm.VoucherEntry(
                voucher_id=voc.id,
                seq=i,
                subject_code=code,
                subject_name=_subject_name(db, code),
                summary=line_summary,
                direction=direction,
                amount=amount,
            )
        )
    db.flush()
    return voc


# ==================== 报销单 → 凭证 ====================
def generate_from_reimbursement(db: Session, bill: "rm.ReimbursementBill", maker: str) -> Optional[vm.Voucher]:
    """报销单审批通过 → 自动凭证。

    规则（与发票明细联动）：
    - 有发票明细：借 管理费用(不含税合计) + 借 进项税额(税额合计) + 贷 其他应付款(价税合计)
    - 无发票明细：借 管理费用(报销金额) + 贷 其他应付款(报销金额)
    幂等：source_type='报销单', source_no=bill_no 已存在则跳过。
    """
    if _exists(db, "报销单", bill.bill_no):
        return None

    v_date = bill.approve_date or date.today()
    # 汇总发票明细（不含税/税额/价税合计）
    invs = db.scalars(
        select(im.Invoice).where(im.Invoice.reimbursement_bill_id == bill.id)
    ).all()
    sum_amount = Decimal("0")
    sum_tax = Decimal("0")
    sum_total = Decimal("0")
    for inv in invs:
        for d in inv.details:
            sum_amount += d.amount or Decimal("0")
            sum_tax += d.tax or Decimal("0")
            sum_total += d.total or Decimal("0")

    summary = f"报销单 {bill.bill_no} 报销款（{bill.bill_type}）"
    if sum_total > 0:
        entries = [
            (SUB_MANAGE, "借", summary, sum_amount),
            (SUB_INPUT_TAX, "借", summary, sum_tax),
            (SUB_OTHER_PAY, "贷", summary, sum_total),
        ]
    else:
        amt = bill.amount or Decimal("0")
        entries = [
            (SUB_MANAGE, "借", summary, amt),
            (SUB_OTHER_PAY, "贷", summary, amt),
        ]
    return _make_voucher(
        db, "报销单", bill.bill_no, v_date, maker, summary, entries,
        attach_count=len(invs) or 1,
    )


# ==================== 采购申请 → 凭证 ====================
def generate_from_purchase(db: Session, req: "pm.PurchaseRequisition", maker: str) -> Optional[vm.Voucher]:
    """采购申请审批通过 → 自动凭证（确认应付）。

    规则：借 原材料(1403) [研发项目则借 研发支出(4301)] + 贷 应付账款(2202)，金额=预计金额。
    幂等：source_type='采购申请', source_no=req_no 已存在则跳过。
    """
    if _exists(db, "采购申请", req.req_no):
        return None

    v_date = req.approve_date or date.today()
    amount = req.expected_amount or Decimal("0")
    debit_code = SUB_RDCOST if (req.is_rd_project or "") == "是" else SUB_RAWMAT
    supplier = (req.supplier or "").strip()
    summary = f"采购申请 {req.req_no} 确认应付" + (f"·供应商{supplier}" if supplier else "")
    entries = [
        (debit_code, "借", summary, amount),
        (SUB_AP, "贷", summary, amount),
    ]
    return _make_voucher(
        db, "采购申请", req.req_no, v_date, maker, summary, entries,
        attach_count=1,
    )


# ==================== 工资单 → 凭证 ====================
def generate_from_salary(db: Session, bill: "slm.SalaryBill", maker: str) -> Optional[vm.Voucher]:
    """工资单审核通过 → 自动凭证（计提工资）。

    规则：借 管理费用-工资(5602) + 贷 应付职工薪酬(2211)，金额=应发工资。
    与「报销审批→凭证」「采购审批→凭证」同源，体现「业务单→账务」联动地基。
    幂等：source_type='工资单', source_no=salary_no 已存在则跳过。
    """
    if _exists(db, "工资单", bill.salary_no):
        return None

    v_date = bill.approve_date or date.today()
    gross = bill.gross_pay or Decimal("0")
    summary = f"计提工资 {bill.salary_no} {bill.employee_name}({bill.period})"
    entries = [
        (SUB_WAGE, "借", summary, gross),
        (SUB_PAYROLL_PAY, "贷", summary, gross),
    ]
    return _make_voucher(
        db, "工资单", bill.salary_no, v_date, maker, summary, entries,
        attach_count=1,
    )


# ==================== 支付环节 → 联动付款凭证 ====================
# 关键缺失修复（H1）：此前「支付/发放」动作只改状态、不生成凭证，导致
# 应付/其他应付长期挂账、银行存款从不减少、现金流量表看不到经营流出。
# 以下三个生成器与审批凭证同源、幂等（同 source_type/source_no 仅一张）。
def generate_reimbursement_payment(db: Session, bill: "rm.ReimbursementBill", maker: str) -> Optional[vm.Voucher]:
    """报销款支付 → 自动凭证（结算其他应付款）。

    规则：借 其他应付款(2241) = 报销应付额 + 贷 银行存款(1002) = 同额。
    报销应付额与审批凭证贷方口径一致：有发票取价税合计，否则取报销金额。
    幂等：source_type='报销支付', source_no=bill_no 已存在则跳过。
    """
    if _exists(db, "报销支付", bill.bill_no):
        return None
    v_date = date.today()
    invs = db.scalars(
        select(im.Invoice).where(im.Invoice.reimbursement_bill_id == bill.id)
    ).all()
    sum_total = Decimal("0")
    for inv in invs:
        for d in inv.details:
            sum_total += d.total or Decimal("0")
    pay_amount = sum_total if sum_total > 0 else (bill.amount or Decimal("0"))
    if pay_amount <= 0:
        return None
    summary = f"支付报销款 {bill.bill_no}（{bill.bill_type}）"
    entries = [
        (SUB_OTHER_PAY, "借", summary, pay_amount),
        (SUB_BANK, "贷", summary, pay_amount),
    ]
    return _make_voucher(
        db, "报销支付", bill.bill_no, v_date, maker, summary, entries, attach_count=1,
    )


def generate_salary_payment(db: Session, bill: "slm.SalaryBill", maker: str) -> Optional[vm.Voucher]:
    """工资发放 → 自动凭证（结算应付职工薪酬）。

    规则：借 应付职工薪酬(2211) = 应发 + 贷 银行存款(1002) = 实发(应发−代扣) + 贷 其他应付款(2241) = 代扣(社保/公积金/个税)。
    代扣进入其他应付款，待后续缴纳社保/个税时再清账；银行存款按实发减少。
    幂等：source_type='工资支付', source_no=salary_no 已存在则跳过。
    """
    if _exists(db, "工资支付", bill.salary_no):
        return None
    v_date = date.today()
    gross = bill.gross_pay or Decimal("0")
    deduct = bill.deduct_total or Decimal("0")
    net = (gross - deduct).quantize(Decimal("0.01"))
    if gross <= 0:
        return None
    summary = f"发放工资 {bill.salary_no} {bill.employee_name}({bill.period})"
    entries = [
        (SUB_PAYROLL_PAY, "借", summary, gross),
        (SUB_BANK, "贷", summary, net),
    ]
    if deduct > 0:
        entries.append((SUB_OTHER_PAY, "贷", summary, deduct))
    return _make_voucher(
        db, "工资支付", bill.salary_no, v_date, maker, summary, entries, attach_count=1,
    )


def generate_purchase_payment(db: Session, req: "pm.PurchaseRequisition", maker: str) -> Optional[vm.Voucher]:
    """采购付款 → 自动凭证（结算应付账款）。

    规则：借 应付账款(2202) = 应付额 + 贷 银行存款(1002) = 同额。
    幂等：source_type='采购支付', source_no=req_no 已存在则跳过。
    """
    if _exists(db, "采购支付", req.req_no):
        return None
    v_date = date.today()
    amount = req.expected_amount or Decimal("0")
    if amount <= 0:
        return None
    supplier = (req.supplier or "").strip()
    summary = f"支付采购款 {req.req_no}" + (f"·供应商{supplier}" if supplier else "")
    entries = [
        (SUB_AP, "借", summary, amount),
        (SUB_BANK, "贷", summary, amount),
    ]
    return _make_voucher(
        db, "采购支付", req.req_no, v_date, maker, summary, entries, attach_count=1,
    )


# ==================== 固定资产 → 凭证 ====================
def generate_from_asset_purchase(
    db: Session,
    asset: "fam.FixedAsset",
    maker: str,
    pay_subject: str = SUB_BANK,
    v_date: Optional[date] = None,
) -> Optional[vm.Voucher]:
    """固定资产入账 → 自动凭证（购置）。

    规则：借 固定资产(1601) 原值 + 贷 银行存款(1002) [赊购则贷 应付账款(2202)]，金额=原值。
    幂等：source_type='固定资产', source_no=asset_no 已存在则跳过。
    """
    if _exists(db, "固定资产", asset.asset_no):
        return None
    d = v_date or asset.acquisition_date or date.today()
    amount = asset.original_value or Decimal("0")
    pay_name = _subject_name(db, pay_subject)
    summary = f"固定资产入账 {asset.asset_no} {asset.name}"
    entries = [
        (SUB_FIXED_ASSET, "借", summary, amount),
        (pay_subject, "贷", summary, amount),
    ]
    voc = _make_voucher(
        db, "固定资产", asset.asset_no, d, maker, summary, entries, attach_count=1,
    )
    asset.record_voucher_no = voc.voucher_no
    db.add(asset)
    return voc


def generate_depreciation_voucher(
    db: Session,
    period: str,
    maker: str,
    lines: List[Tuple[str, Decimal]],  # (折旧费用科目 code, 该科目当月折旧合计)
    total_amount: Decimal,
    v_date: Optional[date] = None,
) -> Optional[vm.Voucher]:
    """计提折旧汇总凭证：所有在用资产当月折旧合并成一张凭证。

    规则：借 折旧费用科目(按资产类别分摊：管理费用5602 / 研发支出4301…) + 贷 累计折旧(1602) 总额。
    幂等：source_type='固定资产折旧', source_no='ZCDEP|{period}' 已存在则跳过（同月重计提不再重复）。
    """
    if _exists(db, "固定资产折旧", f"ZCDEP|{period}"):
        return None
    y, m = period.split("-")
    d = v_date or date(int(y), int(m), 28)
    summary = f"计提固定资产折旧 {period}"
    entries: List[Tuple[str, str, str, Decimal]] = []
    for code, amt in lines:
        if amt and amt > 0:
            entries.append((code, "借", summary, amt))
    entries.append((SUB_ACCUM_DEP, "贷", summary, total_amount))
    return _make_voucher(
        db, "固定资产折旧", f"ZCDEP|{period}", d, maker, summary, entries, attach_count=1,
    )


def generate_disposal_voucher(
    db: Session,
    asset: "fam.FixedAsset",
    maker: str,
    v_date: Optional[date] = None,
) -> Optional[vm.Voucher]:
    """固定资产处置 → 自动凭证（报废/清理，按账面净值转费用）。

    规则：借 累计折旧(1602) 累计额 + 借 管理费用(5602) 账面净值(原值−累计) + 贷 固定资产(1601) 原值。
    处置净损失计入管理费用（小企业简化处理，不留「固定资产清理」挂账）。
    幂等：source_type='固定资产处置', source_no=asset_no 已存在则跳过。
    """
    if _exists(db, "固定资产处置", asset.asset_no):
        return None
    d = v_date or date.today()
    accum = asset.accum_dep or Decimal("0")
    original = asset.original_value or Decimal("0")
    net = (original - accum).quantize(Decimal("0.01"))
    summary = f"固定资产处置 {asset.asset_no} {asset.name}"
    entries = [
        (SUB_ACCUM_DEP, "借", summary, accum),
        (SUB_MANAGE, "借", summary, net),
        (SUB_FIXED_ASSET, "贷", summary, original),
    ]
    voc = _make_voucher(
        db, "固定资产处置", asset.asset_no, d, maker, summary, entries, attach_count=1,
    )
    asset.dispose_voucher_no = voc.voucher_no
    db.add(asset)
    return voc


# ==================== 批量补生成（回填历史已通过单据）====================
def sync_from_approved(db: Session, maker: str) -> Tuple[int, int, List[str]]:
    """扫描所有「已通过」的报销单/采购申请，对尚未生成凭证的补生成。

    用于：(1) 历史数据回填；(2) 一键把联动铺开到现有业务单。
    返回 (生成数, 跳过数, 明细日志)。
    """
    generated = 0
    skipped = 0
    logs: List[str] = []

    bills = db.scalars(
        select(rm.ReimbursementBill).where(rm.ReimbursementBill.status == "已通过")
    ).all()
    for b in bills:
        v = generate_from_reimbursement(db, b, maker)
        if v:
            generated += 1
            logs.append(f"报销单 {b.bill_no} → {v.voucher_no}")
        else:
            skipped += 1

    reqs = db.scalars(
        select(pm.PurchaseRequisition).where(pm.PurchaseRequisition.status == "已通过")
    ).all()
    for r in reqs:
        v = generate_from_purchase(db, r, maker)
        if v:
            generated += 1
            logs.append(f"采购申请 {r.req_no} → {v.voucher_no}")
        else:
            skipped += 1

    sbills = db.scalars(
        select(slm.SalaryBill).where(slm.SalaryBill.status == "已通过")
    ).all()
    for b in sbills:
        v = generate_from_salary(db, b, maker)
        if v:
            generated += 1
            logs.append(f"工资单 {b.salary_no} → {v.voucher_no}")
        else:
            skipped += 1

    db.commit()
    return generated, skipped, logs
