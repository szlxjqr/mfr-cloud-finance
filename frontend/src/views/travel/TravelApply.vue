<template>
  <div class="page">
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索单号/申请人/出差人/地点/事由" clearable style="width: 280px" @keyup.enter="load" @clear="load" />
      <el-select v-model="statusFilter" placeholder="全部状态" clearable style="width: 140px" @change="load">
        <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
      </el-select>
      <el-button type="primary" @click="openCreate">新建差旅申请</el-button>
    </div>

    <DataLoader :loading="loading" :is-empty="!list.length">
      <el-table :data="list" border stripe>
      <el-table-column prop="req_no" label="单号" width="160" />
      <el-table-column prop="applicant" label="申请人" width="100" />
      <el-table-column prop="traveler" label="出差人" width="100" />
      <el-table-column prop="destination" label="出差地点" width="160" show-overflow-tooltip />
      <el-table-column label="出差起止" width="200">
        <template #default="{ row }">
          <span v-if="row.travel_start || row.travel_end">{{ row.travel_start || '-' }} 至 {{ row.travel_end || '-' }}</span>
          <span v-else class="text-muted">-</span>
        </template>
      </el-table-column>
      <el-table-column label="差旅预算" width="130" align="right">
        <template #default="{ row }">{{ row.expected_amount != null ? '¥' + Number(row.expected_amount).toFixed(2) : '-' }}</template>
      </el-table-column>
      <el-table-column prop="reason" label="事由" min-width="140" show-overflow-tooltip />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <StatusTag :status="row.status" />
        </template>
      </el-table-column>
      <el-table-column prop="approve_date" label="审批日期" width="120" />
      <el-table-column label="操作" width="240" fixed="right">
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
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑差旅申请' : '新建差旅申请'" width="720px" :close-on-click-modal="false">
      <el-form :model="form" label-width="100px">
        <el-form-item label="申请单号">
          <el-input :model-value="form.req_no || previewReqNo || '保存后自动生成'" disabled />
        </el-form-item>
        <el-form-item label="申请人" required>
          <el-input v-model="form.applicant" placeholder="必填" />
        </el-form-item>
        <el-form-item label="部门">
          <el-select v-model="form.department" placeholder="请选择部门" clearable style="width: 100%">
            <el-option v-for="d in DEPARTMENTS" :key="d" :label="d" :value="d" />
          </el-select>
        </el-form-item>
        <el-form-item label="出差人">
          <el-input v-model="form.traveler" placeholder="出差人员姓名（可与申请人不同）" />
        </el-form-item>
        <el-form-item label="出差地点">
          <el-input v-model="form.destination" placeholder="如：赣州、南昌" />
        </el-form-item>
        <el-form-item label="出差起止">
          <el-date-picker
            v-model="travelRange"
            type="daterange"
            range-separator="至"
            start-placeholder="出发日期"
            end-placeholder="返回日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="差旅预算">
          <el-input v-model.number="form.expected_amount" type="number" placeholder="0.00" />
        </el-form-item>
        <el-form-item label="是否研发">
          <el-radio-group v-model="form.is_rd_project">
            <el-radio value="是">是</el-radio>
            <el-radio value="否">否</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="form.is_rd_project === '是'" label="研发项目编码">
          <el-input v-model="form.rd_project_code" placeholder="如 RD-2026-001" />
        </el-form-item>
        <el-form-item label="出差事由">
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

    <!-- 审批弹窗 -->
    <el-dialog
      v-model="approveDialogVisible"
      :title="approveAction === 'approve' ? '审批通过' : '驳回差旅申请'"
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

    <!-- 差旅申请单浏览弹窗 -->
    <el-dialog
      v-model="detailVisible"
      title="差旅申请单浏览"
      width="900px"
      :close-on-click-modal="false"
      class="detail-dialog"
    >
      <div v-if="detailLoading" class="detail-loading">正在加载差旅申请单…</div>
      <TravelPrint v-else-if="detail.id" :row="detail" />
      <template #footer>
        <div class="detail-footer">
          <el-button @click="detailVisible = false">关闭</el-button>
          <el-button type="primary" @click="doPrint">打印差旅申请单</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { travelApi } from '@/api/travel'
import type { TravelReq } from '@/types/travel'
import TravelPrint from './TravelPrint.vue'
import { printTravelApplication } from '@/utils/travelPrint'

const router = useRouter()

const statusOptions = ['草稿', '待审批', '已通过', '已驳回']
const DEPARTMENTS = ['总经办', '综合办', '研发部', '市场部']

const keyword = ref('')
const statusFilter = ref<string | null>(null)
const list = ref<TravelReq[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const editing = ref(false)
const editingId = ref<number | null>(null)
const previewReqNo = ref<string | null>(null)

const approveDialogVisible = ref(false)
const approveAction = ref<'approve' | 'reject' | null>(null)
const approveRow = ref<TravelReq | null>(null)
const approveForm = ref({ approver: '', remark: '' })
const approveFormRef = ref<any>(null)
const approveRules = {
  approver: [{ required: true, message: '请输入审批人', trigger: 'blur' }],
}

// 浏览弹窗：内嵌打印，采购申请同款
const detailVisible = ref(false)
const detailLoading = ref(false)
const detail = reactive<TravelReq>({
  id: 0,
  req_no: '',
  applicant: '',
  department: '',
  traveler: '',
  destination: '',
  travel_start: '',
  travel_end: '',
  expected_amount: null,
  reason: '',
  status: '草稿',
  is_rd_project: '否',
  rd_project_code: '',
  remark: '',
})
async function viewDetail(row: TravelReq) {
  detailVisible.value = true
  detailLoading.value = true
  try {
    const res = await travelApi.get(row.id)
    Object.assign(detail, res.data)
  } catch (e: any) {
    Object.assign(detail, row)
    ElMessage.warning(e?.response?.data?.detail || '详情加载失败，已展示列表数据')
  } finally {
    detailLoading.value = false
  }
}
function doPrint() {
  printTravelApplication(detail)
}

const emptyForm = () => ({
  req_no: null as string | null,
  applicant: '沈雷',
  department: '',
  traveler: '',
  destination: '',
  travel_start: null as string | null,
  travel_end: null as string | null,
  expected_amount: null as number | null,
  reason: '',
  is_rd_project: '否',
  rd_project_code: '',
  remark: '',
})
const form = reactive(emptyForm())

// 出差起止日期区间：与 travel_start / travel_end 双向联动
const travelRange = computed<string[]>({
  get: () => [form.travel_start || '', form.travel_end || ''],
  set: (v) => {
    form.travel_start = v?.[0] || null
    form.travel_end = v?.[1] || null
  },
})

interface RowAction {
  action: 'submit' | 'approve' | 'reject' | 'revert' | 'convert' | 'view'
  label: string
  type: 'warning' | 'success' | 'danger' | 'primary' | 'info'
}
function transformActions(row: TravelReq): RowAction[] {
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
        { action: 'convert', label: '转报销', type: 'primary' },
        { action: 'revert', label: '退回', type: 'info' },
      ]
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
    const res = await travelApi.list(params)
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
    const res = await travelApi.nextReqNo()
    previewReqNo.value = res.data.req_no
  } catch (e) {
    console.warn('预占单号失败', e)
  }
}

function openEdit(row: TravelReq) {
  Object.assign(form, emptyForm(), row)
  editing.value = true
  editingId.value = row.id
  previewReqNo.value = row.req_no ?? null
  dialogVisible.value = true
}

async function save() {
  if (!form.applicant.trim()) {
    ElMessage.warning('请填写申请人')
    return
  }
  const payload: Record<string, unknown> = { ...form }
  if (payload.expected_amount === '' || payload.expected_amount === null) payload.expected_amount = null
  try {
    if (editing.value && editingId.value != null) {
      await travelApi.update(editingId.value, payload)
      ElMessage.success('已更新')
    } else {
      if (previewReqNo.value && !payload.req_no) payload.req_no = previewReqNo.value
      await travelApi.create(payload)
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  }
}

async function runAction(action: RowAction['action'], row: TravelReq) {
  if (action === 'approve' || action === 'reject') {
    approveAction.value = action
    approveRow.value = row
    approveForm.value = { approver: '', remark: '' }
    approveDialogVisible.value = true
    return
  }
  if (action === 'revert') {
    await travelApi.revert(row.id)
    ElMessage.success('已退回草稿')
    load()
    return
  }
  if (action === 'view') {
    viewDetail(row)
    return
  }
  if (action === 'convert') {
    try {
      await ElMessageBox.confirm(
        `确认将差旅申请单「${row.req_no || ('#' + row.id)}」转为报销单？生成后进入草稿态，可挂接发票后提交审批。`,
        '转报销单确认',
        { type: 'warning', confirmButtonText: '确认转换', cancelButtonText: '取消' },
      )
    } catch {
      return
    }
    try {
      const res = await travelApi.convertTravel(row.id)
      ElMessage.success(`已生成报销单「${res.data.bill_no}」，请挂接发票后提交`)
      router.push('/travel/reimburse')
    } catch (e: any) {
      const status = e?.response?.status
      const errDetail = e?.response?.data?.detail || '操作失败'
      if (status === 409) {
        ElMessage.warning(errDetail + '，将跳转到差旅报销列表')
        router.push('/travel/reimburse')
      } else {
        ElMessage.error(errDetail)
      }
    }
    return
  }
  await travelApi.submit(row.id)
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
      await travelApi.approve(row.id, data)
      ElMessage.success('审批通过')
    } else {
      await travelApi.reject(row.id, data)
      ElMessage.success('已驳回')
    }
    approveDialogVisible.value = false
    load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '操作失败')
  }
}

async function remove(row: TravelReq) {
  await ElMessageBox.confirm(`确认删除差旅申请 ${row.req_no ?? row.id}？`, '提示', { type: 'warning' })
  await travelApi.remove(row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
</script>

<style scoped>
.page { padding: 16px; }
.toolbar { display: flex; gap: 12px; margin-bottom: 12px; }
.text-muted { color: var(--el-text-color-secondary); }
.detail-footer { display: flex; justify-content: flex-end; gap: 12px; }
.detail-loading { padding: 80px 0; text-align: center; color: var(--text-muted); }
</style>
