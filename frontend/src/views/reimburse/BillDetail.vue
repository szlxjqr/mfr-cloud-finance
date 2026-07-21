<template>
  <div class="expense-form" ref="formRef">
    <div class="form-title">
      <div class="company">深圳市流形机器人科技有限公司</div>
      <div class="doc-type">物品报销单</div>
      <div class="unit">单位：元</div>
    </div>

    <!-- 一、基本信息 -->
    <div class="section-title">一、基本信息</div>
    <table class="info-table">
      <tr>
        <td class="label">报销单号</td>
        <td>{{ bill.bill_no || '-' }}</td>
        <td class="label">申请日期</td>
        <td>{{ bill.submit_date || '-' }}</td>
        <td class="label">报销人</td>
        <td>{{ bill.applicant || '-' }}</td>
        <td class="label">部门</td>
        <td>{{ bill.department || '-' }}</td>
      </tr>
      <tr>
        <td class="label">成本中心</td>
        <td>{{ bill.department || '-' }}</td>
        <td class="label">项目编号</td>
        <td>-</td>
        <td class="label">项目名称</td>
        <td>-</td>
        <td class="label">报销类型</td>
        <td>物品采购/费用报销</td>
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

    <!-- 三、费用明细（模拟发票票面，方框卡片） -->
    <div class="section-title">三、费用明细</div>
    <div class="invoice-cards">
      <div class="invoice-box" v-for="inv in invoiceRows" :key="inv.id">
        <div class="ib-head">
          <span class="ib-code">{{ inv.invoice_code || '-' }}</span>
          <span class="ib-meta">{{ inv.invoice_type }} · {{ inv.invoice_date || '日期不详' }}</span>
        </div>
        <div class="ib-body">
          <div class="ib-row ib-full"><span class="ib-label">销方</span><span class="ib-val">{{ inv.seller_name }}</span></div>
          <div class="ib-row ib-full"><span class="ib-label">项目</span><span class="ib-val">{{ inv.items }}</span></div>
          <div class="ib-row"><span class="ib-label">数量</span><span class="ib-val num">{{ inv.qty }}</span></div>
          <div class="ib-row"><span class="ib-label">不含税</span><span class="ib-val num">¥{{ inv.amount.toFixed(2) }}</span></div>
          <div class="ib-row"><span class="ib-label">税率</span><span class="ib-val num">{{ inv.tax_rate }}</span></div>
          <div class="ib-row"><span class="ib-label">税金</span><span class="ib-val num">¥{{ inv.tax.toFixed(2) }}</span></div>
          <div class="ib-row ib-full ib-total"><span class="ib-label">价税合计</span><span class="ib-val num">¥{{ inv.total.toFixed(2) }}</span></div>
        </div>
      </div>
      <div v-if="!invoiceRows.length" class="empty">暂无发票明细</div>
    </div>

    <!-- 四、汇总与付款 -->
    <div class="section-title">四、汇总与付款</div>
    <table class="info-table">
      <tr>
        <td class="label">费用合计(元)</td>
        <td class="num-strong">¥{{ totalAmount.toFixed(2) }}</td>
        <td class="label">税金合计(元)</td>
        <td class="num-strong">¥{{ totalTax.toFixed(2) }}</td>
        <td class="label">价税合计(元)</td>
        <td class="num-strong">¥{{ totalWithTax.toFixed(2) }}</td>
        <td class="label">状态提示</td>
        <td>{{ bill.status }}</td>
      </tr>
      <tr>
        <td class="label">审批人</td>
        <td>{{ bill.approver || '-' }}</td>
        <td class="label">审批日期</td>
        <td>{{ bill.approve_date || '-' }}</td>
        <td class="label">审批意见</td>
        <td colspan="3">{{ bill.approve_remark || '-' }}</td>
      </tr>
      <tr>
        <td class="label">应支付(元)</td>
        <td colspan="7" class="num-strong">¥{{ totalWithTax.toFixed(2) }}</td>
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
      备注：票据金额不一致、非业务相关费用混入报销时，应在审批意见中说明。
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
  invoice_code?: string | null
  invoice_type: string
  seller_name: string
  items: string
  qty: number
  amount: number
  tax_rate: string
  tax: number
  total: number
}

function toNum(v: any): number {
  const n = Number(v)
  return isNaN(n) ? 0 : n
}

// 按发票聚合：一行一发票
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
    // 有效税率 = 税金 / 不含税（四舍五入至整数百分比）
    const rate = amount > 0 ? Math.round((tax / amount) * 100) : 0
    rows.push({
      id: inv.id,
      invoice_date: inv.invoice_date,
      invoice_code: inv.invoice_code,
      invoice_type: inv.invoice_type,
      seller_name: inv.seller_name,
      items: itemsText,
      qty,
      amount,
      tax_rate: rate + '%',
      tax,
      total,
    })
  })
  return rows
})

const totalAmount = computed(() => invoiceRows.value.reduce((s, it) => s + it.amount, 0))
const totalTax = computed(() => invoiceRows.value.reduce((s, it) => s + it.tax, 0))
const totalWithTax = computed(() => invoiceRows.value.reduce((s, it) => s + it.total, 0))
</script>

<style scoped>
.expense-form {
  width: 210mm;
  min-height: 297mm;
  margin: 0 auto;
  padding: 16mm;
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
.company {
  font-size: 16pt;
  font-weight: bold;
  letter-spacing: 2px;
}
.doc-type {
  font-size: 18pt;
  font-weight: bold;
  margin-top: 4px;
}
.unit {
  position: absolute;
  right: 0;
  top: 0;
  font-size: 10pt;
  color: #333;
}

.section-title {
  font-weight: bold;
  margin: 14px 0 6px;
  font-size: 11pt;
}

table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.info-table td,
.detail-table th,
.detail-table td,
.sign-table td {
  border: 1px solid #333;
  padding: 4px 6px;
  word-break: break-all;
  vertical-align: middle;
}

.label {
  background: #f2f2f2;
  font-weight: 600;
  text-align: center;
  width: 90px;
}

/* 模拟发票票面：方框卡片两列网格 */
.invoice-cards {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.invoice-box {
  width: calc(50% - 3px);
  border: 1px solid #333;
  box-sizing: border-box;
  break-inside: avoid;
  font-size: 9.5pt;
}

.ib-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 3px 6px;
  border-bottom: 1px solid #333;
  background: #f2f2f2;
}
.ib-code {
  font-weight: 700;
  font-family: 'Courier New', monospace;
}
.ib-meta {
  font-size: 8.5pt;
  color: #333;
}

.ib-body {
  display: grid;
  grid-template-columns: 1fr 1fr;
  column-gap: 10px;
  row-gap: 2px;
  padding: 4px 6px;
}
.ib-row {
  display: flex;
  justify-content: space-between;
  gap: 6px;
}
.ib-full {
  grid-column: 1 / -1;
}
.ib-label {
  color: #555;
  white-space: nowrap;
}
.ib-val {
  font-weight: 500;
  text-align: right;
  word-break: break-all;
}
.ib-val.num {
  font-family: 'Courier New', monospace;
}
.ib-total {
  border-top: 1px dashed #999;
  padding-top: 3px;
  margin-top: 2px;
  font-weight: 700;
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

@media print {
  .expense-form {
    width: 100%;
    padding: 0;
    margin: 0;
  }
}
</style>
