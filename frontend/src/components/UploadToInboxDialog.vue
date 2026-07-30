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
      <div class="upload-tip">支持 PDF / OFD / 图片（最多 50 个文件）</div>
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
            <el-tag v-if="row.rejected" size="small" type="danger">已拒绝</el-tag>
            <el-tag v-else-if="row.needsReview" size="small" type="warning">待复核</el-tag>
            <el-tag v-else-if="row.valid" size="small" type="success">识别成功</el-tag>
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

    <!-- 入池结果面板（确认后展示，用户看完手动关） -->
    <div v-if="showResult" class="result-panel">
      <el-result :title="resultSummary" :sub-title="'明细如下：'" icon="success">
        <template #extra>
          <el-table :data="resultItems" border stripe size="small" height="300">
            <el-table-column prop="fileName" label="文件名" min-width="200" show-overflow-tooltip />
            <el-table-column label="结果" width="90" align="center">
              <template #default="{ row }">
            <el-tag v-if="row.status === '成功'" size="small" type="success">成功</el-tag>
            <el-tag v-else-if="row.status === '重复'" size="small" type="warning">重复</el-tag>
            <el-tag v-else-if="row.status === '待复核'" size="small" type="info">待复核</el-tag>
            <el-tag v-else size="small" type="danger">失败</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="detail" label="说明" min-width="250" show-overflow-tooltip />
          </el-table>
          <div class="result-actions">
            <el-button @click="resetAndClose">关闭</el-button>
            <el-button v-if="resultItems.some(i => i.status === '失败')" type="primary" @click="showResult = false; saving = false">
              返回重新上传
            </el-button>
          </div>
        </template>
      </el-result>
    </div>

    <template #footer>
      <el-button v-if="!showResult" @click="$emit('update:modelValue', false)">取消</el-button>
      <el-button v-else @click="resetAndClose">关闭</el-button>
      <el-button v-if="!showResult" type="primary" :disabled="!recognizedInvoices.length || processing" :loading="saving" @click="confirmAll">
        <template v-if="reviewCount === 0 && failCount === 0">
          确认入库（{{ poolableCount }} 张）
        </template>
        <template v-else>
          确认处理（{{ poolableCount }} 张入池{{ reviewCount ? `，${reviewCount} 张待复核` : '' }}{{ failCount ? `，${failCount} 张失败` : '' }}）
        </template>
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { parseInvoiceFile, validateInvoice, verifyInvoice, type ParsedInvoice } from '@/utils/invoiceParser'
import { inboxApi } from '@/api/inboxApi'
import { invoiceApi } from '@/api/invoice'

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
  needsReview?: boolean
  rejected?: boolean
  rejectReason?: string
}

const recognizedInvoices = ref<RecognizedRow[]>([])

// 动态计数：入池 / 待复核 / 解析失败
const poolableCount = computed(() => recognizedInvoices.value.filter(canEnterPool).length)
const reviewCount = computed(() => recognizedInvoices.value.filter((r) => r.valid && r.needsReview).length)
const failCount = computed(() => recognizedInvoices.value.filter((r) => !r.valid).length)

// 入池结果面板
interface ResultItem {
  fileName: string
  status: '成功' | '重复' | '失败' | '待复核' | '已拒绝'
  detail: string
}
const showResult = ref(false)
const resultItems = ref<ResultItem[]>([])
const resultSummary = ref('')

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
  showResult.value = false
  resultItems.value = []
  resultSummary.value = ''
}

// ======== 文件处理（原生 input 多选 + 拖拽多选） ========
function addFiles(files: FileList | File[]) {
  const arr = Array.from(files)
  for (const f of arr) {
    if (pendingFiles.value.length >= 50) {
      ElMessage.warning('最多上传 50 个文件')
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
      const validated = validateInvoice(parsed)
      const recognitionConsistent = parsed.recognition?.consistent !== false
      recognizedInvoices.value.push({
        fileName: pf.name,
        file: pf.file,
        parsed,
        no: parsed.no || '',
        sellerName: parsed.sellerName || '',
        amount: parsed.amount ?? 0,
        tax: parsed.tax ?? 0,
        total: parsed.total ?? 0,
        // 可入库：核心四字段齐全
        valid: validated.ok,
        // 需复核：核心字段齐全但 r1 与 r2 不一致（比对金额/税额/价税合计三项）
        needsReview: validated.ok && !recognitionConsistent,
        // 彻底拒绝：购买方为个人姓名（火车票除外），不可入库、不可人工放行
        rejected: !!validated.reject,
        rejectReason: validated.rejectReason,
      })
    } catch (e: any) {
      console.error('发票解析异常：', e)
      // 自动识别抛错时不再直接"解析失败"，而是给出一个可手动补录的待复核行，
      // 确保文件仍能进入发票箱，而不是阻断在弹窗里。
      const nameLow = pf.name.toLowerCase()
      const fallbackType = nameLow.includes('行程单') || nameLow.includes('机票') || nameLow.includes('航空')
        ? '航空运输电子客票行程单'
        : nameLow.includes('火车') || nameLow.includes('铁路')
          ? '铁路电子客票'
          : '增值税专用发票'
      const fallbackParsed: ParsedInvoice = {
        type: fallbackType,
        no: '',
        code: '',
        date: '',
        buyerName: '',
        buyerTaxNo: '',
        sellerName: '',
        sellerTaxNo: '',
        amount: 0,
        tax: 0,
        total: 0,
        taxRate: 0,
        items: [],
        recognition: { consistent: false, diffs: [], method: 'manual' },
      } as any
      pf.status = 'done'
      recognizedInvoices.value.push({
        fileName: pf.name,
        file: pf.file,
        parsed: fallbackParsed,
        no: '',
        sellerName: '',
        amount: 0,
        tax: 0,
        total: 0,
        valid: true,
        needsReview: true,
        rejected: false,
        rejectReason: undefined,
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
  // 人工修正后视为已确认：重置 recognition 为一致，否则 confirmAll 仍会把
  // 该发票当成 needs_review 隔离到发票箱，导致「复核后入库仍显示待复核」。
  p.recognition = { consistent: true, diffs: [], method: 'manual' }
  // 用最新字段重新跑公式核对
  p.validation = verifyInvoice(p)
  // 人工修正只改了表头三数，明细行必须同步重建，否则正式发票/发票箱 details 仍是旧值
  if (p.amount !== undefined && p.total !== undefined) {
    const itemName = p.item || (p.items && p.items[0]?.name) || '费用'
    p.items = [{
      name: itemName,
      qty: 1,
      amount: p.amount,
      tax: p.tax ?? 0,
      taxRate: p.taxRate ?? 0,
      total: p.total,
    }]
  }
  row.parsed = p
  row.no = p.no
  row.sellerName = p.sellerName
  row.amount = p.amount
  row.tax = p.tax
  row.total = p.total
  const validated = validateInvoice(p)
  row.valid = validated.ok
  row.rejected = !!validated.reject
  row.rejectReason = validated.rejectReason
  // 人工修正后重新比对双识别一致性
  row.needsReview = validated.ok && p.recognition?.consistent === false
  editVisible.value = false
  ElMessage.success('已更新')
}

// ======== 映射：ParsedInvoice → 发票池创建负载 ========
function round2(n: number): number {
  return Math.round((Number(n) || 0) * 100) / 100
}

function mapToCreatePayload(p: ParsedInvoice) {
  const details = (p.items && p.items.length)
    ? p.items.map((it) => ({
        biz_type: it.name || null,
        item: it.name || null,
        qty: it.qty ?? 1,
        amount: it.amount ?? 0,
        tax_rate: it.taxRate ?? 0,
        tax: it.tax ?? 0,
        total: round2((it.amount ?? 0) + (it.tax ?? 0)),
      }))
    : [{
        biz_type: p.item || '费用',
        item: p.item || '费用',
        qty: 1,
        amount: p.amount ?? 0,
        tax_rate: p.taxRate ?? 0,
        tax: p.tax ?? 0,
        total: round2((p.amount ?? 0) + (p.tax ?? 0)),
      }]
  return {
    invoice_type: p.type || '增值税专用发票',
    code: p.code || null,
    no: p.no || '',
    invoice_date: p.date || null,
    buyer_name: p.buyerName || null,
    buyer_tax_no: p.buyerTaxNo || null,
    seller_name: p.sellerName || '未知销售方',
    seller_tax_no: p.sellerTaxNo || null,
    account: p.account || null,
    certify: 'none',
    remark: '上传自动识别入库',
    reimbursement_bill_id: null,
    purchase_requisition_item_id: null,
    attachment_path: null,
    details,
  } as any
}

// 判定一张识别结果是否「可信可入库」：核心四字段齐全 + r1 与 r2 一致。
function canEnterPool(row: RecognizedRow): boolean {
  if (!row.valid) return false
  if (row.parsed?.recognition?.consistent === false) return false
  return true
}

// ======== 确认入库（压平流程：可信发票直入发票池，可疑/失败隔离到发票箱） ========
async function confirmAll() {
  saving.value = true
  const items: ResultItem[] = []
  for (const row of recognizedInvoices.value) {
    const ej = JSON.stringify(row.parsed || {})
    // 彻底拒绝：购买方为个人姓名（火车票除外）→ 不入库、不隔离待复核，直接标记已拒绝
    if (row.rejected) {
      try {
        await inboxApi.upload(row.file, ej) // 后端置 rejected 状态，留痕且不可放行
      } catch (e) {
        // 即便上传失败也不入库，忽略网络错误
      }
      items.push({ fileName: row.fileName, status: '已拒绝', detail: row.rejectReason || '购买方为个人姓名，不能入库' })
      continue
    }
    const poolable = canEnterPool(row)
    try {
      if (poolable) {
        // 核心三数自洽 + 双识别一致 → 直接写入发票池
        const created = await invoiceApi.create(mapToCreatePayload(row.parsed!))
        // 附件归档到发票池（失败不阻断：发票已入库）
        try {
          if (row.file) await invoiceApi.uploadAttachment(created.data.id, row.file)
        } catch (e) {
          console.warn('附件归档失败（发票已入池）', e)
        }
        items.push({ fileName: row.fileName, status: '成功', detail: '已入发票池，可在挂发票时使用' })
      } else {
        // 核心字段缺失 / 公式不自洽 / 双识别不一致 → 隔离到发票箱待复核，不污染发票池
        const res = await inboxApi.upload(row.file, ej)
        if (res.data?.duplicated) {
          items.push({ fileName: row.fileName, status: '重复', detail: '发票箱中已存在同号码发票，识别结果已更新' })
        } else {
          const reasons: string[] = []
          if (!row.valid) reasons.push('核心字段缺失')
          if (row.parsed?.validation?.passed === false) reasons.push(row.parsed?.validation?.message || '核心三数不自洽')
          if (row.parsed?.recognition?.consistent === false) {
            reasons.push(row.parsed?.recognition?.method === 'manual' ? '自动识别失败' : '双识别不一致')
          }
          items.push({
            fileName: row.fileName,
            status: '待复核',
            detail: reasons.length ? `${reasons.join('；')}，已隔离到发票箱待复核` : '识别失败，已隔离到发票箱待人工补录',
          })
        }
      }
    } catch (e: any) {
      const status = e?.response?.status
      if (status === 409) {
        items.push({
          fileName: row.fileName,
          status: '重复',
          detail: poolable ? '发票池中已存在同号码发票' : '发票箱中已存在同号码发票',
        })
      } else {
        const msg = e?.response?.data?.detail || '请求失败'
        items.push({ fileName: row.fileName, status: '失败', detail: msg })
      }
    }
  }
  resultItems.value = items
  const ok = items.filter((i) => i.status === '成功').length
  const review = items.filter((i) => i.status === '待复核').length
  const dup = items.filter((i) => i.status === '重复').length
  const fail = items.filter((i) => i.status === '失败').length
  const parts = [`${ok} 张入池`]
  if (review) parts.push(`${review} 张待复核`)
  if (dup) parts.push(`${dup} 张重复`)
  if (fail) parts.push(`${fail} 张失败`)
  resultSummary.value = `入库完毕：${parts.join('，')}`
  showResult.value = true
  saving.value = false
  emit('saved')
}

function resetAndClose() {
  showResult.value = false
  resultItems.value = []
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
  color: var(--text-strong);
  font-weight: 500;
  margin-bottom: 4px;
}
.upload-tip {
  font-size: 12px;
  color: var(--text-muted);
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
.file-status.pending { background: var(--bg-subtle); color: #999; }

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
  color: var(--text-strong);
  margin-bottom: 8px;
}
.result-tip {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 6px;
}
.result-panel {
  min-height: 300px;
}
.result-actions {
  margin-top: 16px;
  display: flex;
  gap: 10px;
  justify-content: center;
}
</style>