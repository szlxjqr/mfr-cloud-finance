<script setup lang="ts">
/** 财务 · 股东入资：入资单 CRUD + 确认入账（联动凭证并自动审核）。 */
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { capitalContributionApi } from '@/api/capitalContribution'
import type { CapitalContribution } from '@/types/finance'

const keyword = ref('')
const statusFilter = ref('')
const loading = ref(false)
const rows = ref<CapitalContribution[]>([])

const statusOptions = ['草稿', '已确认']

const confirmedTotal = computed(() =>
  rows.value.filter((r) => r.status === '已确认').reduce((s, r) => s + (Number(r.amount) || 0), 0),
)

async function load() {
  loading.value = true
  try {
    const params: Record<string, any> = {}
    if (keyword.value.trim()) params.keyword = keyword.value.trim()
    if (statusFilter.value) params.status = statusFilter.value
    const res = await capitalContributionApi.list(params)
    rows.value = res.data
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载股东入资失败')
  } finally {
    loading.value = false
  }
}
onMounted(load)

// ── 新建 / 编辑弹窗 ──
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const form = ref<Partial<CapitalContribution>>({})

function today(): string {
  return new Date().toISOString().slice(0, 10)
}

function openCreate() {
  editingId.value = null
  form.value = {
    investor: '',
    amount: undefined,
    capital_type: '货币资金',
    receive_subject: '1002',
    contribution_date: today(),
    status: '草稿',
    remark: '',
  }
  dialogVisible.value = true
}

function openEdit(row: CapitalContribution) {
  if (row.status === '已确认') {
    ElMessage.warning('已确认入账不可编辑，如需调整请在账簿中做调整分录')
    return
  }
  editingId.value = row.id
  form.value = { ...row }
  dialogVisible.value = true
}

async function save() {
  if (!form.value.investor?.trim()) {
    ElMessage.warning('请填写股东名称')
    return
  }
  if (!form.value.amount || Number(form.value.amount) <= 0) {
    ElMessage.warning('请填写有效的入资金额')
    return
  }
  saving.value = true
  try {
    if (editingId.value) {
      await capitalContributionApi.update(editingId.value, form.value)
    } else {
      await capitalContributionApi.create(form.value)
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

async function confirm(row: CapitalContribution) {
  try {
    await capitalContributionApi.confirm(row.id)
    ElMessage.success(`已确认并入账，凭证号 ${row.voucher_no || ''}`.trim())
    load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '确认失败')
  }
}

async function remove(row: CapitalContribution) {
  try {
    await ElMessageBox.confirm(`确认删除入资单 ${row.bill_no || '（未生成单号）'}？`, '提示', {
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await capitalContributionApi.remove(row.id)
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
          placeholder="股东名称/备注"
          style="width: 200px;"
          clearable
          @clear="load"
          @keyup.enter="load"
        />
        <el-select v-model="statusFilter" placeholder="全部状态" clearable style="width: 140px;" @change="load">
          <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
        </el-select>
        <el-button type="primary" @click="load">查询</el-button>
        <el-button type="success" @click="openCreate">新建股东入资</el-button>
        <el-tag type="success" style="margin-left: auto;">
          已确认入资合计 ¥{{ confirmedTotal.toFixed(2) }}
        </el-tag>
      </div>
    </el-card>

    <DataLoader :loading="loading" :is-empty="!rows.length">
      <el-table :data="rows" border stripe height="560">
        <el-table-column prop="bill_no" label="单号" width="150" />
        <el-table-column prop="investor" label="股东名称" min-width="140" />
        <el-table-column prop="capital_type" label="入资方式" width="110" />
        <el-table-column prop="contribution_date" label="入资日期" width="130" />
        <el-table-column label="入资金额" width="150" align="right">
          <template #default="{ row }">¥{{ Number(row.amount || 0).toFixed(2) }}</template>
        </el-table-column>
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
      :title="editingId ? '编辑股东入资' : '新建股东入资'"
      width="520px"
      :close-on-click-modal="false"
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="股东名称" required>
          <el-input v-model="form.investor" placeholder="如：沈雷 / 某某投资有限公司" />
        </el-form-item>
        <el-form-item label="入资金额" required>
          <el-input-number
            v-model="form.amount"
            :min="0"
            :precision="2"
            :controls="false"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item label="入资方式">
          <el-select v-model="form.capital_type" style="width: 100%">
            <el-option label="货币资金" value="货币资金" />
            <el-option label="实物资产" value="实物资产" />
          </el-select>
        </el-form-item>
        <el-form-item label="收款科目">
          <el-select v-model="form.receive_subject" style="width: 100%">
            <el-option label="银行存款(1002)" value="1002" />
          </el-select>
        </el-form-item>
        <el-form-item label="入资日期">
          <el-date-picker
            v-model="form.contribution_date"
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
