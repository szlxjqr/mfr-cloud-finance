"""工资管理 API：工资单的 CRUD 与状态流转。

联动：审核通过（含一人公司提交即自动审批）时，自动生成记账凭证：
    借 管理费用-工资(5602) = 应发
    贷 应付职工薪酬(2211) = 应发
与「报销审批→凭证」「采购审批→凭证」同源，体现「业务单→账务」联动地基。
"""
from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import salary as m
from app.schemas import salary as s
from app.utils.codegen import gen_salary_no
from app.utils import approval
from app.services import voucher_service  # 联动：归档 → 自动生成凭证（审核通过不再生成，遵循归档闸门）
from app.services import salary_service as svc  # 部门汇总 / 个税报表 / 设置计算
from app.models import employee as emp  # 权限判定用的 Account 模型
from app.api.auth import require_admin_gm  # 反归档/冲销限 admin/gm

router = APIRouter(prefix="/salaries", tags=["salaries"])

# 状态流转白名单：当前状态 -> 允许的动作 -> 目标状态
# 新流程：草稿→待审批→已通过→已归档(生成计提凭证)→已发放(生成支付凭证)
# 反归档(限admin/gm)：已归档→已通过，删除计提凭证；冲销(限admin/gm)：已发放→已冲销，红冲计提+支付凭证
_STATUS_FLOW = {
    "草稿": {"submit": "待审批"},
    "待审批": {"approve": "已通过", "reject": "已驳回"},
    "已通过": {"archive": "已归档"},                       # 归档闸门：生成计提凭证(已审核)
    "已归档": {"pay": "已发放", "unarchive": "已通过"},    # 反归档(限admin/gm,删凭证)
    "已驳回": {"submit": "待审批"},                       # 重新提交
    "已发放": {"writeoff": "已冲销"},                     # 冲销(限admin/gm,红冲)
    "已冲销": {},                                          # 终态
}


def _get_or_404(db: Session, pk: int):
    obj = db.get(m.SalaryBill, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="工资单不存在")
    return obj


def _to_decimal(v) -> Decimal:
    if v is None or v == "":
        return Decimal("0")
    try:
        return Decimal(str(v))
    except Exception:
        return Decimal("0")


def _derive(data: dict) -> dict:
    """由组件字段计算派生值（应发/代扣/实发），统一前后端口径。"""
    base = _to_decimal(data.get("base_salary"))
    perf = _to_decimal(data.get("performance"))
    ot = _to_decimal(data.get("overtime"))
    bonus = _to_decimal(data.get("bonus"))
    gross = base + perf + ot + bonus
    social = _to_decimal(data.get("social_personal"))
    fund = _to_decimal(data.get("fund_personal"))
    tax = _to_decimal(data.get("tax_personal"))
    deduct = social + fund + tax
    net = gross - deduct
    data["base_salary"] = base
    data["performance"] = perf
    data["overtime"] = ot
    data["bonus"] = bonus
    data["gross_pay"] = gross
    data["social_personal"] = social
    data["fund_personal"] = fund
    data["tax_personal"] = tax
    data["deduct_total"] = deduct
    data["net_pay"] = net
    return data


def _recompute(obj: m.SalaryBill) -> None:
    """对已有对象按其当前组件字段重算派生值并写回。"""
    d = _derive(
        {
            "base_salary": obj.base_salary,
            "performance": obj.performance,
            "overtime": obj.overtime,
            "bonus": obj.bonus,
            "social_personal": obj.social_personal,
            "fund_personal": obj.fund_personal,
            "tax_personal": obj.tax_personal,
        }
    )
    obj.gross_pay = d["gross_pay"]
    obj.deduct_total = d["deduct_total"]
    obj.net_pay = d["net_pay"]


# ================= CRUD =================
@router.get("", response_model=list[s.SalaryBillRead])
def list_bills(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    employee_name: Optional[str] = None,
    period: Optional[str] = None,
    db: Session = Depends(get_db),
):
    stmt = select(m.SalaryBill)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(
            (m.SalaryBill.salary_no.like(like))
            | (m.SalaryBill.employee_name.like(like))
            | (m.SalaryBill.department.like(like))
        )
    if status:
        stmt = stmt.where(m.SalaryBill.status == status)
    if employee_name:
        stmt = stmt.where(m.SalaryBill.employee_name == employee_name)
    if period:
        stmt = stmt.where(m.SalaryBill.period == period)
    return db.scalars(stmt).all()


@router.get("/allocation", response_model=dict)
def salary_allocation(
    period: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """工资分摊：按部门归集工资成本并计算分摊占比（研发部占比=研发投入人力成本）。"""
    return svc.salary_allocation(db, period=period, status=status)


@router.get("/next-salary-no", response_model=dict)
def next_salary_no(db: Session = Depends(get_db)):
    """新建工资单前预占下一个单号（仅预览/预填）。"""
    salary_no = gen_salary_no(db)
    db.commit()  # 预占必须 commit；否则 session close 时 SQLAlchemy 会自动 rollback，计数器不递增
    return {"salary_no": salary_no}


@router.get("/dept-summary", response_model=list[dict])
def dept_summary(
    period: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """部门工资汇总表：按 (部门, 工资月份) 聚合应发/代扣/实发。"""
    return svc.dept_summary(db, period=period, status=status)


@router.get("/tax-report", response_model=list[dict])
def tax_report(
    period: Optional[str] = None,
    employee_name: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """个税报表：按 (员工, 部门, 工资月份) 聚合个税与应发。"""
    return svc.tax_report(db, period=period, employee_name=employee_name)


@router.post("", response_model=s.SalaryBillRead, status_code=201)
def create_bill(payload: s.SalaryBillCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()
    if not data.get("salary_no"):
        data["salary_no"] = gen_salary_no(db)
    _derive(data)
    obj = m.SalaryBill(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{bid}", response_model=s.SalaryBillRead)
def get_bill(bid: int, db: Session = Depends(get_db)):
    return _get_or_404(db, bid)


@router.put("/{bid}", response_model=s.SalaryBillRead)
def update_bill(bid: int, payload: s.SalaryBillUpdate, db: Session = Depends(get_db)):
    obj = _get_or_404(db, bid)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    _recompute(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{bid}")
def delete_bill(bid: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, bid)
    db.delete(obj)
    db.commit()
    return {"ok": True}


# ================= 状态流转 =================
@router.post("/{bid}/submit", response_model=s.SalaryBillRead)
def submit_bill(bid: int, db: Session = Depends(get_db)):
    """提交工资单 → 一人公司自动审批通过（并联动生成凭证）。"""
    obj = _get_or_404(db, bid)
    if "submit" not in _STATUS_FLOW.get(obj.status, {}):
        raise HTTPException(status_code=400, detail=f"当前状态「{obj.status}」不允许提交")
    obj.status = _STATUS_FLOW[obj.status]["submit"]
    obj.submit_date = date.today()
    # 一人公司：提交即自动审批完成（总经理的审批由 admin、其他由总经理）
    approver = approval.resolve_auto_approver(db, obj.employee_name)
    obj.status = _STATUS_FLOW.get("待审批", {}).get("approve", "已通过")
    obj.approve_date = date.today()
    obj.approver = approver
    obj.approve_remark = "系统自动审批（一人公司）"
    # 归档闸门：提交/审批通过不再生成凭证，凭证在「归档」动作时生成（避免未归档即入账）
    _recompute(obj)
    db.add(obj)
    db.flush()
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/{bid}/approve", response_model=s.SalaryBillRead)
def approve_bill(bid: int, body: s.ApprovalBody, db: Session = Depends(get_db)):
    obj = _get_or_404(db, bid)
    if "approve" not in _STATUS_FLOW.get(obj.status, {}):
        raise HTTPException(status_code=400, detail=f"当前状态「{obj.status}」不允许审批通过")
    if not body.approver or not body.approver.strip():
        raise HTTPException(status_code=422, detail="审批人不能为空")
    obj.status = _STATUS_FLOW[obj.status]["approve"]
    obj.approve_date = date.today()
    obj.approver = body.approver.strip()
    obj.approve_remark = body.remark.strip() if body.remark else None
    # 归档闸门：审批通过不再生成凭证，凭证在「归档」动作时生成
    _recompute(obj)
    db.add(obj)
    db.flush()
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/{bid}/reject", response_model=s.SalaryBillRead)
def reject_bill(bid: int, body: s.ApprovalBody, db: Session = Depends(get_db)):
    obj = _get_or_404(db, bid)
    if "reject" not in _STATUS_FLOW.get(obj.status, {}):
        raise HTTPException(status_code=400, detail=f"当前状态「{obj.status}」不允许驳回")
    if not body.approver or not body.approver.strip():
        raise HTTPException(status_code=422, detail="审批人不能为空")
    obj.status = _STATUS_FLOW[obj.status]["reject"]
    obj.approve_date = date.today()
    obj.approver = body.approver.strip()
    obj.approve_remark = body.remark.strip() if body.remark else None
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/{bid}/pay", response_model=s.SalaryBillRead)
def pay_bill(bid: int, body: Optional[s.ApprovalBody] = None, db: Session = Depends(get_db)):
    obj = _get_or_404(db, bid)
    if "pay" not in _STATUS_FLOW.get(obj.status, {}):
        raise HTTPException(status_code=400, detail=f"当前状态「{obj.status}」不允许发放")
    obj.status = _STATUS_FLOW[obj.status]["pay"]
    obj.pay_date = date.today()
    if body and body.approver and body.approver.strip():
        obj.payee = body.approver.strip()
        obj.pay_remark = body.remark.strip() if body.remark else None
    # 联动：发放工资 → 自动生成付款凭证（借应付职工薪酬 / 贷银行存款，代扣转其他应付款，幂等）
    voucher_service.generate_salary_payment(db, obj, maker=obj.payee or obj.approver or "system")
    db.commit()
    db.refresh(obj)
    return obj


# ================= 归档闸门 / 反归档 / 冲销 =================
@router.post("/{bid}/archive", response_model=s.SalaryBillRead)
def archive_bill(bid: int, db: Session = Depends(get_db)):
    """归档：已通过 → 已归档，联动生成计提凭证（借管理费用-工资 / 贷应付职工薪酬）并自动审核入账。

    归档闸门：只有归档动作才联动账务，未归档的工资单不进凭证/账簿/报表。
    幂等：source_type='工资单', source_no=salary_no 已存在凭证则跳过。
    """
    obj = _get_or_404(db, bid)
    if "archive" not in _STATUS_FLOW.get(obj.status, {}):
        raise HTTPException(status_code=400, detail=f"当前状态「{obj.status}」不允许归档（仅已通过可归档）")
    obj.status = _STATUS_FLOW[obj.status]["archive"]
    _recompute(obj)
    db.add(obj)
    db.flush()
    voucher_service.generate_from_salary(db, obj, maker=obj.approver or "system")
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/{bid}/unarchive", response_model=s.SalaryBillRead)
def unarchive_bill(
    bid: int,
    current_user: emp.Account = Depends(require_admin_gm),
    db: Session = Depends(get_db),
):
    """反归档（撤销）：已归档 → 已通过，删除该工资单联动的计提凭证（级联删分录），回退待重新归档。

    限 admin/gm。已发放（已支付）不可反归档，须走冲销（红字冲销）。工资单未存 voucher_no，直接按 source_no 删凭证。
    """
    obj = _get_or_404(db, bid)
    if "unarchive" not in _STATUS_FLOW.get(obj.status, {}):
        raise HTTPException(status_code=400, detail=f"当前状态「{obj.status}」不允许反归档（仅已归档可反归档）")
    obj.status = _STATUS_FLOW[obj.status]["unarchive"]
    db.add(obj)
    db.flush()
    # 撤销账务：按 source_no 删除计提凭证（工资单未支付时无支付凭证；即便存在也一并清除）
    voucher_service.void_vouchers_by_source_no(db, obj.salary_no)
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/{bid}/writeoff", response_model=s.SalaryBillRead)
def writeoff_bill(
    bid: int,
    current_user: emp.Account = Depends(require_admin_gm),
    db: Session = Depends(get_db),
):
    """冲销（红字冲销）：已发放 → 已冲销，对该工资单联动的计提+支付凭证做红字冲销（原凭证标记已冲销保留）。

    限 admin/gm。支付后不可反归档，故提供冲销：生成借贷反向、金额相同的红冲凭证（已审核）即时抵消，
    原+冲销+新 三套凭证共存、账务闭合。若已冲销则拒绝重复冲销。
    """
    obj = _get_or_404(db, bid)
    if "writeoff" not in _STATUS_FLOW.get(obj.status, {}):
        raise HTTPException(status_code=400, detail=f"当前状态「{obj.status}」不允许冲销（仅已发放可冲销）")
    obj.status = _STATUS_FLOW[obj.status]["writeoff"]
    db.add(obj)
    db.flush()
    try:
        red_no, cnt = voucher_service.reverse_vouchers_by_source_no(
            db, obj.salary_no, maker=current_user.username
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    db.commit()
    db.refresh(obj)
    return obj
