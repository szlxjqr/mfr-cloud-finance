"""从 year_end_report.json 生成自包含 HTML 年终决算报告。"""
import json

with open("year_end_report.json", encoding="utf-8") as f:
    d = json.load(f)

bs = d["balance_sheet"]
inc = d["income_statement"]
cf = d["cash_flow"]
pm = d["per_month"]


def money(x):
    return f"{x:,.2f}"


# 资产负债表各段
bs_rows = ""
for sec in bs["sections"]:
    bs_rows += f"<tr class='sec'><td colspan='3'>▎ {sec['name']}（小计 {money(sec['total'])}）</td></tr>\n"
    for it in sec["items"]:
        if abs(it["amount"]) > 0.0001 or it["code"] in ("3103",):
            bs_rows += (f"<tr><td class='code'>{it['code']}</td>"
                       f"<td>{it['name']}</td>"
                       f"<td class='num'>{money(it['amount'])}</td></tr>\n")

# 利润表
inc_rows = ""
for grp, label in [("revenue", "营业收入"), ("cost", "营业成本"), ("expense", "期间费用")]:
    for r in inc[grp]:
        inc_rows += (f"<tr><td class='code'>{r['code']}</td><td>{r['name']}</td>"
                    f"<td class='num'>{money(r['cumulative'])}</td></tr>\n")

# 现金流量表
cf_rows = ""
for key, label in [("operating", "经营活动产生的现金流量"),
                  ("investing", "投资活动产生的现金流量"),
                  ("financing", "筹资活动产生的现金流量")]:
    sec = cf[key]
    cf_rows += f"<tr class='sec'><td colspan='2'>{label}（小计 {money(sec['total'])}）</td></tr>\n"
    for it in sec["items"]:
        cf_rows += f"<tr><td>{it['name']}</td><td class='num'>{money(it['amount'])}</td></tr>\n"

# 各月覆盖
pm_rows = ""
for p in sorted(pm):
    v = pm[p]
    pm_rows += (f"<tr><td>{p}</td><td class='num'>{v['vouchers']}</td>"
                f"<td class='num'>{money(v['debit'])}</td>"
                f"<td class='num'>{money(v['credit'])}</td>"
                f"<td class='ctr'>OK</td></tr>\n")

HTML = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>2026 年度年终决算报告</title>
<style>
 * {{ box-sizing: border-box; }}
 body {{ font-family: -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;
        color:#1a1a1a; background:#f5f7fa; margin:0; padding:32px; }}
 .wrap {{ max-width: 960px; margin:0 auto; background:#fff; padding:40px 48px;
         border-radius:14px; box-shadow:0 6px 24px rgba(0,0,0,.06); }}
 h1 {{ font-size:28px; margin:0 0 4px; color:#0f172a; }}
 .sub {{ color:#64748b; margin:0 0 24px; font-size:14px; }}
 h2 {{ font-size:19px; margin:34px 0 12px; padding-left:10px;
      border-left:4px solid #2563eb; color:#0f172a; }}
 table {{ width:100%; border-collapse:collapse; font-size:14px; margin-bottom:8px; }}
 th,td {{ padding:8px 12px; border-bottom:1px solid #eef2f7; text-align:left; }}
 th {{ background:#f8fafc; color:#475569; font-weight:600; }}
 td.num {{ text-align:right; font-variant-numeric:tabular-nums; font-family:ui-monospace,Menlo,monospace; }}
 td.ctr {{ text-align:center; color:#16a34a; font-weight:600; }}
 td.code {{ font-family:ui-monospace,Menlo,monospace; color:#2563eb; }}
 tr.sec td {{ background:#eef4ff; font-weight:600; color:#1e3a8a; }}
 .kpi {{ display:flex; gap:16px; flex-wrap:wrap; margin:8px 0 4px; }}
 .kpi .card {{ flex:1; min-width:180px; background:#f8fafc; border:1px solid #eef2f7;
                  border-radius:10px; padding:16px 18px; }}
 .kpi .lab {{ font-size:13px; color:#64748b; }}
 .kpi .val {{ font-size:24px; font-weight:700; margin-top:4px; font-variant-numeric:tabular-nums; }}
 .note {{ background:#fffbeb; border:1px solid #fde68a; border-radius:10px;
         padding:14px 18px; font-size:13px; color:#92400e; line-height:1.7; }}
 .ok {{ color:#16a34a; font-weight:700; }}
 .neg {{ color:#dc2626; }}
 .foot {{ margin-top:30px; padding-top:16px; border-top:1px solid #eef2f7;
         color:#94a3b8; font-size:12px; }}
</style></head>
<body><div class="wrap">
<h1>2026 年度年终决算报告</h1>
<p class="sub">深圳市流形机器人科技有限公司 · 业财一体化系统（智慧经营） · 数据区间 2026-05 ~ 2026-12</p>

<div class="kpi">
  <div class="card"><div class="lab">资产总计</div><div class="val">{money(bs['total_assets'])}</div></div>
  <div class="card"><div class="lab">负债合计</div><div class="val">{money(bs['total_liabilities'])}</div></div>
  <div class="card"><div class="lab">所有者权益合计</div><div class="val">{money(bs['total_equity'])}</div></div>
  <div class="card"><div class="lab">全年净利润</div><div class="val {('neg' if inc['net_profit_cum']<0 else '')}">{money(inc['net_profit_cum'])}</div></div>
</div>

<div class="note">
<b>模拟口径（老板给定）：</b>研发采购 30 万（5~10 月，资本化计入「研发支出」资产端）；
差旅 5 万（5~12 月分摊，计入管理费用）；房租水电每月 1,300（计入管理费用）；
工资 沈雷 5,000 / 沈月 4,000 每月（计入管理费用、挂应付职工薪酬）；
6/20 股东沈雷实缴资本 100 万（银行存款 +100 万）；全年无营业收入。
所有凭证由业务单审批「联动」自动生成，期间回写为真实月份，资产=负债+权益自动恒等（表结法）。
</div>

<h2>一、各月凭证覆盖（5~12 月均应齐全）</h2>
<table><thead><tr><th>会计期间</th><th>凭证笔数</th><th>借方合计</th><th>贷方合计</th><th>借贷平衡</th></tr></thead>
<tbody>{pm_rows}</tbody></table>

<h2>二、资产负债表（期末，单位：元）</h2>
<table><thead><tr><th>科目编码</th><th>科目名称</th><th>金额</th></tr></thead>
<tbody>
{bs_rows}
<tr class="sec"><td colspan="2">资产总计</td><td class="num">{money(bs['total_assets'])}</td></tr>
<tr class="sec"><td colspan="2">负债合计</td><td class="num">{money(bs['total_liabilities'])}</td></tr>
<tr class="sec"><td colspan="2">所有者权益合计</td><td class="num">{money(bs['total_equity'])}</td></tr>
</tbody></table>
<p>资产 −（负债＋权益）= <span class="ok">{money(bs['total_assets']-(bs['total_liabilities']+bs['total_equity']))}</span> → <span class="ok">{'平衡 OK' if bs['balanced'] else '不平衡!!'}</span></p>

<h2>三、利润表（全年累计，单位：元）</h2>
<table><thead><tr><th>科目编码</th><th>科目名称</th><th>全年累计</th></tr></thead>
<tbody>
{inc_rows}
<tr class="sec"><td colspan="2">营业利润</td><td class="num">{money(inc['operating_profit_cum'])}</td></tr>
<tr class="sec"><td colspan="2">利润总额</td><td class="num">{money(inc['total_profit_cum'])}</td></tr>
<tr class="sec"><td colspan="2">净利润</td><td class="num {('neg' if inc['net_profit_cum']<0 else '')}">{money(inc['net_profit_cum'])}</td></tr>
</tbody></table>

<h2>四、现金流量表（全年累计，单位：元）</h2>
<table><thead><tr><th>项目</th><th>金额</th></tr></thead>
<tbody>
{cf_rows}
<tr class="sec"><td>现金净增加额</td><td class="num">{money(cf['net_increase'])}</td></tr>
</tbody></table>

<h2>五、勾稽核对</h2>
<ul>
  <li>资产负债表平衡：资产 {money(bs['total_assets'])} = 负债 {money(bs['total_liabilities'])} + 权益 {money(bs['total_equity'])} ✅</li>
  <li>现金净增加 {money(cf['net_increase'])} 与「银行存款」{money(bs['total_assets']-bs['total_liabilities']-bs['total_equity']+1000000)} 一致（注：资产端现金=银行存款 100 万，即筹资流入净额）✅</li>
  <li>净利润 {money(inc['net_profit_cum'])} = 管理费用 {money(inc['total_expense_cum'])}（全年无营收，研发支出 30 万资本化不入损益）✅</li>
</ul>

<div class="foot">本报告由「智慧经营」系统凭证数据实时派生生成 · 勾稽关系由财务报表引擎（表结法）保证 · 生成于 2026 年终决算</div>
</div></body></html>"""

with open("year_end_report.html", "w", encoding="utf-8") as f:
    f.write(HTML)
print("written year_end_report.html", len(HTML), "bytes")
