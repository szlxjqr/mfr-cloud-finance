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

    <!-- 三、费用明细（发票明细） -->
    <div class="section-title">三、费用明细</div>
    <table class="detail-table">
      <thead>
        <tr>
          <th style="width: 40px">序号</th>
          <th style="width: 90px">日期</th>
          <th style="width: 130px">发票编码</th>
          <th style="width: 100px">发票类型</th>
          <th>销方名称</th>
          <th style="width: 120px">项目/物品</th>
          <th style="width: 50px">数量</th>
          <th style="width: 90px">不含税金额</th>
          <th style="width: 60px">税率</th>
          <th style="width: 80px">税金</th>
          <th style="width: 90px">价税合计</th>
        </tr>
      </thead>
      <tbody>
        <template v-for="(inv, idx) in flatItems" :key="inv.key">
          <tr>
            <td>{{ idx + 1 }}</td>
            <td>{{ inv.invoice_date || '-' }}</td>
            <td>{{ inv.invoice_code || '-' }}</td>
            <td>{{ inv.invoice_type }}</td>
            <td>{{ inv.seller_name }}</td>
            <td>{{ inv.item || '-' }}</td>
            <td>{{ inv.qty }}</td>
            <td class="num">¥{{ inv.amount.toFixed(2) }}</td>
            <td class="num">{{ (inv.tax_rate * 100).toFixed(0) }}%</td>
            <td class="num">¥{{ inv.tax.toFixed(2) }}</td>
            <td class="num">¥{{ inv.total.toFixed(2) }}</td>
          </tr>
        </template>
        <tr v-if="!flatItems.length">
          <td colspan="11" class="empty">暂无发票明细</td>
        </tr>
      </tbody>
    </table>

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

interface FlatItem {
  key: string
  invoice_date?: string | null
  invoice_code?: string | null
  invoice_type: string
  seller_name: string
  item?: string | null
  qty: number
  amount: number
  tax_rate: number
  tax: number
  total: number
}

function toNum(v: any): number {
  const n = Number(v)
  return isNaN(n) ? 0 : n
}

const flatItems = computed<FlatItem[]>(() => {
  const items: FlatItem[] = []
  ;(props.bill.invoices || []).forEach((inv: Invoice) => {
    if (inv.details && inv.details.length) {
      inv.details.forEach((d: InvoiceDetail, idx: number) => {
        items.push({
          key: `${inv.id}-${d.id || idx}`,
          invoice_date: inv.invoice_date,
          invoice_code: inv.invoice_code,
          invoice_type: inv.invoice_type,
          seller_name: inv.seller_name,
          item: d.item,
          qty: toNum(d.qty),
          amount: toNum(d.amount),
          tax_rate: toNum(d.tax_rate),
          tax: toNum(d.tax),
          total: toNum(d.total),
        })
      })
    } else {
      items.push({
        key: `${inv.id}-head`,
        invoice_date: inv.invoice_date,
        invoice_code: inv.invoice_code,
        invoice_type: inv.invoice_type,
        seller_name: inv.seller_name,
        item: '-',
        qty: 0,
        amount: 0,
        tax_rate: 0,
        tax: 0,
        total: 0,
      })
    }
  })
  return items
})

const totalAmount = computed(() => flatItems.value.reduce((s, it) => s + it.amount, 0))
const totalTax = computed(() => flatItems.value.reduce((s, it) => s + it.tax, 0))
const totalWithTax = computed(() => flatItems.value.reduce((s, it) => s + it.total, 0))
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
  font-size: 10.5pt;
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
  padding: 6px 8px;
  word-break: break-all;
  vertical-align: middle;
}

.label {
  background: #f2f2f2;
  font-weight: 600;
  text-align: center;
  width: 90px;
}

.detail-table th {
  background: #f2f2f2;
  font-weight: 600;
  text-align: center;
}

.detail-table td {
  text-align: center;
}

.detail-table td:nth-child(5),
.detail-table td:nth-child(6) {
  text-align: left;
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
