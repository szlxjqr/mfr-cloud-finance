<template>
  <div class="page">
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索单号/出差地/事由" clearable style="width: 260px" @keyup.enter="load" @clear="load" />
      <el-select v-model="statusFilter" placeholder="全部状态" clearable style="width: 140px" @change="load">
        <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
      </el-select>
      <el-tag type="info" effect="plain">当前用户：{{ currentUser }}</el-tag>
    </div>

    <DataLoader :loading="loading" :is-empty="!list.length">
      <el-table :data="list" border stripe>
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
          <StatusTag :status="row.status" />
        </template>
      </el-table-column>
      <el-table-column prop="approve_date" label="审批日期" width="120" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">查看</el-button>
          <el-button
            v-if="row.status === '已通过'"
            link
            type="primary"
            @click="convertTravel(row)"
          >转报销</el-button>
          <el-button
            v-if="row.status === '已通过'"
            link
            type="primary"
            @click="openPrint(row)"
          >打印</el-button>
        </template>
      </el-table-column>
    </el-table>
    </DataLoader>

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
          <StatusTag :status="detail.status" />
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

    <!-- 打印预览弹窗 -->
    <el-dialog
      v-model="printVisible"
      title="差旅申请单打印预览"
      width="800px"
      :close-on-click-modal="false"
    >
      <TravelPrint v-if="printRow" :row="printRow" />
      <template #footer>
        <el-button @click="printVisible = false">关闭</el-button>
        <el-button type="primary" @click="doPrint">打印差旅申请单</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { travelApi } from '@/api/travel'
import type { TravelReq } from '@/types/travel'
import TravelPrint from './TravelPrint.vue'
import { printTravelApplication } from '@/utils/travelPrint'

const router = useRouter()
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

const printVisible = ref(false)
const printRow = ref<TravelReq | null>(null)
function openPrint(row: TravelReq) {
  printRow.value = row
  printVisible.value = true
}
function doPrint() {
  if (!printRow.value) return
  printTravelApplication(printRow.value)
}

async function convertTravel(row: TravelReq) {
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
}

onMounted(load)
</script>

<style scoped>
.page { padding: 16px; }
.toolbar { display: flex; gap: 12px; margin-bottom: 12px; align-items: center; }
.detail-footer { display: flex; justify-content: flex-end; gap: 12px; }
</style>
