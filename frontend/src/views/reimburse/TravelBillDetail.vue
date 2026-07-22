<template>
  <div class="expense-form" ref="formRef">
    <div class="form-title">
      <div class="company">深圳市流形机器人科技有限公司</div>
      <div class="doc-type">差旅报销单</div>
      <div class="unit">单位：元</div>
    </div>

    <!-- 一、基本信息 -->
    <div class="section-title">一、基本信息</div>
    <table class="info-table base-table">
      <tr>
        <td class="label">报销单号</td>
        <td class="bill-no">{{ bill.bill_no || '-' }}</td>
        <td class="label">申请日期</td>
        <td class="date-cell">{{ bill.submit_date || '-' }}</td>
        <td class="label">报销人</td>
        <td>{{ bill.applicant || '-' }}</td>
      </tr>
      <tr>
        <td class="label">部门</td>
        <td>{{ bill.department || '-' }}</td>
        <td class="label">出差人</td>
        <td>{{ bill.traveler || bill.applicant || '-' }}</td>
        <td class="label">报销类型</td>
        <td>差旅报销</td>
      </tr>
      <tr>
        <td class="label">出差地点</td>
        <td colspan="3">{{ bill.travel_destination || '-' }}</td>
        <td class="label">出差天数</td>
        <td>{{ travelDays > 0 ? travelDays + ' 天' : '-' }}</td>
      </tr>
      <tr>
        <td class="label">出差起止</td>
        <td colspan="5" class="date-cell">{{ travelRangeText }}</td>
      </tr>
    </table>

    <!-- 二、报销事由 -->
    <div class="section-title">二、报销事由</div>
    <table class="info-table">
      <tr>
        <td class="label">事由说明</td>
        <td colspan="7">{{ bill.reason || '-' }}</td>
      </tr>
      <tr>
        <td class="label">备注</td>
        <td colspan="7">{{ bill.remark || '-' }}</td>
      </tr>
    </table>

    <!-- 三、差旅费用明细（发票卡片，同采购报销单） -->
    <div class="section-title">三、差旅费用明细</div>
    <div class="invoice-cards">
      <div class="invoice-box" v-for="inv in invoiceRows" :key="inv.id">
        <div class="ib-stripe">
          <span class="ib-stripe-text" :class="{ long: (inv.invoice_type || '').length > 2 }">{{ inv.invoice_type }}</span>
        </div>
        <div class="ib-main">
          <div class="ib-head">
            <span class="ib-code" :title="inv.invoice_no || ''">{{ inv.invoice_no || '-' }}</span>
            <span class="ib-date">{{ inv.invoice_date || '日期不详' }}</span>
          </div>
          <div class="ib-seller" :title="inv.seller_name">{{ inv.seller_name }}</div>
          <div class="ib-item" :title="inv.items">内容：{{ inv.items }}</div>
          <div class="ib-trip" v-if="inv.trip" :title="inv.trip">{{ inv.trip }}</div>
          <div class="ib-stats">
            <div class="ib-stat"><span class="l">数量</span><span class="v">{{ inv.qty }}</span></div>
            <div class="ib-stat"><span class="l">不含税</span><span class="v">¥{{ inv.amount.toFixed(2) }}</span></div>
            <div class="ib-stat"><span class="l">税率</span><span class="v">{{ inv.tax_rate }}</span></div>
            <div class="ib-stat"><span class="l">进项税</span><span class="v">¥{{ inv.tax.toFixed(2) }}</span></div>
          </div>
        </div>
        <div class="ib-stub">
          <div class="l">价税合计</div>
          <div class="amt">¥{{ inv.total.toFixed(2) }}</div>
        </div>
      </div>
      <div v-if="!invoiceRows.length" class="empty">暂无差旅发票明细</div>
    </div>
    <div class="trip-note" v-if="invoiceRows.length">
      注：火车票 / 机票按（票价 + 燃油附加费）×9% 计算进项税；民航发展基金不计入计税基数。
    </div>

    <!-- 四、汇总与付款 -->
    <div class="section-title">四、汇总与付款</div>
    <table class="info-table summary-table">
      <tr>
        <td class="label">报销金额<br><span class="unit-sub">（元）</span></td>
        <td class="num-strong" colspan="2">¥{{ totalWithTax.toFixed(2) }}</td>
        <td class="label">支付金额<br><span class="unit-sub">（元）</span></td>
        <td class="num-strong" colspan="2">¥{{ totalWithTax.toFixed(2) }}</td>
        <td class="label">状态提示</td>
        <td>{{ bill.status }}</td>
      </tr>
      <tr>
        <td class="label">审批人</td>
        <td>{{ bill.approver || '-' }}</td>
        <td class="label">审批日期</td>
        <td class="date-cell" colspan="2">{{ bill.approve_date || '-' }}</td>
        <td class="label">审批意见</td>
        <td colspan="2">{{ bill.approve_remark || '-' }}</td>
      </tr>
    </table>

    <!-- 五、审批签章 -->
    <div class="section-title">五、审批签章</div>
    <table class="sign-table">
      <tr>
        <td class="label">报销人</td>
        <td class="label">项目负责人/部门负责人</td>
        <td class="label">财务负责人</td>
        <td class="label">总经理</td>
      </tr>
      <tr class="sign-row">
        <td></td>
        <td></td>
        <td></td>
        <td></td>
      </tr>
    </table>

    <div class="form-footer">
      备注：出差期间与出差事由无关的费用、超标准住宿费，应在审批意见中说明。
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ReimbursementBill } from '@/types/reimburse'
import type { Invoice, InvoiceDetail } from '@/types/invoice'

const props = defineProps<{
  bill: ReimbursementBill
}>()

interface InvoiceRow {
  id: number
  invoice_date?: string | null
  invoice_no?: string | null
  invoice_type: string
  seller_name: string
  items: string
  qty: number
  amount: number
  tax_rate: string
  tax: number
  total: number
  trip?: string
}

function toNum(v: any): number {
  const n = Number(v)
  return isNaN(n) ? 0 : n
}

// 发票类型缩写（如火车票/登机牌上的简短标识）
function abbrevInvoiceType(type?: string | null): string {
  if (!type) return '发票'
  const t = String(type).trim()
  if (t.includes('电子') && t.includes('专用')) return '电子专票'
  if (t.includes('电子') && t.includes('普通')) return '电子普票'
  if (t.includes('专用')) return '专票'
  if (t.includes('普通')) return '普票'
  if (t.includes('电子')) return '电票'
  if (t.includes('火车') || t.includes('铁路')) return '火车票'
  if (t.includes('机票') || t.includes('航空')) return '机票'
  if (t.includes('机动车')) return '机动车'
  if (t.includes('卷票')) return '卷票'
  return t.length > 4 ? t.slice(0, 4) : t
}

// 解析路线：出发地 → 到达地（兼容 → / -> / 至 / ~ / - / —）
function parseRoute(route?: string | null): { from: string; to: string } {
  const r = (route || '').trim()
  if (!r) return { from: '-', to: '-' }
  const seps = ['→', '->', '至', '—', '~', '-']
  for (const s of seps) {
    if (r.includes(s)) {
      const [a, b] = r.split(s).map((x) => x.trim())
      if (a && b) return { from: a, to: b }
    }
  }
  return { from: r, to: '-' }
}

// 按发票聚合：一行一发票（卡片模式，同采购报销单）
const invoiceRows = computed<InvoiceRow[]>(() => {
  const rows: InvoiceRow[] = []
  ;(props.bill.invoices || []).forEach((inv: Invoice) => {
    const details = inv.details || []
    let qty = 0
    let amount = 0
    let tax = 0
    let total = 0
    const itemSet = new Set<string>()
    details.forEach((d: InvoiceDetail) => {
      qty += toNum(d.qty)
      amount += toNum(d.amount)
      tax += toNum(d.tax)
      total += toNum(d.total)
      if (d.item) itemSet.add(String(d.item).trim())
    })
    let itemsText = '-'
    if (itemSet.size) {
      const arr = Array.from(itemSet)
      itemsText = arr.length > 3 ? arr.slice(0, 3).join('、') + '等' : arr.join('、')
    }
    const rate = amount > 0 ? Math.round((tax / amount) * 100) : 0
    // 行程 + 旅客
    const route = parseRoute(inv.route_info)
    const tripParts: string[] = []
    if (route.from !== '-' || route.to !== '-') {
      tripParts.push(`行程：${route.from}→${route.to}`)
    }
    const traveler = inv.traveler || props.bill.traveler
    if (traveler) tripParts.push(`旅客：${traveler}`)
    rows.push({
      id: inv.id,
      invoice_date: inv.invoice_date,
      invoice_no: inv.no,
      invoice_type: abbrevInvoiceType(inv.invoice_type),
      seller_name: inv.seller_name,
      items: itemsText,
      qty,
      amount,
      tax_rate: rate + '%',
      tax,
      total,
      trip: tripParts.join(' · ') || undefined,
    })
  })
  return rows
})

const totalWithTax = computed(() => invoiceRows.value.reduce((s, it) => s + it.total, 0))

// 出差天数（含首尾）
const travelDays = computed(() => {
  const s = props.bill.travel_start
  const e = props.bill.travel_end
  if (!s || !e) return 0
  const d1 = new Date(s).getTime()
  const d2 = new Date(e).getTime()
  if (isNaN(d1) || isNaN(d2)) return 0
  const days = Math.floor((d2 - d1) / 86400000) + 1
  return days > 0 ? days : 0
})

const travelRangeText = computed(() => {
  const s = props.bill.travel_start
  const e = props.bill.travel_end
  if (s && e) return `${s} 至 ${e}`
  return s || e || '-'
})
</script>

<style scoped>
.expense-form {
  width: 210mm;
  min-height: 297mm;
  margin: 0 auto;
  padding: 14mm 16mm;
  box-sizing: border-box;
  background: #fff;
  color: #000;
  font-size: 9pt;
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.form-title {
  position: relative;
  text-align: center;
  border-bottom: 2px solid #000;
  padding-bottom: 8px;
  margin-bottom: 12px;
}
.company {
  font-size: 15pt;
  font-weight: bold;
  letter-spacing: 2px;
}
.doc-type {
  font-size: 17pt;
  font-weight: bold;
  margin-top: 3px;
}
.unit {
  position: absolute;
  right: 0;
  top: 0;
  font-size: 9pt;
  color: #333;
}

.section-title {
  font-weight: bold;
  margin: 12px 0 5px;
  font-size: 10pt;
}

table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.info-table td,
.sign-table td {
  border: 1px solid #333;
  padding: 3px 5px;
  word-break: break-all;
  vertical-align: middle;
}

.label {
  background: #f2f2f2;
  font-weight: 600;
  text-align: center;
  width: 78px;
  font-size: 8.5pt;
}
.label .unit-sub {
  font-size: 7pt;
  font-weight: normal;
  color: #555;
}

.base-table td {
  font-size: 9pt;
}

.bill-no {
  word-break: break-all;
  line-height: 1.2;
  text-align: center;
  font-size: 8.5pt;
  font-family: 'Courier New', monospace;
}

.date-cell {
  white-space: nowrap;
  font-size: 8pt;
  text-align: center;
}

.summary-table .num-strong {
  font-size: 9pt;
}

/* 发票卡片（黑白灰度打印友好，同采购报销单） */
.invoice-cards {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.invoice-box {
  width: calc(50% - 4px);
  display: flex;
  border: 1px solid #999;
  border-radius: 6px;
  box-sizing: border-box;
  break-inside: avoid;
  background: #fff;
  overflow: hidden;
}

/* 左侧类型带：浅灰底 + 黑字 */
.ib-stripe {
  flex: 0 0 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e6e6e6;
  border-right: 1px solid #999;
}
.ib-stripe-text {
  writing-mode: vertical-rl;
  text-orientation: upright;
  color: #000;
  font-size: 12pt;
  font-weight: 700;
  letter-spacing: 2px;
  line-height: 1;
  white-space: nowrap;
}
.ib-stripe-text.long {
  font-size: 9pt;
  letter-spacing: 1px;
}

.ib-main {
  flex: 1 1 auto;
  min-width: 0;
  padding: 5px 8px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

/* 顶部：发票号码 + 开票日期 左右分置 */
.ib-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 3px;
}
.ib-code {
  flex: 1 1 auto;
  min-width: 0;
  font-family: 'Courier New', monospace;
  font-weight: 700;
  font-size: 8.5pt;
  letter-spacing: 0.3px;
  color: #000;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.ib-date {
  flex: 0 0 auto;
  font-size: 6.5pt;
  color: #555;
  white-space: nowrap;
}

/* 销方 / 内容 */
.ib-seller {
  font-weight: 600;
  font-size: 8.5pt;
  color: #000;
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 1px;
}
.ib-item {
  font-size: 7pt;
  color: #444;
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 1px;
}
/* 行程 / 旅客：差旅专属 */
.ib-trip {
  font-size: 6.5pt;
  color: #1a1a1a;
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 3px;
}

/* 底部统计：4 列紧凑 */
.ib-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 2px 6px;
  border-top: 1px dashed #999;
  padding-top: 4px;
  margin-top: auto;
}
.ib-stat {
  text-align: center;
  min-width: 0;
}
.ib-stat .l {
  display: block;
  font-size: 6pt;
  color: #555;
  letter-spacing: 0.3px;
  line-height: 1.1;
}
.ib-stat .v {
  display: block;
  font-size: 8pt;
  font-weight: 600;
  color: #000;
  font-family: 'Courier New', monospace;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.25;
}

/* 右侧存根区：浅灰底 + 黑字 */
.ib-stub {
  flex: 0 0 23%;
  position: relative;
  border-left: 1px dashed #999;
  padding: 4px 5px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  background: #f2f2f2;
}
.ib-stub .l {
  font-size: 6pt;
  color: #555;
  letter-spacing: 0.5px;
  line-height: 1.1;
}
.ib-stub .amt {
  font-family: 'Courier New', monospace;
  font-weight: 700;
  font-size: 10pt;
  color: #000;
  line-height: 1.15;
  margin: 2px 0;
  white-space: nowrap;
}

.num {
  text-align: right;
  font-family: 'Courier New', monospace;
}
.num-strong {
  text-align: right;
  font-weight: bold;
  font-family: 'Courier New', monospace;
}

.trip-note {
  margin-top: 4px;
  font-size: 7.5pt;
  color: #555;
  line-height: 1.4;
}

.empty {
  text-align: center;
  color: #999;
  padding: 20px;
}

.sign-table td {
  text-align: center;
  height: 28px;
}
.sign-row td {
  height: 56px;
}

.form-footer {
  margin-top: 12px;
  font-size: 9pt;
  color: #333;
}
</style>
