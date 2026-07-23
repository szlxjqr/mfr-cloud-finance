<template>
  <div class="page">
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索单号/员工/部门" clearable style="width: 240px" @keyup.enter="load" @clear="load" />
      <el-select v-model="statusFilter" placeholder="全部状态" clearable style="width: 140px" @change="load">
        <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
      </el-select>
      <el-select v-model="periodFilter" placeholder="全部月份" clearable filterable style="width: 150px" @change="load">
        <el-option v-for="p in periodOptions" :key="p" :label="p" :value="p" />
      </el-select>
      <el-button type="primary" @click="openCreate">新建工资单</el-button>
    </div>

    <el-table :data="list" border stripe v-loading="loading">
      <el-table-column prop="salary_no" label="单号" width="150" />
      <el-table-column prop="employee_name" label="员工" width="100" />
      <el-table-column prop="department" label="部门" width="120" />
      <el-table-column prop="period" label="工资月份" width="110" align="center" />
      <el-table-column label="应发" width="120" align="right">
        <template #default="{ row }">{{ fmt(row.gross_pay) }}</template>
      </el-table-column>
      <el-table-column label="代扣" width="120" align="right">
        <template #default="{ row }">{{ fmt(row.deduct_total) }}</template>
      </el-table-column>
      <el-table-column label="实发" width="120" align="right">
        <template #default="{ row }">
          <span style="font-weight: 600; color: var(--el-color-success)">{{ fmt(row.net_pay) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="statusTag(row.status)" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="approve_date" label="审核日期" width="110" />
      <el-table-column prop="pay_date" label="发放日期" width="110" />
      <el-table-column label="操作" width="320" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openView(row)">查看</el-button>
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button
            v-for="act in rowActions(row)"
            :key="act.action"
            link
            :type="act.type"
            @click="runAction(act.action, row)"
          >{{ act.label }}</el-button>
          <el-button link type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新建 / 编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑工资单' : '新建工资单'" width="760px" :close-on-click-modal="false">
      <el-form :model="form" label-width="110px">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="工资单编号">
              <el-input :model-value="form.salary_no || previewNo || '保存后自动生成'" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="工资月份" required>
              <el-date-picker v-model="form.period" type="month" value-format="YYYY-MM" placeholder="选择月份" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="员工姓名" required>
              <el-input v-model="form.employee_name" placeholder="必填" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="工号">
              <el-input v-model="form.employee_no" placeholder="选填" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="部门">
          <el-input v-model="form.department" placeholder="选填" />
        </el-form-item>

        <el-divider content-position="left">应发构成</el-divider>
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="基本工资"><el-input-number v-model="form.base_salary" :min="0" :precision="2" :controls="false" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="绩效"><el-input-number v-model="form.performance" :min="0" :precision="2" :controls="false" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="加班"><el-input-number v-model="form.overtime" :min="0" :precision="2" :controls="false" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="奖金/补贴"><el-input-number v-model="form.bonus" :min="0" :precision="2" :controls="false" style="width: 100%" /></el-form-item></el-col>
        </el-row>

        <el-divider content-position="left">代扣（个人部分）</el-divider>
        <el-row :gutter="12" style="margin-bottom: 8px">
          <el-col :span="24" style="text-align: right">
            <el-button size="small" @click="calcBySetting" :loading="calcLoading">
              按设置自动计算（社保/公积金/个税）
            </el-button>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="8"><el-form-item label="社保"><el-input-number v-model="form.social_personal" :min="0" :precision="2" :controls="false" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="公积金"><el-input-number v-model="form.fund_personal" :min="0" :precision="2" :controls="false" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="个税"><el-input-number v-model="form.tax_personal" :min="0" :precision="2" :controls="false" style="width: 100%" /></el-form-item></el-col>
        </el-row>

        <el-alert
          type="info"
          :closable="false"
          show-icon
          style="margin-top: 4px"
          :title="`应发 ¥${fmt(derived.gross)} ｜ 代扣 ¥${fmt(derived.deduct)} ｜ 实发 ¥${fmt(derived.net)}`"
        />
        <el-form-item label="备注" style="margin-top: 12px">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <!-- 审批弹窗 -->
    <el-dialog
      v-model="approveDialogVisible"
      :title="approveAction === 'approve' ? '审批通过' : '驳回工资单'"
      width="420px"
      :close-on-click-modal="false"
    >
      <el-form ref="approveFormRef" :model="approveForm" :rules="approveRules" label-width="90px">
        <el-form-item label="工资单号">
          <el-input :model-value="approveRow?.salary_no ?? approveRow?.id" disabled />
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

    <!-- 发放弹窗 -->
    <el-dialog v-model="payDialogVisible" title="发放工资" width="420px" :close-on-click-modal="false">
      <el-form ref="payFormRef" :model="payForm" :rules="payRules" label-width="90px">
        <el-form-item label="工资单号">
          <el-input :model-value="payRow?.salary_no ?? payRow?.id" disabled />
        </el-form-item>
        <el-form-item label="实发金额">
          <el-input :model-value="fmt(payRow?.net_pay)" disabled />
        </el-form-item>
        <el-form-item label="发放人" prop="approver">
          <el-input v-model="payForm.approver" placeholder="请输入发放人姓名" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="payForm.remark" type="textarea" :rows="3" placeholder="选填" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="payDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitPay">确认发放</el-button>
      </template>
    </el-dialog>

    <!-- 详情弹窗 -->
    <el-dialog v-model="viewVisible" title="工资单详情" width="680px" :close-on-click-modal="false">
      <el-descriptions v-if="viewRow" :column="2" border>
        <el-descriptions-item label="单号">{{ viewRow.salary_no }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusTag(viewRow.status)" size="small">{{ viewRow.status }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="员工">{{ viewRow.employee_name }}</el-descriptions-item>
        <el-descriptions-item label="工号">{{ viewRow.employee_no || '-' }}</el-descriptions-item>
        <el-descriptions-item label="部门">{{ viewRow.department || '-' }}</el-descriptions-item>
        <el-descriptions-item label="工资月份">{{ viewRow.period }}</el-descriptions-item>
        <el-descriptions-item label="基本工资">{{ fmt(viewRow.base_salary) }}</el-descriptions-item>
        <el-descriptions-item label="绩效">{{ fmt(viewRow.performance) }}</el-descriptions-item>
        <el-descriptions-item label="加班">{{ fmt(viewRow.overtime) }}</el-descriptions-item>
        <el-descriptions-item label="奖金/补贴">{{ fmt(viewRow.bonus) }}</el-descriptions-item>
        <el-descriptions-item label="应发" :span="2"><strong>{{ fmt(viewRow.gross_pay) }}</strong></el-descriptions-item>
        <el-descriptions-item label="社保(个人)">{{ fmt(viewRow.social_personal) }}</el-descriptions-item>
        <el-descriptions-item label="公积金(个人)">{{ fmt(viewRow.fund_personal) }}</el-descriptions-item>
        <el-descriptions-item label="个税(个人)">{{ fmt(viewRow.tax_personal) }}</el-descriptions-item>
        <el-descriptions-item label="代扣合计">{{ fmt(viewRow.deduct_total) }}</el-descriptions-item>
        <el-descriptions-item label="实发" :span="2"><strong style="color: var(--el-color-success)">{{ fmt(viewRow.net_pay) }}</strong></el-descriptions-item>
        <el-descriptions-item label="审批人">{{ viewRow.approver || '-' }}</el-descriptions-item>
        <el-descriptions-item label="审批意见">{{ viewRow.approve_remark || '-' }}</el-descriptions-item>
        <el-descriptions-item label="发放人">{{ viewRow.payee || '-' }}</el-descriptions-item>
        <el-descriptions-item label="备注">{{ viewRow.remark || '-' }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="viewVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { salaryApi } from '@/api/salary'
import type { SalaryBill } from '@/types/salary'

const statusOptions = ['草稿', '待审批', '已通过', '已驳回', '已发放']

const keyword = ref('')
const statusFilter = ref<string | null>(null)
const periodFilter = ref<string | null>(null)
const periodOptions = ref<string[]>([])
const list = ref<SalaryBill[]>([])
const loading = ref(false)

const dialogVisible = ref(false)
const editing = ref(false)
const editingId = ref<number | null>(null)
const previewNo = ref<string | null>(null)

const approveDialogVisible = ref(false)
const approveAction = ref<'approve' | 'reject' | null>(null)
const approveRow = ref<SalaryBill | null>(null)
const approveForm = ref({ approver: '', remark: '' })
const approveFormRef = ref<any>(null)
const approveRules = {
  approver: [{ required: true, message: '请输入审批人', trigger: 'blur' }],
}

const payDialogVisible = ref(false)
const payRow = ref<SalaryBill | null>(null)
const payForm = ref({ approver: '', remark: '' })
const payFormRef = ref<any>(null)
const payRules = {
  approver: [{ required: true, message: '请输入发放人', trigger: 'blur' }],
}

const viewVisible = ref(false)
const viewRow = ref<SalaryBill | null>(null)

const calcLoading = ref(false)
async function calcBySetting() {
  calcLoading.value = true
  try {
    const res = await salaryApi.calcDeductions({
      base_salary: toNum(form.base_salary),
      performance: toNum(form.performance),
      overtime: toNum(form.overtime),
      bonus: toNum(form.bonus),
    })
    const d = res.data
    form.social_personal = d.social_personal as number
    form.fund_personal = d.fund_personal as number
    form.tax_personal = d.tax_personal as number
    ElMessage.success('已按当前工资设置计算代扣')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '计算失败，请先在「工资设置」配置比例')
  } finally {
    calcLoading.value = false
  }
}

function emptyForm() {
  return {
    salary_no: null as string | null,
    employee_name: '',
    employee_no: '' as string | null,
    department: '' as string | null,
    period: '' as string,
    base_salary: 0 as number | null,
    performance: 0 as number | null,
    overtime: 0 as number | null,
    bonus: 0 as number | null,
    social_personal: 0 as number | null,
    fund_personal: 0 as number | null,
    tax_personal: 0 as number | null,
    remark: '' as string | null,
  }
}
const form = reactive(emptyForm())

function toNum(v: any): number {
  if (v === null || v === undefined || v === '') return 0
  const n = Number(v)
  return Number.isFinite(n) ? n : 0
}

const derived = computed(() => {
  const gross = toNum(form.base_salary) + toNum(form.performance) + toNum(form.overtime) + toNum(form.bonus)
  const deduct = toNum(form.social_personal) + toNum(form.fund_personal) + toNum(form.tax_personal)
  return { gross, deduct, net: gross - deduct }
})

function fmt(v: any): string {
  return '¥' + toNum(v).toFixed(2)
}

function statusTag(status: string): '' | 'success' | 'warning' | 'danger' | 'info' | 'primary' {
  switch (status) {
    case '待审批': return 'warning'
    case '已通过': return 'success'
    case '已驳回': return 'danger'
    case '已发放': return 'primary'
    default: return 'info'
  }
}

interface RowAction {
  action: 'submit' | 'approve' | 'reject' | 'pay'
  label: string
  type: 'warning' | 'success' | 'danger' | 'primary'
}
function rowActions(row: SalaryBill): RowAction[] {
  switch (row.status) {
    case '草稿':
    case '已驳回':
      return [{ action: 'submit', label: '提交', type: 'warning' }]
    case '待审批':
      return [
        { action: 'approve', label: '通过', type: 'success' },
        { action: 'reject', label: '驳回', type: 'danger' },
      ]
    case '已通过':
      return [{ action: 'pay', label: '发放', type: 'primary' }]
    default:
      return []
  }
}

async function load() {
  loading.value = true
  try {
    const params: { keyword?: string; status?: string; period?: string } = {}
    if (keyword.value) params.keyword = keyword.value
    if (statusFilter.value) params.status = statusFilter.value
    if (periodFilter.value) params.period = periodFilter.value
    const res = await salaryApi.list(params)
    list.value = res.data
    const ps = Array.from(new Set(res.data.map((b) => b.period).filter(Boolean))) as string[]
    ps.sort()
    periodOptions.value = ps
  } finally {
    loading.value = false
  }
}

async function openCreate() {
  Object.assign(form, emptyForm())
  editing.value = false
  editingId.value = null
  previewNo.value = null
  dialogVisible.value = true
  try {
    const res = await salaryApi.nextSalaryNo()
    previewNo.value = res.data.salary_no
  } catch (e) {
    console.warn('预占单号失败', e)
  }
}

function openEdit(row: SalaryBill) {
  Object.assign(form, emptyForm(), row, {
    base_salary: toNum(row.base_salary),
    performance: toNum(row.performance),
    overtime: toNum(row.overtime),
    bonus: toNum(row.bonus),
    social_personal: toNum(row.social_personal),
    fund_personal: toNum(row.fund_personal),
    tax_personal: toNum(row.tax_personal),
  })
  editing.value = true
  editingId.value = row.id
  previewNo.value = row.salary_no ?? null
  dialogVisible.value = true
}

async function save() {
  if (!form.employee_name || !form.employee_name.trim()) {
    ElMessage.warning('请填写员工姓名')
    return
  }
  if (!form.period) {
    ElMessage.warning('请选择工资月份')
    return
  }
  const payload: Record<string, unknown> = {
    employee_name: form.employee_name.trim(),
    employee_no: form.employee_no || null,
    department: form.department || null,
    period: form.period,
    base_salary: toNum(form.base_salary),
    performance: toNum(form.performance),
    overtime: toNum(form.overtime),
    bonus: toNum(form.bonus),
    social_personal: toNum(form.social_personal),
    fund_personal: toNum(form.fund_personal),
    tax_personal: toNum(form.tax_personal),
    remark: form.remark || null,
  }
  if (previewNo.value && !editing.value && !payload.salary_no) {
    payload.salary_no = previewNo.value
  }
  try {
    if (editing.value && editingId.value != null) {
      await salaryApi.update(editingId.value, payload)
      ElMessage.success('已更新')
    } else {
      await salaryApi.create(payload)
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    await load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  }
}

async function runAction(action: RowAction['action'], row: SalaryBill) {
  if (action === 'approve' || action === 'reject') {
    approveAction.value = action
    approveRow.value = row
    approveForm.value = { approver: '', remark: '' }
    approveDialogVisible.value = true
    return
  }
  if (action === 'pay') {
    payRow.value = row
    payForm.value = { approver: '', remark: '' }
    payDialogVisible.value = true
    return
  }
  if (action === 'submit') {
    await ElMessageBox.confirm(`确认提交工资单 ${row.salary_no ?? row.id}？提交后一人公司自动审核通过并存证。`, '提示', { type: 'warning' })
    await salaryApi.submit(row.id)
    ElMessage.success('已提交并自动审核')
    await load()
  }
}

async function submitApprove() {
  if (!approveFormRef.value) return
  await approveFormRef.value.validate()
  if (!approveRow.value || !approveAction.value) return
  const data = { approver: approveForm.value.approver, remark: approveForm.value.remark }
  try {
    if (approveAction.value === 'approve') {
      await salaryApi.approve(approveRow.value.id, data)
      ElMessage.success('审批通过，已自动生成工资凭证')
    } else {
      await salaryApi.reject(approveRow.value.id, data)
      ElMessage.success('已驳回')
    }
    approveDialogVisible.value = false
    await load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '操作失败')
  }
}

async function submitPay() {
  if (!payFormRef.value) return
  await payFormRef.value.validate()
  if (!payRow.value) return
  try {
    await salaryApi.pay(payRow.value.id, { approver: payForm.value.approver, remark: payForm.value.remark })
    ElMessage.success('已发放')
    payDialogVisible.value = false
    await load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '发放失败')
  }
}

async function remove(row: SalaryBill) {
  await ElMessageBox.confirm(`确认删除工资单 ${row.salary_no ?? row.id}？`, '提示', { type: 'warning' })
  await salaryApi.remove(row.id)
  ElMessage.success('已删除')
  await load()
}

function openView(row: SalaryBill) {
  viewRow.value = row
  viewVisible.value = true
}

onMounted(load)
</script>

<style scoped>
.page { padding: 16px; }
.toolbar { display: flex; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; }
</style>
