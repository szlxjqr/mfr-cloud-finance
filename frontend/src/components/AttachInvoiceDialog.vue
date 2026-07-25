<template>
  <el-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    title="挂发票"
    width="960px"
    :close-on-click-modal="false"
    @open="onOpen"
  >
    <!-- 一、报销单完整内容 -->
    <div v-if="bill" class="bill-context">
      <div class="ctx-title">报销单信息</div>
      <table class="ctx-table">
        <tr>
          <td class="lbl">报销单号</td>
          <td><strong>{{ bill.bill_no || ('#' + bill.id) }}</strong></td>
          <td class="lbl">申请人</td>
          <td>{{ bill.applicant || '-' }}</td>
          <td class="lbl">部门</td>
          <td>{{ bill.department || '-' }}</td>
        </tr>
        <tr>
          <td class="lbl">报销金额</td>
          <td>¥{{ formatNum(bill.amount) }}</td>
          <td class="lbl">状态</td>
          <td>
            <el-tag size="small" :type="bill.status === '已通过' ? 'success' : 'info'">{{ bill.status || '-' }}</el-tag>
          </td>
          <td class="lbl">提交日期</td>
          <td>{{ bill.submit_date || '-' }}</td>
        </tr>
        <tr v-if="bill.reason">
          <td class="lbl">报销事由</td>
          <td colspan="5">{{ bill.reason }}</td>
        </tr>
      </table>
    </div>

    <!-- 二、来源采购单完整内容（仅采购报销且有来源时显示） -->
    <div v-if="purchase" class="bill-context purchase-context">
      <div class="ctx-title">来源采购单（采购报销的依据）</div>
      <table class="ctx-table">
        <tr>
          <td class="lbl">采购单号</td>
          <td><strong>{{ purchase.req_no || ('#' + purchase.id) }}</strong></td>
          <td class="lbl">申请人</td>
          <td>{{ purchase.applicant || '-' }}</td>
          <td class="lbl">部门</td>
          <td>{{ purchase.department || '-' }}</td>
        </tr>
        <tr>
          <td class="lbl">预计总金额</td>
          <td>¥{{ formatNum(purchase.expected_amount) }}</td>
          <td class="lbl">状态</td>
          <td>{{ purchase.status || '-' }}</td>
          <td class="lbl">归属研发</td>
          <td>{{ purchase.is_rd_project || '否' }}</td>
        </tr>
        <tr v-if="purchase.reason">
          <td class="lbl">采购事由</td>
          <td colspan="5">{{ purchase.reason }}</td>
        </tr>
      </table>
    </div>

    <!-- 三、采购细项选择 -->
    <div v-if="showItemStep" class="item-step">
      <div class="step-title">③ 请选择对应的采购细项：</div>
      <DataLoader :loading="itemLoading" :is-empty="!purchaseItems.length">
        <el-table
          :data="purchaseItems"
          border stripe size="small"
          highlight-current-row
          height="180"
          @current-change="onItemRowChange"
        >
          <el-table-column label="序号" width="55" align="center">
            <template #default="{ $index }">{{ $index + 1 }}</template>
          </el-table-column>
          <el-table-column label="物品/服务" prop="item_name" min-width="140" show-overflow-tooltip />
          <el-table-column label="规格" prop="spec" width="110" show-overflow-tooltip />
          <el-table-column label="数量" prop="quantity" width="60" align="center" />
          <el-table-column label="金额" width="100" align="right">
            <template #default="{ row }">¥{{ formatNum(row.amount) }}</template>
          </el-table-column>
          <el-table-column label="供应商" prop="supplier" min-width="100" show-overflow-tooltip />
          <el-table-column label="已挂" width="80" align="center">
            <template #default="{ row }">
              <span :class="{ 'has-invoices': (itemInvoiceCount.get(row.id) || 0) > 0 }">
                {{ itemInvoiceCount.get(row.id) || 0 }} 张
              </span>
            </template>
          </el-table-column>
        </el-table>
      </DataLoader>
      <div v-if="selectedItemId" class="item-selected-hint">
        已选细项：<strong>{{ itemNameMap[selectedItemId] || ('#' + selectedItemId) }}</strong>
        <span v-if="(itemInvoiceCount.get(selectedItemId) || 0) > 0" class="muted">（已挂 {{ itemInvoiceCount.get(selectedItemId) }} 张，可继续追加）</span>
      </div>
    </div>

    <!-- 四、发票选择（仅当选择了细项或无来源采购单时显示） -->
    <template v-if="!showItemStep || selectedItemId">
      <div class="step-title">④ 选择要挂载的发票：</div>
      <div class="link-toolbar">
        <el-input v-model="invoiceKeyword" placeholder="搜索销方/发票号" clearable style="width: 220px" @input="debounceLoadUnlinked" />
        <span class="text-muted">仅显示未关联报销单的发票</span>
      </div>
      <DataLoader :loading="invoiceLoading" :is-empty="!unlinkedInvoices.length">
        <el-table :data="unlinkedInvoices" border stripe height="300" @selection-change="handleSelectionChange">
          <el-table-column type="selection" width="48" align="center" />
          <el-table-column prop="invoice_date" label="开票日期" width="110" />
          <el-table-column prop="invoice_type" label="类型" width="120" />
          <el-table-column prop="no" label="发票号码" width="120" />
          <el-table-column prop="seller_name" label="销方名称" show-overflow-tooltip />
          <el-table-column label="金额/税额/合计" width="180" align="right">
            <template #default="{ row }">
              ¥{{ formatNum(row.total_amount) }}
              <span class="tax-hint">（税 ¥{{ formatNum(row.total_tax) }}）</span>
            </template>
          </el-table-column>
        </el-table>
      </DataLoader>
    </template>

    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">取消</el-button>
      <el-button
        type="primary"
        :disabled="(showItemStep && !selectedItemId) || selectedInvoiceIds.length === 0"
        :loading="linking"
        @click="confirmLink"
      >
        关联 {{ selectedInvoiceIds.length }} 张发票
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { invoiceApi } from '@/api/invoice'
import { purchaseApi } from '@/api/purchase'
import type { Invoice } from '@/types/invoice'
import type { ReimbursementBill } from '@/types/reimburse'
import type { PurchaseItem, PurchaseReq } from '@/types/purchase'

const props = defineProps<{
  modelValue: boolean
  bill: ReimbursementBill | null
  /** 可选：打开时预选采购细项 id（编辑弹窗里点"挂发票"按钮传入） */
  initialItemId?: number | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
  (e: 'attached', payload: { billId: number; itemId: number | null; invoiceIds: number[] }): void
}>()

// ======== 工具 ========
function formatNum(v: any): string {
  const n = Number(v)
  return isFinite(n) ? n.toFixed(2) : '0.00'
}
function toNum(v: any): number {
  if (v === null || v === undefined || v === '') return 0
  const n = Number(v)
  return isFinite(n) ? n : 0
}

// ======== 来源采购单 ========
const purchase = ref<PurchaseReq | null>(null)
const purchaseItems = ref<PurchaseItem[]>([])
const showItemStep = ref(false)
const selectedItemId = ref<number | null>(null)
const itemNameMap = ref<Record<number, string>>({})
const itemInvoiceCount = ref<Map<number, number>>(new Map())
const itemLoading = ref(false)

// ======== 发票 ========
const unlinkedInvoices = ref<(Invoice & { total_amount?: number; total_tax?: number })[]>([])
const invoiceKeyword = ref('')
const invoiceLoading = ref(false)
const selectedInvoiceIds = ref<number[]>([])
const linking = ref(false)
let invoiceTimer: ReturnType<typeof setTimeout> | null = null

// ======== 监听：bill 变化或打开时重置 ========
watch(
  () => [props.modelValue, props.bill?.id],
  () => {
    if (props.modelValue) onOpen()
  },
)

async function onOpen() {
  // 重置
  invoiceKeyword.value = ''
  selectedInvoiceIds.value = []
  selectedItemId.value = null
  purchaseItems.value = []
  itemInvoiceCount.value = new Map()
  showItemStep.value = false
  purchase.value = null

  if (!props.bill) return

  // 加载来源采购单（若有）
  if (props.bill.purchase_requisition_id) {
    await loadPurchaseContext(props.bill.purchase_requisition_id, props.bill.id)
  } else {
    // 非采购报销（差旅等）无来源采购单 → 直接显示发票选择
    loadUnlinked()
  }
}

async function loadPurchaseContext(purchaseReqId: number, billId: number) {
  itemLoading.value = true
  try {
    const [purchaseRes, linkedRes] = await Promise.all([
      purchaseApi.get(purchaseReqId),
      invoiceApi.list({ reimbursement_bill_id: billId }),
    ])
    const items: PurchaseItem[] = purchaseRes.data.items || []
    purchaseItems.value = items
    purchase.value = purchaseRes.data

    const map: Record<number, string> = {}
    items.forEach((it) => { if (it.id) map[it.id] = it.item_name })
    itemNameMap.value = map

    // 统计每个细项已挂发票数
    const counts = new Map<number, number>()
    ;(linkedRes.data || []).forEach((inv: Invoice) => {
      if (inv.purchase_requisition_item_id) {
        counts.set(inv.purchase_requisition_item_id, (counts.get(inv.purchase_requisition_item_id) || 0) + 1)
      }
    })
    itemInvoiceCount.value = counts

    showItemStep.value = items.length > 0
    if (!showItemStep.value) loadUnlinked()
    // 应用外部传入的预选细项（编辑弹窗里点"挂发票"传入）
    if (showItemStep.value && props.initialItemId && items.some((it) => it.id === props.initialItemId)) {
      selectedItemId.value = props.initialItemId
      loadUnlinked()
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载来源采购单失败')
    loadUnlinked()
  } finally {
    itemLoading.value = false
  }
}

function onItemRowChange(item: PurchaseItem) {
  selectedItemId.value = item?.id ?? null
  selectedInvoiceIds.value = []
  if (selectedItemId.value) loadUnlinked()
}

function debounceLoadUnlinked() {
  if (invoiceTimer) clearTimeout(invoiceTimer)
  invoiceTimer = setTimeout(() => loadUnlinked(), 300)
}

async function loadUnlinked() {
  invoiceLoading.value = true
  try {
    const params: { keyword?: string; unlinked: boolean } = { unlinked: true }
    if (invoiceKeyword.value.trim()) params.keyword = invoiceKeyword.value.trim()
    const res = await invoiceApi.list(params)
    unlinkedInvoices.value = (res.data || []).map((inv) => {
      const totalAmount = inv.details.reduce((s, d) => s + toNum(d.amount), 0)
      const totalTax = inv.details.reduce((s, d) => s + toNum(d.tax), 0)
      return { ...inv, total_amount: totalAmount, total_tax: totalTax }
    })
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载未关联发票失败')
  } finally {
    invoiceLoading.value = false
  }
}

function handleSelectionChange(rows: Invoice[]) {
  selectedInvoiceIds.value = rows.map((r) => r.id)
}

async function confirmLink() {
  if (!props.bill || selectedInvoiceIds.value.length === 0) return
  if (showItemStep.value && !selectedItemId.value) return
  linking.value = true
  try {
    await invoiceApi.batchLink(selectedInvoiceIds.value, props.bill.id, selectedItemId.value ?? undefined)
    ElMessage.success(`已关联 ${selectedInvoiceIds.value.length} 张发票`)
    emit('attached', {
      billId: props.bill.id,
      itemId: selectedItemId.value,
      invoiceIds: [...selectedInvoiceIds.value],
    })
    // 局部刷新 itemInvoiceCount，避免重新弹窗
    const cnt = itemInvoiceCount.value
    const inc = selectedInvoiceIds.value.length
    if (selectedItemId.value) {
      cnt.set(selectedItemId.value, (cnt.get(selectedItemId.value) || 0) + inc)
      itemInvoiceCount.value = new Map(cnt)
    }
    selectedInvoiceIds.value = []
    loadUnlinked()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '关联发票失败')
  } finally {
    linking.value = false
  }
}
</script>

<style scoped>
.bill-context {
  margin-bottom: 14px;
  padding: 10px 12px;
  background: #f8fafc;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
}
.purchase-context {
  background: #f0f7ff;
  border-color: #c6ddf7;
}
.ctx-title {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}
.ctx-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}
.ctx-table td {
  border: 1px solid #dcdfe6;
  padding: 4px 8px;
  vertical-align: middle;
}
.ctx-table td.lbl {
  background: #fff;
  color: #606266;
  font-weight: 500;
  width: 80px;
  text-align: center;
}

.item-step {
  margin-bottom: 12px;
}
.step-title {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  margin: 8px 0 8px;
}
.item-selected-hint {
  margin-top: 8px;
  padding: 6px 12px;
  background: #e6f7ff;
  border: 1px solid #91d5ff;
  border-radius: 4px;
  font-size: 13px;
  color: #303133;
}
.item-selected-hint .muted {
  margin-left: 6px;
  color: #909399;
  font-size: 12px;
}

.has-invoices {
  color: #67c23a;
  font-weight: 600;
}

.link-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.text-muted {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}
.tax-hint {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  margin-left: 4px;
}
</style>