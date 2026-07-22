<template>
  <div class="page">
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索单号/申请人/物品/事由" clearable style="width: 260px" @keyup.enter="load" @clear="load" />
      <el-select v-model="statusFilter" placeholder="全部状态" clearable style="width: 140px" @change="load">
        <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
      </el-select>
      <el-button type="primary" @click="openCreate">新建采购申请</el-button>
    </div>

    <el-table :data="list" border stripe v-loading="loading">
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
          <el-tag :type="statusTag(row.status)" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="approve_date" label="审批日期" width="120" />
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
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
            <el-table-column label="单价(元)" width="120">
              <template #default="{ row }">
                <el-input-number v-model="row.unit_price" :min="0" :precision="2" :controls="false" size="small" style="width: 100%" />
              </template>
            </el-table-column>
            <el-table-column label="金额(元)" width="120" align="right">
              <template #default="{ row }">
                <span class="amt">{{ itemAmount(row) }}</span>
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
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { purchaseApi } from '@/api/purchase'
import type { PurchaseReq, PurchaseItem } from '@/types/purchase'

const statusOptions = ['草稿', '待审批', '已通过', '已驳回']

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
    unit_price: null,
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

function statusTag(status: string): '' | 'success' | 'warning' | 'danger' | 'info' | 'primary' {
  switch (status) {
    case '待审批': return 'warning'
    case '已通过': return 'success'
    case '已驳回': return 'danger'
    default: return 'info'
  }
}

interface RowAction {
  action: 'submit' | 'approve' | 'reject'
  label: string
  type: 'warning' | 'success' | 'danger'
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
function itemAmount(it: PurchaseItem): string {
  const q = Number(it.quantity) || 0
  const p = Number(it.unit_price) || 0
  return '¥' + (q * p).toFixed(2)
}
// 明细合计（数量 × 单价）
const itemsTotal = computed(() =>
  (form.items || []).reduce((s, it) => s + (Number(it.quantity) || 0) * (Number(it.unit_price) || 0), 0)
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
  const items = (form.items || []).map((it) => ({
    item_name: it.item_name,
    spec: it.spec || null,
    quantity: Number(it.quantity) || 1,
    unit_price: it.unit_price != null ? Number(it.unit_price) : null,
    amount: (Number(it.quantity) || 0) * (Number(it.unit_price) || 0),
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
</style>
