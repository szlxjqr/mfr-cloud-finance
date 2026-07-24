"""年终决算校验：拉取三大报表（截至 2026-12）+ 序时账，输出并保存 JSON。"""
import requests, json

BASE = "http://127.0.0.1:8521/api"
H = {"Authorization": "Bearer " + requests.post(
    BASE + "/auth/login", json={"username": "admin", "password": "admin123"}, timeout=30
).json()["token"]}


def get(path, params=None):
    r = requests.get(BASE + path, params=params, headers=H, timeout=30)
    if r.status_code >= 400:
        raise SystemExit(f"GET {path} -> {r.status_code} {r.text[:200]}")
    return r.json()


def main():
    bs = get("/financial/balance-sheet", {"period": "2026-12"})
    inc = get("/financial/income-statement", {"period": "2026-12"})
    cf = get("/financial/cash-flow")  # 全年累计（不传 period）
    jour = get("/ledger/journal")  # 全部序时账

    # 各月凭证数（按凭证号去重）& 借贷合计
    per_month = {}
    for ln in jour["lines"]:
        p = ln["period"]
        d = per_month.setdefault(p, {"vnos": set(), "debit": 0.0, "credit": 0.0})
        d["vnos"].add(ln["voucher_no"])
        if ln["direction"] == "借":
            d["debit"] += ln["amount"]
        else:
            d["credit"] += ln["amount"]

    print("=" * 64)
    print("            2026 年度年终决算（截至 2026-12）")
    print("=" * 64)

    print("\n【一】各月凭证覆盖（5~12 月均应 >0）")
    for p in sorted(per_month):
        d = per_month[p]
        bal = "OK" if abs(d["debit"] - d["credit"]) < 0.005 else "借贷不平!"
        print(f"  {p}: 凭证 {len(d['vnos']):2d} 笔 | 借 {d['debit']:>12,.2f} | 贷 {d['credit']:>12,.2f}  {bal}")
    tot_d = sum(d["debit"] for d in per_month.values())
    tot_c = sum(d["credit"] for d in per_month.values())
    print(f"  全年代借 {tot_d:,.2f} / 全年代贷 {tot_c:,.2f}  总平衡={'OK' if abs(tot_d-tot_c)<0.005 else 'FAIL'}")

    print("\n【二】资产负债表（期末，元）")
    print(f"  资产总计          : {bs['total_assets']:>14,.2f}")
    print(f"  负债合计          : {bs['total_liabilities']:>14,.2f}")
    print(f"  所有者权益合计      : {bs['total_equity']:>14,.2f}")
    print(f"  资产 - (负债+权益) : {bs['total_assets']-(bs['total_liabilities']+bs['total_equity']):>14,.2f}  {'平衡 OK' if bs['balanced'] else '不平衡!!'}")
    for sec in bs["sections"]:
        print(f"\n  ▎ {sec['name']}（小计 {sec['total']:,.2f}）")
        for it in sec["items"]:
            if abs(it["amount"]) > 0.0001 or it["code"] in ("3103",):
                print(f"     {it['code']} {it['name']:<8} : {it['amount']:>14,.2f}")

    print("\n【三】利润表（全年累计，元）")
    print(f"  营业收入合计 : {inc['total_revenue_cum']:>14,.2f}")
    print(f"  营业成本合计 : {inc['total_expense_cum']:>14,.2f}")
    print(f"  营业利润     : {inc['operating_profit_cum']:>14,.2f}")
    print(f"  利润总额     : {inc['total_profit_cum']:>14,.2f}")
    print(f"  净利润       : {inc['net_profit_cum']:>14,.2f}")

    print("\n【四】现金流量表（全年累计，元）")
    print(f"  经营活动净额 : {cf['net_operating']:>14,.2f}")
    print(f"  投资活动净额 : {cf['net_investing']:>14,.2f}")
    print(f"  筹资活动净额 : {cf['net_financing']:>14,.2f}")
    print(f"  现金净增加额 : {cf['net_increase']:>14,.2f}")
    if cf.get("note"):
        print(f"  备注: {cf['note']}")

    out = {
        "as_of": "2026-12",
        "per_month": {p: {"vouchers": len(d["vnos"]), "debit": round(d["debit"], 2), "credit": round(d["credit"], 2)}
                   for p, d in sorted(per_month.items())},
        "balance_sheet": bs,
        "income_statement": inc,
        "cash_flow": cf,
        "journal_lines": len(jour["lines"]),
    }
    with open("year_end_report.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("\n报告已保存: year_end_report.json")


if __name__ == "__main__":
    main()
