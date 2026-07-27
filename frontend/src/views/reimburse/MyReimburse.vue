<template>
  <div class="page">
    <div class="toolbar">
      <div class="toolbar-title">我的报销</div>
      <el-input v-model="applicant" placeholder="当前用户/申请人" clearable style="width: 160px" @change="load" />
      <el-select v-model="statusFilter" placeholder="全部状态" clearable style="width: 130px" @change="load">
        <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
      </el-select>
      <el-button type="primary" @click="load">刷新</el-button>
      <el-button type="success" @click="recognizeVisible = true">上传发票/重新识别</el-button>
    </div>

    <DataLoader :loading="loading" :is-empty="!list.length" :empty-description="'暂无报销单'">
      <el-table :data="list" border stripe>
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
      <el-table-column label="预算金额" width="120" align="right">
        <template #default="{ row }">
          {{ row.amount != null ? '¥' + Number(row.amount).toFixed(2) : '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="reason" label="事由" show-overflow-tooltip />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <StatusTag :status="row.status" />
        </template>
      </el-table-column>
      <el-table-column prop="submit_date" label="提交日期" width="110" />
      <el-table-column prop="approve_date" label="审批日期" width="110" />
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">查看详情</el-button>
          <el-button link type="success" @click="openAttachInvoice(row)">挂发票</el-button>
          <el-button
            v-if="row.status === '已通过'"
            link
            type="primary"
            @click="submitFinanceRow(row)"
          >提交财务</el-button>
          <el-button
            v-if="row.status === '已通过'"
            link
            type="info"
            @click="revertRow(row)"
          >退回</el-button>
          <el-button
            v-if="row.status === '已归档'"
            link
            type="success"
            @click="payRow(row)"
          >支付</el-button>
        </template>
      </el-table-column>
      </el-table>
      </DataLoader>

    <!-- 报销单详情弹窗：BillDetail 内部已用共享打印函数，差旅/采购自动适配 -->
    <el-dialog v-model="detailVisible" :title="detailTitle" width="950px" :close-on-click-modal="false" class="detail-dialog">
      <BillDetail v-if="currentBill" :bill="currentBill" />
      <template #footer>
        <div class="detail-footer">
          <el-button @click="detailVisible = false">关闭</el-button>
          <el-button
            v-if="currentBill && currentBill.status === '已通过'"
            type="primary"
            @click="submitFinanceRow(currentBill)"
          >提交财务</el-button>
          <el-button
            v-if="currentBill && currentBill.status === '已通过'"
            type="info"
            @click="revertRow(currentBill)"
          >退回</el-button>
          <el-button
            v-if="currentBill && currentBill.status === '已归档'"
            type="success"
            @click="payRow(currentBill)"
          >支付</el-button>
          <el-button type="primary" @click="printDetail">打印报销单</el-button>
        </div>
      </template>
    </el-dialog>
    <InvoiceRecognizeDialog v-model:visible="recognizeVisible" @confirm="onInvoiceConfirm" />

    <!-- 挂发票弹窗：显示完整报销单 + 来源采购单 + 细项选择 + 发票选择 -->
    <AttachInvoiceDialog
      v-model="attachVisible"
      :bill="attachBill"
      @attached="onAttached"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { reimburseApi } from '@/api/reimburse'
import type { ReimbursementBill } from '@/types/reimburse'
import BillDetail from './BillDetail.vue'
import { buildReimbursePrintDocument } from '@/utils/reimbursePrint'
import InvoiceRecognizeDialog from '@/components/InvoiceRecognizeDialog.vue'
import AttachInvoiceDialog from '@/components/AttachInvoiceDialog.vue'

const loading = ref(false)
const list = ref<ReimbursementBill[]>([])
const applicant = ref('沈雷')
const statusFilter = ref('')
const detailVisible = ref(false)
const currentBill = ref<ReimbursementBill | null>(null)
const recognizeVisible = ref(false)

// 挂发票弹窗状态
const attachVisible = ref(false)
const attachBill = ref<ReimbursementBill | null>(null)

const detailTitle = computed(() =>
  (currentBill.value?.bill_type || '采购报销') === '差旅报销' ? '差旅报销单' : '物品报销单'
)

const statusOptions = ['待审批', '已通过', '已归档', '已驳回', '已支付']

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

// 打开挂发票弹窗前先拉取最新详情（含关联发票），确保弹窗内"已挂"统计准确
async function openAttachInvoice(row: ReimbursementBill) {
  try {
    const res = await reimburseApi.get(row.id)
    attachBill.value = res.data
    attachVisible.value = true
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载报销单失败')
  }
}

function onAttached(payload: { billId: number; itemId: number | null; invoiceIds: number[] }) {
  // 关联成功后刷新列表的"发票"列（计数与金额），并同步当前详情对象
  const bill = list.value.find((b) => b.id === payload.billId)
  if (bill && currentBill.value && currentBill.value.id === payload.billId) {
    // 详情对象上的 invoices 计数刷新交给详情页逻辑（下次打开再拉），这里只刷列表缩略
    load()
  } else if (bill) {
    load()
  }
}

async function payRow(bill: ReimbursementBill) {
  try {
    await ElMessageBox.confirm(
      `确认支付报销单「${bill.bill_no || ('#' + bill.id)}」？系统将自动生成付款凭证（借：其他应付款，贷：银行存款）。`,
      '付款确认',
      { type: 'warning', confirmButtonText: '确认付款', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  try {
    await reimburseApi.pay(bill.id)
    ElMessage.success('付款成功，已生成付款凭证')
    // 同步详情与列表状态
    if (currentBill.value && currentBill.value.id === bill.id) {
      currentBill.value = { ...currentBill.value, status: '已支付' }
    }
    load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '付款失败')
  }
}

async function submitFinanceRow(bill: ReimbursementBill) {
  try {
    await ElMessageBox.confirm(
      `确认将报销单「${bill.bill_no || ('#' + bill.id)}」提交财务？提交后不可退回，将自动生成记账凭证形成待支付挂账。`,
      '提交财务确认',
      { type: 'warning', confirmButtonText: '确认提交', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  try {
    await reimburseApi.submitFinance(bill.id)
    ElMessage.success('已提交财务，生成记账凭证')
    if (currentBill.value && currentBill.value.id === bill.id) {
      currentBill.value = { ...currentBill.value, status: '已归档' }
    }
    load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '提交财务失败')
  }
}

async function revertRow(bill: ReimbursementBill) {
  try {
    await ElMessageBox.confirm(
      `确认退回报销单「${bill.bill_no || ('#' + bill.id)}」至草稿状态？退回后可修改重新提交。`,
      '退回确认',
      { type: 'warning', confirmButtonText: '确认退回', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  try {
    await reimburseApi.revert(bill.id)
    ElMessage.success('已退回至草稿')
    if (currentBill.value && currentBill.value.id === bill.id) {
      currentBill.value = { ...currentBill.value, status: '草稿' }
    }
    load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '退回失败')
  }
}

function printDetail() {
  const b = currentBill.value
  if (!b) {
    ElMessage.warning('请先打开报销单详情再打印')
    return
  }
  // 弹窗和打印共用同一份 HTML（保证屏幕上看到 = 打印出来的）
  const html = buildReimbursePrintDocument(b, detailTitle.value)

  const iframe = document.createElement('iframe')
  iframe.style.cssText = 'position:fixed;top:-9999px;left:-9999px;width:0;height:0;border:none;'
  document.body.appendChild(iframe)
  const doc = iframe.contentWindow!.document
  doc.open()
  doc.write(html)
  doc.close()
  iframe.contentWindow!.focus()
  iframe.contentWindow!.print()
  setTimeout(() => { if (iframe.parentNode) iframe.parentNode.removeChild(iframe) }, 2000)
}

onMounted(load)

function onInvoiceConfirm(parsed: any) {
  ElMessage.success(`已识别：${parsed.sellerName || ''} ¥${parsed.total || ''}。发票已存入发票箱（可在发票箱页面查看），新建报销单时可引用。`)
}
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
