<template>
  <div class="bill-form">
    <div class="form-title">
      <div class="company">深圳市流形机器人科技有限公司</div>
      <div class="doc-type">报销申请单</div>
      <div class="unit">单位：元</div>
    </div>

    <!-- 一、基本信息 -->
    <div class="section-title">一、基本信息</div>
    <table class="info-table base-table">
      <tr>
        <td class="label">报销单号</td>
        <td class="bill-no">{{ p.bill_no || '-' }}</td>
        <td class="label">报销类型</td>
        <td>{{ billType }}</td>
        <td class="label">申请日期</td>
        <td class="date-cell">{{ p.submit_date || '-' }}</td>
      </tr>
      <tr>
        <td class="label">申请人</td>
        <td>{{ p.applicant || '-' }}</td>
        <td class="label">部门</td>
        <td colspan="3">{{ p.department || '-' }}</td>
      </tr>
      <template v-if="billType === '差旅报销'">
        <tr>
          <td class="label">出差人</td>
          <td>{{ p.traveler || '-' }}</td>
          <td class="label">出差地点</td>
          <td colspan="3">{{ p.travel_destination || '-' }}</td>
        </tr>
        <tr>
          <td class="label">出差起止</td>
          <td colspan="5">{{ p.travel_start || '-' }} 至 {{ p.travel_end || '-' }}</td>
        </tr>
      </template>
      <tr v-if="p.purchase_requisition_id">
        <td class="label">来源采购单</td>
        <td colspan="5">采购单 #{{ p.purchase_requisition_id }}</td>
      </tr>
      <tr>
        <td class="label">事由</td>
        <td colspan="5">{{ p.reason || '-' }}</td>
      </tr>
      <tr>
        <td class="label">备注</td>
        <td colspan="5">{{ p.remark || '-' }}</td>
      </tr>
    </table>

    <!-- 二、采购细项 -->
    <template v-if="hasPurchaseRows">
      <div class="section-title">二、采购细项</div>
      <table class="detail-table">
        <thead>
          <tr>
            <th style="width: 40px">编号</th>
            <th>采购内容</th>
            <th style="width: 130px">发票号</th>
            <th style="width: 140px">销售方</th>
            <th style="width: 100px">开票日期</th>
            <th style="width: 110px">发票金额<br><span class="unit-sub">（价税合计）</span></th>
            <th>备注</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in purchaseRows" :key="row.idx">
            <td style="text-align: center">{{ row.idx }}</td>
            <td class="left">{{ row.item.item_name }}</td>
            <td>{{ row.invoiceNos }}</td>
            <td>{{ row.seller }}</td>
            <td class="date-cell">{{ row.invoiceDate }}</td>
            <td class="num">¥{{ row.total.toFixed(2) }}</td>
            <td class="left">{{ row.item.remark || '-' }}</td>
          </tr>
        </tbody>
      </table>
    </template>

    <!-- 三、金额汇总 -->
    <div class="section-title">三、金额汇总</div>
    <table class="info-table base-table">
      <tr>
        <td class="label">发票张数</td>
        <td>{{ summary.invoice_count }} 张</td>
        <td class="label">不含税金额</td>
        <td class="num">¥{{ Number(summary.amount || 0).toFixed(2) }}</td>
        <td class="label">税额</td>
        <td class="num">¥{{ Number(summary.tax || 0).toFixed(2) }}</td>
      </tr>
      <tr>
        <td class="label">预算金额</td>
        <td class="num" colspan="2">¥{{ budgetAmount.toFixed(2) }}</td>
        <td class="label">发票合计</td>
        <td class="num" colspan="2">¥{{ invoiceTotal.toFixed(2) }}</td>
      </tr>
      <tr>
        <td class="label">报销金额</td>
        <td class="num num-strong" colspan="2">¥{{ reimburse.toFixed(2) }}</td>
        <td class="label">金额大写</td>
        <td class="cn-amount" colspan="2">{{ cnAmount }}</td>
      </tr>
    </table>

    <!-- 四、审批与支付 -->
    <div class="section-title">四、审批与支付</div>
    <table class="info-table base-table">
      <tr>
        <td class="label">状态</td>
        <td>{{ p.status || '-' }}</td>
        <td class="label">审批人</td>
        <td>{{ p.approver || '-' }}</td>
        <td class="label">审批日期</td>
        <td class="date-cell">{{ p.approve_date || '-' }}</td>
      </tr>
      <tr>
        <td class="label">审批意见</td>
        <td colspan="5">{{ p.approve_remark || '-' }}</td>
      </tr>
      <tr>
        <td class="label">付款日期</td>
        <td colspan="5">{{ p.pay_date || '-' }}</td>
      </tr>
    </table>

    <!-- 五、签字栏 -->
    <div class="section-title">五、签字栏</div>
    <table class="sign-table">
      <tr>
        <td class="label">申请人</td>
        <td class="label">部门负责人</td>
        <td class="label">财务负责人</td>
        <td class="label">总经理</td>
      </tr>
      <tr class="sign-row">
        <td>{{ p.applicant || '' }}</td>
        <td></td>
        <td></td>
        <td></td>
      </tr>
    </table>

    <div class="form-footer">
      备注：本单经审批通过并付款后入账；金额以实际发票为准，差异应在审批意见中说明。
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ReimbursementBill } from '@/types/reimburse'
import type { PurchaseReq, PurchaseItem } from '@/types/purchase'
import type { Invoice } from '@/types/invoice'

interface InvoiceSummary {
  amount: number
  tax: number
  total: number
  invoice_count: number
}

const props = defineProps<{
  bill: ReimbursementBill
  summary?: InvoiceSummary
  purchase?: PurchaseReq | null
  invoices?: Invoice[]
}>()

const p = computed(() => props.bill)
const summary = computed<InvoiceSummary>(() => props.summary || { amount: 0, tax: 0, total: 0, invoice_count: 0 })

const billType = computed(() => p.value.bill_type || '采购报销')
const budgetAmount = computed(() => Number(p.value.amount != null ? p.value.amount : 0))
const invoiceTotal = computed(() => Number(summary.value.total || 0))
const reimburse = computed(() =>
  p.value.reimburse_amount != null ? Number(p.value.reimburse_amount) : invoiceTotal.value,
)
const cnAmount = computed(() => moneyToChinese(reimburse.value))

interface PurchaseRow {
  idx: number
  item: PurchaseItem
  invoices: Invoice[]
  invoiceNos: string
  seller: string
  invoiceDate: string
  total: number
}

const purchaseRows = computed<PurchaseRow[]>(() => {
  const items = props.purchase?.items || []
  const invoices = props.invoices || []
  return items.map((it, idx) => {
    const matched = invoices.filter((inv) => inv.purchase_requisition_item_id === it.id)
    const total = matched.reduce(
      (s, inv) => s + (inv.details || []).reduce((ds, d) => ds + (Number(d.total) || 0), 0),
      0,
    )
    return {
      idx: idx + 1,
      item: it,
      invoices: matched,
      invoiceNos: matched.map((inv) => inv.no).join(', ') || '-',
      seller: matched.map((inv) => inv.seller_name).join(', ') || '-',
      invoiceDate: matched.map((inv) => inv.invoice_date).filter(Boolean).join(', ') || '-',
      total,
    }
  })
})
const hasPurchaseRows = computed(() => purchaseRows.value.length > 0)

// 金额大写（人民币）
function moneyToChinese(n: number): string {
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
        if (d === 0) {
          zeroInSec = true
        } else {
          if (zeroInSec || (needZero && secStr.length > 0)) secStr += digit[0]
          secStr += digit[d] + unit[unitPos]
          zeroInSec = false
        }
      }
      if (secStr.length > 0) {
        intStr += secStr + secUnit[secPos]
        needZero = zeroInSec
      } else if (needZero) {
        needZero = false
      }
    })
    intStr += '元'
  } else {
    intStr = '零元'
  }
  const jiao = Math.floor(cents / 10)
  const fen = cents % 10
  let decStr = ''
  if (jiao === 0 && fen === 0) {
    if (intPart > 0) decStr = '整'
  } else {
    if (jiao > 0) decStr += digit[jiao] + '角'
    else if (intPart > 0) decStr += digit[0]
    if (fen > 0) decStr += digit[fen] + '分'
  }
  return intStr + decStr
}
</script>

<style scoped>
/* ============ 打印控制 ============ */
@media print {
  @page {
    size: A4;
    margin: 8mm 12mm;
  }
  body {
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  .bill-form {
    padding: 0;
    margin: 0;
    width: auto;
    min-height: auto;
    box-shadow: none;
  }
}

/* ============ 布局样式 ============ */
.bill-form {
  width: 210mm;
  min-height: 297mm;
  margin: 0 auto;
  padding: 6mm 12mm;
  box-sizing: border-box;
  background: #fff;
  color: #000;
  font-size: 10pt;
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.form-title {
  position: relative;
  text-align: center;
  border-bottom: 2px solid #000;
  padding-bottom: 8px;
  margin-bottom: 12px;
}
.company { font-size: 15pt; font-weight: bold; letter-spacing: 2px; }
.doc-type { font-size: 17pt; font-weight: bold; margin-top: 3px; }
.unit { position: absolute; right: 0; top: 0; font-size: 9pt; color: #333; }

.section-title {
  font-weight: bold;
  margin: 12px 0 5px;
  font-size: 10pt;
}

table { width: 100%; border-collapse: collapse; table-layout: fixed; }

.info-table td,
.sign-table td,
.detail-table th,
.detail-table td {
  border: 1px solid #333;
  padding: 3px 5px;
  word-break: break-all;
  vertical-align: middle;
}

.detail-table th {
  background: #f2f2f2;
  font-weight: 600;
  text-align: center;
  font-size: 10pt;
}
.detail-table td { font-size: 11pt; }
.detail-table td.left { text-align: left; }

.label {
  background: #f2f2f2;
  font-weight: 600;
  text-align: center;
  width: 78px;
  font-size: 10pt;
}

.base-table td { font-size: 11pt; }

.bill-no {
  word-break: break-all;
  line-height: 1.2;
  text-align: center;
  font-size: 12pt;
  font-weight: bold;
  letter-spacing: 0.5px;
  color: #000;
  font-family: 'Courier New', monospace;
}

.date-cell { white-space: nowrap; font-size: 11pt; text-align: center; }

.num { text-align: right; font-family: 'Courier New', monospace; font-size: 14pt; font-weight: bold; color: #000; }
.num-strong { text-align: right; font-weight: bold; font-family: 'Courier New', monospace; font-size: 16pt; color: #000; }
.cn-amount { font-size: 14pt; font-weight: bold; color: #000; }
.unit-sub { font-size: 9pt; font-weight: normal; color: #555; }

.sign-table td { text-align: center; height: 28px; }
.sign-row td { height: 56px; }

.form-footer { margin-top: 12px; font-size: 9pt; color: #333; }
</style>
