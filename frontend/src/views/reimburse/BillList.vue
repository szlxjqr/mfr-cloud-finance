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
      <el-table-column prop="bill_no" label="单号" width="160" />
      <el-table-column prop="applicant" label="申请人" width="100" />
      <el-table-column prop="department" label="部门" width="110" />
      <el-table-column label="发票" width="150" align="center">
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
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑报销单' : '新建报销单'" width="720px" :close-on-click-modal="false">
      <el-form :model="form" label-width="100px">
        <el-form-item label="报销单编号">
          <el-input :model-value="form.bill_no || previewBillNo || '保存后自动生成'" disabled />
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

      <!-- 已关联发票（编辑模式或保存后可见） -->
      <div v-if="editing && editingId" class="linked-invoices">
        <div class="linked-header">
          <span class="linked-title">已关联发票</span>
          <el-button type="primary" size="small" @click="openAddInvoice">
            <el-icon><Plus /></el-icon>增加发票
          </el-button>
        </div>
        <el-table :data="linkedInvoices" border stripe size="small" empty-text="暂无发票，点击上方按钮添加">
          <el-table-column prop="invoice_date" label="开票日期" width="110" />
          <el-table-column prop="invoice_type" label="类型" width="120" />
          <el-table-column prop="no" label="发票号码" width="130" />
          <el-table-column prop="seller_name" label="销方名称" show-overflow-tooltip />
          <el-table-column label="合计" width="120" align="right">
            <template #default="{ row }">
              ¥{{ invoiceTotal(row).toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80" align="center">
            <template #default="{ row }">
              <el-button link type="danger" size="small" @click="unlinkInvoice(row)">移除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

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

    <!-- 增加发票弹窗（支持上传识别 + 人工核实） -->
    <el-dialog v-model="invoiceDialogVisible" title="增加发票" width="780px" :close-on-click-modal="false">
      <!-- 上传识别区 -->
      <div class="recognize-section">
        <div class="recognize-title">
          <el-icon><Picture /></el-icon>
          <span>上传发票自动识别</span>
        </div>
        <el-upload
          drag
          action="#"
          :auto-upload="false"
          accept=".jpg,.jpeg,.png,.pdf,.ofd"
          :show-file-list="false"
          :disabled="recognizing"
          :on-change="onRecognizeFileChange"
          class="recognize-uploader"
        >
          <el-icon class="recognize-upload-icon"><Picture /></el-icon>
          <div class="recognize-upload-text">
            <p>点击或拖拽上传发票图片 / PDF / OFD</p>
            <p class="recognize-upload-tip">支持 JPG、PNG、PDF、OFD 格式，上传后自动识别并填入下方表单</p>
          </div>
        </el-upload>

        <div v-if="recognizeFile" class="recognize-file">
          <div class="recognize-file-info">
            <el-icon><Document /></el-icon>
            <span class="recognize-file-name">{{ recognizeFile.name }}</span>
            <el-button text type="danger" size="small" :disabled="recognizing" @click="removeRecognizeFile">
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
          <div v-if="recognizePreviewUrl && recognizeFile.type.startsWith('image')" class="recognize-image-preview">
            <img :src="recognizePreviewUrl" alt="发票预览" />
          </div>
        </div>

        <div v-if="recognizing" class="recognize-loading">
          <el-icon class="recognize-spin"><Refresh /></el-icon>
          <span>正在识别发票内容，请稍候…</span>
        </div>

        <el-alert
          v-if="recognizeError"
          :title="recognizeError"
          type="warning"
          :closable="false"
          show-icon
          class="recognize-error"
        />
      </div>

      <el-divider content-position="left">识别结果核实</el-divider>

      <el-form ref="invoiceFormRef" :model="invoiceForm" :rules="invoiceRules" label-width="100px">
        <div class="invoice-form-row">
          <el-form-item label="发票类型" prop="invoice_type" style="flex: 1">
            <el-select v-model="invoiceForm.invoice_type" style="width: 100%">
              <el-option v-for="t in invoiceTypes" :key="t" :label="t" :value="t" />
            </el-select>
          </el-form-item>
          <el-form-item label="开票日期" prop="invoice_date" style="flex: 1">
            <el-date-picker v-model="invoiceForm.invoice_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
          </el-form-item>
        </div>
        <div class="invoice-form-row">
          <el-form-item label="发票代码" prop="code" style="flex: 1">
            <el-input v-model="invoiceForm.code" placeholder="数电票可空" />
          </el-form-item>
          <el-form-item label="发票号码" prop="no" style="flex: 1">
            <el-input v-model="invoiceForm.no" placeholder="必填" />
          </el-form-item>
        </div>
        <el-form-item label="购买方">
          <el-input v-model="invoiceForm.buyer_name" placeholder="购买方名称" />
        </el-form-item>
        <el-form-item label="销方名称" prop="seller_name">
          <el-input v-model="invoiceForm.seller_name" placeholder="必填" />
        </el-form-item>
        <div class="invoice-form-row">
          <el-form-item label="结算科目" prop="account" style="flex: 1">
            <el-select v-model="invoiceForm.account" placeholder="请选择" style="width: 100%">
              <el-option v-for="a in accountOptions" :key="a" :label="a" :value="a" />
            </el-select>
          </el-form-item>
          <el-form-item label="是否认证" style="flex: 1">
            <el-radio-group v-model="invoiceForm.certify">
              <el-radio label="current">本期认证</el-radio>
              <el-radio label="none">暂不认证</el-radio>
            </el-radio-group>
          </el-form-item>
        </div>
        <el-form-item label="备注">
          <el-input v-model="invoiceForm.remark" type="textarea" :rows="2" />
        </el-form-item>

        <!-- 明细 -->
        <div class="detail-section">
          <table class="detail-table">
            <thead>
              <tr>
                <th style="width: 120px">业务类型</th>
                <th style="min-width: 160px">开票项目</th>
                <th style="width: 70px">数量</th>
                <th style="width: 110px">金额</th>
                <th style="width: 90px">税率%</th>
                <th style="width: 100px">税额</th>
                <th style="width: 110px">价税合计</th>
                <th style="width: 50px">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(d, idx) in invoiceForm.details" :key="idx">
                <td>
                  <el-select v-model="d.biz_type" size="small" style="width: 100%">
                    <el-option v-for="b in bizTypeOptions" :key="b" :label="b" :value="b" />
                  </el-select>
                </td>
                <td>
                  <el-input v-model="d.item" size="small" placeholder="开票项目" />
                </td>
                <td>
                  <el-input-number v-model="d.qty" :min="1" :controls="false" size="small" style="width: 100%" />
                </td>
                <td>
                  <el-input-number v-model="d.amount" :min="0" :precision="2" :controls="false" size="small" style="width: 100%" @change="calcDetail(d)" />
                </td>
                <td>
                  <el-select v-model="d.tax_rate" size="small" style="width: 100%" @change="calcDetail(d)">
                    <el-option v-for="r in taxRateOptions" :key="r" :label="r" :value="Number(r)" />
                  </el-select>
                </td>
                <td>
                  <el-input-number v-model="d.tax" :precision="2" :controls="false" size="small" style="width: 100%" disabled />
                </td>
                <td>
                  <el-input-number v-model="d.total" :precision="2" :controls="false" size="small" style="width: 100%" disabled />
                </td>
                <td>
                  <el-button text type="danger" size="small" @click="removeDetail(idx)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </td>
              </tr>
            </tbody>
          </table>
          <el-button text type="primary" size="small" @click="addDetail">
            <el-icon><Plus /></el-icon>添加明细行
          </el-button>
        </div>
      </el-form>

      <template #footer>
        <el-button @click="invoiceDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitInvoice">保存并关联</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Picture, Document, Close, Refresh } from '@element-plus/icons-vue'
import { reimburseApi } from '@/api/reimburse'
import { invoiceApi } from '@/api/invoice'
import type { ReimbursementBill } from '@/types/reimburse'
import type { Invoice, InvoiceCreatePayload } from '@/types/invoice'
import { parseInvoiceFile, type ParsedInvoice } from '@/utils/invoiceParser'

const statusOptions = ['草稿', '待审批', '已通过', '已驳回', '已支付']

const invoiceTypes = [
  '增值税专用发票',
  '增值税普通发票',
  '电子专用发票',
  '电子普通发票',
  '机动车销售统一发票',
  '火车票',
  '机票',
  '航空运输电子客票行程单',
  '铁路电子客票',
]
const taxRateOptions = ['0', '1', '3', '6', '9', '13']
const accountOptions = ['库存商品', '管理费用', '销售费用', '固定资产', '原材料', '工程施工', '管理费用-差旅费']
const bizTypeOptions = ['采购商品', '接受服务', '采购固定资产', '费用报销', '其他']

const keyword = ref('')
const statusFilter = ref<string | null>(null)
const list = ref<ReimbursementBill[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const editing = ref(false)
const editingId = ref<number | null>(null)
const previewBillNo = ref<string | null>(null)
const linkedInvoices = ref<Invoice[]>([])

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

async function loadLinkedInvoices() {
  if (!editingId.value) {
    linkedInvoices.value = []
    return
  }
  try {
    const res = await invoiceApi.list({ reimbursement_bill_id: editingId.value })
    linkedInvoices.value = res.data
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载已关联发票失败')
  }
}

function invoiceTotal(inv: Invoice): number {
  return inv.details.reduce((sum, d) => sum + (d.total || 0), 0)
}

async function openCreate() {
  Object.assign(form, emptyForm())
  editing.value = false
  editingId.value = null
  previewBillNo.value = null
  linkedInvoices.value = []
  dialogVisible.value = true
  try {
    const res = await reimburseApi.nextBillNo()
    previewBillNo.value = res.data.bill_no
  } catch (e: any) {
    // 预占单号失败仍可继续，保存时后端会生成
    console.warn('预占单号失败', e)
  }
}

function openEdit(row: ReimbursementBill) {
  Object.assign(form, emptyForm(), row)
  editing.value = true
  editingId.value = row.id
  previewBillNo.value = row.bill_no ?? null
  dialogVisible.value = true
  loadLinkedInvoices()
}

async function save() {
  const payload: Record<string, unknown> = { ...form }
  if (payload.amount === '' || payload.amount === null) payload.amount = null
  if (editing.value && editingId.value != null) {
    await reimburseApi.update(editingId.value, payload)
    ElMessage.success('已更新')
    dialogVisible.value = false
    load()
  } else {
    // 新建：若有预占单号则传入，保持前后一致
    if (previewBillNo.value && !payload.bill_no) {
      payload.bill_no = previewBillNo.value
    }
    const res = await reimburseApi.create(payload)
    ElMessage.success('已创建')
    // 保存后进入编辑态，方便继续增加发票
    editing.value = true
    editingId.value = res.data.id
    form.bill_no = res.data.bill_no ?? null
    previewBillNo.value = res.data.bill_no ?? null
    await loadLinkedInvoices()
    await load()
  }
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

/* ============ 增加发票（上传识别） ============ */
const invoiceDialogVisible = ref(false)
const invoiceFormRef = ref<any>(null)

const recognizeFile = ref<File | null>(null)
const recognizePreviewUrl = ref('')
const recognizing = ref(false)
const recognizeError = ref('')

function resetRecognizeState() {
  recognizeFile.value = null
  recognizePreviewUrl.value = ''
  recognizing.value = false
  recognizeError.value = ''
}

function onRecognizeFileChange(uploadFile: any) {
  const raw = uploadFile?.raw || uploadFile
  if (!raw) return
  recognizeFile.value = raw
  recognizePreviewUrl.value = raw.type?.startsWith('image/') ? URL.createObjectURL(raw) : ''
  recognizeError.value = ''
  startRecognize()
}

function removeRecognizeFile() {
  resetRecognizeState()
}

async function startRecognize() {
  if (!recognizeFile.value) return
  recognizing.value = true
  recognizeError.value = ''
  try {
    const parsed = await parseInvoiceFile(recognizeFile.value)
    applyRecognized(parsed)
    ElMessage.success('发票识别完成，请核对下方信息')
  } catch (err: any) {
    console.error('发票识别失败', err)
    recognizeError.value = '发票识别失败：' + (err?.message || '请检查文件格式或改为手工录入')
  } finally {
    recognizing.value = false
  }
}

function applyRecognized(p: ParsedInvoice) {
  // 1. 发票类型推断
  let invoiceType = p.type || '增值税普通发票'
  if (/专票/.test(invoiceType)) invoiceType = '增值税专用发票'
  else if (/普通发票|电子发票/.test(invoiceType) && !/专用/.test(invoiceType)) invoiceType = '增值税普通发票'
  else if (/火车|铁路/.test(invoiceType)) invoiceType = '火车票'
  else if (/机票|航空/.test(invoiceType)) invoiceType = '机票'

  // 2. 根据类型给默认科目和税率
  const isTravel = /火车|铁路|机票|航空/.test(invoiceType)
  const isService = /服务|代理/.test(invoiceType)
  const defaultAccount = isTravel ? '管理费用-差旅费' : isService ? '管理费用' : '管理费用'
  const defaultTaxRate = isTravel ? 9 : isService ? 6 : 13

  // 3. 明细映射
  let details: InvoiceCreatePayload['details'] = []
  if (p.items && p.items.length > 0) {
    details = p.items.map((it) => {
      const amount = Number(it.amount) || 0
      const taxRate = it.taxRate && it.taxRate > 0 ? it.taxRate : defaultTaxRate
      const tax = Number(it.tax) || Number((amount * (taxRate / 100)).toFixed(2))
      return {
        biz_type: isTravel ? '费用报销' : '采购商品',
        item: it.name || (isTravel ? '差旅费' : '见发票明细'),
        qty: Number(it.qty) || 1,
        amount,
        tax_rate: taxRate,
        tax,
        total: Number((amount + tax).toFixed(2)),
      }
    })
  } else {
    const amount = Number(p.amount) || 0
    const tax = Number(p.tax) || 0
    const total = Number(p.total) || Number((amount + tax).toFixed(2))
    details = [
      {
        biz_type: isTravel ? '费用报销' : '采购商品',
        item: p.item || (isTravel ? '差旅费' : '见发票明细'),
        qty: 1,
        amount,
        tax_rate: p.taxRate && p.taxRate > 0 ? p.taxRate : defaultTaxRate,
        tax,
        total,
      },
    ]
  }

  // 4. 填充表单（保留原值兜底，便于用户只修改错误字段）
  Object.assign(invoiceForm, {
    invoice_type: invoiceType,
    code: p.code || null,
    no: p.no || invoiceForm.no,
    invoice_date: p.date || invoiceForm.invoice_date,
    buyer_name: p.buyerName || invoiceForm.buyer_name,
    buyer_tax_no: p.buyerTaxNo || invoiceForm.buyer_tax_no,
    seller_name: p.sellerName || invoiceForm.seller_name,
    seller_tax_no: p.sellerTaxNo || invoiceForm.seller_tax_no,
    account: defaultAccount,
    details,
  })
}

function emptyInvoiceForm(): InvoiceCreatePayload {
  return {
    invoice_type: '增值税专用发票',
    code: null,
    no: '',
    invoice_date: null,
    buyer_name: null,
    buyer_tax_no: null,
    seller_name: '',
    seller_tax_no: null,
    seller_address_phone: null,
    seller_bank_account: null,
    account: null,
    certify: 'none',
    remark: null,
    reimbursement_bill_id: editingId.value,
    attachment_path: null,
    route_info: null,
    traveler: null,
    details: [{ biz_type: '费用报销', item: '', qty: 1, amount: 0, tax_rate: 13, tax: 0, total: 0 }],
  }
}
const invoiceForm = reactive<InvoiceCreatePayload>(emptyInvoiceForm())

const invoiceRules = {
  invoice_type: [{ required: true, message: '请选择发票类型', trigger: 'change' }],
  no: [{ required: true, message: '请输入发票号码', trigger: 'blur' }],
  seller_name: [{ required: true, message: '请输入销方名称', trigger: 'blur' }],
  account: [{ required: true, message: '请选择结算科目', trigger: 'change' }],
}

function calcDetail(d: any) {
  d.tax = Number((d.amount * (d.tax_rate / 100)).toFixed(2))
  d.total = Number((d.amount + d.tax).toFixed(2))
}

function addDetail() {
  invoiceForm.details.push({ biz_type: '费用报销', item: '', qty: 1, amount: 0, tax_rate: 13, tax: 0, total: 0 })
}

function removeDetail(idx: number) {
  if (invoiceForm.details.length <= 1) {
    ElMessage.warning('至少保留一条明细')
    return
  }
  invoiceForm.details.splice(idx, 1)
}

function openAddInvoice() {
  if (!editingId.value) {
    ElMessage.warning('请先保存报销单')
    return
  }
  Object.assign(invoiceForm, emptyInvoiceForm())
  invoiceForm.reimbursement_bill_id = editingId.value
  resetRecognizeState()
  invoiceDialogVisible.value = true
}

async function submitInvoice() {
  invoiceFormRef.value?.validate(async (valid: boolean) => {
    if (!valid) return
    if (!editingId.value) {
      ElMessage.warning('报销单未保存')
      return
    }
    for (const d of invoiceForm.details) {
      calcDetail(d)
      if (!d.item) {
        ElMessage.warning('请完善开票项目')
        return
      }
    }
    const payload: InvoiceCreatePayload = { ...invoiceForm, reimbursement_bill_id: editingId.value }
    try {
      await invoiceApi.create(payload)
      ElMessage.success('发票已保存并关联')
      invoiceDialogVisible.value = false
      await loadLinkedInvoices()
      // 自动按关联发票汇总更新报销单金额
      await syncBillAmount()
      await load()
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.detail || '保存发票失败')
    }
  })
}

async function syncBillAmount() {
  if (!editingId.value) return
  try {
    const sumRes = await invoiceApi.summaryByBill(editingId.value)
    const summary = sumRes.data
    if (summary.total > 0) {
      await reimburseApi.update(editingId.value, { amount: summary.total })
      form.amount = summary.total
    }
  } catch (e) {
    // 汇总更新失败不影响主流程
    console.warn('汇总更新报销单金额失败', e)
  }
}

async function unlinkInvoice(inv: Invoice) {
  try {
    await invoiceApi.unlink(inv.id)
    ElMessage.success('已移除关联')
    await loadLinkedInvoices()
    await syncBillAmount()
    await load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '移除关联失败')
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

/* 已关联发票 */
.linked-invoices {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px dashed var(--el-border-color);
}
.linked-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.linked-title {
  font-weight: 600;
  color: var(--el-text-color-regular);
}

/* 增加发票弹窗 */
.invoice-form-row {
  display: flex;
  gap: 16px;
}
.invoice-form-row .el-form-item {
  flex: 1;
  min-width: 0;
}
.detail-section {
  margin-top: 12px;
}
.detail-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  margin-bottom: 8px;
}
.detail-table th,
.detail-table td {
  border: 1px solid var(--el-border-color-lighter);
  padding: 6px;
  text-align: center;
  font-size: 13px;
}
.detail-table th {
  background: #f5f7fa;
  font-weight: 600;
}

/* 上传识别区 */
.recognize-section {
  margin-bottom: 8px;
}
.recognize-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: var(--el-color-primary);
  margin-bottom: 12px;
}
.recognize-uploader :deep(.el-upload-dragger) {
  width: 100%;
  padding: 32px 20px;
  border: 2px dashed var(--el-color-primary-light-5);
  border-radius: 8px;
  background: var(--el-color-primary-light-9);
}
.recognize-uploader :deep(.el-upload-dragger:hover) {
  border-color: var(--el-color-primary);
}
.recognize-uploader :deep(.el-upload.is-disabled .el-upload-dragger) {
  opacity: 0.7;
  cursor: not-allowed;
}
.recognize-upload-icon {
  font-size: 40px;
  color: var(--el-color-primary);
  margin-bottom: 8px;
}
.recognize-upload-text p {
  margin: 0;
  color: var(--el-text-color-primary);
  font-size: 15px;
  font-weight: 500;
}
.recognize-upload-tip {
  font-size: 12px !important;
  color: var(--el-text-color-secondary) !important;
  margin-top: 6px !important;
}
.recognize-file {
  margin-top: 12px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  padding: 10px 12px;
  background: #fff;
}
.recognize-file-info {
  display: flex;
  align-items: center;
  gap: 8px;
}
.recognize-file-name {
  flex: 1;
  font-size: 14px;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.recognize-image-preview {
  display: flex;
  justify-content: center;
  max-height: 200px;
  overflow: hidden;
  margin-top: 8px;
}
.recognize-image-preview img {
  max-width: 100%;
  max-height: 200px;
  border-radius: 4px;
  border: 1px solid var(--el-border-color-lighter);
}
.recognize-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-top: 12px;
  padding: 16px;
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  border-radius: 6px;
}
.recognize-spin {
  font-size: 22px;
  animation: recognize-spin 1s linear infinite;
}
@keyframes recognize-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.recognize-error {
  margin-top: 12px;
}
</style>
