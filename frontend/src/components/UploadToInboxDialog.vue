<template>
  <el-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    title="上传发票自动识别"
    width="820px"
    :close-on-click-modal="false"
    @open="onOpen"
  >
    <!-- 拖拽上传区（原生 input 避免 el-upload multiple 不生效的问题） -->
    <div
      class="native-zone"
      :class="{ dragover }"
      @click="fileInput?.click()"
      @dragover.prevent="dragover = true"
      @dragleave.prevent="dragover = false"
      @drop.prevent="onDrop"
    >
      <input
        ref="fileInput"
        type="file"
        multiple
        accept=".pdf,.ofd,.png,.jpg,.jpeg"
        style="display:none"
        @change="onInputChange"
      />
      <AppIcon name="UploadFilled" class="upload-icon" />
      <div class="upload-text">点击上传或拖拽发票文件到此处</div>
      <div class="upload-tip">支持 PDF / OFD / 图片（最多 20 个文件）</div>
    </div>

    <!-- 已选文件列表 -->
    <div v-if="pendingFiles.length" class="file-list">
      <div class="list-title">已选 {{ pendingFiles.length }} 个文件：</div>
      <div class="file-items">
        <div v-for="(f, i) in pendingFiles" :key="i" class="file-row">
          <span class="file-name">{{ f.name }}</span>
          <span v-if="f.status" class="file-status" :class="f.status">{{ statusLabel(f.status) }}</span>
          <el-button text size="small" type="danger" @click="removeFile(i)" :disabled="f.status === 'parsing'">
            <AppIcon name="Close" />
          </el-button>
        </div>
      </div>
    </div>

    <!-- 批量处理中 -->
    <div v-if="processing" class="processing-bar">
      <AppIcon name="Loading" class="spin" /> 正在识别第 {{ processedCount + 1 }} / {{ pendingFiles.length }} 张发票…
    </div>

    <!-- 识别结果列表 -->
    <div v-if="recognizedInvoices.length" class="results">
      <div class="section-title">OCR 识别结果</div>
      <el-table :data="recognizedInvoices" border stripe size="small" height="260" @row-click="onResultRowClick">
        <el-table-column label="文件" prop="fileName" min-width="140" show-overflow-tooltip />
        <el-table-column label="发票号码" prop="no" width="120" show-overflow-tooltip />
        <el-table-column label="销方名称" prop="sellerName" min-width="120" show-overflow-tooltip />
        <el-table-column label="金额" width="100" align="right">
          <template #default="{ row }">¥{{ formatNum(row.total) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.valid" size="small" type="success">识别成功</el-tag>
            <el-tag v-else size="small" type="danger">解析失败</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <div class="result-tip">点击行可编辑识别字段；识别失败的可手动填写后重试</div>
    </div>

    <!-- 编辑单条识别结果的内嵌面板 -->
    <el-dialog v-model="editVisible" title="编辑识别结果" width="560px" :close-on-click-modal="false" append-to-body>
      <el-form label-width="100px" class="edit-form">
        <el-form-item label="发票类型">
          <el-input v-model="editing.no" disabled />
        </el-form-item>
        <el-form-item label="发票号码">
          <el-input v-model="editing.no" />
        </el-form-item>
        <el-form-item label="开票日期">
          <el-input v-model="editing.date" placeholder="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="销方名称">
          <el-input v-model="editing.sellerName" />
        </el-form-item>
        <el-form-item label="金额(不含税)">
          <el-input-number v-model="editing.amount" :min="0" controls-position="right" style="width:100%" />
        </el-form-item>
        <el-form-item label="税额">
          <el-input-number v-model="editing.tax" :min="0" controls-position="right" style="width:100%" />
        </el-form-item>
        <el-form-item label="价税合计">
          <el-input-number v-model="editing.total" :min="0" controls-position="right" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmEdit">确认</el-button>
      </template>
    </el-dialog>

    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :disabled="!recognizedInvoices.length || processing" :loading="saving" @click="confirmAll">
        全部暂存到发票池（{{ recognizedInvoices.length }} 张）
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { parseInvoiceFile, type ParsedInvoice } from '@/utils/invoiceParser'
import { inboxApi } from '@/api/inboxApi'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
  (e: 'saved'): void
}>()

// ======== 状态 ========
const dragover = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const pendingFiles = ref<{ file: File; name: string; status: string }[]>([])
const processing = ref(false)
const processedCount = ref(0)
const saving = ref(false)

interface RecognizedRow {
  fileName: string
  file: File
  parsed: ParsedInvoice | null
  no: string
  sellerName: string
  amount: number
  tax: number
  total: number
  valid: boolean
}

const recognizedInvoices = ref<RecognizedRow[]>([])

// 编辑状态
const editVisible = ref(false)
const editingIndex = ref(-1)
const editing = ref<Record<string, any>>({})

function formatNum(v: any): string {
  const n = Number(v)
  return isFinite(n) ? n.toFixed(2) : '0.00'
}

function statusLabel(s: string): string {
  const map: Record<string, string> = { pending: '待识别', parsing: '识别中', done: '已识别', fail: '失败' }
  return map[s] || s
}

// ======== 重置 ========
function onOpen() {
  pendingFiles.value = []
  recognizedInvoices.value = []
  processing.value = false
  processedCount.value = 0
  saving.value = false
  editVisible.value = false
}

// ======== 文件处理（原生 input 多选 + 拖拽多选） ========
function addFiles(files: FileList | File[]) {
  const arr = Array.from(files)
  for (const f of arr) {
    if (pendingFiles.value.length >= 20) {
      ElMessage.warning('最多上传 20 个文件')
      break
    }
    const low = f.name.toLowerCase()
    if (!low.match(/\.(pdf|ofd|png|jpg|jpeg)$/)) continue
    // 避免重复添加同名文件
    if (pendingFiles.value.some((pf) => pf.name === f.name)) continue
    pendingFiles.value.push({ file: f, name: f.name, status: 'pending' })
  }
  if (!processing.value && pendingFiles.value.length) startParsing()
}

function onInputChange(e: Event) {
  const files = (e.target as HTMLInputElement).files
  if (!files || !files.length) return
  addFiles(files)
  // 清空 value 以便同一文件重新选取
  ;(e.target as HTMLInputElement).value = ''
}

function onDrop(e: DragEvent) {
  dragover.value = false
  const files = e.dataTransfer?.files
  if (files && files.length) addFiles(files)
}

function removeFile(idx: number) {
  pendingFiles.value.splice(idx, 1)
  const ri = recognizedInvoices.value.findIndex((r) => r.fileName === pendingFiles.value[idx]?.name)
  if (ri >= 0) recognizedInvoices.value.splice(ri, 1)
}

// ======== 批量解析 ========
async function startParsing() {
  if (processing.value) return
  processing.value = true
  processedCount.value = 0
  recognizedInvoices.value = []

  for (const pf of pendingFiles.value) {
    if (pf.status === 'done') {
      processedCount.value++
      continue
    }
    pf.status = 'parsing'
    try {
      const parsed = await parseInvoiceFile(pf.file)
      pf.status = 'done'
      recognizedInvoices.value.push({
        fileName: pf.name,
        file: pf.file,
        parsed,
        no: parsed.no || '',
        sellerName: parsed.sellerName || '',
        amount: parsed.amount ?? 0,
        tax: parsed.tax ?? 0,
        total: parsed.total ?? 0,
        valid: !!parsed.no,
      })
    } catch {
      pf.status = 'fail'
      recognizedInvoices.value.push({
        fileName: pf.name,
        file: pf.file,
        parsed: null,
        no: '',
        sellerName: '',
        amount: 0,
        tax: 0,
        total: 0,
        valid: false,
      })
    }
    processedCount.value++
  }
  processing.value = false
}

// 点击结果行编辑
function onResultRowClick(row: RecognizedRow) {
  const idx = recognizedInvoices.value.indexOf(row)
  if (idx < 0) return
  editingIndex.value = idx
  editing.value = {
    no: row.parsed?.no || '',
    date: row.parsed?.date || '',
    sellerName: row.parsed?.sellerName || '',
    amount: row.parsed?.amount ?? 0,
    tax: row.parsed?.tax ?? 0,
    total: row.parsed?.total ?? 0,
    type: row.parsed?.type || '增值税专用发票',
  }
  editVisible.value = true
}

function confirmEdit() {
  if (editingIndex.value < 0 || editingIndex.value >= recognizedInvoices.value.length) return
  const row = recognizedInvoices.value[editingIndex.value]
  const p = row.parsed || {} as any
  p.no = editing.value.no
  p.date = editing.value.date
  p.sellerName = editing.value.sellerName
  p.amount = editing.value.amount
  p.tax = editing.value.tax
  p.total = editing.value.total
  p.type = editing.value.type
  row.parsed = p
  row.no = p.no
  row.sellerName = p.sellerName
  row.amount = p.amount
  row.tax = p.tax
  row.total = p.total
  row.valid = !!p.no
  editVisible.value = false
  ElMessage.success('已更新')
}

// ======== 确认入池 ========
async function confirmAll() {
  saving.value = true
  let ok = 0
  let fail = 0
  for (const row of recognizedInvoices.value) {
    try {
      const ej = JSON.stringify(row.parsed || {})
      await inboxApi.upload(row.file, ej)
      ok++
    } catch (e: any) {
      if (e?.response?.status === 409) {
        ok++ // 已存在视为成功（不重复入池）
      } else {
        fail++
        console.error('入池失败', row.fileName, e)
      }
    }
  }
  saving.value = false
  ElMessage.success(`入库完成：成功 ${ok} 张${fail ? `，失败 ${fail} 张` : ''}`)
  emit('saved')
  emit('update:modelValue', false)
}
</script>

<style scoped>
.native-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 140px;
  border: 2px dashed var(--el-border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all .2s;
  margin-bottom: 12px;
  background: var(--el-fill-color-lighter);
}
.native-zone:hover,
.native-zone.dragover {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}
.upload-icon {
  font-size: 40px;
  color: var(--el-color-primary);
  margin-bottom: 8px;
}
.upload-text {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
  margin-bottom: 4px;
}
.upload-tip {
  font-size: 12px;
  color: #909399;
}

/* 文件列表 */
.file-list {
  margin-bottom: 12px;
}
.list-title {
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 6px;
}
.file-items {
  max-height: 160px;
  overflow-y: auto;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  padding: 4px 8px;
}
.file-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 3px 0;
  font-size: 12px;
}
.file-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.file-status {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 3px;
  white-space: nowrap;
}
.file-status.parsing { background: #e6f7ff; color: #1890ff; }
.file-status.done { background: #f6ffed; color: #52c41a; }
.file-status.fail { background: #fff2f0; color: #ff4d4f; }
.file-status.pending { background: #fafafa; color: #999; }

/* 批量处理 */
.processing-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #e6f7ff;
  border-radius: 4px;
  font-size: 13px;
  color: #1890ff;
  margin-bottom: 12px;
}
.spin { animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

/* 识别结果 */
.results {
  margin-top: 12px;
}
.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}
.result-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 6px;
}
</style>