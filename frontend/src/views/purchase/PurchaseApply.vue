<template>
  <div class="page">
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索单号/申请人/物品/事由" clearable style="width: 260px" @keyup.enter="load" @clear="load" />
      <el-select v-model="statusFilter" placeholder="全部状态" clearable style="width: 140px" @change="load">
        <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
      </el-select>
      <el-button type="primary" @click="openCreate">新建采购申请</el-button>
    </div>

    <DataLoader :loading="loading" :is-empty="!list.length">
      <el-table :data="list" border stripe>
      <el-table-column prop="req_no" label="单号" width="160" />
      <el-table-column prop="applicant" label="申请人" width="100" />
      <el-table-column prop="department" label="部门" width="110" />
      <el-table-column label="采购物品" min-width="160" show-overflow-tooltip>
        <template #default="{ row }">{{ itemSummary(row) }}</template>
      </el-table-column>
      <el-table-column label="数量" width="80" align="center">
        <template #default="{ row }">{{ totalQty(row) }}</template>
      </el-table-column>
      <el-table-column label="预计金额" width="130" align="right">
        <template #default="{ row }">{{ row.expected_amount != null ? '¥' + Number(row.expected_amount).toFixed(2) : '-' }}</template>
      </el-table-column>
      <el-table-column prop="expected_date" label="预计日期" width="120" />
      <el-table-column prop="reason" label="事由" min-width="140" show-overflow-tooltip />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <StatusTag :status="row.status" />
        </template>
      </el-table-column>
      <el-table-column prop="approve_date" label="审批日期" width="120" />
      <el-table-column label="操作" width="300" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status === '草稿' || row.status === '已驳回'" link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button
            v-for="act in transformActions(row)"
            :key="act.action"
            link
            :type="act.type"
            @click="runAction(act.action, row)"
          >{{ act.label }}</el-button>
          <el-button v-if="row.status === '草稿' || row.status === '已驳回'" link type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    </DataLoader>

    <!-- 新建/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑采购申请' : '新建采购申请'" width="860px" :close-on-click-modal="false">
      <el-form :model="form" label-width="110px">
        <!-- 抬头区 -->
        <el-form-item label="申请单号">
          <el-input :model-value="form.req_no || previewReqNo || '保存后自动生成'" disabled />
        </el-form-item>
        <el-form-item label="申请人" required>
          <el-input v-model="form.applicant" placeholder="必填" />
        </el-form-item>
        <el-form-item label="部门">
          <el-input v-model="form.department" />
        </el-form-item>
        <el-form-item label="是否归属研发项目">
          <el-radio-group v-model="form.is_rd_project">
            <el-radio label="是">是</el-radio>
            <el-radio label="否">否</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="项目编码" required v-if="form.is_rd_project === '是'">
          <el-input v-model="form.rd_project_code" placeholder="如：RD2026-001" />
        </el-form-item>
        <el-form-item label="采购事由">
          <el-input v-model="form.reason" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>

        <!-- 明细区 -->
        <el-divider content-position="left">采购明细（可一次采购多个物品 / 服务）</el-divider>
        <div class="items-wrap">
          <el-table :data="form.items" border>
            <el-table-column label="序号" width="50" align="center">
              <template #default="{ $index }">{{ $index + 1 }}</template>
            </el-table-column>
            <el-table-column label="物品 / 服务名称" min-width="170">
              <template #default="{ row }">
                <el-input v-model="row.item_name" placeholder="必填，如：研发测试用笔记本电脑" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="规格 / 型号" min-width="120">
              <template #default="{ row }">
                <el-input v-model="row.spec" size="small" placeholder="选填" />
              </template>
            </el-table-column>
            <el-table-column label="数量" width="100">
              <template #default="{ row }">
                <el-input-number v-model="row.quantity" :min="1" :controls="false" size="small" style="width: 100%" />
              </template>
            </el-table-column>
            <el-table-column label="预算金额(元)" width="140" align="right">
              <template #default="{ row }">
                <el-input-number
                  v-model="row.amount"
                  :min="0"
                  :precision="2"
                  :controls="false"
                  size="small"
                  style="width: 100%"
                />
              </template>
            </el-table-column>
            <el-table-column label="建议供应商" min-width="120">
              <template #default="{ row }">
                <el-input v-model="row.supplier" size="small" placeholder="选填" />
              </template>
            </el-table-column>
            <el-table-column label="备注" min-width="110">
              <template #default="{ row }">
                <el-input v-model="row.remark" size="small" placeholder="选填" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="70" align="center" fixed="right">
              <template #default="{ $index }">
                <el-button link type="danger" size="small" @click="removeItem($index)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="items-footer">
            <el-button type="primary" plain size="small" @click="addItem">＋ 添加明细</el-button>
            <span class="items-total">合计金额：<b>¥{{ itemsTotal.toFixed(2) }}</b></span>
          </div>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <!-- 审批弹窗（通过/驳回共用） -->
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

    <!-- 采购申请单浏览弹窗 -->
    <el-dialog
      v-model="detailVisible"
      title="采购申请单浏览"
      width="900px"
      :close-on-click-modal="false"
      class="detail-dialog"
    >
      <div v-if="detailLoading" class="detail-loading">正在加载采购申请单…</div>
      <PurchasePrint v-else :purchase="detail" />
      <template #footer>
        <div class="detail-footer">
          <el-button @click="detailVisible = false">关闭</el-button>
          <el-button type="primary" @click="printPurchase">打印采购申请单</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { purchaseApi } from '@/api/purchase'
import { reimburseApi } from '@/api/reimburse'
import type { PurchaseReq, PurchaseItem } from '@/types/purchase'
import PurchasePrint from './PurchasePrint.vue'

const router = useRouter()
const statusOptions = ['草稿', '待审批', '已通过', '已驳回', '已支付']

const keyword = ref('')
const statusFilter = ref<string | null>(null)
const list = ref<PurchaseReq[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const editing = ref(false)
const editingId = ref<number | null>(null)
const previewReqNo = ref<string | null>(null)

const approveDialogVisible = ref(false)
const approveAction = ref<'approve' | 'reject' | null>(null)

// 浏览弹窗
const detailVisible = ref(false)
const detailLoading = ref(false)
const detail = reactive<PurchaseReq>({
  id: 0,
  req_no: '',
  applicant: '',
  department: '',
  item_name: '',
  spec: '',
  quantity: 1,
  expected_amount: 0,
  supplier: '',
  expected_date: '',
  reason: '',
  status: '草稿',
  submit_date: '',
  approver: '',
  approve_date: '',
  approve_remark: '',
  is_rd_project: '否',
  rd_project_code: '',
  remark: '',
  items: [],
})
const approveRow = ref<PurchaseReq | null>(null)
const approveForm = ref({ approver: '', remark: '' })
const approveFormRef = ref<any>(null)
const approveRules = {
  approver: [{ required: true, message: '请输入审批人', trigger: 'blur' }],
}

function emptyItem(): PurchaseItem {
  return {
    item_name: '',
    spec: '',
    quantity: 1,
    amount: null,
    supplier: '',
    remark: '',
  }
}

const emptyForm = () => ({
  req_no: null as string | null,
  applicant: '沈雷',
  department: '研发部',
  item_name: '',
  spec: '',
  quantity: 1,
  expected_amount: null as number | null,
  supplier: '',
  expected_date: null as string | null,
  reason: '',
  is_rd_project: '否',
  rd_project_code: '',
  remark: '',
  items: [emptyItem()],
})
const form = reactive(emptyForm())

interface RowAction {
  action: 'submit' | 'approve' | 'reject' | 'revert' | 'to_reimburse' | 'view'
  label: string
  type: 'warning' | 'success' | 'danger' | 'info' | 'primary'
}
function transformActions(row: PurchaseReq): RowAction[] {
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
      return [
        { action: 'view', label: '浏览', type: 'info' },
        { action: 'to_reimburse', label: '转报销', type: 'primary' },
        { action: 'revert', label: '退回', type: 'info' },
      ]
    default:
      return []
  }
}

// 列表「采购物品」摘要：首项 + 多件时「等N项」
function itemSummary(row: PurchaseReq): string {
  const items = row.items && row.items.length ? row.items : null
  if (items) {
    const first = items[0].item_name || '-'
    return items.length > 1 ? `${first} 等${items.length}项` : first
  }
  return row.item_name || '-'
}
function totalQty(row: PurchaseReq): number {
  if (row.items && row.items.length) {
    return row.items.reduce((s, it) => s + (Number(it.quantity) || 0), 0)
  }
  return Number(row.quantity) || 0
}
// 明细合计：所有明细的「预算金额」之和（手填，不再自动算 数量×单价）
const itemsTotal = computed(() =>
  (form.items || []).reduce((s, it) => s + (Number(it.amount) || 0), 0)
)

function addItem() {
  form.items.push(emptyItem())
}
function removeItem(idx: number) {
  if (form.items.length <= 1) {
    ElMessage.warning('至少保留一条明细')
    return
  }
  form.items.splice(idx, 1)
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

async function openCreate() {
  Object.assign(form, emptyForm())
  editing.value = false
  editingId.value = null
  previewReqNo.value = null
  dialogVisible.value = true
  try {
    const res = await purchaseApi.nextReqNo()
    previewReqNo.value = res.data.req_no
  } catch (e) {
    console.warn('预占单号失败', e)
  }
}

function openEdit(row: PurchaseReq) {
  Object.assign(form, emptyForm(), row)
  form.items = row.items && row.items.length ? row.items.map((it) => ({ ...it })) : [emptyItem()]
  editing.value = true
  editingId.value = row.id
  previewReqNo.value = row.req_no ?? null
  dialogVisible.value = true
}

function buildPayload(): Record<string, unknown> {
  // 过滤掉没有实际内容的细项行（名称为空即视为无效）
  const items = (form.items || [])
    .filter((it) => it.item_name && it.item_name.trim())
    .map((it) => ({
      item_name: it.item_name.trim(),
      spec: it.spec || null,
      quantity: Number(it.quantity) || 1,
      amount: it.amount != null ? Number(it.amount) : null,
      supplier: it.supplier || null,
      remark: it.remark || null,
    }))
  const totalQty = items.reduce((s: number, it: any) => s + (it.quantity || 0), 0)
  const payload: Record<string, unknown> = {
    ...form,
    items,
    item_name: items[0]?.item_name || form.item_name,
    quantity: totalQty,
    expected_amount: Number(itemsTotal.value.toFixed(2)),
  }
  delete (payload as any).req_no
  if (form.req_no) payload.req_no = form.req_no
  return payload
}

async function save() {
  if (!form.applicant.trim()) {
    ElMessage.warning('请填写申请人')
    return
  }
  const items = form.items || []
  if (!items.length || !items.some((it) => it.item_name.trim())) {
    ElMessage.warning('请至少填写一条有名称的采购明细')
    return
  }
  if (form.is_rd_project === '是' && !form.rd_project_code.trim()) {
    ElMessage.warning('请填写研发项目编码')
    return
  }
  const payload = buildPayload()
  if (form.is_rd_project !== '是') payload.rd_project_code = ''
  try {
    if (editing.value && editingId.value != null) {
      await purchaseApi.update(editingId.value, payload)
      ElMessage.success('已更新')
    } else {
      if (previewReqNo.value) payload.req_no = previewReqNo.value
      await purchaseApi.create(payload)
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  }
}

async function runAction(action: RowAction['action'], row: PurchaseReq) {
  if (action === 'approve' || action === 'reject') {
    approveAction.value = action
    approveRow.value = row
    approveForm.value = { approver: '', remark: '' }
    approveDialogVisible.value = true
    return
  }
  if (action === 'revert') {
    try {
      await ElMessageBox.confirm(
        `确认退回采购申请「${row.req_no ?? row.id}」至草稿状态？退回后可修改重新提交。`,
        '退回确认',
        { type: 'warning', confirmButtonText: '确认退回', cancelButtonText: '取消' },
      )
    } catch {
      return
    }
    try {
      await purchaseApi.revert(row.id)
      ElMessage.success('已退回至草稿')
      load()
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.detail || '退回失败')
    }
    return
  }
  if (action === 'to_reimburse') {
    try {
      await ElMessageBox.confirm(
        `确认将采购申请「${row.req_no ?? row.id}」转为报销单？转后进入草稿态，可挂接发票后提交审批。`,
        '转报销确认',
        { type: 'warning', confirmButtonText: '确认转报销', cancelButtonText: '取消' },
      )
    } catch {
      return
    }
    try {
      await reimburseApi.fromPurchase(row.id)
      ElMessage.success('已生成报销单，正在跳转…')
      router.push('/purchase/reimburse')
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.detail || '转报销失败')
    }
    return
  }
  if (action === 'view') {
    openDetail(row)
    return
  }
  await purchaseApi.submit(row.id)
  ElMessage.success('已提交')
  load()
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

async function remove(row: PurchaseReq) {
  await ElMessageBox.confirm(`确认删除采购申请 ${row.req_no ?? row.id}？`, '提示', { type: 'warning' })
  await purchaseApi.remove(row.id)
  ElMessage.success('已删除')
  load()
}

async function openDetail(row: PurchaseReq) {
  detailVisible.value = true
  detailLoading.value = true
  try {
    const res = await purchaseApi.get(row.id)
    Object.assign(detail, res.data)
  } catch (e: any) {
    Object.assign(detail, row)
    ElMessage.warning(e?.response?.data?.detail || '详情加载失败，已展示列表数据')
  } finally {
    detailLoading.value = false
  }
}

function printPurchase() {
  const p = detail
  const rows = (p.items && p.items.length) ? p.items : []

  // 金额安全格式化：兼容 number / 数字字符串 / null
  const fmtMoney = (v: any, fallback = '-'): string => {
    const n = Number(v)
    return Number.isFinite(n) ? n.toFixed(2) : fallback
  }

  const moneyToChinese = (n: number): string => {
    if (!isFinite(n)) return '-'
    if (n < 0) return '负' + moneyToChinese(-n)
    if (n === 0) return '零元整'
    const intPart = Math.floor(n)
    const cents = Math.round((n - intPart) * 100)
    const digit = ['零', '壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖']
    const unit = ['', '拾', '佰', '仟']
    const secUnit = ['', '万', '亿', '兆']
    let intStr = ''
    if (intPart > 0) {
      const s = String(intPart)
      const secs: string[] = []
      for (let i = s.length; i > 0; i -= 4) secs.unshift(s.slice(Math.max(0, i - 4), i))
      let needZero = false
      secs.forEach((sec, idx) => {
        const secPos = secs.length - 1 - idx
        let secStr = ''
        let zeroInSec = false
        for (let i = 0; i < sec.length; i++) {
          const d = sec.charCodeAt(i) - 48
          const unitPos = sec.length - 1 - i
          if (d === 0) { zeroInSec = true }
          else {
            if (zeroInSec || (needZero && secStr.length > 0)) secStr += digit[0]
            secStr += digit[d] + unit[unitPos]
            zeroInSec = false
          }
        }
        if (secStr.length > 0) { intStr += secStr + secUnit[secPos]; needZero = zeroInSec }
        else if (needZero) { needZero = false }
      })
      intStr += '元'
    } else { intStr = '零元' }
    const jiao = Math.floor(cents / 10)
    const fen = cents % 10
    let decStr = ''
    if (jiao === 0 && fen === 0) { if (intPart > 0) decStr = '整' }
    else {
      if (jiao > 0) decStr += digit[jiao] + '角'
      else if (intPart > 0) decStr += digit[0]
      if (fen > 0) decStr += digit[fen] + '分'
    }
    return intStr + decStr
  }

  const amountInWords = moneyToChinese(Number(p.expected_amount != null ? p.expected_amount : 0))

  const detailRows = rows.length
    ? rows.map((it, idx) => `
      <tr>
        <td style="text-align:center;width:40px">${idx + 1}</td>
        <td class="left">${it.item_name}</td>
        <td class="left">${it.spec || '-'}</td>
        <td style="text-align:center">${it.quantity}</td>
        <td class="num">${fmtMoney(it.amount ?? 0, '0.00')}</td>
        <td class="left">${it.supplier || '-'}</td>
        <td class="left">${it.remark || '-'}</td>
      </tr>`).join('')
    : `<tr><td colspan="7" style="text-align:center;color:#999;padding:20px">暂无采购明细</td></tr>`

  const html = `<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>采购申请单</title>
<style>
@page { size: A4; margin: 8mm 12mm; }
body { font-family: 'PingFang SC','Microsoft YaHei',sans-serif; padding:0; margin:0; }
.purchase-form { width:210mm; min-height:297mm; margin:0 auto; padding:6mm 12mm; box-sizing:border-box; background:#fff; color:#000; font-size:10pt; }
.form-title { position:relative; text-align:center; border-bottom:2px solid #000; padding-bottom:8px; margin-bottom:12px; }
.company { font-size:15pt; font-weight:bold; letter-spacing:2px; }
.doc-type { font-size:17pt; font-weight:bold; margin-top:3px; }
.unit { position:absolute; right:0; top:0; font-size:9pt; color:#333; }
.section-title { font-weight:bold; margin:12px 0 5px; font-size:10pt; }
table { width:100%; border-collapse:collapse; table-layout:fixed; }
.info-table td, .detail-table th, .detail-table td, .sign-table td { border:1px solid #333; padding:3px 5px; word-break:break-all; vertical-align:middle; }
.label { background:#f2f2f2; font-weight:600; text-align:center; width:78px; font-size:10pt; }
.detail-table th { background:#f2f2f2; font-weight:600; text-align:center; font-size:10pt; }
.detail-table td { font-size:11pt; }
.base-table td { font-size:11pt; }
.num { text-align:right; font-family:'Courier New',monospace; font-size:14pt; font-weight:bold; color:#000; }
.num-strong { text-align:right; font-weight:bold; font-family:'Courier New',monospace; font-size:16pt; color:#000; }
.cn-amount { font-size:14pt; font-weight:bold; color:#000; }
.sign-table td { text-align:center; height:28px; }
.sign-row td { height:56px; }
.form-footer { margin-top:12px; font-size:9pt; color:#333; }
@media print { .no-print { display:none; } }
</style></head>
<body>
<div class="purchase-form">
  <div class="form-title">
    <div class="company">深圳市流形机器人科技有限公司</div>
    <div class="doc-type">采购申请单</div>
    <div class="unit">单位：元</div>
  </div>
  <div class="section-title">一、基本信息</div>
  <table class="info-table base-table">
    <tr>
      <td class="label">申请单号</td><td class="bill-no" style="word-break:break-all;text-align:center;font-family:'Courier New',monospace;font-size:12pt;font-weight:bold;letter-spacing:0.5px;color:#000">${p.req_no || '-'}</td>
      <td class="label">申请日期</td><td style="white-space:nowrap;text-align:center;font-size:11pt">${p.submit_date || '-'}</td>
      <td class="label">申请人</td><td>${p.applicant || '-'}</td>
    </tr>
    <tr>
      <td class="label">部门</td><td>${p.department || '-'}</td>
      <td class="label">成本中心</td><td>${p.department || '-'}</td>
      <td class="label">归属研发</td><td>${p.is_rd_project || '否'}${p.is_rd_project === '是' && p.rd_project_code ? '（' + p.rd_project_code + '）' : ''}</td>
    </tr>
    <tr><td class="label">采购事由</td><td colspan="5">${p.reason || '-'}</td></tr>
    <tr><td class="label">备注</td><td colspan="5">${p.remark || '-'}</td></tr>
  </table>
  <div class="section-title">二、采购明细</div>
  <table class="detail-table">
    <thead><tr>
      <th style="width:40px">序号</th><th>物品/服务名称</th><th style="width:120px">规格/型号</th>
      <th style="width:70px">数量</th><th style="width:120px">预算金额(元)</th>
      <th style="width:130px">建议供应商</th><th>备注</th>
    </tr></thead>
    <tbody>${detailRows}</tbody>
  </table>
  <div class="section-title">三、汇总与付款</div>
  <table class="info-table summary-table">
    <tr>
      <td class="label">采购总金额<br><span style="font-size:9pt;font-weight:normal;color:#555">（元）</span></td>
      <td class="num-strong" colspan="2">¥${fmtMoney(p.expected_amount, '0.00')}</td>
      <td class="label">金额大写</td>
      <td colspan="3" class="cn-amount">${amountInWords}</td>
    </tr>
    <tr>
      <td class="label">状态</td><td>${p.status}</td>
      <td class="label">审批人</td><td>${p.approver || '-'}</td>
      <td class="label">审批日期</td><td style="white-space:nowrap;text-align:center;font-size:11pt" colspan="2">${p.approve_date || '-'}</td>
    </tr>
    <tr><td class="label">审批意见</td><td colspan="6">${p.approve_remark || '-'}</td></tr>
  </table>
  <div class="section-title">四、审批签章</div>
  <table class="sign-table">
    <tr><td class="label">申请人</td><td class="label">项目负责人/部门负责人</td><td class="label">财务负责人</td><td class="label">总经理</td></tr>
    <tr class="sign-row"><td>${p.applicant || ''}</td><td></td><td></td><td></td></tr>
  </table>
  <div class="form-footer">备注：本单经审批通过后方可执行采购；金额以实际采购发票为准，差异应在审批意见中说明。</div>
</div>
</body></html>`

  // 使用隐藏 iframe 打印，不被浏览器弹窗拦截
  const iframe = document.createElement('iframe')
  iframe.style.cssText = 'position:fixed;top:-9999px;left:-9999px;width:0;height:0;border:none;'
  document.body.appendChild(iframe)
  const doc = iframe.contentWindow!.document
  doc.open()
  doc.write(html)
  doc.close()
  // 等 iframe 加载完成后触发打印
  iframe.contentWindow!.focus()
  iframe.contentWindow!.print()
  // 打印完后清理 iframe
  setTimeout(() => { if (iframe.parentNode) iframe.parentNode.removeChild(iframe) }, 2000)
}

onMounted(load)
</script>

<style scoped>
.page { padding: 16px; }
.toolbar { display: flex; gap: 12px; margin-bottom: 12px; }
.form-row { display: flex; gap: 16px; }
.form-row .el-form-item { flex: 1; min-width: 0; }
.items-wrap { margin-top: 4px; }
.items-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 10px;
}
.items-total { font-size: 14px; color: #303133; }
.items-total b { color: #f56c6c; font-size: 16px; }
.amt { font-family: 'Courier New', monospace; font-weight: 600; }
.detail-footer { display: flex; justify-content: flex-end; gap: 12px; }
.detail-loading { padding: 80px 0; text-align: center; color: #909399; }
</style>
