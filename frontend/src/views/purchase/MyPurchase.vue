<template>
  <div class="page">
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索单号/物品/事由" clearable style="width: 260px" @keyup.enter="load" @clear="load" />
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
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">查看</el-button>
          <el-button
            v-if="row.status === '已通过'"
            link
            type="primary"
            @click="payReq(row)"
          >报销</el-button>
        </template>
      </el-table-column>
    </el-table>
    </DataLoader>

    <!-- 采购申请单详情弹窗（A4 预览 + 打印） -->
    <el-dialog v-model="detailVisible" title="采购申请单" width="900px" :close-on-click-modal="false" class="detail-dialog">
      <div v-if="detailLoading" class="detail-loading">正在加载采购申请单…</div>
      <PurchasePrint v-else :purchase="detail" />
      <template #footer>
        <div class="detail-footer">
          <el-button @click="detailVisible = false">关闭</el-button>
          <el-button type="primary" @click="printPurchase">打印采购申请单</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 独立打印层：不放在 el-dialog 内，避免弹窗遮罩/transform/高度影响打印内容 -->
    <div class="print-layer">
      <PurchasePrint v-if="!detailLoading && detail.id" :purchase="detail" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { purchaseApi } from '@/api/purchase'
import { reimburseApi } from '@/api/reimburse'
import type { PurchaseReq } from '@/types/purchase'
import PurchasePrint from './PurchasePrint.vue'

const router = useRouter()
const currentUser = '沈雷'
const statusOptions = ['草稿', '待审批', '已通过', '已驳回']

const keyword = ref('')
const statusFilter = ref<string | null>(null)
const list = ref<PurchaseReq[]>([])
const loading = ref(false)

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

async function openDetail(row: PurchaseReq) {
  // 列表数据可能不含完整 items，打开打印预览时必须重新取详情。
  detailLoading.value = true
  detailVisible.value = true
  try {
    const res = await purchaseApi.get(row.id)
    Object.assign(detail, res.data)
  } catch (e: any) {
    // 详情接口失败时仍展示列表行，避免弹窗白屏。
    Object.assign(detail, row)
    ElMessage.warning(e?.response?.data?.detail || '详情加载失败，已展示列表数据')
  } finally {
    detailLoading.value = false
  }
}

function printPurchase() {
  window.print()
}

async function payReq(row: PurchaseReq) {
  try {
    await ElMessageBox.confirm(
      `确认将采购单「${row.req_no || ('#' + row.id)}」转为报销单？生成后请在「报销审批」中审核，审核通过后再执行付款（付款仅作账务调整，不实际打款）。`,
      '转报销单确认',
      { type: 'warning', confirmButtonText: '确认转换', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  try {
    const res = await reimburseApi.fromPurchase(row.id)
    ElMessage.success(`已生成报销单「${res.data.bill_no}」，请到报销审批中审核`)
    router.push('/reimburse/bill')
  } catch (e: any) {
    const status = e?.response?.status
    const detail = e?.response?.data?.detail || '操作失败'
    if (status === 409) {
      ElMessage.warning(detail + '，将跳转到报销审批列表')
      router.push('/reimburse/bill')
    } else {
      ElMessage.error(detail)
    }
  }
}

onMounted(load)
</script>

<style scoped>
.page { padding: 16px; }
.toolbar { display: flex; gap: 12px; margin-bottom: 12px; align-items: center; }
.detail-footer { display: flex; justify-content: flex-end; gap: 12px; }
.detail-loading { padding: 80px 0; text-align: center; color: #909399; }
.print-layer { display: none; }
</style>
<style>
@media print {
  body * { visibility: hidden !important; }
  .print-layer,
  .print-layer * { visibility: visible !important; }
  .print-layer {
    display: block !important;
    position: fixed !important;
    inset: 0 !important;
    z-index: 99999 !important;
    background: #fff !important;
  }
  .el-overlay { display: none !important; }
}
</style>
