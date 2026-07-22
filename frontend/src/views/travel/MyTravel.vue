<template>
  <div class="page">
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索单号/出差地/事由" clearable style="width: 260px" @keyup.enter="load" @clear="load" />
      <el-select v-model="statusFilter" placeholder="全部状态" clearable style="width: 140px" @change="load">
        <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
      </el-select>
      <el-tag type="info" effect="plain">当前用户：{{ currentUser }}</el-tag>
    </div>

    <el-table :data="list" border stripe v-loading="loading">
      <el-table-column prop="req_no" label="单号" width="160" />
      <el-table-column prop="applicant" label="申请人" width="100" />
      <el-table-column prop="department" label="部门" width="110" />
      <el-table-column prop="traveler" label="出差人" width="100" />
      <el-table-column prop="destination" label="出差地" min-width="140" show-overflow-tooltip />
      <el-table-column label="出差期间" width="180">
        <template #default="{ row }">{{ row.travel_start || '-' }} ~ {{ row.travel_end || '-' }}</template>
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
      <el-table-column prop="approve_date" label="审批日期" width="120" />
      <el-table-column label="操作" width="90" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">查看</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 差旅申请单详情弹窗 -->
    <el-dialog v-model="detailVisible" title="差旅申请单详情" width="640px" :close-on-click-modal="false">
      <el-descriptions :column="2" border v-if="detail.id">
        <el-descriptions-item label="单号" :span="2">{{ detail.req_no || '-' }}</el-descriptions-item>
        <el-descriptions-item label="申请人">{{ detail.applicant || '-' }}</el-descriptions-item>
        <el-descriptions-item label="部门">{{ detail.department || '-' }}</el-descriptions-item>
        <el-descriptions-item label="出差人">{{ detail.traveler || '-' }}</el-descriptions-item>
        <el-descriptions-item label="出差地">{{ detail.destination || '-' }}</el-descriptions-item>
        <el-descriptions-item label="出差开始">{{ detail.travel_start || '-' }}</el-descriptions-item>
        <el-descriptions-item label="出差结束">{{ detail.travel_end || '-' }}</el-descriptions-item>
        <el-descriptions-item label="差旅预算">{{ detail.expected_amount != null ? '¥' + Number(detail.expected_amount).toFixed(2) : '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusTag(detail.status)" size="small">{{ detail.status }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="事由" :span="2">{{ detail.reason || '-' }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ detail.remark || '-' }}</el-descriptions-item>
        <el-descriptions-item label="审批人">{{ detail.approver || '-' }}</el-descriptions-item>
        <el-descriptions-item label="审批日期">{{ detail.approve_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="审批意见" :span="2">{{ detail.approve_remark || '-' }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <div class="detail-footer">
          <el-button @click="detailVisible = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { travelApi } from '@/api/travel'
import type { TravelReq } from '@/types/travel'

const currentUser = '沈雷'
const statusOptions = ['草稿', '待审批', '已通过', '已驳回']

const keyword = ref('')
const statusFilter = ref<string | null>(null)
const list = ref<TravelReq[]>([])
const loading = ref(false)

const detailVisible = ref(false)
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
  remark: '',
})

function statusTag(status: string): '' | 'success' | 'warning' | 'danger' | 'info' | 'primary' {
  switch (status) {
    case '待审批': return 'warning'
    case '已通过': return 'success'
    case '已驳回': return 'danger'
    default: return 'info'
  }
}

async function load() {
  loading.value = true
  try {
    const params: { keyword?: string; status?: string; applicant: string } = { applicant: currentUser }
    if (keyword.value) params.keyword = keyword.value
    if (statusFilter.value) params.status = statusFilter.value
    const res = await travelApi.list(params)
    list.value = res.data
  } finally {
    loading.value = false
  }
}

function openDetail(row: TravelReq) {
  Object.assign(detail, row)
  detailVisible.value = true
}

onMounted(load)
</script>

<style scoped>
.page { padding: 16px; }
.toolbar { display: flex; gap: 12px; margin-bottom: 12px; align-items: center; }
.detail-footer { display: flex; justify-content: flex-end; gap: 12px; }
</style>
