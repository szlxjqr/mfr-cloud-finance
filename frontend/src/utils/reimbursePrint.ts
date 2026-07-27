/**
 * 报销单 / 差旅报销单 统一打印 HTML 生成器
 *
 * 设计原则：弹窗显示 和 打印输出 用同一份 HTML 字符串，
 * 保证老板在屏幕上看到的和打印出来的完全一致。
 *
 * - 纯函数：输入 bill，输出完整 HTML
 * - 自包含：所有 CSS 内联，不依赖外部样式表
 * - A4 尺寸：210mm × 297mm，预留打印边距
 * - 数据安全：fmtMoney 处理 number / string / null；esc 处理 XSS
 */

import type { ReimbursementBill } from '@/types/reimburse'

/** 金额安全格式化：兼容 number / 数字字符串 / null */
export function fmtMoney(v: any, fallback = '-'): string {
  const n = Number(v)
  return Number.isFinite(n) ? n.toFixed(2) : fallback
}

/** HTML 转义 */
export function esc(s: any): string {
  return String(s ?? '').replace(/[&<>"']/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c] as string))
}

/** 数字转人民币大写 */
export function moneyToChinese(n: number): string {
  if (!isFinite(n)) return '-'
  if (n < 0) return '负' + moneyToChinese(-n)
  if (n === 0) return '零元整'
  const intPart = Math.floor(n)
  const cents = Math.round((n - intPart) * 100)
  const digit = ['零', '壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖']
  const unit = ['', '拾', '佰', '仟']
  const secUnit = ['', '万', '亿', '兆']
  let intStr = ''
  if (intPart > 0) {
    const s = String(intPart)
    const secs: string[] = []
    for (let i = s.length; i > 0; i -= 4) secs.unshift(s.slice(Math.max(0, i - 4), i))
    let needZero = false
    secs.forEach((sec, idx) => {
      const secPos = secs.length - 1 - idx
      let secStr = ''
      let zeroInSec = false
      for (let i = 0; i < sec.length; i++) {
        const d = sec.charCodeAt(i) - 48
        const unitPos = sec.length - 1 - i
        if (d === 0) { zeroInSec = true }
        else {
          if (zeroInSec || (needZero && secStr.length > 0)) secStr += digit[0]
          secStr += digit[d] + unit[unitPos]
          zeroInSec = false
        }
      }
      if (secStr.length > 0) { intStr += secStr + secUnit[secPos]; needZero = zeroInSec }
      else if (needZero) { needZero = false }
    })
    intStr += '元'
  } else { intStr = '零元' }
  const jiao = Math.floor(cents / 10)
  const fen = cents % 10
  let decStr = ''
  if (jiao === 0 && fen === 0) { if (intPart > 0) decStr = '整' }
  else {
    if (jiao > 0) decStr += digit[jiao] + '角'
    else if (intPart > 0) decStr += digit[0]
    if (fen > 0) decStr += digit[fen] + '分'
  }
  return intStr + decStr
}

/** 状态中文映射 */
const STATUS_MAP: Record<string, string> = {
  '草稿': '草稿',
  '待审批': '待审批',
  '已通过': '已通过',
  '已驳回': '已驳回',
  '已支付': '已支付',
}

/** 单据类型 → 标题 */
const TITLE_MAP: Record<string, string> = {
  '采购报销': '采购报销单',
  '差旅报销': '差旅报销单',
}

/**
 * 生成报销单 / 差旅报销单 的完整 HTML。
 * 直接被 BillDetail.vue（弹窗显示）和 printDetail（打印输出）共用。
 */
export function buildReimbursePrintHtml(bill: ReimbursementBill): string {
  const isTravel = bill.bill_type === '差旅报销'
  const invoices = bill.invoices || []
  const statusText = STATUS_MAP[bill.status] || bill.status || '-'
  const docTitle = TITLE_MAP[bill.bill_type || ''] || '费用报销单'

  // 发票行：聚合 iv.details 的金额（后端金额字段在 details 子表里）
  // 同时计算整张报销单的发票合计 = 报销金额（不依赖 bill.amount，避免和明细对不上）
  let totalAmount = 0
  let totalTax = 0
  let totalGrand = 0
  const invoiceRows = invoices.length
    ? invoices.map((iv: any, idx: number) => {
        const details: any[] = iv.details || []
        const sumAmount = details.reduce((s: number, d: any) => s + (Number(d.amount) || 0), 0)
        const sumTax = details.reduce((s: number, d: any) => s + (Number(d.tax) || 0), 0)
        const sumTotal = details.reduce((s: number, d: any) => s + (Number(d.total) || 0), 0)
        totalAmount += sumAmount
        totalTax += sumTax
        totalGrand += sumTotal
        return `
        <tr>
          <td style="text-align:center;width:40px">${idx + 1}</td>
          <td class="left">${esc(iv.no || '-')}</td>
          <td class="left">${esc(iv.seller_name || '-')}</td>
          <td class="left">${esc(iv.invoice_date || '-')}</td>
          <td class="num invoice-total">${fmtMoney(sumTotal, '0.00')}</td>
        </tr>`
      }).join('')
    : `<tr><td colspan="5" style="text-align:center;color:#999;padding:20px">暂无关联发票</td></tr>`

  // 报销金额 = 发票合计（实际给员工的钱，不依赖 bill.amount 字段）
  // bill.amount 是从采购单预算/手动输入的旧值，挂接发票后未联动更新，所以用发票合计更准确
  const amount = invoices.length > 0 ? totalGrand : Number(bill.amount != null ? bill.amount : 0)
  const amountInWords = moneyToChinese(amount)
  // 申请金额（参考列）
  const appliedAmount = Number(bill.amount != null ? bill.amount : 0)

  // 差旅专属：出差信息（差旅报销才显示）
  const travelSection = isTravel ? `
    <div class="section-title">二、出差信息</div>
    <table class="info-table base-table">
      <tr>
        <td class="label">出差人</td><td colspan="2">${esc(bill.traveler || '-')}</td>
        <td class="label">目的地</td><td colspan="2">${esc(bill.travel_destination || '-')}</td>
      </tr>
      <tr>
        <td class="label">出发日期</td><td colspan="2">${esc(bill.travel_start || '-')}</td>
        <td class="label">返回日期</td><td colspan="2">${esc(bill.travel_end || '-')}</td>
      </tr>
    </table>
  ` : ''

  // 发票表序号（差旅：二 之后接三；非差旅：紧接二）
  const invoiceSectionIndex = isTravel ? '三' : '二'
  const summarySectionIndex = isTravel ? '四' : '三'
  const signSectionIndex = isTravel ? '五' : '四'

  return `<div class="expense-form">
  <div class="form-title">
    <div class="company">深圳市流形机器人科技有限公司</div>
    <div class="doc-type">${esc(docTitle)}</div>
    <div class="unit">单位：元</div>
  </div>

  <div class="section-title">一、基本信息</div>
  <table class="info-table base-table">
    <tr>
      <td class="label">报销单号</td><td class="bill-no">${esc(bill.bill_no || '-')}</td>
      <td class="label">报销类型</td><td>${esc(bill.bill_type || '采购报销')}</td>
      <td class="label">状态</td><td>${esc(statusText)}</td>
    </tr>
    <tr>
      <td class="label">申请人</td><td>${esc(bill.applicant || '-')}</td>
      <td class="label">部门</td><td>${esc(bill.department || '-')}</td>
      <td class="label">申请日期</td><td class="date-cell">${esc(bill.submit_date || '-')}</td>
    </tr>
    <tr>
      <td class="label">报销事由</td><td colspan="5">${esc(bill.reason || '-')}</td>
    </tr>
    <tr>
      <td class="label">备注</td><td colspan="5">${esc(bill.remark || '-')}</td>
    </tr>
  </table>

  ${travelSection}

  <div class="section-title">${invoiceSectionIndex}、关联发票（${invoices.length} 张）</div>
  <table class="detail-table">
    <thead><tr>
      <th style="width:40px">序号</th><th>发票号</th><th>销售方</th>
      <th style="width:100px">开票日期</th>
      <th style="width:120px">报销金额</th>
    </tr></thead>
    <tbody>${invoiceRows}</tbody>
  </table>

  <div class="section-title">${summarySectionIndex}、汇总与审批</div>
  <table class="info-table summary-table">
    <tr>
      <td class="label">报销单合计</td>
      <td class="num-strong" colspan="2">¥${fmtMoney(amount, '0.00')}</td>
      <td class="label">金额大写</td>
      <td colspan="3" class="cn-amount">${esc(amountInWords)}</td>
    </tr>
    <tr>
      <td class="label">申请金额<br><span class="unit-sub">（参考）</span></td>
      <td class="num" colspan="2">¥${fmtMoney(appliedAmount, '0.00')}</td>
      <td class="label">发票张数</td>
      <td colspan="3" class="cn-amount">${invoices.length} 张（含税额 ¥${fmtMoney(totalTax, '0.00')}）</td>
    </tr>
    <tr>
      <td class="label">审批人</td><td>${esc(bill.approver || '-')}</td>
      <td class="label">审批日期</td><td class="date-cell">${esc(bill.approve_date || '-')}</td>
      <td class="label">付款日期</td><td class="date-cell">${esc(bill.pay_date || '-')}</td>
      <td></td>
    </tr>
    <tr>
      <td class="label">审批意见</td><td colspan="6">${esc(bill.approve_remark || '-')}</td>
    </tr>
  </table>

  <div class="section-title">${signSectionIndex}、审批签章</div>
  <table class="sign-table">
    <tr>
      <td class="label">申请人</td>
      <td class="label">${esc(isTravel ? '项目负责人' : '部门负责人')}</td>
      <td class="label">财务负责人</td>
      <td class="label">总经理</td>
    </tr>
    <tr class="sign-row">
      <td>${esc(bill.applicant || '')}</td><td></td><td></td><td></td>
    </tr>
  </table>

  <div class="form-footer">备注：本单经审批通过后由财务统一支付；报销金额以实际审核通过为准。</div>
</div>`
}

/** 完整的打印 HTML 文档（包含 head/style），用于 iframe 打印 */
export function buildReimbursePrintDocument(bill: ReimbursementBill, title: string): string {
  return `<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>${esc(title)}</title>
<style>
@page { size: A4; margin: 8mm 12mm; }
body { font-family: 'PingFang SC','Microsoft YaHei',sans-serif; padding:0; margin:0; color:#000; }
.expense-form { width:210mm; min-height:297mm; margin:0 auto; padding:6mm 12mm; box-sizing:border-box; background:#fff; font-size:9pt; }
.form-title { position:relative; text-align:center; border-bottom:2px solid #000; padding-bottom:8px; margin-bottom:12px; }
.company { font-size:15pt; font-weight:bold; letter-spacing:2px; }
.doc-type { font-size:17pt; font-weight:bold; margin-top:3px; }
.unit { position:absolute; right:0; top:0; font-size:9pt; color:#333; }
.section-title { font-weight:bold; margin:12px 0 5px; font-size:10pt; }
table { width:100%; border-collapse:collapse; table-layout:fixed; }
.info-table td, .detail-table th, .detail-table td, .sign-table td { border:1px solid #333; padding:3px 5px; word-break:break-all; vertical-align:middle; }
.label { background:#f2f2f2; font-weight:600; text-align:center; width:78px; font-size:8.5pt; }
.detail-table th { background:#f2f2f2; font-weight:600; text-align:center; font-size:8pt; }
.detail-table td { font-size:8pt; }
.left { text-align:left; }
.num { text-align:right; font-family:'Courier New',monospace; color:#000; font-weight:600; }
.num-strong { text-align:right; font-weight:bold; font-family:'Courier New',monospace; font-size:9pt; color:#000; }
.cn-amount { font-size:9pt; font-weight:600; color:#000; }
.sign-table td { text-align:center; height:28px; }
.sign-row td { height:56px; }
.bill-no { word-break:break-all; text-align:center; font-family:'Courier New',monospace; font-size:11pt; font-weight:600; }
.date-cell { white-space:nowrap; text-align:center; font-size:8pt; }
.invoice-total { text-align:right; font-family:'Courier New',monospace; color:#000; font-weight:bold; font-size:10pt; }
.form-footer { margin-top:12px; font-size:9pt; color:#333; }
</style></head>
<body>${buildReimbursePrintHtml(bill)}</body></html>`
}
