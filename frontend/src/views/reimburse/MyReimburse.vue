<template>
  <div class="page">
    <div class="toolbar">
      <div class="toolbar-title">我的报销</div>
      <el-input v-model="applicant" placeholder="当前用户/申请人" clearable style="width: 160px" @change="load" />
      <el-select v-model="statusFilter" placeholder="全部状态" clearable style="width: 130px" @change="load">
        <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
      </el-select>
      <el-button type="primary" @click="load">刷新</el-button>
    </div>

    <el-table :data="list" border stripe v-loading="loading" empty-text="暂无报销单">
      <el-table-column prop="bill_no" label="报销单号" width="160" />
      <el-table-column prop="applicant" label="报销人" width="100" />
      <el-table-column prop="department" label="部门" width="120" show-overflow-tooltip />
      <el-table-column label="类型" width="110">
        <template #default="{ row }">
          <el-tag :type="(row.bill_type || '采购报销') === '差旅报销' ? 'warning' : 'info'" size="small">
            {{ row.bill_type || '采购报销' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="发票" width="150" align="center">
        <template #default="{ row }">
          <span v-if="row.invoices?.length">
            {{ row.invoices.length }} 张 /
            ¥{{ invoiceTotal(row).toFixed(2) }}
          </span>
          <span v-else class="text-muted">未挂票</span>
        </template>
      </el-table-column>
      <el-table-column label="报销金额" width="120" align="right">
        <template #default="{ row }">
          {{ row.amount != null ? '¥' + Number(row.amount).toFixed(2) : '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="reason" label="事由" show-overflow-tooltip />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTag(row.status)" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="submit_date" label="提交日期" width="110" />
      <el-table-column prop="approve_date" label="审批日期" width="110" />
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">查看详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 报销单详情弹窗：按报销类型渲染物品报销单 / 差旅报销单 -->
    <el-dialog v-model="detailVisible" :title="detailTitle" width="950px" :close-on-click-modal="false" class="detail-dialog">
      <BillDetail v-if="currentBill && billType(currentBill) === '采购报销'" :bill="currentBill" />
      <TravelBillDetail v-else-if="currentBill" :bill="currentBill" />
      <template #footer>
        <div class="detail-footer">
          <el-button @click="detailVisible = false">关闭</el-button>
          <el-button type="primary" @click="printDetail">打印报销单</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { reimburseApi } from '@/api/reimburse'
import type { ReimbursementBill } from '@/types/reimburse'
import BillDetail from './BillDetail.vue'
import TravelBillDetail from './TravelBillDetail.vue'

const loading = ref(false)
const list = ref<ReimbursementBill[]>([])
const applicant = ref('沈雷')
const statusFilter = ref('')
const detailVisible = ref(false)
const currentBill = ref<ReimbursementBill | null>(null)

const billType = (b: ReimbursementBill) => b.bill_type || '采购报销'
const detailTitle = computed(() =>
  (currentBill.value?.bill_type || '采购报销') === '差旅报销' ? '差旅报销单' : '物品报销单'
)

const statusOptions = ['待审批', '已通过', '已驳回', '已支付']

function statusTag(status: string) {
  const map: Record<string, string> = {
    草稿: 'info',
    待审批: 'warning',
    已通过: 'success',
    已驳回: 'danger',
    已支付: 'primary',
  }
  return map[status] || 'info'
}

function invoiceTotal(bill: ReimbursementBill): number {
  return (bill.invoices || []).reduce((sum, inv) => {
    return sum + (inv.details || []).reduce((s, d) => s + Number(d.total || 0), 0)
  }, 0)
}

async function load() {
  loading.value = true
  try {
    const params: Record<string, string> = {}
    if (applicant.value.trim()) params.applicant = applicant.value.trim()
    if (statusFilter.value) params.status = statusFilter.value
    const res = await reimburseApi.list(params)
    list.value = res.data
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

async function openDetail(row: ReimbursementBill) {
  try {
    const res = await reimburseApi.get(row.id)
    currentBill.value = res.data
    detailVisible.value = true
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载详情失败')
  }
}

function printDetail() {
  // 克隆报销单表单到独立打印窗口：
  // 彻底绕开 el-dialog 的 fixed/overflow/居中 对打印分页的干扰（它会把表单头部顶出可打印区而被裁掉）。
  const form = document.querySelector('.detail-dialog .expense-form') as HTMLElement | null
  if (!form) {
    window.print()
    return
  }

  const win = window.open('', '_blank')
  if (!win) {
    // 弹窗被拦截时的兜底：仍用整页打印
    window.print()
    return
  }

  // 收集当前页面的全部样式（dev 为 <style> 注入、生产为 <link>），保证克隆出的表单样式一致
  const styleTexts = Array.from(document.querySelectorAll('style'))
    .map((s) => s.textContent || '')
    .filter(Boolean)
  const linkHrefs = Array.from(document.querySelectorAll('link[rel="stylesheet"]')).map(
    (l) => (l as HTMLLinkElement).href
  )

  // 打印窗口专用：A4 + 整卡不跨页 + 灰度保留
  const printCss = `
    @page { size: A4; margin: 12mm; }
    html, body { margin: 0; padding: 0; background: #fff; }
    .expense-form {
      width: auto !important;
      min-height: 0 !important;
      margin: 0 !important;
      padding: 0 !important;
      box-shadow: none !important;
      print-color-adjust: exact;
      -webkit-print-color-adjust: exact;
    }
    .form-title, .section-title { break-after: avoid; page-break-after: avoid; }
    .info-table, .sign-table, .detail-table { break-inside: avoid; page-break-inside: avoid; }
    .invoice-cards { break-inside: auto; }
    .invoice-box { break-inside: avoid; page-break-inside: avoid; -webkit-column-break-inside: avoid; }
  `

  win.document.open()
  win.document.write('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">')
  win.document.write(`<title>${detailTitle.value}</title>`)
  linkHrefs.forEach((h) => win.document.write(`<link rel="stylesheet" href="${h}">`))
  styleTexts.forEach((css) => win.document.write(`<style>${css}</style>`))
  win.document.write(`<style>${printCss}</style>`)
  win.document.write('</head><body>')
  win.document.write(form.outerHTML)
  win.document.write('</body></html>')
  win.document.close()

  // 等样式与字体加载完成再打印，避免空白/错位；用守卫避免重复打印
  let printed = false
  const triggerPrint = () => {
    if (printed) return
    printed = true
    win.focus()
    win.print()
  }
  if (win.document.readyState === 'complete') {
    setTimeout(triggerPrint, 300)
  } else {
    win.onload = triggerPrint
    // 兜底：若 onload 未触发，600ms 后强制打印
    setTimeout(triggerPrint, 600)
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
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.toolbar-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-right: auto;
}
.text-muted {
  color: #909399;
}
.detail-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
