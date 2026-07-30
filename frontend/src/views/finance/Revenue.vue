<script setup lang="ts">
/** 财务 · 收入：收入单 CRUD + 确认入账（联动凭证并自动审核）。 */
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { revenueApi } from '@/api/revenue'
import type { Revenue } from '@/types/finance'

const keyword = ref('')
const statusFilter = ref('')
const loading = ref(false)
const rows = ref<Revenue[]>([])

const statusOptions = ['草稿', '已确认']
const taxRateOptions = [
  { label: '13%', value: 0.13 },
  { label: '9%', value: 0.09 },
  { label: '6%', value: 0.06 },
  { label: '1%', value: 0.01 },
  { label: '免税/不征税(0%)', value: 0 },
]
const settleOptions = ['银行收讫', '应收账款']

const confirmedTotal = computed(() =>
  rows.value.filter((r) => r.status === '已确认').reduce((s, r) => s + (Number(r.total_amount) || 0), 0),
)

async function load() {
  loading.value = true
  try {
    const params: Record<string, any> = {}
    if (keyword.value.trim()) params.keyword = keyword.value.trim()
    if (statusFilter.value) params.status = statusFilter.value
    const res = await revenueApi.list(params)
    rows.value = res.data
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载收入失败')
  } finally {
    loading.value = false
  }
}
onMounted(load)

// ── 新建 / 编辑弹窗 ──
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const form = ref<Partial<Revenue>>({})

function today(): string {
  return new Date().toISOString().slice(0, 10)
}

function openCreate() {
  editingId.value = null
  form.value = {
    customer: '',
    total_amount: undefined,
    tax_rate: 0.13,
    settle_method: '银行收讫',
    revenue_date: today(),
    status: '草稿',
    remark: '',
  }
  dialogVisible.value = true
}

function openEdit(row: Revenue) {
  if (row.status === '已确认') {
    ElMessage.warning('已确认入账不可编辑，如需调整请在账簿中做调整分录')
    return
  }
  editingId.value = row.id
  form.value = { ...row }
  dialogVisible.value = true
}

async function save() {
  if (!form.value.customer?.trim()) {
    ElMessage.warning('请填写客户名称')
    return
  }
  if (!form.value.total_amount || Number(form.value.total_amount) <= 0) {
    ElMessage.warning('请填写有效的价税合计金额')
    return
  }
  saving.value = true
  try {
    if (editingId.value) {
      await revenueApi.update(editingId.value, form.value)
    } else {
      await revenueApi.create(form.value)
    }
    dialogVisible.value = false
    ElMessage.success('保存成功')
    load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function confirm(row: Revenue) {
  try {
    await revenueApi.confirm(row.id)
    ElMessage.success(`已确认并入账，凭证号 ${row.voucher_no || ''}`.trim())
    load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '确认失败')
  }
}

async function remove(row: Revenue) {
  try {
    await ElMessageBox.confirm(`确认删除收入单 ${row.bill_no || '（未生成单号）'}？`, '提示', {
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await revenueApi.remove(row.id)
    ElMessage.success('已删除')
    load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}
</script>

<template>
  <div style="padding: 16px;">
    <el-card shadow="never" style="margin-bottom: 12px;">
      <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
        <el-input
          v-model="keyword"
          placeholder="客户名称/备注"
          style="width: 200px;"
          clearable
          @clear="load"
          @keyup.enter="load"
        />
        <el-select v-model="statusFilter" placeholder="全部状态" clearable style="width: 140px;" @change="load">
          <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
        </el-select>
        <el-button type="primary" @click="load">查询</el-button>
        <el-button type="success" @click="openCreate">新建收入</el-button>
        <el-tag type="success" style="margin-left: auto;">
          已确认收入合计 ¥{{ confirmedTotal.toFixed(2) }}
        </el-tag>
      </div>
    </el-card>

    <DataLoader :loading="loading" :is-empty="!rows.length">
      <el-table :data="rows" border stripe height="560">
        <el-table-column prop="bill_no" label="单号" width="150" />
        <el-table-column prop="customer" label="客户名称" min-width="140" />
        <el-table-column label="价税合计" width="150" align="right">
          <template #default="{ row }">¥{{ Number(row.total_amount || 0).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="税率" width="90" align="center">
          <template #default="{ row }">{{ ((Number(row.tax_rate) || 0) * 100).toFixed(0) }}%</template>
        </el-table-column>
        <el-table-column prop="settle_method" label="结算方式" width="110" />
        <el-table-column prop="revenue_date" label="确认日期" width="130" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === '已确认' ? 'success' : 'info'">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="voucher_no" label="凭证号" width="160" />
        <el-table-column prop="remark" label="备注" min-width="140" show-overflow-tooltip />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === '草稿'" link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button v-if="row.status === '草稿'" link type="success" @click="confirm(row)">确认入账</el-button>
            <el-button v-if="row.status === '草稿'" link type="danger" @click="remove(row)">删除</el-button>
            <el-tag v-if="row.status === '已确认'" type="success" size="small">已入账</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </DataLoader>

    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑收入' : '新建收入'"
      width="520px"
      :close-on-click-modal="false"
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="客户名称" required>
          <el-input v-model="form.customer" placeholder="如：某某科技有限公司" />
        </el-form-item>
        <el-form-item label="价税合计" required>
          <el-input-number
            v-model="form.total_amount"
            :min="0"
            :precision="2"
            :controls="false"
            style="width: 100%;"
          />
          <div style="color: #909399; font-size: 12px; margin-top: 4px;">
            填含税总额，系统按税率自动拆出不含税收入与销项税额
          </div>
        </el-form-item>
        <el-form-item label="税率">
          <el-select v-model="form.tax_rate" style="width: 100%">
            <el-option v-for="t in taxRateOptions" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="结算方式">
          <el-select v-model="form.settle_method" style="width: 100%">
            <el-option v-for="s in settleOptions" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="确认日期">
          <el-date-picker
            v-model="form.revenue_date"
            type="date"
            value-format="YYYY-MM-DD"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
