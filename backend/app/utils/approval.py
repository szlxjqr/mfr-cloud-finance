"""一人公司审批链工具。

业务背景（2026-07-22 确认）：
- 一人公司，员工 / 部门负责人 / 总经理 实为同一人。
- 审批规则：
  * 若申请人本人就是「总经理」(role=gm)，则其审批由「系统管理员」(admin) 自动完成；
  * 其他员工提交的审批，由「总经理」(gm) 自动完成；
  * 若系统中尚不存在总经理(gm)，则一律兜底由 admin 自动完成。

返回审批人姓名（写入业务单 approver 字段），全部自动、无需人工点审。
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import employee as m


def resolve_auto_approver(db: Session, applicant_name: str) -> str:
    """根据申请人姓名，解析应执行审批的账号，返回其姓名。

    查找顺序：
    1. 申请人自身账号（按姓名关联 Employee → Account）；
    2. 系统中唯一的 gm（总经理）账号；
    3. 兜底：employee_no = 00000000 的 admin 账号。

    返回审批人姓名（admin 缺省显示「管理员」）。
    """
    # 申请人账号
    applicant_acc = None
    if applicant_name:
        applicant_emp = db.scalar(
            select(m.Employee).where(m.Employee.name == applicant_name)
        )
        if applicant_emp:
            applicant_acc = db.scalar(
                select(m.Account).where(m.Account.employee_no == applicant_emp.employee_no)
            )

    # 总经理账号（取第一个 gm）
    gm_acc = db.scalar(select(m.Account).where(m.Account.role == "gm"))
    # 管理员账号（兜底）
    admin_acc = db.scalar(
        select(m.Account).where(m.Account.employee_no == "00000000")
    )

    # 规则 1：申请人本身就是 gm → 由 admin 审批
    if applicant_acc is not None and applicant_acc.role == "gm":
        if admin_acc is not None:
            return admin_acc.employee.name if admin_acc.employee else "管理员"
        return "管理员"

    # 规则 2：其他员工 → 由 gm 审批
    if gm_acc is not None:
        return gm_acc.employee.name if gm_acc.employee else "总经理"

    # 规则 3：无 gm → admin 兜底
    if admin_acc is not None:
        return admin_acc.employee.name if admin_acc.employee else "管理员"
    return "管理员"
