<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  Plus,
  Delete,
  Refresh,
  Setting,
  QuestionFilled,
  Filter,
  MagicStick,
  DocumentChecked,
  ArrowDown,
  EditPen,
  Upload,
  Picture,
  Document,
  Close,
} from '@element-plus/icons-vue'
import { parseInvoiceFile, validateInvoice, verifyInvoice, type ParsedInvoice } from '../../utils/invoiceParser'
import { invoiceApi } from '@/api/invoice'
import type { Invoice, InvoiceCreatePayload } from '@/types/invoice'

/** 发票明细行（前端编辑态） */
interface InvoiceDetail {
  id: string
  bizType: string
  item: string
  qty: number
  amount: number
  taxRate: number
  tax: number
  total: number
}

/** 发票记录（前端表格展平形态：一条明细一行，同发票 invoiceId 相同） */
interface InvoiceRecord {
  id: string
  invoiceId: number
  invoiceCode: string
  type: string
  code: string
  no: string
  date: string
  sellerName: string
  sellerTaxNo: string
  sellerAddressPhone: string
  sellerBankAccount: string
  buyerName: string
  buyerTaxNo: string
  account: string
  certify: 'current' | 'none'
  remark: string
  bizType: string
  item: string
  qty: number
  amount: number
  taxRate: number
  tax: number
  total: number
}

let _seq = 0
function genId(): string {
  _seq += 1
  return `inv_${Date.now().toString(36)}_${_seq}`
}

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

/** 表格数据源（从后端加载） */
const rows = reactive<InvoiceRecord[]>([])
const loading = ref(false)

/** 期间 */
const period = ref<string>('2026-05')

/** 搜索关键字 */
const keyword = ref('')
const filteredRows = computed<InvoiceRecord[]>(() => rows)

/** 选中行 */
const selectedIds = ref<Set<string>>(new Set())
function isSelected(id: string): boolean {
  return selectedIds.value.has(id)
}
function toggleSelect(row: InvoiceRecord, e: Event) {
  e.stopPropagation()
  if (selectedIds.value.has(row.id)) selectedIds.value.delete(row.id)
  else selectedIds.value.add(row.id)
}
function onRowClick(row: InvoiceRecord) {
  if (selectedIds.value.has(row.id)) selectedIds.value.delete(row.id)
  else selectedIds.value.add(row.id)
}

/* ============ 数据加载 ============ */
function lastDayOfMonth(ym: string): string {
  const [y, m] = ym.split('-').map(Number)
  const d = new Date(y, m, 0)
  return `${y}-${String(m).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function flattenInvoices(invoices: Invoice[]): InvoiceRecord[] {
  const result: InvoiceRecord[] = []
  for (const inv of invoices) {
    const header = {
      invoiceId: inv.id,
      invoiceCode: inv.invoice_code || '',
      type: inv.invoice_type,
      code: inv.code || '',
      no: inv.no,
      date: inv.invoice_date || '',
      sellerName: inv.seller_name,
      sellerTaxNo: inv.seller_tax_no || '',
      sellerAddressPhone: inv.seller_address_phone || '',
      sellerBankAccount: inv.seller_bank_account || '',
      buyerName: inv.buyer_name || '',
      buyerTaxNo: inv.buyer_tax_no || '',
      account: inv.account || '',
      certify: (inv.certify as 'current' | 'none') || 'none',
      remark: inv.remark || '',
    }
    if (!inv.details || inv.details.length === 0) {
      result.push({
        id: `inv_${inv.id}_empty`,
        ...header,
        bizType: '',
        item: '',
        qty: 0,
        amount: 0,
        taxRate: 0,
        tax: 0,
        total: 0,
      })
    } else {
      for (const d of inv.details) {
        result.push({
          id: String(d.id),
          ...header,
          bizType: d.biz_type || '',
          item: d.item || '',
          qty: Number(d.qty) || 0,
          amount: Number(d.amount) || 0,
          taxRate: Number(d.tax_rate) || 0,
          tax: Number(d.tax) || 0,
          total: Number(d.total) || 0,
        })
      }
    }
  }
  return result
}

async function loadList() {
  loading.value = true
  try {
    const params: Record<string, any> = {}
    if (keyword.value.trim()) params.keyword = keyword.value.trim()
    if (period.value) {
      params.start_date = `${period.value}-01`
      params.end_date = lastDayOfMonth(period.value)
    }
    const res = await invoiceApi.list(params)
    rows.splice(0, rows.length, ...flattenInvoices(res.data))
    selectedIds.value.clear()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载发票列表失败')
  } finally {
    loading.value = false
  }
}

let listTimer: ReturnType<typeof setTimeout> | null = null
function debouncedLoadList() {
  if (listTimer) clearTimeout(listTimer)
  listTimer = setTimeout(() => loadList(), 300)
}

onMounted(loadList)
watch([keyword, period], debouncedLoadList)

/* ============ AI 发票识别弹窗 ============ */
const aiDialogVisible = ref(false)
const aiRecognizing = ref(false)
const aiFile = ref<File | null>(null)
const aiPreviewUrl = ref('')
const aiResult = ref<Partial<typeof formModel> | null>(null)

const aiAccept = '.jpg,.jpeg,.png,.pdf,.ofd'

function openAiDialog() {
  aiDialogVisible.value = true
  aiFile.value = null
  aiPreviewUrl.value = ''
  aiResult.value = null
  aiRecognizing.value = false
}

function onAiFileChange(uploadFile: any) {
  const raw = uploadFile?.raw || uploadFile
  if (!raw) return
  aiFile.value = raw
  aiPreviewUrl.value = URL.createObjectURL(raw)
  aiResult.value = null
  startAiRecognize()
}

function removeAiFile() {
  aiFile.value = null
  aiPreviewUrl.value = ''
  aiResult.value = null
}

function startAiRecognize() {
  if (!aiFile.value) {
    ElMessage.warning('请先上传发票图片或 PDF')
    return
  }
  aiRecognizing.value = true
  aiResult.value = null
  const file = aiFile.value
  parseInvoiceFile(file)
    .then((parsed: ParsedInvoice) => {
      aiResult.value = buildResultFromParsed(parsed)
      aiRecognizing.value = false
      setTimeout(() => applyAiResult(parsed), 1000)
    })
    .catch((err) => {
      console.error('发票识别失败', err)
      aiRecognizing.value = false
      ElMessage.error('发票文件解析失败，请检查文件格式或改为手动录入')
    })
}

function buildResultFromParsed(p: ParsedInvoice): Partial<typeof formModel> {
  let details: InvoiceDetail[]
  if (p.items && p.items.length > 0) {
    details = p.items.map((it) => ({
      id: genId(),
      bizType: '采购商品',
      item: it.name || '见发票明细',
      qty: it.qty || 1,
      amount: it.amount ?? 0,
      taxRate: it.taxRate ?? p.taxRate ?? 13,
      tax: it.tax ?? 0,
      total: Number(((it.amount ?? 0) + (it.tax ?? 0)).toFixed(2)),
    }))
  } else {
    details = [
      {
        id: genId(),
        bizType: '采购商品',
        item: p.item || '见发票明细',
        qty: 1,
        amount: p.amount ?? 0,
        taxRate: p.taxRate ?? 13,
        tax: p.tax ?? 0,
        total: p.total ?? 0,
      },
    ]
  }

  // 根据发票类型给默认税率：火车票/机票 9%；代理/服务 6%；其余默认 13%
  const typeHint = p.type || ''
  const isTravel = /火车|铁路|机票|航空/.test(typeHint)
  const isService = /服务|代理/.test(typeHint)
  details.forEach((d) => {
    if (isTravel && (!d.taxRate || d.taxRate === 13)) d.taxRate = 9
    else if (isService && (!d.taxRate || d.taxRate === 13)) d.taxRate = 6
    ensureDetailComputed(d)
  })

  return {
    invoiceId: null,
    type: p.type || '增值税专用发票',
    code: p.code || '',
    no: p.no || '',
    account: isTravel ? '管理费用-差旅费' : (p.account || '库存商品'),
    date: p.date || '2026-05-18',
    sellerName: p.sellerName || '',
    sellerTaxNo: p.sellerTaxNo || '',
    sellerAddressPhone: '',
    sellerBankAccount: '',
    buyerName: p.buyerName || '',
    buyerTaxNo: p.buyerTaxNo || '',
    certify: 'none',
    remark: '',
    details,
  }
}

async function applyAiResult(parsed: ParsedInvoice) {
  if (!aiResult.value) return
  const validation = validateInvoice(parsed)
  if (validation.ok) {
    const data = aiResult.value
    const details = data.details?.length ? data.details : [emptyDetail()]
    try {
      await invoiceApi.create(buildPayload({ ...data, details } as typeof formModel))
      await loadList()
      aiDialogVisible.value = false
      const verify = verifyInvoice(parsed)
      if (verify.consistent) {
        ElMessage.success('已识别并保存发票')
      } else {
        ElMessage.warning(`已保存，但识别数据疑似不符（已保留票面原值）：${verify.warnings.join('；')}`)
      }
    } catch (e: any) {
      if (e?.response?.status === 409) {
        ElMessage.warning(e?.response?.data?.detail || '该发票已存在，不能重复录入')
      } else {
        ElMessage.error(e?.response?.data?.detail || '保存识别结果失败')
      }
    }
  } else {
    resetForm()
    Object.assign(formModel, aiResult.value)
    if (!formModel.details || formModel.details.length === 0) {
      formModel.details = [emptyDetail()]
    }
    aiDialogVisible.value = false
    dialogMode.value = 'add'
    dialogVisible.value = true
    formRef.value?.clearValidate()
    ElMessage.warning(
      `核心字段识别不完整（${validation.missing.join('、')}），已预填可识别内容，请补充后保存`,
    )
  }
}

const dialogVisible = ref(false)
const dialogMode = ref<'add' | 'edit'>('add')
const formRef = ref<FormInstance>()

const formModel = reactive<{
  invoiceId: number | null
  type: string
  code: string
  no: string
  account: string
  date: string
  sellerName: string
  sellerTaxNo: string
  sellerAddressPhone: string
  sellerBankAccount: string
  buyerName: string
  buyerTaxNo: string
  certify: 'current' | 'none'
  remark: string
  details: InvoiceDetail[]
}>({
  invoiceId: null,
  type: '增值税专用发票',
  code: '',
  no: '',
  account: '',
  date: '2026-05-01',
  sellerName: '',
  sellerTaxNo: '',
  sellerAddressPhone: '',
  sellerBankAccount: '',
  buyerName: '',
  buyerTaxNo: '',
  certify: 'none',
  remark: '',
  details: [],
})

const rules: FormRules = {
  code: [{ required: true, message: '请输入发票代码', trigger: 'blur' }],
  no: [{ required: true, message: '请输入发票号码', trigger: 'blur' }],
  account: [{ required: true, message: '请选择结算科目', trigger: 'change' }],
  date: [{ required: true, message: '请选择开票日期', trigger: 'change' }],
  sellerName: [{ required: true, message: '请输入销方名称', trigger: 'blur' }],
}

function emptyDetail(): InvoiceDetail {
  return {
    id: genId(),
    bizType: '',
    item: '',
    qty: 1,
    amount: 0,
    taxRate: 13,
    tax: 0,
    total: 0,
  }
}

function resetForm() {
  Object.assign(formModel, {
    invoiceId: null,
    type: '增值税专用发票',
    code: '',
    no: '',
    account: '',
    date: '2026-05-01',
    sellerName: '',
    sellerTaxNo: '',
    sellerAddressPhone: '',
    sellerBankAccount: '',
    buyerName: '',
    buyerTaxNo: '',
    certify: 'none',
    remark: '',
    details: [emptyDetail()],
  })
}

function calcDetail(row: InvoiceDetail) {
  row.tax = Number((row.amount * (row.taxRate / 100)).toFixed(2))
  row.total = Number((row.amount + row.tax).toFixed(2))
}

function ensureDetailComputed(row: InvoiceDetail) {
  if (row.tax > 0 && row.total > 0) return
  if (row.tax <= 0) row.tax = Number((row.amount * (row.taxRate / 100)).toFixed(2))
  if (row.total <= 0) row.total = Number((row.amount + row.tax).toFixed(2))
}

const detailTotal = computed(() => {
  return formModel.details.reduce(
    (sum, d) => ({
      amount: sum.amount + d.amount,
      tax: sum.tax + d.tax,
      total: sum.total + d.total,
    }),
    { amount: 0, tax: 0, total: 0 },
  )
})

function addDetail() {
  formModel.details.push(emptyDetail())
}

function removeDetail(idx: number) {
  if (formModel.details.length <= 1) {
    ElMessage.warning('至少保留一条明细')
    return
  }
  formModel.details.splice(idx, 1)
}

function openAdd() {
  dialogMode.value = 'add'
  resetForm()
  dialogVisible.value = true
  formRef.value?.clearValidate()
}

function openEdit(row: InvoiceRecord) {
  dialogMode.value = 'edit'
  const siblings = rows.filter((r) => r.invoiceId === row.invoiceId)
  const details: InvoiceDetail[] = siblings.map((r) => ({
    id: r.id,
    bizType: r.bizType,
    item: r.item,
    qty: r.qty,
    amount: r.amount,
    taxRate: r.taxRate,
    tax: r.tax,
    total: r.total,
  }))
  Object.assign(formModel, {
    invoiceId: row.invoiceId,
    type: row.type,
    code: row.code,
    no: row.no,
    account: row.account,
    date: row.date,
    sellerName: row.sellerName,
    sellerTaxNo: row.sellerTaxNo,
    sellerAddressPhone: row.sellerAddressPhone,
    sellerBankAccount: row.sellerBankAccount,
    buyerName: row.buyerName,
    buyerTaxNo: row.buyerTaxNo,
    certify: row.certify,
    remark: row.remark,
    details: details.length ? details : [emptyDetail()],
  })
  dialogVisible.value = true
  formRef.value?.clearValidate()
}

function buildPayload(model: typeof formModel): InvoiceCreatePayload {
  return {
    invoice_type: model.type,
    code: model.code || null,
    no: model.no,
    invoice_date: model.date || null,
    buyer_name: model.buyerName || null,
    buyer_tax_no: model.buyerTaxNo || null,
    seller_name: model.sellerName,
    seller_tax_no: model.sellerTaxNo || null,
    seller_address_phone: model.sellerAddressPhone || null,
    seller_bank_account: model.sellerBankAccount || null,
    account: model.account || null,
    certify: model.certify,
    remark: model.remark || null,
    details: model.details.map((d) => ({
      biz_type: d.bizType || null,
      item: d.item || null,
      qty: d.qty,
      amount: d.amount,
      tax_rate: d.taxRate,
      tax: d.tax,
      total: d.total,
    })),
  }
}

async function submitForm() {
  formRef.value?.validate(async (valid) => {
    if (!valid) return
    if (formModel.details.length === 0) {
      ElMessage.warning('请至少录入一条明细')
      return
    }
    for (const d of formModel.details) {
      if (!d.bizType || !d.item) {
        ElMessage.warning('请完善业务类型和开票项目')
        return
      }
      ensureDetailComputed(d)
    }

    const payload = buildPayload(formModel)
    try {
      if (dialogMode.value === 'add') {
        await invoiceApi.create(payload)
      } else if (formModel.invoiceId) {
        await invoiceApi.update(formModel.invoiceId, payload)
      }
      await loadList()
      ElMessage.success(dialogMode.value === 'add' ? '已新增' : '已保存')
      dialogVisible.value = false
    } catch (e: any) {
      if (e?.response?.status === 409) {
        ElMessage.warning(e?.response?.data?.detail || '该发票已存在，不能重复录入')
      } else {
        ElMessage.error(e?.response?.data?.detail || '保存失败')
      }
    }
  })
}

/* ============ 删除 ============ */
async function deleteRows(row?: InvoiceRecord) {
  const ids = row ? new Set([row.id]) : selectedIds.value
  if (ids.size === 0) {
    ElMessage.warning('请先勾选要删除的发票')
    return
  }
  const invoiceIds = new Set<number>()
  rows.forEach((r) => {
    if (ids.has(r.id)) invoiceIds.add(r.invoiceId)
  })
  ElMessageBox.confirm(`确定要删除选中的 ${invoiceIds.size} 张发票吗？`, '删除确认', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(async () => {
      for (const iid of invoiceIds) {
        try {
          await invoiceApi.remove(iid)
        } catch (e: any) {
          ElMessage.error(`删除发票 ${iid} 失败：${e?.response?.data?.detail || '未知错误'}`)
        }
      }
      await loadList()
      ElMessage.success(`已删除 ${invoiceIds.size} 张发票`)
    })
    .catch(() => {})
}

/* ============ 工具栏操作 ============ */
function aiRecognize() {
  openAiDialog()
}
function aiMatch() {
  ElMessage.info('AI 科目匹配功能开发中')
}
function smartFetch(cmd: string) {
  ElMessage.info(`智能取票：${cmd}`)
}

async function generateVoucher(_cmd: string) {
  const selectedInvoiceIds = new Set<number>()
  rows.forEach((r) => {
    if (selectedIds.value.has(r.id)) selectedInvoiceIds.add(r.invoiceId)
  })
  if (selectedInvoiceIds.size === 0) {
    ElMessage.warning('请先勾选要生成凭证的发票')
    return
  }
  try {
    const res = await invoiceApi.voucherDraft(Array.from(selectedInvoiceIds))
    const entries = res.data.entries
    const totalDebit = entries.reduce((s, e) => s + e.debit, 0)
    const totalCredit = entries.reduce((s, e) => s + e.credit, 0)
    const rowsText = entries
      .map((e) => `借 ${e.debit.toFixed(2)}  贷 ${e.credit.toFixed(2)}  ${e.account}`)
      .join('\n')
    ElMessageBox.alert(
      `凭证分录（${res.data.invoice_count} 张发票）：\n\n${rowsText}\n\n合计：借 ${totalDebit.toFixed(2)} / 贷 ${totalCredit.toFixed(2)}`,
      '凭证草稿',
      { confirmButtonText: '知道了' },
    )
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '生成凭证草稿失败')
  }
}

function adjustAccount() {
  if (selectedIds.value.size === 0) {
    ElMessage.warning('请先勾选要调整科目的发票')
    return
  }
  ElMessage.info('调整科目功能开发中')
}

async function handleRefresh() {
  keyword.value = ''
  selectedIds.value.clear()
  await loadList()
  ElMessage.success('已刷新')
}

function showHelp() {
  ElMessageBox.alert(
    '进项发票用于管理企业收到的增值税专用发票/普通发票：\n\n' +
      '• 发票代码 / 发票号码：纸质发票左上角和右上角信息\n' +
      '• 结算科目：该发票对应入账的会计科目\n' +
      '• 销方单位：销售方名称、税号、地址电话、开户行及账号\n' +
      '• 是否认证：专票是否在本期进行进项认证\n' +
      '• 明细：业务类型、开票项目、数量、金额、税率、税额、价税合计\n\n' +
      '勾选发票后可进行批量删除、调整科目或生成凭证。',
    '进项发票说明',
    { confirmButtonText: '知道了' },
  )
}

/* ============ 附件上传 ============ */
async function handleAttachment(row: InvoiceRecord, file?: File) {
  if (!file) return
  try {
    await invoiceApi.uploadAttachment(row.invoiceId, file)
    ElMessage.success('附件已归档')
    await loadList()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '附件上传失败')
  }
}
</script>

<template>
  <div class="invoice-input-page">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <span class="toolbar-label">期间</span>
        <el-date-picker
          v-model="period"
          type="month"
          format="YYYY年MM期"
          value-format="YYYY-MM"
          class="period-picker"
        />
        <el-input
          v-model="keyword"
          placeholder="搜索销方/发票号/科目"
          clearable
          style="width: 200px"
        />
        <el-dropdown trigger="click" @command="(c: string) => ElMessage.info(`筛选：${c}`)">
          <el-button>
            <el-icon><Filter /></el-icon>筛选<el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="全部">全部</el-dropdown-item>
              <el-dropdown-item command="已认证">已认证</el-dropdown-item>
              <el-dropdown-item command="未认证">未认证</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button text circle @click="handleRefresh">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
      <div class="toolbar-right">
        <el-button text circle @click="showHelp">
          <el-icon><QuestionFilled /></el-icon>帮助
        </el-button>
        <el-button class="ai-btn" @click="aiRecognize">
          <el-icon><MagicStick /></el-icon>AI 发票识别
        </el-button>
        <el-button class="ai-btn purple" @click="aiMatch">
          <el-icon><MagicStick /></el-icon>AI 科目匹配
        </el-button>
        <el-dropdown trigger="click" @command="smartFetch">
          <el-button type="primary">
            智能取票<el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="邮箱">邮箱取票</el-dropdown-item>
              <el-dropdown-item command="税盘">税盘取票</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button type="primary" @click="openAdd">
          <el-icon><Plus /></el-icon>新增
        </el-button>
        <el-dropdown trigger="click" @command="generateVoucher">
          <el-button>
            生成凭证(本月)<el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="本月">生成凭证（本月）</el-dropdown-item>
              <el-dropdown-item command="全部">生成凭证（全部）</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button @click="deleteRows()">
          <el-icon><Delete /></el-icon>全部删除
        </el-button>
        <el-button text circle>
          <el-icon><Setting /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 批量操作栏 -->
    <div class="batch-bar">
      <span class="selected-tip">已选中 <strong>{{ selectedIds.size }}</strong> 条</span>
      <el-button text @click="adjustAccount">
        <el-icon><EditPen /></el-icon>调整科目
      </el-button>
      <el-dropdown trigger="click" @command="generateVoucher">
        <el-button text>
          <el-icon><DocumentChecked /></el-icon>生成凭证<el-icon class="el-icon--right"><ArrowDown /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="本月">生成凭证（本月）</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
      <el-button text type="danger" @click="deleteRows()">
        <el-icon><Delete /></el-icon>删除
      </el-button>
    </div>

    <!-- 主表格 -->
    <div class="table-wrap">
      <el-table
        v-loading="loading"
        :data="filteredRows"
        border
        stripe
        size="small"
        height="100%"
        :header-cell-style="{ background: '#f5f7fa', color: '#303133', fontWeight: 600 }"
        @row-click="onRowClick"
      >
        <el-table-column width="48" align="center">
          <template #header>
            <el-checkbox
              :model-value="selectedIds.size > 0 && selectedIds.size === filteredRows.length"
              @change="(val: any) => {
                if (val) filteredRows.forEach(r => selectedIds.add(r.id))
                else selectedIds.clear()
              }"
            />
          </template>
          <template #default="{ row }">
            <el-checkbox :model-value="isSelected(row.id)" @change="toggleSelect(row, $event as unknown as Event)" />
          </template>
        </el-table-column>

        <el-table-column prop="invoiceCode" label="发票编码" width="190" show-overflow-tooltip />
        <el-table-column prop="code" label="发票代码" width="130" show-overflow-tooltip />
        <el-table-column prop="no" label="发票号码" width="110" show-overflow-tooltip />
        <el-table-column prop="bizType" label="业务类型" min-width="110" show-overflow-tooltip />
        <el-table-column prop="item" label="开票项目" min-width="150" show-overflow-tooltip />
        <el-table-column prop="account" label="结算科目" min-width="120" show-overflow-tooltip />
        <el-table-column prop="qty" label="数量" width="80" align="right" />
        <el-table-column prop="amount" label="金额" width="120" align="right">
          <template #default="{ row }">{{ row.amount.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="taxRate" label="税率(%)" width="80" align="right" />
        <el-table-column prop="tax" label="税额" width="110" align="right">
          <template #default="{ row }">{{ row.tax.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="total" label="价税合计" width="120" align="right">
          <template #default="{ row }">{{ row.total.toFixed(2) }}</template>
        </el-table-column>

        <el-table-column label="操作" width="180" fixed="right" align="center">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click.stop="openEdit(row)">编辑</el-button>
            <el-button text type="danger" size="small" @click.stop="deleteRows(row)">删除</el-button>
            <el-upload
              action="#"
              :auto-upload="false"
              :show-file-list="false"
              :on-change="(f: any) => handleAttachment(row, f.raw)"
              style="display: inline-block"
            >
              <el-button text type="success" size="small" @click.stop>归档</el-button>
            </el-upload>
          </template>
        </el-table-column>

        <template #empty>
          <el-empty description="暂无进项发票，点击「新增」添加" :image-size="80" />
        </template>
      </el-table>
    </div>

    <!-- 新增 / 编辑 弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="`${dialogMode === 'add' ? '新增' : '编辑'}进项发票`"
      class="invoice-dialog"
      width="96%"
      :close-on-click-modal="false"
      @closed="formRef?.clearValidate()"
    >
      <el-form ref="formRef" :model="formModel" :rules="rules" label-width="0" class="invoice-form">
        <!-- 发票类型 -->
        <div class="invoice-type-bar">
          <el-select v-model="formModel.type" class="invoice-type-select" popper-class="invoice-type-popper">
            <el-option v-for="t in invoiceTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </div>

        <!-- 发票头信息 -->
        <div class="invoice-header">
          <div class="form-row">
            <el-form-item prop="code" class="required">
              <template #label><span class="form-label">发票代码</span></template>
              <el-input v-model="formModel.code" placeholder="10或12位发票代码（数电票可空）" />
            </el-form-item>
            <el-form-item prop="no" class="required">
              <template #label><span class="form-label">发票号码</span></template>
              <el-input v-model="formModel.no" placeholder="8位或20位发票号码" />
            </el-form-item>
            <el-form-item prop="account" class="required">
              <template #label><span class="form-label">结算科目</span></template>
              <el-select v-model="formModel.account" placeholder="请选择" style="width: 100%">
                <el-option v-for="a in accountOptions" :key="a" :label="a" :value="a" />
              </el-select>
            </el-form-item>
            <el-form-item prop="date" class="required">
              <template #label><span class="form-label">开票日期</span></template>
              <el-date-picker v-model="formModel.date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </div>
        </div>

        <!-- 购买方单位 -->
        <div class="buyer-section">
          <div class="seller-title">购买方单位</div>
          <div class="form-row">
            <el-form-item>
              <template #label><span class="form-label">名 称</span></template>
              <el-input v-model="formModel.buyerName" placeholder="请输入购买方名称（识别自动填充）" />
            </el-form-item>
            <el-form-item>
              <template #label><span class="form-label">纳税人识别号</span></template>
              <el-input v-model="formModel.buyerTaxNo" placeholder="请输入购买方纳税人识别号" />
            </el-form-item>
          </div>
        </div>

        <!-- 销方单位 + 认证/备注 -->
        <div class="seller-section">
          <div class="seller-left">
            <div class="seller-title">销方单位</div>
            <el-form-item prop="sellerName" class="required">
              <template #label><span class="form-label">名 称</span></template>
              <el-input v-model="formModel.sellerName" placeholder="请输入名称" />
            </el-form-item>
            <el-form-item>
              <template #label><span class="form-label">纳税人识别号</span></template>
              <el-input v-model="formModel.sellerTaxNo" />
            </el-form-item>
            <el-form-item>
              <template #label><span class="form-label">地址、电话</span></template>
              <el-input v-model="formModel.sellerAddressPhone" />
            </el-form-item>
            <el-form-item>
              <template #label><span class="form-label">开户行及账号</span></template>
              <el-input v-model="formModel.sellerBankAccount" />
            </el-form-item>
          </div>
          <div class="seller-right">
            <el-form-item>
              <template #label><span class="form-label">是否认证</span></template>
              <el-radio-group v-model="formModel.certify">
                <el-radio label="current">本期认证</el-radio>
                <el-radio label="none">暂不认证</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item>
              <template #label><span class="form-label">备 注</span></template>
              <el-input v-model="formModel.remark" type="textarea" :rows="4" />
            </el-form-item>
          </div>
        </div>

        <!-- 明细表格 -->
        <div class="detail-section">
          <div class="detail-table-wrap">
          <table class="detail-table">
            <thead>
              <tr>
                <th class="required" style="width: 140px">业务类型</th>
                <th class="required" style="min-width: 180px">开票项目</th>
                <th style="width: 80px">数量</th>
                <th class="required" style="width: 130px">金额</th>
                <th class="required" style="width: 110px">税率(%)</th>
                <th class="required" style="width: 110px">税额</th>
                <th class="required" style="width: 120px">价税合计</th>
                <th style="width: 60px">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, idx) in formModel.details" :key="row.id">
                <td>
                  <el-select v-model="row.bizType" placeholder="请选择" size="small">
                    <el-option v-for="b in bizTypeOptions" :key="b" :label="b" :value="b" />
                  </el-select>
                </td>
                <td>
                  <el-input v-model="row.item" placeholder="请输入" size="small" />
                </td>
                <td>
                  <el-input-number v-model="row.qty" :min="1" :controls="false" size="small" style="width: 100%" />
                </td>
                <td>
                  <el-input-number
                    v-model="row.amount"
                    :min="0"
                    :precision="2"
                    :controls="false"
                    size="small"
                    style="width: 100%"
                    @change="calcDetail(row)"
                  />
                </td>
                <td>
                  <el-select v-model="row.taxRate" size="small" style="width: 100%" @change="calcDetail(row)">
                    <el-option v-for="r in taxRateOptions" :key="r" :label="r" :value="Number(r)" />
                  </el-select>
                </td>
                <td>
                  <el-input-number v-model="row.tax" :precision="2" :controls="false" size="small" style="width: 100%" disabled />
                </td>
                <td>
                  <el-input-number v-model="row.total" :precision="2" :controls="false" size="small" style="width: 100%" disabled />
                </td>
                <td>
                  <el-button text type="danger" size="small" @click="removeDetail(idx)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </td>
              </tr>
            </tbody>
            <tfoot>
              <tr>
                <td colspan="2" class="total-label">合计</td>
                <td></td>
                <td class="total-num">{{ detailTotal.amount.toFixed(2) }}</td>
                <td></td>
                <td class="total-num">{{ detailTotal.tax.toFixed(2) }}</td>
                <td class="total-num">{{ detailTotal.total.toFixed(2) }}</td>
                <td></td>
              </tr>
            </tfoot>
          </table>
          </div>
          <el-button text type="primary" class="add-detail-btn" @click="addDetail">
            <el-icon><Plus /></el-icon>添加明细行
          </el-button>
        </div>

        <!-- 上传附件 -->
        <div class="upload-section">
          <el-upload action="#" :auto-upload="false" :show-file-list="false">
            <el-button text>
              <el-icon><Upload /></el-icon>上传附件（请在表格行操作「归档」上传）
            </el-button>
          </el-upload>
        </div>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>

    <!-- AI 发票识别弹窗 -->
    <el-dialog
      v-model="aiDialogVisible"
      title="AI 发票识别"
      class="ai-dialog"
      width="680px"
      :close-on-click-modal="false"
    >
      <div class="ai-body">
        <!-- 上传区 -->
        <div v-if="!aiResult" class="ai-upload-area">
          <el-upload
            drag
            action="#"
            :auto-upload="false"
            :accept="aiAccept"
            :show-file-list="false"
            :on-change="onAiFileChange"
            class="ai-uploader"
          >
            <el-icon class="ai-upload-icon"><Picture /></el-icon>
            <div class="ai-upload-text">
              <p>点击或拖拽上传发票图片 / PDF</p>
              <p class="ai-upload-tip">上传后系统将自动识别并填充发票信息</p>
            </div>
          </el-upload>

          <!-- 已选文件预览 -->
          <div v-if="aiFile" class="ai-file-preview">
            <div class="ai-file-info">
              <el-icon><Document /></el-icon>
              <span class="ai-file-name">{{ aiFile.name }}</span>
              <el-button text type="danger" size="small" @click="removeAiFile">
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
            <div v-if="aiPreviewUrl && aiFile.type.startsWith('image')" class="ai-image-preview">
              <img :src="aiPreviewUrl" alt="发票预览" />
            </div>
          </div>
        </div>

        <!-- 识别中 -->
        <div v-if="aiRecognizing" class="ai-loading">
          <el-icon class="ai-spin"><Refresh /></el-icon>
          <p>AI 正在识别发票内容，请稍候…</p>
        </div>

        <!-- 识别结果 -->
        <div v-if="aiResult" class="ai-result">
          <div class="ai-result-title">
            <el-icon><DocumentChecked /></el-icon>
            <span>识别结果</span>
          </div>
          <div class="ai-result-grid">
            <div class="ai-result-item"><label>发票类型</label><span>{{ aiResult.type }}</span></div>
            <div class="ai-result-item"><label>发票代码</label><span>{{ aiResult.code }}</span></div>
            <div class="ai-result-item"><label>发票号码</label><span>{{ aiResult.no }}</span></div>
            <div class="ai-result-item"><label>开票日期</label><span>{{ aiResult.date }}</span></div>
            <div class="ai-result-item"><label>结算科目</label><span>{{ aiResult.account }}</span></div>
            <div class="ai-result-item"><label>销方名称</label><span>{{ aiResult.sellerName }}</span></div>
            <div class="ai-result-item wide"><label>销方税号</label><span>{{ aiResult.sellerTaxNo }}</span></div>
            <div class="ai-result-item"><label>购买方名称</label><span>{{ aiResult.buyerName }}</span></div>
            <div class="ai-result-item wide"><label>购买方税号</label><span>{{ aiResult.buyerTaxNo }}</span></div>
            <div class="ai-result-item wide"><label>明细</label><span>{{ aiResult.details?.[0]?.item }} × {{ aiResult.details?.[0]?.qty }}，金额 {{ aiResult.details?.[0]?.amount?.toFixed(2) }}，税额 {{ aiResult.details?.[0]?.tax?.toFixed(2) }}</span></div>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button :disabled="aiRecognizing" @click="aiDialogVisible = false">取消</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.invoice-input-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 12px 16px 0;
  box-sizing: border-box;
  background: #fff;
  overflow: hidden;
}

/* 顶部工具栏 */
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 0 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  gap: 12px;
  flex-wrap: wrap;
}
.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.toolbar-label {
  font-size: 14px;
  color: var(--el-text-color-regular);
}
.period-picker {
  width: 150px;
}

/* AI 按钮 */
.ai-btn {
  background: linear-gradient(90deg, #7c3aed 0%, #a855f7 100%);
  color: #fff;
  border: none;
}
.ai-btn:hover {
  background: linear-gradient(90deg, #6d28d9 0%, #9333ea 100%);
  color: #fff;
}
.ai-btn.purple {
  background: linear-gradient(90deg, #ec4899 0%, #f472b6 100%);
}
.ai-btn.purple:hover {
  background: linear-gradient(90deg, #db2777 0%, #ec4899 100%);
}

/* 批量操作栏 */
.batch-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 10px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
  margin-bottom: 8px;
}
.selected-tip {
  font-size: 14px;
  color: var(--el-text-color-regular);
}
.selected-tip strong {
  color: var(--el-color-primary);
}

/* 表格 */
.table-wrap {
  flex: 1;
  min-height: 0;
}

/* ====== 发票录入弹窗样式 ====== */
.invoice-form :deep(.el-form-item) {
  margin-bottom: 12px;
}
.invoice-form :deep(.el-form-item__label) {
  padding: 0 8px 0 0;
  line-height: 32px;
}
.invoice-form :deep(.el-input__inner) {
  border-radius: 0;
  border-top: none;
  border-left: none;
  border-right: none;
  border-bottom: 1px solid #d8b692;
  background: transparent;
}
.invoice-form :deep(.el-input__inner:focus) {
  border-bottom-color: #a0522d;
}
.invoice-form :deep(.el-input__wrapper) {
  box-shadow: none !important;
}
.invoice-form :deep(.el-textarea__inner) {
  border-radius: 0;
  border: 1px solid #d8b692;
  background: transparent;
}
.invoice-form :deep(.el-textarea__inner:focus) {
  border-color: #a0522d;
}
.invoice-form :deep(.el-radio__input.is-checked .el-radio__inner) {
  background-color: #409eff;
  border-color: #409eff;
}
.invoice-form :deep(.el-radio__input.is-checked + .el-radio__label) {
  color: #409eff;
}

.invoice-type-bar {
  text-align: center;
  padding: 8px 0 16px;
  border-bottom: 2px solid #a0522d;
  margin-bottom: 16px;
}
.invoice-type-select :deep(.el-input__inner) {
  font-size: 18px;
  font-weight: 600;
  color: #a0522d;
  text-align: center;
  border: none;
  width: 240px;
}

.form-label {
  color: #a0522d;
  font-size: 14px;
  white-space: nowrap;
}
.required .form-label::before {
  content: '*';
  color: #f56c6c;
  margin-right: 4px;
}

.form-row {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}
.form-row .el-form-item {
  flex: 1;
  min-width: 260px;
}

/* 购买方单位区域 */
.buyer-section {
  display: block;
  border: 1px solid #d8b692;
  padding: 16px;
  margin: 16px 0 0;
  position: relative;
}
.buyer-section .form-row {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}
.buyer-section .form-row .el-form-item {
  flex: 1;
  min-width: 260px;
}
.buyer-section :deep(.el-form-item__label) {
  width: 120px !important;
  text-align: left;
  padding-right: 8px;
  box-sizing: border-box;
}
.buyer-section :deep(.el-form-item__content) {
  margin-left: 120px !important;
}

/* 销方单位区域 */
.seller-section {
  display: flex;
  gap: 24px;
  border: 1px solid #d8b692;
  padding: 16px;
  margin: 16px 0;
  position: relative;
}
.seller-left {
  flex: 1.4;
  min-width: 420px;
}
.seller-right {
  flex: 1;
  min-width: 300px;
}
.seller-left :deep(.el-form-item__label),
.seller-right :deep(.el-form-item__label) {
  width: 120px !important;
  text-align: left;
  padding-right: 8px;
  box-sizing: border-box;
}
.seller-left :deep(.el-form-item__content),
.seller-right :deep(.el-form-item__content) {
  margin-left: 120px !important;
}
.seller-title {
  font-size: 14px;
  font-weight: 600;
  color: #a0522d;
  letter-spacing: 1px;
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px dashed #d8b692;
}
.seller-left {
  padding-left: 0;
}

/* 明细表格 */
.detail-section {
  border: 1px solid #d8b692;
  padding: 12px;
  margin-bottom: 16px;
}
.detail-table-wrap {
  overflow-x: auto;
}
.detail-table {
  width: 100%;
  min-width: 1100px;
  border-collapse: collapse;
  table-layout: fixed;
}
.detail-table th,
.detail-table td {
  border: 1px solid #d8b692;
  padding: 6px;
  text-align: center;
  font-size: 13px;
}
.detail-table th {
  color: #a0522d;
  background: #fdf8f3;
  font-weight: 600;
}
.detail-table tfoot td {
  background: #fff8e6;
  color: #a0522d;
  font-weight: 600;
}
.total-label {
  text-align: center !important;
}
.total-num {
  text-align: right !important;
  padding-right: 12px !important;
}
.add-detail-btn {
  margin-top: 8px;
}

/* 上传附件 */
.upload-section {
  padding: 8px 0;
}

/* 响应式 */
@media (max-width: 768px) {
  .seller-section {
    flex-direction: column;
  }
}

/* ====== AI 发票识别弹窗样式 ====== */
.ai-body {
  min-height: 260px;
}
.ai-uploader :deep(.el-upload-dragger) {
  width: 100%;
  padding: 40px 20px;
  border: 2px dashed #d8b692;
  border-radius: 8px;
  background: #fdf8f3;
}
.ai-uploader :deep(.el-upload-dragger:hover) {
  border-color: #a0522d;
}
.ai-upload-icon {
  font-size: 48px;
  color: #a0522d;
  margin-bottom: 12px;
}
.ai-upload-text p {
  margin: 0;
  color: #a0522d;
  font-size: 16px;
  font-weight: 500;
}
.ai-upload-tip {
  font-size: 12px !important;
  color: #999 !important;
  margin-top: 8px !important;
}
.ai-file-preview {
  margin-top: 16px;
  border: 1px solid #d8b692;
  border-radius: 6px;
  padding: 12px;
  background: #fff;
}
.ai-file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.ai-file-name {
  flex: 1;
  font-size: 14px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.ai-image-preview {
  display: flex;
  justify-content: center;
  max-height: 240px;
  overflow: hidden;
}
.ai-image-preview img {
  max-width: 100%;
  max-height: 240px;
  border-radius: 4px;
  border: 1px solid #ebeef5;
}
.ai-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  color: #a0522d;
}
.ai-loading p {
  margin-top: 12px;
  font-size: 14px;
}
.ai-spin {
  font-size: 36px;
  animation: ai-spin 1s linear infinite;
}
@keyframes ai-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.ai-result {
  border: 1px solid #d8b692;
  border-radius: 6px;
  padding: 16px;
  background: #fff;
}
.ai-result-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #a0522d;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px dashed #d8b692;
}
.ai-result-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px 24px;
}
.ai-result-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.ai-result-item.wide {
  grid-column: span 2;
}
.ai-result-item label {
  font-size: 12px;
  color: #999;
}
.ai-result-item span {
  font-size: 14px;
  color: #303133;
  word-break: break-all;
}
</style>

<!-- 弹窗根与主体：因 el-dialog 经 teleport 渲染到 body，需用非 scoped 规则控制尺寸与滚动 -->
<style>
.invoice-dialog {
  max-width: 1400px;
}
.invoice-dialog .el-dialog__header {
  padding: 16px 20px;
  margin-right: 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}
.invoice-dialog .el-dialog__title {
  color: #a0522d;
  font-weight: 600;
}
.invoice-dialog .el-dialog__body {
  max-height: 80vh;
  overflow-y: auto;
  padding: 16px 24px 8px;
  box-sizing: border-box;
}
.invoice-dialog .el-dialog__footer {
  padding: 12px 20px 16px;
  border-top: 1px solid var(--el-border-color-lighter);
}
</style>
