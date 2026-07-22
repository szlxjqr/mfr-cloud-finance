<template>
  <div class="page">
    <div class="toolbar">
      <el-select v-model="statusFilter" placeholder="审批状态" clearable style="width: 160px" @change="load">
        <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
      </el-select>
      <el-input v-model="keyword" placeholder="搜索单号/申请人/出差人/地点/事由" clearable style="width: 280px" @keyup.enter="load" @clear="load" />
      <span class="text-muted">默认显示「待审批」</span>
    </div>

    <el-table :data="list" border stripe v-loading="loading">
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
          <el-tag :type="statusTag(row.status)" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
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
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { travelApi } from '@/api/travel'
import type { TravelReq } from '@/types/travel'

const statusOptions = ['待审批', '已通过', '已驳回']

const keyword = ref('')
const statusFilter = ref<string | null>('待审批')
const list = ref<TravelReq[]>([])
const loading = ref(false)

const approveDialogVisible = ref(false)
const approveAction = ref<'approve' | 'reject' | null>(null)
const approveRow = ref<TravelReq | null>(null)
const approveForm = ref({ approver: '', remark: '' })
const approveFormRef = ref<any>(null)
const approveRules = {
  approver: [{ required: true, message: '请输入审批人', trigger: 'blur' }],
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
function rowActions(row: TravelReq): RowAction[] {
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
    const res = await travelApi.list(params)
    list.value = res.data
  } finally {
    loading.value = false
  }
}

function runAction(action: RowAction['action'], row: TravelReq) {
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

onMounted(load)
</script>

<style scoped>
.page { padding: 16px; }
.toolbar { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.text-muted { color: var(--el-text-color-secondary); font-size: 13px; }
</style>
