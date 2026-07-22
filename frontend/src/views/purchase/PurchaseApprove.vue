<template>
  <div class="page">
    <div class="toolbar">
      <el-select v-model="statusFilter" placeholder="审批状态" clearable style="width: 160px" @change="load">
        <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
      </el-select>
      <el-input v-model="keyword" placeholder="搜索单号/申请人/物品/事由" clearable style="width: 260px" @keyup.enter="load" @clear="load" />
      <span class="text-muted">默认显示「待审批」</span>
    </div>

    <el-table :data="list" border stripe v-loading="loading">
      <el-table-column prop="req_no" label="单号" width="160" />
      <el-table-column prop="applicant" label="申请人" width="100" />
      <el-table-column prop="department" label="部门" width="110" />
      <el-table-column prop="item_name" label="采购物品" min-width="140" show-overflow-tooltip />
      <el-table-column prop="quantity" label="数量" width="70" align="center" />
      <el-table-column label="预计金额" width="130" align="right">
        <template #default="{ row }">{{ row.expected_amount != null ? '¥' + Number(row.expected_amount).toFixed(2) : '-' }}</template>
      </el-table-column>
      <el-table-column prop="supplier" label="建议供应商" width="160" show-overflow-tooltip />
      <el-table-column prop="expected_date" label="预计日期" width="120" />
      <el-table-column prop="reason" label="事由" min-width="140" show-overflow-tooltip />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTag(row.status)" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">查看</el-button>
          <el-button
            v-for="act in rowActions(row)"
            :key="act.action"
            link
            :type="act.type"
            @click="runAction(act.action, row)"
          >{{ act.label }}</el-button>
          <span v-if="rowActions(row).length === 0" class="text-muted">—</span>
        </template>
      </el-table-column>
    </el-table>

    <!-- 采购申请单详情弹窗（含打印） -->
    <el-dialog v-model="detailVisible" title="采购申请单" width="900px" :close-on-click-modal="false" class="detail-dialog">
      <PurchasePrint v-if="currentReq" :purchase="currentReq" />
      <template #footer>
        <div class="detail-footer">
          <el-button @click="detailVisible = false">关闭</el-button>
          <el-button type="primary" @click="printPurchase">打印采购申请单</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 审批弹窗 -->
    <el-dialog
      v-model="approveDialogVisible"
      :title="approveAction === 'approve' ? '审批通过' : '驳回采购申请'"
      width="420px"
      :close-on-click-modal="false"
    >
      <el-form ref="approveFormRef" :model="approveForm" :rules="approveRules" label-width="90px">
        <el-form-item label="申请单号">
          <el-input :model-value="approveRow?.req_no ?? approveRow?.id" disabled />
        </el-form-item>
        <el-form-item label="审批人" prop="approver">
          <el-input v-model="approveForm.approver" placeholder="请输入审批人姓名" />
        </el-form-item>
        <el-form-item label="审批意见">
          <el-input v-model="approveForm.remark" type="textarea" :rows="3" placeholder="选填" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="approveDialogVisible = false">取消</el-button>
        <el-button :type="approveAction === 'approve' ? 'success' : 'danger'" @click="submitApprove">
          {{ approveAction === 'approve' ? '确认通过' : '确认驳回' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { purchaseApi } from '@/api/purchase'
import type { PurchaseReq } from '@/types/purchase'
import PurchasePrint from './PurchasePrint.vue'

const statusOptions = ['待审批', '已通过', '已驳回']

const keyword = ref('')
const statusFilter = ref<string | null>('待审批')
const list = ref<PurchaseReq[]>([])
const loading = ref(false)

const approveDialogVisible = ref(false)
const approveAction = ref<'approve' | 'reject' | null>(null)
const approveRow = ref<PurchaseReq | null>(null)
const approveForm = ref({ approver: '', remark: '' })
const approveFormRef = ref<any>(null)
const approveRules = {
  approver: [{ required: true, message: '请输入审批人', trigger: 'blur' }],
}

const detailVisible = ref(false)
const currentReq = ref<PurchaseReq | null>(null)

async function openDetail(row: PurchaseReq) {
  try {
    const res = await purchaseApi.get(row.id)
    currentReq.value = res.data
    detailVisible.value = true
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载详情失败')
  }
}

function printPurchase() {
  const form = document.querySelector('.detail-dialog .purchase-form') as HTMLElement | null
  if (!form) {
    window.print()
    return
  }
  const win = window.open('', '_blank')
  if (!win) {
    window.print()
    return
  }
  const styleTexts = Array.from(document.querySelectorAll('style'))
    .map((s) => s.textContent || '')
    .filter(Boolean)
  const linkHrefs = Array.from(document.querySelectorAll('link[rel="stylesheet"]')).map(
    (l) => (l as HTMLLinkElement).href
  )
  const printCss = `
    @page { size: A4; margin: 12mm; }
    html, body { margin:0; padding:0; background:#fff; }
    .purchase-form {
      width: auto !important;
      min-height: 0 !important;
      margin: 0 !important;
      padding: 0 !important;
      box-shadow: none !important;
      print-color-adjust: exact;
      -webkit-print-color-adjust: exact;
    }
    .form-title, .section-title { break-after: avoid; page-break-after: avoid; }
    .info-table, .sign-table, .detail-table { break-inside: avoid; page-break-inside: avoid; }
  `
  win.document.open()
  win.document.write('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">')
  win.document.write('<title>采购申请单</title>')
  linkHrefs.forEach((h) => win.document.write(`<link rel="stylesheet" href="${h}">`))
  styleTexts.forEach((css) => win.document.write(`<style>${css}</style>`))
  win.document.write(`<style>${printCss}</style>`)
  win.document.write('</head><body>')
  win.document.write(form.outerHTML)
  win.document.write('</body></html>')
  win.document.close()
  let printed = false
  const triggerPrint = () => {
    if (printed) return
    printed = true
    win.focus()
    win.print()
  }
  if (win.document.readyState === 'complete') setTimeout(triggerPrint, 300)
  else {
    win.onload = triggerPrint
    setTimeout(triggerPrint, 600)
  }
}

function statusTag(status: string): '' | 'success' | 'warning' | 'danger' | 'info' | 'primary' {
  switch (status) {
    case '待审批': return 'warning'
    case '已通过': return 'success'
    case '已驳回': return 'danger'
    default: return 'info'
  }
}

interface RowAction {
  action: 'approve' | 'reject'
  label: string
  type: 'success' | 'danger'
}
function rowActions(row: PurchaseReq): RowAction[] {
  if (row.status === '待审批') {
    return [
      { action: 'approve', label: '通过', type: 'success' },
      { action: 'reject', label: '驳回', type: 'danger' },
    ]
  }
  return []
}

async function load() {
  loading.value = true
  try {
    const params: { keyword?: string; status?: string } = {}
    if (keyword.value) params.keyword = keyword.value
    if (statusFilter.value) params.status = statusFilter.value
    const res = await purchaseApi.list(params)
    list.value = res.data
  } finally {
    loading.value = false
  }
}

function runAction(action: RowAction['action'], row: PurchaseReq) {
  approveAction.value = action
  approveRow.value = row
  approveForm.value = { approver: '', remark: '' }
  approveDialogVisible.value = true
}

async function submitApprove() {
  if (!approveFormRef.value) return
  await approveFormRef.value.validate()
  if (!approveRow.value || !approveAction.value) return
  const row = approveRow.value
  const data = { approver: approveForm.value.approver, remark: approveForm.value.remark }
  try {
    if (approveAction.value === 'approve') {
      await purchaseApi.approve(row.id, data)
      ElMessage.success('审批通过')
    } else {
      await purchaseApi.reject(row.id, data)
      ElMessage.success('已驳回')
    }
    approveDialogVisible.value = false
    load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '操作失败')
  }
}

onMounted(load)
</script>

<style scoped>
.page { padding: 16px; }
.toolbar { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.text-muted { color: var(--el-text-color-secondary); font-size: 13px; }
.detail-footer { display: flex; justify-content: flex-end; gap: 12px; }
</style>
