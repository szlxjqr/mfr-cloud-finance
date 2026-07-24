"""通过后端 API 造数：覆盖 2026-05 ~ 2026-12 共 8 个月，每模块每月都有业务单。

口径（老板给定）：
- 工资：沈雷 5000/月、沈月 4000/月（提交即自动审批并联动生成凭证）
- 房租水电：1300/月（费用报销，借管理费用/贷其他应付款）
- 差旅：全年 50000，分摊到 8 个月（差旅报销，借管理费用/贷其他应付款）
- 研发采购：5~10 月共 300000，is_rd_project=是（借研发支出/贷应付账款）
- 差旅申请：每月 1 单（仅流程数据，不联动凭证）
- 资本实缴 100 万（6/20）由 patch_periods.py 直接插凭证（无对应业务接口）

注意：接口审批会把凭证日期写成「今天」，故本脚本造完后由 patch_periods.py
把每张凭证的 voucher_date/period 回写为正确月份，并重排凭证号。
"""
import requests

BASE = "http://localhost:8521/api"
EMP_LEI = "沈雷"
EMP_YUE = "沈月"

# 研发采购分摊（5~10月，合计 300000）
RD_PLAN = {5: 60000, 6: 60000, 7: 60000, 8: 30000, 9: 30000, 10: 60000}
# 差旅费分摊（5~12月，合计 50000）
TRAVEL_PLAN = {5: 8000, 6: 7000, 7: 7000, 8: 6000, 9: 6000, 10: 5000, 11: 5000, 12: 6000}
RENT = 1300
SALARY_LEI = 5000
SALARY_YUE = 4000


def login():
    r = requests.post(BASE + "/auth/login",
                      json={"username": "admin", "password": "admin123"}, timeout=30)
    if r.status_code >= 400:
        raise SystemExit(f"login failed {r.status_code} {r.text[:200]}")
    tok = r.json()["token"]
    print("login OK, token len =", len(tok))
    return {"Authorization": f"Bearer {tok}"}


def post(path, payload, H):
    r = requests.post(BASE + path, json=payload, headers=H, timeout=30)
    if r.status_code >= 400:
        print(f"  ERR POST {path} {r.status_code} {r.text[:200]}")
        return None
    return r.json()


def submit(path, rid, H):
    r = requests.post(BASE + f"{path}/{rid}/submit", headers=H, timeout=30)
    if r.status_code >= 400:
        print(f"  ERR submit {path}/{rid} {r.status_code} {r.text[:200]}")
        return None
    return r.json()


def main():
    H = login()
    created = []
    for m in range(5, 13):
        ym = f"2026-{m:02d}"
        # 1) 工资 ×2（沈雷 / 沈月）
        for emp, amt in [(EMP_LEI, SALARY_LEI), (EMP_YUE, SALARY_YUE)]:
            b = post("/salaries", {"employee_name": emp, "period": ym,
                                 "base_salary": amt, "remark": f"测试{ym}"}, H)
            if b:
                submit("/salaries", b["id"], H)
                created.append(("工资", ym, b.get("salary_no")))
        # 2) 房租水电报销 1300（费用报销）
        b = post("/reimbursements", {"applicant": EMP_LEI, "amount": RENT,
                               "reason": f"房租水电-测试{ym}", "remark": ym,
                               "bill_type": "费用报销"}, H)
        if b:
            submit("/reimbursements", b["id"], H)
            created.append(("房租", ym, b.get("bill_no")))
        # 3) 差旅报销（分摊）
        tv = TRAVEL_PLAN[m]
        b = post("/reimbursements", {"applicant": EMP_LEI, "amount": tv,
                               "reason": f"差旅费-测试{ym}", "remark": ym,
                               "bill_type": "差旅报销", "travel_destination": "赣州/深圳"}, H)
        if b:
            submit("/reimbursements", b["id"], H)
            created.append(("差旅报销", ym, b.get("bill_no")))
        # 4) 研发采购（仅 5~10 月）
        if m in RD_PLAN:
            b = post("/purchases", {"applicant": EMP_LEI,
                                 "item_name": f"研发物料/算力-测试{ym}",
                                 "expected_amount": RD_PLAN[m], "is_rd_project": "是",
                                 "supplier": "测试供应商-智元科技",
                                 "expected_date": f"{ym}-05",
                                 "reason": f"研发采购-测试{ym}"}, H)
            if b:
                submit("/purchases", b["id"], H)
                created.append(("研发采购", ym, b.get("req_no")))
        # 5) 差旅申请（仅流程数据，无凭证）
        b = post("/travels", {"applicant": EMP_LEI, "traveler": EMP_LEI,
                              "destination": f"赣州/深圳-测试{ym}",
                              "travel_start": f"{ym}-10", "travel_end": f"{ym}-12",
                              "reason": f"出差-测试{ym}", "expected_amount": TRAVEL_PLAN[m]}, H)
        if b:
            submit("/travels", b["id"], H)
            created.append(("差旅申请", ym, b.get("req_no")))

    print(f"TOTAL 业务单据创建: {len(created)}")
    for kind, ym, no in created:
        print(f"  {kind:6s} {ym}  {no}")


if __name__ == "__main__":
    main()
