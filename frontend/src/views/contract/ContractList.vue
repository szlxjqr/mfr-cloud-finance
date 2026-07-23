<template>
  <div class="page">
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索" clearable style="width: 220px" @keyup.enter="load" @clear="load" />
      <el-button type="primary" @click="openCreate">新建劳动合同</el-button>
      <el-button :type="onlyExpiring ? 'warning' : 'default'" @click="toggleExpiring">
        {{ onlyExpiring ? '显示全部' : '仅看即将到期(30天)' }}
      </el-button>
    </div>

    <el-table :data="filteredList" :row-class-name="rowClass" border stripe>
      <el-table-column type="index" label="#" width="50" />
      <template v-if="type === 'hr'">
        <el-table-column prop="employee_name" label="员工" />
        <el-table-column prop="id_number" label="身份证" />
        <el-table-column prop="contract_type" label="类型" />
        <el-table-column prop="party_a" label="甲方(公司)" />
        <el-table-column prop="party_b" label="乙方(员工)" />
        <el-table-column label="薪资" width="100">
          <template #default="{ row }">{{ fmt(row.salary) }}</template>
        </el-table-column>
        <el-table-column label="开始" prop="start_date" width="110" />
        <el-table-column label="结束" prop="end_date" width="120">
          <template #default="{ row }">
            <span>{{ row.end_date }}</span>
            <el-tag v-if="daysLeftText(row)" :type="expireTag(row)" size="small" style="margin-left: 6px">
              {{ daysLeftText(row) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
      </template>
      <template v-else>
        <el-table-column prop="contract_no" label="合同号" />
        <el-table-column :label="type === 'sales' ? '客户' : '供应商'">
          <template #default="{ row }">{{ partyName(row) }}</template>
        </el-table-column>
        <el-table-column prop="amount" label="金额" />
        <el-table-column prop="tax_rate" label="税率" />
        <el-table-column prop="tax_amount" label="税额" />
        <el-table-column prop="sign_date" label="签立" />
        <el-table-column prop="end_date" label="到期">
          <template #default="{ row }">
            <span>{{ row.end_date }}</span>
            <el-tag v-if="daysLeftText(row)" :type="expireTag(row)" size="small" style="margin-left: 6px">
              {{ daysLeftText(row) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" />
      </template>
      <el-table-column label="操作" :width="type === 'hr' ? 300 : 150">
        <template #default="{ row }">
          <template v-if="type === 'hr'">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button v-if="row.status === '草稿'" link type="success" @click="doSubmit(row)">提交</el-button>
            <el-button v-if="row.status === '已生效' || row.status === '已到期' || row.status === '已终止'" link type="primary" @click="goPrint(row)">打印</el-button>
            <el-button v-if="row.status === '已生效' || row.status === '已到期'" link type="danger" @click="doTerminate(row)">终止</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
          <template v-else>
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新建 / 编辑弹窗（仅人事合同类型，类型完整；销售/采购走原表单） -->
    <el-dialog
      v-model="dialogVisible"
      :title="editing ? '编辑劳动合同' : '新建劳动合同'"
      width="880px"
      :close-on-click-modal="false"
    >
      <template v-if="type === 'hr'">
        <el-form :model="form" label-width="110px">
          <el-divider content-position="left">员工与公司（联动）</el-divider>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="员工姓名" required>
                <el-select
                  v-model="form.employee_id"
                  filterable
                  remote
                  :remote-method="searchEmployees"
                  :loading="empLoading"
                  placeholder="搜索员工姓名/工号"
                  style="width: 100%"
                  @change="onEmployeeChange"
                >
                  <el-option
                    v-for="e in employeeOptions"
                    :key="e.id"
                    :label="`${e.name}（${e.employee_no} · ${e.department || ''}）`"
                    :value="e.id"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="身份证">
                <el-input v-model="form.id_number" placeholder="员工档案带出" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="12">
            <el-col :span="8"><el-form-item label="工号"><el-input v-model="form.employee_no" disabled /></el-form-item></el-col>
            <el-col :span="8"><el-form-item label="部门"><el-input v-model="form.department" /></el-form-item></el-col>
            <el-col :span="8"><el-form-item label="岗位"><el-input v-model="form.position" /></el-form-item></el-col>
          </el-row>
          <el-row :gutter="12">
            <el-col :span="12"><el-form-item label="甲方(公司)"><el-input v-model="form.party_a" disabled placeholder="自动取系统公司设置" /></el-form-item></el-col>
            <el-col :span="12"><el-form-item label="乙方(员工)"><el-input v-model="form.party_b" disabled placeholder="自动从员工带出" /></el-form-item></el-col>
          </el-row>
          <el-alert
            type="info"
            :closable="false"
            show-icon
            :title="`甲方取自「公司设置」（${form.party_a || '未设置'}），乙方取自所选员工。新签合同无状态，保存后由「提交」按钮走一人公司自动审批生效。`"
            style="margin-bottom: 8px"
          />

          <el-divider content-position="left">合同期限</el-divider>
          <el-row :gutter="12">
            <el-col :span="8">
              <el-form-item label="合同类型">
                <el-select v-model="form.contract_type" style="width: 100%">
                  <el-option label="劳动合同" value="劳动合同" />
                  <el-option label="劳务合同" value="劳务合同" />
                  <el-option label="实习协议" value="实习协议" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="期限类型">
                <el-select v-model="form.contract_term" style="width: 100%">
                  <el-option label="有固定期限" value="有固定期限" />
                  <el-option label="无固定期限" value="无固定期限" />
                  <el-option label="以完成一定工作任务为期限" value="以完成一定工作任务为期限" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8"><el-form-item label="签订日期"><el-date-picker v-model="form.sign_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" /></el-form-item></el-col>
          </el-row>
          <el-row :gutter="12">
            <el-col :span="12"><el-form-item label="开始日期"><el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" /></el-form-item></el-col>
            <el-col :span="12"><el-form-item label="结束日期"><el-date-picker v-model="form.end_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" /></el-form-item></el-col>
          </el-row>
          <el-row :gutter="12">
            <el-col :span="8"><el-form-item label="试用期(月)"><el-input-number v-model="form.probation_months" :min="0" :max="6" :controls="false" style="width: 100%" /></el-form-item></el-col>
            <el-col :span="8"><el-form-item label="试用期工资"><el-input-number v-model="form.probation_salary" :min="0" :precision="2" :controls="false" style="width: 100%" /></el-form-item></el-col>
            <el-col :span="8"><el-form-item label="每月发放日"><el-input-number v-model="form.pay_day" :min="1" :max="31" :controls="false" style="width: 100%" /></el-form-item></el-col>
          </el-row>

          <el-divider content-position="left">工作内容与报酬</el-divider>
          <el-row :gutter="12">
            <el-col :span="12"><el-form-item label="岗位(工种)"><el-input v-model="form.work_content" placeholder="如 软件开发工程师" /></el-form-item></el-col>
            <el-col :span="12"><el-form-item label="工作地点"><el-input v-model="form.work_location" placeholder="如 深圳市南山区" /></el-form-item></el-col>
          </el-row>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="工时制度">
                <el-select v-model="form.work_hours_type" style="width: 100%">
                  <el-option label="标准工时制" value="标准工时制" />
                  <el-option label="综合计算工时制" value="综合计算工时制" />
                  <el-option label="不定时工作制" value="不定时工作制" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="工资形式">
                <el-select v-model="form.pay_method" style="width: 100%">
                  <el-option label="计时工资" value="计时工资" />
                  <el-option label="计件工资" value="计件工资" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="12">
            <el-col :span="12"><el-form-item label="基本工资(¥)"><el-input-number v-model="form.salary" :min="0" :precision="2" :controls="false" style="width: 100%" /></el-form-item></el-col>
            <el-col :span="12"><el-form-item label="联系电话"><el-input v-model="form.phone" /></el-form-item></el-col>
          </el-row>
          <el-form-item label="福利待遇"><el-input v-model="form.benefits" type="textarea" :rows="2" placeholder="如 年终奖、节日福利等" /></el-form-item>
          <el-form-item label="备注"><el-input v-model="form.remark" type="textarea" :rows="2" /></el-form-item>
        </el-form>
      </template>
      <template v-else>
        <el-form :model="form" label-width="110px">
          <el-form-item label="合同号"><el-input v-model="form.contract_no" /></el-form-item>
          <el-form-item :label="type === 'sales' ? '客户' : '供应商'">
            <el-select v-model="form.party_id" filterable placeholder="选择">
              <el-option v-for="p in partyOptions" :key="p.id" :label="p.name" :value="p.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="金额"><el-input v-model.number="form.amount" type="number" @input="calcTax" /></el-form-item>
          <el-form-item label="税率"><el-input v-model.number="form.tax_rate" type="number" @input="calcTax" /></el-form-item>
          <el-form-item label="税额"><el-input :model-value="form.tax_amount" disabled /></el-form-item>
          <el-form-item label="签立日期">
            <el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" />
          </el-form-item>
          <el-form-item label="到期日期">
            <el-date-picker v-model="form.end_date" type="date" value-format="YYYY-MM-DD" />
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="form.status">
              <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
            </el-select>
          </el-form-item>
          <el-form-item label="备注"><el-input v-model="form.remark" type="textarea" /></el-form-item>
        </el-form>
      </template>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <!-- 审批弹窗 -->
    <el-dialog v-model="approveDialogVisible" title="审批劳动合同" width="420px" :close-on-click-modal="false">
      <el-form :model="approveForm" label-width="90px">
        <el-form-item label="员工">{{ approveRow?.employee_name }}</el-form-item>
        <el-form-item label="审批人" required>
          <el-input v-model="approveForm.approver" placeholder="请输入审批人姓名" />
        </el-form-item>
        <el-form-item label="审批意见">
          <el-input v-model="approveForm.remark" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="approveDialogVisible = false">取消</el-button>
        <el-button type="success" @click="submitApprove">确认通过</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { hrApi, partyApi, purchaseApi, salesApi } from '@/api/contract'
import { listEmployees } from '@/api/employee'
import { companyApi } from '@/api/company'
import type { HRContract } from '@/types/contract'
import type { Employee } from '@/types/employee'
import type { CompanySettings } from '@/types/company'

const props = defineProps<{ type: 'hr' | 'sales' | 'purchase' }>()
const router = useRouter()

const keyword = ref('')
const onlyExpiring = ref(false)
const list = ref<any[]>([])
const partyOptions = ref<any[]>([])
const dialogVisible = ref(false)
const editing = ref(false)
const editingId = ref<number | null>(null)
const employeeOptions = ref<Employee[]>([])
const empLoading = ref(false)
const companySettings = ref<CompanySettings | null>(null)

const approveDialogVisible = ref(false)
const approveRow = ref<HRContract | null>(null)
const approveForm = reactive({ approver: '', remark: '' })

const statusOptions = computed(() =>
  props.type === 'hr'
    ? ['草稿', '待审批', '已生效', '已到期', '已终止']
    : ['草稿', '执行中', '已完成', '终止', '纠纷'],
)

const emptyForm = () => ({
  // 员工联动
  employee_id: null as number | null,
  employee_no: '' as string | null,
  employee_name: '',
  id_number: '' as string | null,
  department: '' as string | null,
  position: '' as string | null,
  phone: '' as string | null,
  // 合同期限
  contract_type: '劳动合同',
  contract_term: '有固定期限' as string | null,
  sign_date: new Date().toISOString().slice(0, 10) as string | null,
  start_date: new Date().toISOString().slice(0, 10) as string | null,
  end_date: '' as string | null,
  // 试用期
  probation_months: 3 as number | null,
  probation_salary: 0 as number | null,
  pay_day: 15 as number | null,
  // 工作
  work_content: '' as string | null,
  work_location: '深圳市' as string | null,
  work_hours_type: '标准工时制' as string | null,
  // 报酬
  salary: 0 as number | null,
  pay_method: '计时工资' as string | null,
  // 福利
  benefits: '' as string | null,
  // 甲方乙方
  party_a: '' as string | null,
  party_b: '' as string | null,
  // 销售/采购
  contract_no: '',
  party_id: null as number | null,
  amount: null as number | null,
  tax_rate: null as number | null,
  tax_amount: null as number | null,
  status: props.type === 'hr' ? '草稿' : '草稿',
  remark: '',
})
const form = reactive(emptyForm())

const api = computed(() =>
  props.type === 'hr' ? hrApi : props.type === 'sales' ? salesApi : purchaseApi,
)

function partyField() {
  return props.type === 'sales' ? 'customer_id' : 'supplier_id'
}

function toNum(v: any): number {
  if (v === null || v === undefined || v === '') return 0
  const n = Number(v)
  return Number.isFinite(n) ? n : 0
}
function fmt(v: any): string {
  return '¥' + toNum(v).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

// === 员工搜索（远程） ===
async function searchEmployees(q: string) {
  empLoading.value = true
  try {
    const res = await listEmployees({ keyword: q || undefined, status: '在职' })
    employeeOptions.value = res.data
  } finally {
    empLoading.value = false
  }
}

// === 员工选择 → 自动带出所有员工字段 ===
function onEmployeeChange(empId: number | null) {
  if (!empId) {
    form.employee_name = ''
    form.employee_no = ''
    form.id_number = ''
    form.department = ''
    form.position = ''
    form.phone = ''
    form.party_b = ''
    return
  }
  const emp = employeeOptions.value.find((e) => e.id === empId)
  if (emp) {
    form.employee_name = emp.name
    form.employee_no = emp.employee_no
    form.id_number = emp.id_card || ''
    form.department = emp.department || ''
    form.position = emp.position || ''
    form.phone = emp.phone || ''
    form.party_b = emp.name
  }
}

async function loadCompanySettings() {
  try {
    const res = await companyApi.get()
    companySettings.value = res.data
  } catch (e) {
    console.warn('加载公司设置失败', e)
  }
}

async function load() {
  const params: any = {}
  if (keyword.value) params.keyword = keyword.value
  const res = await api.value.list(params)
  list.value = res.data
}
async function loadParties() {
  if (props.type === 'sales' || props.type === 'purchase') {
    const res = await partyApi.list({ ptype: props.type === 'sales' ? 'customer' : 'supplier' })
    partyOptions.value = res.data
  }
}
const partyMap = computed(() => {
  const m: Record<number, string> = {}
  partyOptions.value.forEach((p) => (m[p.id] = p.name))
  return m
})
function partyName(row: any) {
  const id = row.customer_id ?? row.supplier_id
  return id != null ? partyMap.value[id] ?? `#${id}` : '-'
}

function daysLeft(row: any) {
  if (!row.end_date) return null
  return Math.ceil((new Date(row.end_date).getTime() - Date.now()) / 86400000)
}
function daysLeftText(row: any): string | null {
  const d = daysLeft(row)
  if (d === null) return null
  return d >= 0 ? `剩${d}天` : `已过期${-d}天`
}
function expireTag(row: any) {
  const d = daysLeft(row)
  if (d === null) return 'info'
  return d < 0 ? 'danger' : d <= 30 ? 'warning' : 'success'
}
function statusTag(status: string): '' | 'success' | 'warning' | 'danger' | 'info' | 'primary' {
  switch (status) {
    case '已生效': return 'success'
    case '已到期': return 'warning'
    case '已终止': return 'info'
    case '待审批': return 'warning'
    case '草稿': return 'info'
    default: return 'primary'
  }
}
function rowClass({ row }: any) {
  const d = daysLeft(row)
  if (d !== null && d < 0) return 'row-expired'
  if (d !== null && d <= 30) return 'row-expiring'
  return ''
}

const filteredList = computed(() => {
  if (!onlyExpiring.value) return list.value
  return list.value.filter((r) => {
    const d = daysLeft(r)
    return d !== null && d <= 30
  })
})

function calcTax() {
  if (form.amount != null && form.tax_rate != null) {
    form.tax_amount = Math.round(Number(form.amount) * Number(form.tax_rate) * 100) / 100
  }
}

async function openCreate() {
  Object.assign(form, emptyForm())
  // 甲方自动取公司设置
  if (!companySettings.value) await loadCompanySettings()
  form.party_a = companySettings.value?.company_name || '深圳市流形机器人科技有限公司'
  form.status = '草稿'
  editing.value = false
  editingId.value = null
  dialogVisible.value = true
  // 预加载员工列表（空关键字 → 在职全部）
  await searchEmployees('')
}

function openEdit(row: any) {
  Object.assign(form, emptyForm(), row)
  if (props.type === 'hr') {
    form.party_id = null
    // 加载员工列表以便 select 选中
    if (row.employee_id) {
      searchEmployees('').then(() => {
        form.employee_id = row.employee_id
      })
    }
  } else {
    form.party_id = row.customer_id ?? row.supplier_id ?? null
  }
  editing.value = true
  editingId.value = row.id
  dialogVisible.value = true
}

async function save() {
  const payload: any = { ...form }
  if (props.type === 'hr') {
    // 销售/采购字段清空
    delete payload.contract_no
    delete payload.party_id
    delete payload.amount
    delete payload.tax_rate
    delete payload.tax_amount
  } else {
    delete payload.employee_id
    delete payload.employee_no
    delete payload.employee_name
    delete payload.id_number
    delete payload.department
    delete payload.position
    delete payload.phone
    delete payload.contract_term
    delete payload.sign_date
    delete payload.probation_months
    delete payload.probation_salary
    delete payload.work_content
    delete payload.work_location
    delete payload.work_hours_type
    delete payload.salary
    delete payload.pay_method
    delete payload.pay_day
    delete payload.benefits
    delete payload.party_a
    delete payload.party_b
    delete payload[partyField()]
    delete payload.party_id
  }
  // 空字符串字段统一置 null
  ;['sign_date', 'start_date', 'end_date', 'salary', 'amount', 'tax_rate', 'probation_salary'].forEach((k) => {
    if (payload[k] === '') payload[k] = null
  })
  if (props.type === 'hr') {
    // 新签合同无状态：保存即草稿
    if (!editing.value) payload.status = '草稿'
  }
  try {
    if (editing.value && editingId.value != null) {
      await api.value.update(editingId.value, payload)
      ElMessage.success('已保存')
    } else {
      await api.value.create(payload)
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    await load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  }
}

async function doSubmit(row: HRContract) {
  await ElMessageBox.confirm(
    `确认提交劳动合同（${row.employee_name}）？一人公司将自动审批生效，可直接打印。`,
    '提交确认',
    { type: 'warning' },
  )
  try {
    const res = await hrApi.submit(row.id)
    ElMessage.success(`已生效，审批人：${res.data.approver}`)
    await load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '提交失败')
  }
}

async function submitApprove() {
  if (!approveForm.approver.trim()) {
    ElMessage.warning('请输入审批人')
    return
  }
  if (!approveRow.value) return
  try {
    await hrApi.approve(approveRow.value.id, {
      approver: approveForm.approver.trim(),
      remark: approveForm.remark.trim() || undefined,
    })
    ElMessage.success('已审批生效')
    approveDialogVisible.value = false
    await load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '审批失败')
  }
}

async function doTerminate(row: HRContract) {
  const { value: remark } = await ElMessageBox.prompt('请输入终止原因（选填）', '终止合同', { inputPlaceholder: '原因' })
  try {
    await hrApi.terminate(row.id, { remark: remark || undefined })
    ElMessage.success('已终止')
    await load()
  } catch (e: any) {
    if (e === 'cancel') return
    ElMessage.error(e?.response?.data?.detail || '终止失败')
  }
}

function goPrint(row: HRContract) {
  router.push({ name: 'HRContractPrint', params: { id: String(row.id) } })
}

async function remove(row: any) {
  await ElMessageBox.confirm('确认删除该合同？', '提示', { type: 'warning' })
  try {
    await api.value.remove(row.id)
    ElMessage.success('已删除')
    await load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}

function toggleExpiring() {
  onlyExpiring.value = !onlyExpiring.value
}

onMounted(async () => {
  await load()
  await loadParties()
  if (props.type === 'hr') {
    await loadCompanySettings()
  }
})
</script>

<style scoped>
.page {
  padding: 16px;
}
.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}
:deep(.row-expired) {
  background: #fef0f0;
}
:deep(.row-expiring) {
  background: #fdf6ec;
}
</style>
