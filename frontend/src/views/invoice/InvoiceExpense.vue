<script setup lang="ts">
/** 发票 · 费用发票：由进项发票（invoices 表）按「费用类」业务类型筛选。
 * 数据来自 invoiceApi.list（与进项发票同源），仅做视图下钻，零后端改动。
 */
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { invoiceApi } from '@/api/invoice'
import type { Invoice, InvoiceDetail } from '@/types/invoice'

const period = ref<string>('')
const keyword = ref('')
const bizType = ref<string>('费用报销')
const loading = ref(false)
const rows = ref<any[]>([])

const bizTypeOptions = ['费用报销', '接受服务', '采购商品', '采购固定资产', '其他']

function lastDayOfMonth(ym: string): string {
  const [y, m] = ym.split('-').map(Number)
  const d = new Date(y, m, 0)
  return `${y}-${String(m).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function flatten(invoices: Invoice[]): any[] {
  const out: any[] = []
  for (const inv of invoices) {
    const header = {
      id: inv.id,
      no: inv.no,
      type: inv.invoice_type,
      date: inv.invoice_date || '',
      sellerName: inv.seller_name,
      sellerTaxNo: inv.seller_tax_no || '',
      buyerName: inv.buyer_name || '',
      account: inv.account || '',
      certify: (inv.certify as 'current' | 'none') || 'none',
      remark: inv.remark || '',
    }
    const details: InvoiceDetail[] = inv.details && inv.details.length ? inv.details : []
    if (!details.length) {
      out.push({ ...header, bizType: '', item: '', amount: 0, tax: 0, total: 0 })
    } else {
      for (const d of details) {
        out.push({
          ...header,
          bizType: d.biz_type || '',
          item: d.item || '',
          amount: Number(d.amount) || 0,
          tax: Number(d.tax) || 0,
          total: Number(d.total) || 0,
        })
      }
    }
  }
  return out
}

async function load() {
  loading.value = true
  try {
    const params: Record<string, any> = {}
    if (keyword.value.trim()) params.keyword = keyword.value.trim()
    if (period.value) {
      params.start_date = `${period.value}-01`
      params.end_date = lastDayOfMonth(period.value)
    }
    const res = await invoiceApi.list(params)
    rows.value = flatten(res.data)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载费用发票失败')
  } finally {
    loading.value = false
  }
}

onMounted(load)

const filteredRows = computed(() =>
  rows.value.filter((r) => !bizType.value || r.bizType === bizType.value),
)

const totalAmount = computed(() =>
  filteredRows.value.reduce((s, r) => s + (Number(r.amount) || 0), 0),
)
const totalTax = computed(() =>
  filteredRows.value.reduce((s, r) => s + (Number(r.tax) || 0), 0),
)
const total = computed(() =>
  filteredRows.value.reduce((s, r) => s + (Number(r.total) || 0), 0),
)
</script>

<template>
  <div style="padding: 16px;">
    <el-card shadow="never" style="margin-bottom: 12px;">
      <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
        <span style="color: #606266; font-size: 14px;">期间</span>
        <el-input v-model="period" placeholder="如 2026-07" style="width: 140px;" clearable @clear="load" />
        <span style="color: #606266; font-size: 14px;">业务类型</span>
        <el-select v-model="bizType" placeholder="业务类型" style="width: 150px;" @change="() => {}">
          <el-option label="全部" value="" />
          <el-option v-for="b in bizTypeOptions" :key="b" :label="b" :value="b" />
        </el-select>
        <el-input v-model="keyword" placeholder="发票号/销售方" style="width: 180px;" clearable @clear="load" />
        <el-button type="primary" @click="load">查询</el-button>
        <el-tag type="info" style="margin-left: auto;">
          笔数 {{ filteredRows.length }} ｜ 金额 {{ totalAmount.toFixed(2) }} ｜ 税额 {{ totalTax.toFixed(2) }} ｜ 价税合计 {{ total.toFixed(2) }}
        </el-tag>
      </div>
    </el-card>

    <el-table :data="filteredRows" v-loading="loading" border height="560">
      <el-table-column prop="date" label="开票日期" width="120" />
      <el-table-column prop="no" label="发票号码" width="150" />
      <el-table-column prop="type" label="票种" width="140" />
      <el-table-column prop="sellerName" label="销售方" min-width="160" />
      <el-table-column prop="bizType" label="业务类型" width="120" />
      <el-table-column prop="item" label="项目" min-width="140" />
      <el-table-column prop="amount" label="金额" width="120" align="right">
        <template #default="{ row }">{{ Number(row.amount || 0).toFixed(2) }}</template>
      </el-table-column>
      <el-table-column prop="tax" label="税额" width="110" align="right">
        <template #default="{ row }">{{ Number(row.tax || 0).toFixed(2) }}</template>
      </el-table-column>
      <el-table-column prop="total" label="价税合计" width="130" align="right">
        <template #default="{ row }">{{ Number(row.total || 0).toFixed(2) }}</template>
      </el-table-column>
      <el-table-column prop="certify" label="认证" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="row.certify === 'current' ? 'success' : 'info'">
            {{ row.certify === 'current' ? '本期认证' : '暂不认证' }}
          </el-tag>
        </template>
      </el-table-column>
    </el-table>

    <el-alert
      type="info"
      :closable="false"
      show-icon
      style="margin-top: 12px;"
      title="数据说明"
      description="费用发票即进项发票中「费用类」业务（默认按费用报销筛选），数据来自统一的发票库（invoices 表），与进项发票同源。"
    />
  </div>
</template>
