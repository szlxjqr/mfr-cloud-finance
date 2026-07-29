import type { TravelReq } from '@/types/travel'

const fmt = (v: any, fallback = '-'): string => {
  const n = Number(v)
  return Number.isFinite(n) ? n.toFixed(2) : fallback
}

/**
 * 打印差旅申请单
 * 技术方案对齐 PurchaseApply.printPurchase()：动态生成完整 HTML 并写入隐藏 iframe，
 * 避免 el-dialog transform/遮罩影响打印内容，也不受 #app 层级限制。
 */
export function printTravelApplication(p: TravelReq) {
  const html = `<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>差旅申请单</title>
<style>
@page { size: A4; margin: 8mm 12mm; }
body { font-family: 'PingFang SC','Microsoft YaHei',sans-serif; padding:0; margin:0; }
.travel-form { width:210mm; min-height:297mm; margin:0 auto; padding:6mm 12mm; box-sizing:border-box; background:#fff; color:#000; font-size:10pt; }
.form-title { position:relative; text-align:center; border-bottom:2px solid #000; padding-bottom:8px; margin-bottom:12px; }
.company { font-size:15pt; font-weight:bold; letter-spacing:2px; }
.doc-type { font-size:17pt; font-weight:bold; margin-top:3px; }
.unit { position:absolute; right:0; top:0; font-size:9pt; color:#333; }
.section-title { font-weight:bold; margin:12px 0 5px; font-size:10pt; }
table { width:100%; border-collapse:collapse; table-layout:fixed; }
.info-table td, .sign-table td { border:1px solid #333; padding:3px 5px; word-break:break-all; vertical-align:middle; }
.label { background:#f2f2f2; font-weight:600; text-align:center; width:78px; font-size:10pt; }
.bill-no { word-break:break-all; line-height:1.2; text-align:center; font-size:12pt; font-weight:bold; letter-spacing:0.5px; color:#000; font-family:'Courier New',monospace; }
.date-cell { white-space:nowrap; font-size:11pt; text-align:center; }
.num-strong { text-align:right; font-weight:bold; font-family:'Courier New',monospace; font-size:16pt; color:#000; }
.sign-table td { text-align:center; height:28px; }
.sign-row td { height:56px; }
.form-footer { margin-top:12px; font-size:9pt; color:#333; }
@media print { .no-print { display:none; } }
</style></head>
<body>
<div class="travel-form">
  <div class="form-title">
    <div class="company">深圳市流形机器人科技有限公司</div>
    <div class="doc-type">差旅申请单</div>
    <div class="unit">单位：元</div>
  </div>
  <div class="section-title">一、基本信息</div>
  <table class="info-table base-table">
    <tr>
      <td class="label">申请单号</td><td class="bill-no">${p.req_no || '-'}</td>
      <td class="label">申请日期</td><td class="date-cell">${p.submit_date || '-'}</td>
      <td class="label">申请人</td><td>${p.applicant || '-'}</td>
    </tr>
    <tr>
      <td class="label">部门</td><td>${p.department || '-'}</td>
      <td class="label">出差人</td><td>${p.traveler || '-'}</td>
      <td class="label">出差地点</td><td>${p.destination || '-'}</td>
    </tr>
    <tr>
      <td class="label">出差起止</td><td colspan="3">${p.travel_start || '-'} 至 ${p.travel_end || '-'}</td>
      <td class="label">差旅预算</td><td class="num-strong">¥${fmt(p.expected_amount, '0.00')}</td>
    </tr>
    <tr>
      <td class="label">归属研发</td><td colspan="5">${p.is_rd_project || '否'}${p.is_rd_project === '是' && p.rd_project_code ? '（' + p.rd_project_code + '）' : ''}</td>
    </tr>
    <tr><td class="label">出差事由</td><td colspan="5">${p.reason || '-'}</td></tr>
    <tr><td class="label">备注</td><td colspan="5">${p.remark || '-'}</td></tr>
  </table>
  <div class="section-title">二、审批</div>
  <table class="info-table summary-table">
    <tr>
      <td class="label">状态</td><td>${p.status}</td>
      <td class="label">审批人</td><td>${p.approver || '-'}</td>
      <td class="label">审批日期</td><td class="date-cell" colspan="2">${p.approve_date || '-'}</td>
    </tr>
    <tr><td class="label">审批意见</td><td colspan="6">${p.approve_remark || '-'}</td></tr>
  </table>
  <div class="section-title">三、审批签章</div>
  <table class="sign-table">
    <tr><td class="label">申请人</td><td class="label">项目负责人 / 部门负责人</td><td class="label">财务负责人</td><td class="label">总经理</td></tr>
    <tr class="sign-row"><td>${p.applicant || ''}</td><td></td><td></td><td></td></tr>
  </table>
  <div class="form-footer">备注：本单经审批通过后方可出行；费用凭发票报销，差异应在审批意见中说明。</div>
</div>
</body></html>`

  const iframe = document.createElement('iframe')
  iframe.style.cssText = 'position:fixed;top:-9999px;left:-9999px;width:0;height:0;border:none;'
  document.body.appendChild(iframe)
  const doc = iframe.contentWindow!.document
  doc.open()
  doc.write(html)
  doc.close()
  iframe.contentWindow!.focus()
  iframe.contentWindow!.print()
  setTimeout(() => { if (iframe.parentNode) iframe.parentNode.removeChild(iframe) }, 2000)
}
