<template>
  <div class="page">
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索单号/物品/事由" clearable style="width: 260px" @keyup.enter="load" @clear="load" />
      <el-select v-model="statusFilter" placeholder="全部状态" clearable style="width: 140px" @change="load">
        <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
      </el-select>
      <el-tag type="info" effect="plain">当前用户：{{ currentUser }}</el-tag>
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
      <el-table-column label="操作" width="90" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">查看</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 采购申请单详情弹窗（A4 预览 + 打印） -->
    <el-dialog v-model="detailVisible" title="采购申请单" width="900px" :close-on-click-modal="false" class="detail-dialog">
      <PurchasePrint v-if="detail.id" :purchase="detail" />
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
import { onMounted, reactive, ref } from 'vue'
import { purchaseApi } from '@/api/purchase'
import type { PurchaseReq } from '@/types/purchase'
import PurchasePrint from './PurchasePrint.vue'

const currentUser = '沈雷'
const statusOptions = ['草稿', '待审批', '已通过', '已驳回']

const keyword = ref('')
const statusFilter = ref<string | null>(null)
const list = ref<PurchaseReq[]>([])
const loading = ref(false)

const detailVisible = ref(false)
const detail = reactive<PurchaseReq>({
  id: 0,
  req_no: '',
  applicant: '',
  department: '',
  item_name: '',
  spec: '',
  quantity: 1,
  expected_amount: null,
  supplier: '',
  expected_date: '',
  reason: '',
  status: '草稿',
  is_rd_project: '否',
  rd_project_code: '',
  remark: '',
  items: [],
})

function statusTag(status: string): '' | 'success' | 'warning' | 'danger' | 'info' | 'primary' {
  switch (status) {
    case '待审批': return 'warning'
    case '已通过': return 'success'
    case '已驳回': return 'danger'
    default: return 'info'
  }
}

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

async function load() {
  loading.value = true
  try {
    const params: { keyword?: string; status?: string; applicant: string } = { applicant: currentUser }
    if (keyword.value) params.keyword = keyword.value
    if (statusFilter.value) params.status = statusFilter.value
    const res = await purchaseApi.list(params)
    list.value = res.data
  } finally {
    loading.value = false
  }
}

function openDetail(row: PurchaseReq) {
  Object.assign(detail, row)
  detailVisible.value = true
}

function printPurchase() {
  window.print()
}

onMounted(load)
</script>

<style scoped>
.page { padding: 16px; }
.toolbar { display: flex; gap: 12px; margin-bottom: 12px; align-items: center; }
.detail-footer { display: flex; justify-content: flex-end; gap: 12px; }
</style>
