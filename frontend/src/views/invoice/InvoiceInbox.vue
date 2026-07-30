<template>
  <div class="inbox">
    <div class="toolbar">
      <el-button type="primary" :loading="uploading" @click="uploadDialogVisible = true">批量上传并识别</el-button>
      <el-input
        v-model="keyword"
        placeholder="搜索文件名/销售方/税号"
        clearable
        style="width: 240px"
        @clear="load"
        @keyup.enter="load"
      />
      <el-select v-model="statusFilter" placeholder="全部状态" clearable style="width: 130px" @change="load">
        <el-option label="待识别" value="pending" />
        <el-option label="已识别" value="recognized" />
        <el-option label="已复核" value="reviewed" />
        <el-option label="待复核" value="needs_review" />
        <el-option label="已拒绝" value="rejected" />
        <el-option label="已挂接" value="linked" />
      </el-select>
      <el-button @click="load">刷新</el-button>
    </div>

    <!-- 拖拽上传已由统一 UploadToInboxDialog 组件接管 -->

    <BatchActionBar :selected-count="selectedRows.length" @clear="clearSelection">
      <el-button type="danger" plain size="small" :disabled="!selectedRows.length" @click="batchRemove">批量删除</el-button>
    </BatchActionBar>

    <DataLoader :loading="loading" :is-empty="!rows.length" :empty-description="'发票箱为空，拖拽或上传发票开始'">
      <el-table ref="tableRef" :data="rows" stripe border @selection-change="onSelectionChange">
      <el-table-column prop="filename" label="文件名" min-width="160" />
      <el-table-column label="提取摘要" min-width="200">
        <template #default="{ row }">
          <span v-if="row.extracted_json">{{ summary(row) }}</span>
          <span v-else class="muted">（未识别）</span>
        </template>
      </el-table-column>
      <el-table-column type="selection" width="42" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <StatusTag :status="row.status" :label="row.status === 'rejected' ? '已拒绝' : undefined" />
        </template>
      </el-table-column>
      <el-table-column label="查验" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.verify_result && row.verify_result !== 'none'" :type="verifyTag(row.verify_result)" size="small">
            {{ verifyText(row.verify_result) }}
          </el-tag>
          <span v-else class="muted">—</span>
        </template>
      </el-table-column>
      <el-table-column label="挂接" min-width="120">
        <template #default="{ row }">
          <span v-if="row.linked_doc_type === 'reimburse'">报销单 #{{ row.linked_doc_id }}</span>
          <span v-else-if="row.linked_doc_type === 'purchase'">采购申请 #{{ row.linked_doc_id }}</span>
          <span v-else class="muted">—</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="240" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openLink(row)" :disabled="row.status === 'linked' || row.status === 'needs_review' || row.status === 'rejected'">挂接</el-button>
          <el-button v-if="row.status === 'needs_review' || row.status === 'reviewed'" size="small" :type="row.status === 'needs_review' ? 'warning' : 'info'" @click="openReview(row)">{{ row.status === 'needs_review' ? '复核' : '查看' }}</el-button>
          <el-button size="small" @click="openVerify(row)" :disabled="!row.extracted_json">查验</el-button>
          <el-button size="small" type="danger" plain @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    </DataLoader>

    <!-- 挂接对话框 -->
    <el-dialog v-model="linkVisible" title="挂接到业务单" width="420px">
      <el-form label-width="90px">
        <el-form-item label="业务单类型">
          <el-radio-group v-model="linkForm.docType">
            <el-radio value="reimburse">报销单</el-radio>
            <el-radio value="purchase">采购申请</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item :label="linkForm.docType === 'reimburse' ? '报销单 ID' : '采购申请 ID'">
          <el-input-number v-model="linkForm.docId" :min="1" :controls="true" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="linkVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmLink">确认挂接</el-button>
      </template>
    </el-dialog>

    <!-- 查验对话框 -->
    <el-dialog v-model="verifyVisible" title="发票查验（跳税务局平台人工核对）" width="420px">
      <el-alert type="info" :closable="false" style="margin-bottom: 12px">
        系统对接税务局查验 API 为 P1 后续；本期请在
        <a href="https://inv-veri.chinatax.gov.cn" target="_blank" rel="noopener">全国增值税发票查验平台</a>
        按 发票号码 / 税号 / 金额 / 日期 核对后，回填结果。
      </el-alert>
      <el-form label-width="90px">
        <el-form-item label="结果">
          <el-radio-group v-model="verifyForm.result">
            <el-radio value="real">真</el-radio>
            <el-radio value="fake">假</el-radio>
            <el-radio value="abnormal">异常</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="verifyForm.note" type="textarea" :rows="2" placeholder="可填查验时间/平台单号" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="verifyVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmVerify">记录结果</el-button>
      </template>
    </el-dialog>

    <!-- 统一上传弹窗 -->
    <UploadToInboxDialog v-model="uploadDialogVisible" @saved="onUploadInboxSaved" />

    <!-- 复核弹窗（编辑已有 needs_review 记录，修正后 → update 解除隔离） -->
    <InvoiceRecognizeDialog
      :visible="reviewVisible"
      :edit-id="reviewId"
      :initial-parsed="reviewParsed"
      @update:visible="reviewVisible = $event"
      @saved="onReviewSaved"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import UploadToInboxDialog from '@/components/UploadToInboxDialog.vue'
import InvoiceRecognizeDialog from '@/components/InvoiceRecognizeDialog.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { inboxApi } from '@/api/inboxApi'
import type { ParsedInvoice } from '@/utils/invoiceParser'
import type { InvoiceInbox } from '@/types/invoice'

const rows = ref<InvoiceInbox[]>([])
const loading = ref(false)
const uploading = ref(false)
const uploadDialogVisible = ref(false)
const keyword = ref('')
const statusFilter = ref<string | undefined>(undefined)
// dragover 现已由统一上传组件接管

const tableRef = ref()
const selectedRows = ref<InvoiceInbox[]>([])

const linkVisible = ref(false)
const linkForm = reactive({ id: 0, docType: 'reimburse', docId: 1 })
const verifyVisible = ref(false)
const verifyForm = reactive({ id: 0, result: 'real', note: '' })

async function load() {
  loading.value = true
  try {
    const res = await inboxApi.list({ status: statusFilter.value, keyword: keyword.value || undefined })
    rows.value = res.data
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载发票箱失败')
  } finally {
    loading.value = false
  }
}

function summary(row: InvoiceInbox): string {
  if (!row.extracted_json) return '—'
  try {
    const p = JSON.parse(row.extracted_json) as ParsedInvoice
    const parts: string[] = []
    if (p.sellerName) parts.push(p.sellerName)
    if (p.total) parts.push('¥' + p.total)
    return parts.join('  ')
  } catch {
    return '—'
  }
}

function onSelectionChange(rows: any[]) {
  selectedRows.value = rows
}
function clearSelection() {
  tableRef.value?.clearSelection()
}
async function batchRemove() {
  const list = selectedRows.value
  if (!list.length) return
  try {
    await ElMessageBox.confirm(`确认批量删除 ${list.length} 张发票？原文件一并移除。`, '删除确认', { type: 'warning' })
  } catch {
    return
  }
  let ok = 0
  for (const row of list) {
    try {
      await inboxApi.remove(row.id)
      ok++
    } catch (e: any) {
      ElMessage.error((e?.response?.data?.detail || '删除失败') + '：' + row.filename)
    }
  }
  if (ok) ElMessage.success(`已删除 ${ok} 张`)
  load()
}
function verifyText(s: string): string {
  return { real: '真', fake: '假', abnormal: '异常' }[s] || s
}
function verifyTag(s: string): 'success' | 'danger' | 'warning' {
  return ({ real: 'success', fake: 'danger', abnormal: 'warning' }[s] || 'info') as 'success' | 'danger' | 'warning'
}

function onUploadInboxSaved() {
  load()
  ElMessage.success('文件已存入发票池')
}

// 复核（手工录入/修正 needs_review 记录）：打开编辑弹窗，修正后 update 解除隔离
const reviewVisible = ref(false)
const reviewId = ref<number | null>(null)
const reviewParsed = ref<ParsedInvoice | null>(null)
function openReview(row: InvoiceInbox) {
  if (!row.extracted_json) {
    ElMessage.warning('该记录无识别数据，无法复核')
    return
  }
  try {
    reviewParsed.value = JSON.parse(row.extracted_json) as ParsedInvoice
  } catch {
    ElMessage.error('识别数据损坏，无法解析')
    return
  }
  reviewId.value = row.id
  reviewVisible.value = true
}
function onReviewSaved() {
  reviewVisible.value = false
  reviewId.value = null
  reviewParsed.value = null
  load()
  ElMessage.success('已复核并更新发票')
}

function openLink(row: InvoiceInbox) {
  linkForm.id = row.id
  linkForm.docType = 'reimburse'
  linkForm.docId = 1
  linkVisible.value = true
}
async function confirmLink() {
  if (!linkForm.docId) {
    ElMessage.warning('请输入业务单 ID')
    return
  }
  try {
    await inboxApi.link(linkForm.id, linkForm.docType, linkForm.docId)
    ElMessage.success('已挂接并生成正式发票')
    linkVisible.value = false
    load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '挂接失败')
  }
}

function openVerify(row: InvoiceInbox) {
  verifyForm.id = row.id
  verifyForm.result = 'real'
  verifyForm.note = ''
  verifyVisible.value = true
}
async function confirmVerify() {
  try {
    await inboxApi.verify(verifyForm.id, verifyForm.result, verifyForm.note || undefined)
    ElMessage.success('已记录查验结果')
    verifyVisible.value = false
    load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '记录失败')
  }
}

async function remove(row: InvoiceInbox) {
  try {
    await ElMessageBox.confirm(`确认删除「${row.filename}」？原文件一并移除。`, '删除确认', {
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await inboxApi.remove(row.id)
    ElMessage.success('已删除')
    load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}

onMounted(load)
</script>

<style scoped>
.inbox { padding: 16px; }
.toolbar { display: flex; gap: 12px; align-items: center; margin-bottom: 12px; flex-wrap: wrap; }
.dropzone {
  border: 2px dashed var(--border-soft); border-radius: 8px; padding: 28px;
  text-align: center; color: var(--text-muted); margin-bottom: 16px; transition: .2s;
}
.dropzone.dragover { border-color: var(--el-color-primary); color: var(--el-color-primary); background: var(--el-color-primary-light-9); }
.muted { color: var(--border-soft); }
</style>
