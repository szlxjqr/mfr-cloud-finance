<template>
  <div class="page">
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索单号/申请人/事由" clearable style="width: 240px" @keyup.enter="load" @clear="load" />
      <el-select v-model="statusFilter" placeholder="全部状态" clearable style="width: 140px" @change="load">
        <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
      </el-select>
      <el-button type="primary" @click="openCreate">新建报销单</el-button>
    </div>

    <el-table :data="list" border stripe v-loading="loading">
      <el-table-column prop="bill_no" label="单号" width="150" />
      <el-table-column prop="applicant" label="申请人" width="100" />
      <el-table-column prop="department" label="部门" width="110" />
      <el-table-column label="发票" width="130" align="center">
        <template #default="{ row }">
          <span v-if="summaryMap[row.id]?.invoice_count">
            {{ summaryMap[row.id].invoice_count }} 张 /
            ¥{{ Number(summaryMap[row.id].total || 0).toFixed(2) }}
          </span>
          <span v-else class="text-muted">未挂票</span>
        </template>
      </el-table-column>
      <el-table-column prop="amount" label="报销金额" width="120" align="right">
        <template #default="{ row }">{{ row.amount != null ? '¥' + Number(row.amount).toFixed(2) : '-' }}</template>
      </el-table-column>
      <el-table-column prop="reason" label="事由" show-overflow-tooltip />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTag(row.status)" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="submit_date" label="提交日期" width="110" />
      <el-table-column prop="approve_date" label="审批日期" width="110" />
      <el-table-column label="操作" width="300" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="success" @click="openLinkInvoices(row)">挂发票</el-button>
          <el-button
            v-for="act in transformActions(row)"
            :key="act.action"
            link
            :type="act.type"
            @click="runAction(act.action, row)"
          >{{ act.label }}</el-button>
          <el-button link type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 报销单新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑报销单' : '新建报销单'" width="640px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="单号" v-if="editing">
          <el-input :model-value="form.bill_no ?? ''" disabled />
        </el-form-item>
        <el-form-item label="申请人">
          <el-input v-model="form.applicant" placeholder="必填" />
        </el-form-item>
        <el-form-item label="部门">
          <el-input v-model="form.department" />
        </el-form-item>
        <el-form-item label="金额">
          <el-input v-model.number="form.amount" type="number" placeholder="0.00" />
        </el-form-item>
        <el-form-item label="事由">
          <el-input v-model="form.reason" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <!-- 挂发票弹窗 -->
    <el-dialog v-model="linkDialogVisible" title="挂发票" width="900px" :close-on-click-modal="false">
      <div v-if="linkingBill" class="link-summary">
        <span>报销单：<strong>{{ linkingBill.bill_no || linkingBill.id }}</strong></span>
        <span>申请人：{{ linkingBill.applicant }}</span>
        <span>当前已挂：{{ summaryMap[linkingBill.id]?.invoice_count || 0 }} 张</span>
      </div>

      <div class="link-toolbar">
        <el-input v-model="invoiceKeyword" placeholder="搜索销方/发票号" clearable style="width: 220px" @input="debounceLoadUnlinked" />
        <span class="text-muted">仅显示未关联报销单的发票</span>
      </div>

      <el-table :data="unlinkedInvoices" border stripe height="360" v-loading="invoiceLoading" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="48" align="center" />
        <el-table-column prop="invoice_date" label="开票日期" width="110" />
        <el-table-column prop="invoice_type" label="类型" width="120" />
        <el-table-column prop="no" label="发票号码" width="120" />
        <el-table-column prop="seller_name" label="销方名称" show-overflow-tooltip />
        <el-table-column label="金额/税额/合计" width="180" align="right">
          <template #default="{ row }">
            ¥{{ row.total_amount?.toFixed(2) || '0.00' }}
            <span class="tax-hint">（税 ¥{{ row.total_tax?.toFixed(2) || '0.00' }}）</span>
          </template>
        </el-table-column>
      </el-table>

      <template #footer>
        <el-button @click="linkDialogVisible = false">取消</el-button>
        <el-button type="primary" :disabled="selectedInvoiceIds.length === 0" @click="confirmLink">关联 {{ selectedInvoiceIds.length }} 张发票</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { reimburseApi } from '@/api/reimburse'
import { invoiceApi } from '@/api/invoice'
import type { ReimbursementBill } from '@/types/reimburse'
import type { Invoice } from '@/types/invoice'

const statusOptions = ['草稿', '待审批', '已通过', '已驳回', '已支付']

const keyword = ref('')
const statusFilter = ref<string | null>(null)
const list = ref<ReimbursementBill[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const editing = ref(false)
const editingId = ref<number | null>(null)

const emptyForm = () => ({
  bill_no: null as string | null,
  applicant: '',
  department: '',
  amount: null as number | null,
  reason: '',
  remark: '',
})
const form = reactive(emptyForm())

// 每个报销单的发票汇总（金额/张数）
interface InvoiceSummary {
  amount: number
  tax: number
  total: number
  invoice_count: number
}
const summaryMap = ref<Record<number, InvoiceSummary>>({})

function statusTag(status: string): '' | 'success' | 'warning' | 'danger' | 'info' | 'primary' {
  switch (status) {
    case '待审批':
      return 'warning'
    case '已通过':
      return 'success'
    case '已驳回':
      return 'danger'
    case '已支付':
      return 'primary'
    default:
      return 'info'
  }
}

interface RowAction {
  action: 'submit' | 'approve' | 'reject' | 'pay'
  label: string
  type: 'warning' | 'success' | 'danger' | 'primary'
}

function transformActions(row: ReimbursementBill): RowAction[] {
  switch (row.status) {
    case '草稿':
    case '已驳回':
      return [{ action: 'submit', label: '提交', type: 'warning' }]
    case '待审批':
      return [
        { action: 'approve', label: '通过', type: 'success' },
        { action: 'reject', label: '驳回', type: 'danger' },
      ]
    case '已通过':
      return [{ action: 'pay', label: '支付', type: 'primary' }]
    default:
      return []
  }
}

async function load() {
  loading.value = true
  try {
    const params: { keyword?: string; status?: string } = {}
    if (keyword.value) params.keyword = keyword.value
    if (statusFilter.value) params.status = statusFilter.value
    const res = await reimburseApi.list(params)
    list.value = res.data
    await loadInvoiceSummaries(res.data)
  } finally {
    loading.value = false
  }
}

async function loadInvoiceSummaries(bills: ReimbursementBill[]) {
  const map: Record<number, InvoiceSummary> = {}
  await Promise.all(
    bills.map(async (bill) => {
      try {
        const res = await invoiceApi.summaryByBill(bill.id)
        map[bill.id] = res.data
      } catch (e) {
        map[bill.id] = { amount: 0, tax: 0, total: 0, invoice_count: 0 }
      }
    })
  )
  summaryMap.value = map
}

function openCreate() {
  Object.assign(form, emptyForm())
  editing.value = false
  editingId.value = null
  dialogVisible.value = true
}
function openEdit(row: ReimbursementBill) {
  Object.assign(form, emptyForm(), row)
  editing.value = true
  editingId.value = row.id
  dialogVisible.value = true
}
async function save() {
  const payload: Record<string, unknown> = { ...form }
  if (payload.amount === '' || payload.amount === null) payload.amount = null
  if (editing.value && editingId.value != null) {
    await reimburseApi.update(editingId.value, payload)
    ElMessage.success('已更新')
  } else {
    await reimburseApi.create(payload)
    ElMessage.success('已创建')
  }
  dialogVisible.value = false
  load()
}
async function runAction(action: RowAction['action'], row: ReimbursementBill) {
  const map = {
    submit: reimburseApi.submit,
    approve: reimburseApi.approve,
    reject: reimburseApi.reject,
    pay: reimburseApi.pay,
  }
  await map[action](row.id)
  ElMessage.success('操作成功')
  load()
}
async function remove(row: ReimbursementBill) {
  await ElMessageBox.confirm(`确认删除报销单 ${row.bill_no ?? row.id}？`, '提示', { type: 'warning' })
  await reimburseApi.remove(row.id)
  ElMessage.success('已删除')
  load()
}

/* ============ 挂发票 ============ */
const linkDialogVisible = ref(false)
const linkingBill = ref<ReimbursementBill | null>(null)
const unlinkedInvoices = ref<(Invoice & { total_amount?: number; total_tax?: number })[]>([])
const invoiceKeyword = ref('')
const invoiceLoading = ref(false)
const selectedInvoiceIds = ref<number[]>([])
let invoiceTimer: ReturnType<typeof setTimeout> | null = null

async function openLinkInvoices(row: ReimbursementBill) {
  linkingBill.value = row
  linkDialogVisible.value = true
  invoiceKeyword.value = ''
  selectedInvoiceIds.value = []
  await nextTick()
  loadUnlinked()
}

function debounceLoadUnlinked() {
  if (invoiceTimer) clearTimeout(invoiceTimer)
  invoiceTimer = setTimeout(() => loadUnlinked(), 300)
}

async function loadUnlinked() {
  invoiceLoading.value = true
  try {
    const params: { keyword?: string; unlinked: boolean } = { unlinked: true }
    if (invoiceKeyword.value.trim()) params.keyword = invoiceKeyword.value.trim()
    const res = await invoiceApi.list(params)
    unlinkedInvoices.value = res.data.map((inv) => {
      const totalAmount = inv.details.reduce((s, d) => s + (d.amount || 0), 0)
      const totalTax = inv.details.reduce((s, d) => s + (d.tax || 0), 0)
      return { ...inv, total_amount: totalAmount, total_tax: totalTax }
    })
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载未关联发票失败')
  } finally {
    invoiceLoading.value = false
  }
}

function handleSelectionChange(rows: Invoice[]) {
  selectedInvoiceIds.value = rows.map((r) => r.id)
}

async function confirmLink() {
  if (!linkingBill.value || selectedInvoiceIds.value.length === 0) return
  try {
    await invoiceApi.batchLink(selectedInvoiceIds.value, linkingBill.value.id)
    ElMessage.success(`已关联 ${selectedInvoiceIds.value.length} 张发票`)
    linkDialogVisible.value = false
    load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '关联发票失败')
  }
}

onMounted(load)
</script>

<style scoped>
.page {
  padding: 16px;
}
.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}
.text-muted {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
.link-summary {
  display: flex;
  gap: 24px;
  margin-bottom: 12px;
  padding: 10px 12px;
  background: #f5f7fa;
  border-radius: 4px;
}
.link-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.tax-hint {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  margin-left: 4px;
}
</style>
