<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Edit, Delete, View, OfficeBuilding, Plus as PlusIcon } from '@element-plus/icons-vue'
import type { Employee } from '@/types/employee'
import type { HRContract, HRContractStatus } from '@/types/contract'
import {
  listEmployees,
  previewUsername,
  createEmployee,
  updateEmployee,
  deleteEmployee,
} from '@/api/employee'
import { hrApi } from '@/api/contract'
import LaborContractDialog from '@/views/contract/LaborContractDialog.vue'

const router = useRouter()

// 公司部门白名单
const DEPARTMENTS = ['总经办', '综合办', '研发部', '市场部']
// 系统角色
const ROLES = [
  { value: 'employee', label: '普通员工' },
  { value: 'gm', label: '总经理' },
  { value: 'admin', label: '系统管理员' },
]

const loading = ref(false)
const list = ref<Employee[]>([])
const keyword = ref('')

// 账号实时预览（防抖）
const previewAccount = ref('')
let previewTimer: ReturnType<typeof setTimeout> | null = null
function onNameInput() {
  if (previewTimer) clearTimeout(previewTimer)
  previewTimer = setTimeout(async () => {
    if (!form.name.trim()) {
      previewAccount.value = ''
      return
    }
    try {
      const { data } = await previewUsername(form.name.trim())
      previewAccount.value = data.username
    } catch {
      previewAccount.value = ''
    }
  }, 300)
}

// 身份证号解析（前端仅做展示提示，真实解析在后端）
function onIdCardInput() {
  const v = (form.id_card || '').trim()
  if (v.length === 18) {
    if (/^\d{17}[\dX]$/i.test(v)) {
      const y = +v.slice(6, 10)
      const m = +v.slice(10, 12)
      const d = +v.slice(12, 14)
      const dt = new Date(y, m - 1, d)
      if (dt.getFullYear() === y && dt.getMonth() === m - 1 && dt.getDate() === d) {
        const gender = +v[16] % 2 === 1 ? '男' : '女'
        idPreview.value = `${gender} · ${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`
        return
      }
    }
    idPreview.value = '身份证号格式有误'
  } else {
    idPreview.value = ''
  }
}
const idPreview = ref('')

async function load() {
  loading.value = true
  try {
    const { data } = await listEmployees({
      keyword: keyword.value || undefined,
    })
    list.value = data
  } finally {
    loading.value = false
  }
}

// ===== 新增 / 编辑员工 =====
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const editingNo = ref('')
const saving = ref(false)
const form = reactive({
  name: '',
  department: '',
  position: '',
  role: 'employee',
  id_card: '',
  phone: '',
  email: '',
  hire_date: '',
})

function resetForm() {
  Object.assign(form, {
    name: '',
    department: '',
    position: '',
    role: 'employee',
    id_card: '',
    phone: '',
    email: '',
    hire_date: '',
  })
  previewAccount.value = ''
  idPreview.value = ''
}

function openCreate() {
  dialogMode.value = 'create'
  editingNo.value = ''
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: Employee) {
  if (row.employee_no === '00000000') {
    ElMessage.warning('管理员账号不可编辑')
    return
  }
  dialogMode.value = 'edit'
  editingNo.value = row.employee_no
  Object.assign(form, {
    name: row.name,
    department: row.department || '',
    position: row.position || '',
    role: row.role || 'employee',
    id_card: row.id_card || '',
    phone: row.phone || '',
    email: row.email || '',
    hire_date: row.hire_date || '',
  })
  previewAccount.value = row.username || ''
  idPreview.value = row.gender && row.birthday ? `${row.gender} · ${row.birthday}` : ''
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.name.trim()) {
    ElMessage.warning('请输入员工姓名')
    return
  }
  const payload: Record<string, unknown> = {
    name: form.name.trim(),
    department: form.department || null,
    position: form.position || null,
    role: form.role,
    id_card: form.id_card.trim() || null,
    phone: form.phone || null,
    email: form.email || null,
    hire_date: form.hire_date || null,
  }
  saving.value = true
  try {
    if (dialogMode.value === 'create') {
      const { data } = await createEmployee(payload)
      ElMessage.success(`已新增员工 ${data.name}，登录账号「${data.username}」（初始密码 123456）`)
    } else {
      await updateEmployee(editingNo.value, payload)
      ElMessage.success('员工信息已更新')
    }
    dialogVisible.value = false
    await load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: Employee) {
  if (row.employee_no === '00000000') {
    ElMessage.warning('管理员账号不可删除')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确认删除员工「${row.name}」（${row.employee_no}）？其登录账号将一并删除。`,
      '删除确认',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  try {
    await deleteEmployee(row.employee_no)
    ElMessage.success('已删除')
    await load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}

// 身份证脱敏展示（如 440***********1234）
function maskIdCard(v?: string | null) {
  if (!v) return '—'
  if (v.length !== 18) return v
  return `${v.slice(0, 4)}***********${v.slice(-4)}`
}

function roleLabel(role?: string) {
  return ROLES.find(r => r.value === role)?.label || role || '普通员工'
}

// ===== 员工详情抽屉（含劳动合同）=====
const detailVisible = ref(false)
const detailEmployee = ref<Employee | null>(null)
const detailContracts = ref<HRContract[]>([])
const detailContractsLoading = ref(false)
const contractDialogVisible = ref(false)
const editingContract = ref<HRContract | null>(null)

async function openDetail(row: Employee) {
  detailEmployee.value = row
  detailVisible.value = true
  await loadDetailContracts()
}

async function loadDetailContracts() {
  if (!detailEmployee.value) return
  detailContractsLoading.value = true
  try {
    const res = await hrApi.list({ employee_id: detailEmployee.value.id })
    detailContracts.value = res.data
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载合同失败')
  } finally {
    detailContractsLoading.value = false
  }
}

function openNewContract() {
  if (!detailEmployee.value) return
  editingContract.value = null
  contractDialogVisible.value = true
}

function openEditContract(c: HRContract) {
  editingContract.value = c
  contractDialogVisible.value = true
}

async function onContractSaved() {
  await loadDetailContracts()
}

async function submitContract(c: HRContract) {
  try {
    await ElMessageBox.confirm(
      `确认提交劳动合同（${c.employee_name}）？一人公司将自动审批生效，可直接打印。`,
      '提交确认',
      { type: 'warning' },
    )
    const res = await hrApi.submit(c.id)
    ElMessage.success(`已生效，审批人：${res.data.approver}`)
    await loadDetailContracts()
  } catch (e: any) {
    if (e === 'cancel' || e?.toString().includes('cancel')) return
    ElMessage.error(e?.response?.data?.detail || '提交失败')
  }
}

function goPrintContract(c: HRContract) {
  router.push({ name: 'HRContractPrint', params: { id: String(c.id) } })
}

async function terminateContract(c: HRContract) {
  try {
    const { value: remark } = await ElMessageBox.prompt('请输入终止原因（选填）', '终止合同', { inputPlaceholder: '原因' })
    await hrApi.terminate(c.id, { remark: remark || undefined })
    ElMessage.success('已终止')
    await loadDetailContracts()
  } catch (e: any) {
    if (e === 'cancel' || e?.toString().includes('cancel')) return
    ElMessage.error(e?.response?.data?.detail || '终止失败')
  }
}

async function deleteContract(c: HRContract) {
  try {
    await ElMessageBox.confirm('确认删除该合同？', '提示', { type: 'warning' })
    await hrApi.remove(c.id)
    ElMessage.success('已删除')
    await loadDetailContracts()
  } catch (e: any) {
    if (e === 'cancel' || e?.toString().includes('cancel')) return
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}

function statusTagType(status: HRContractStatus): '' | 'success' | 'warning' | 'danger' | 'info' | 'primary' {
  switch (status) {
    case '已生效': return 'success'
    case '已到期': return 'warning'
    case '已终止': return 'info'
    case '待审批': return 'warning'
    case '草稿': return 'info'
    default: return 'primary'
  }
}

function daysLeft(row: HRContract): number | null {
  if (!row.end_date) return null
  return Math.ceil((new Date(row.end_date).getTime() - Date.now()) / 86400000)
}

function contractNo(row: HRContract): string {
  return `合同 #${row.id}`
}

function endDateText(row: HRContract): string {
  const d = daysLeft(row)
  if (d === null) return row.end_date || '—'
  if (d < 0) return row.end_date || '—'
  return row.end_date || '—'
}

function remainingTag(row: HRContract): { show: boolean; type: string; text: string } {
  const d = daysLeft(row)
  if (d === null) return { show: false, type: 'info', text: '' }
  if (d < 0) return { show: true, type: 'danger', text: `已过期${-d}天` }
  if (d <= 30) return { show: true, type: 'warning', text: `剩${d}天` }
  return { show: true, type: 'success', text: `剩${d}天` }
}

function toNum(v: any): number {
  if (v === null || v === undefined || v === '') return 0
  const n = Number(v)
  return Number.isFinite(n) ? n : 0
}
function fmt(v: any): string {
  return '¥' + toNum(v).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function goCompanySettings() {
  router.push({ name: 'CompanySettings' })
}

onMounted(load)
</script>

<template>
  <div class="emp-page">
    <!-- 操作栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="keyword"
          placeholder="搜索姓名 / 部门 / 工号"
          :prefix-icon="Search"
          clearable
          class="kw-input"
          @keyup.enter="load"
          @clear="load"
        />
        <el-button @click="load">查询</el-button>
      </div>
      <div class="toolbar-right">
        <el-button :icon="OfficeBuilding" @click="goCompanySettings">公司设置</el-button>
        <el-button type="primary" :icon="Plus" @click="openCreate">新增员工</el-button>
      </div>
    </div>

    <!-- 员工表格 -->
    <el-table :data="list" v-loading="loading" class="emp-table" border stripe>
      <el-table-column prop="employee_no" label="工号" width="100" />
      <el-table-column prop="name" label="姓名" width="100" />
      <el-table-column prop="department" label="部门" min-width="110" />
      <el-table-column prop="position" label="职位" min-width="110" />
      <el-table-column label="账号 / 角色" min-width="200">
        <template #default="{ row }">
          <div class="acct-cell">
            <el-tag v-if="row.username" type="primary" effect="light">{{ row.username }}</el-tag>
            <span v-else class="muted">—</span>
            <el-tag size="small" :type="row.role === 'employee' ? 'info' : 'warning'" effect="plain">
              {{ roleLabel(row.role) }}
            </el-tag>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="身份证号" min-width="180">
        <template #default="{ row }">
          <span class="muted">{{ maskIdCard(row.id_card) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="性别 / 生日" min-width="160">
        <template #default="{ row }">
          <span v-if="row.gender || row.birthday">
            {{ [row.gender, row.birthday].filter(Boolean).join(' · ') }}
          </span>
          <span v-else class="muted">—</span>
        </template>
      </el-table-column>
      <el-table-column prop="phone" label="手机号" width="130" />
      <el-table-column prop="hire_date" label="入职日期" width="120" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" :icon="View" @click="openDetail(row)">详情</el-button>
          <template v-if="row.employee_no === '00000000'">
            <span class="muted">—</span>
          </template>
          <template v-else>
            <el-button link type="primary" :icon="Edit" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" :icon="Delete" @click="handleDelete(row)">删除</el-button>
          </template>
        </template>
      </el-table-column>
    </el-table>

    <div class="hint">
      提示：点击「详情」可查看员工的劳动合同、提交/打印/终止合同。新增员工时系统按「姓名全拼」自动创建登录账号（如：沈雷 → shenlei），初始密码统一为
      <b>123456</b>，请通知员工首次登录后自行修改。工号 8 位数字自增（admin 固定 00000000）。
    </div>

    <!-- 新增 / 编辑员工弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '新增员工' : '编辑员工'"
      width="560px"
    >
      <el-form :model="form" label-width="92px">
        <el-form-item label="姓名" required>
          <el-input v-model="form.name" placeholder="如：沈雷" @input="onNameInput" />
        </el-form-item>
        <el-form-item label="登录账号">
          <el-input :model-value="previewAccount" readonly placeholder="保存时按姓名全拼自动生成">
            <template v-if="previewAccount" #suffix>
              <span class="acct-preview">{{ previewAccount }}</span>
            </template>
          </el-input>
          <div class="field-tip">姓名输入后自动带出（重名会追加数字后缀）</div>
        </el-form-item>
        <el-form-item label="部门">
          <el-select v-model="form.department" placeholder="选择部门" clearable filterable style="width:100%">
            <el-option v-for="d in DEPARTMENTS" :key="d" :label="d" :value="d" />
          </el-select>
        </el-form-item>
        <el-form-item label="职位">
          <el-input v-model="form.position" placeholder="如：工程师 / 市场专员（仅作展示，不含权限）" />
        </el-form-item>
        <el-form-item label="系统角色">
          <el-select v-model="form.role" style="width:100%">
            <el-option v-for="r in ROLES" :key="r.value" :label="r.label" :value="r.value" />
          </el-select>
          <div class="field-tip">总经理与系统管理员拥有同等权限；职位仅作人事展示，不绑定权限。</div>
        </el-form-item>
        <el-form-item label="身份证号">
          <el-input v-model="form.id_card" placeholder="18 位身份证号" maxlength="18" @input="onIdCardInput" />
          <div v-if="idPreview" class="field-tip" :class="{ 'tip-err': idPreview.includes('有误') }">
            解析结果：{{ idPreview }}
          </div>
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.phone" placeholder="11 位手机号" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" placeholder="name@company.com" />
        </el-form-item>
        <el-form-item label="入职日期">
          <el-date-picker
            v-model="form.hire_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择日期"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 员工详情抽屉（含劳动合同） -->
    <el-drawer
      v-model="detailVisible"
      :title="`员工详情 — ${detailEmployee?.name || ''}`"
      direction="rtl"
      size="78%"
      :close-on-click-modal="false"
    >
      <div v-if="detailEmployee" class="detail-page">
        <!-- 员工信息 -->
        <el-card class="info-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>员工信息</span>
              <el-button link type="primary" :icon="Edit" @click="openEdit(detailEmployee)">编辑员工</el-button>
            </div>
          </template>
          <el-descriptions :column="3" border>
            <el-descriptions-item label="工号">{{ detailEmployee.employee_no }}</el-descriptions-item>
            <el-descriptions-item label="姓名">{{ detailEmployee.name }}</el-descriptions-item>
            <el-descriptions-item label="部门">{{ detailEmployee.department || '—' }}</el-descriptions-item>
            <el-descriptions-item label="职位">{{ detailEmployee.position || '—' }}</el-descriptions-item>
            <el-descriptions-item label="登录账号">{{ detailEmployee.username || '—' }}</el-descriptions-item>
            <el-descriptions-item label="系统角色">
              <el-tag size="small" :type="detailEmployee.role === 'employee' ? 'info' : 'warning'" effect="plain">
                {{ roleLabel(detailEmployee.role) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="身份证号">{{ maskIdCard(detailEmployee.id_card) }}</el-descriptions-item>
            <el-descriptions-item label="性别">{{ detailEmployee.gender || '—' }}</el-descriptions-item>
            <el-descriptions-item label="生日">{{ detailEmployee.birthday || '—' }}</el-descriptions-item>
            <el-descriptions-item label="手机号">{{ detailEmployee.phone || '—' }}</el-descriptions-item>
            <el-descriptions-item label="邮箱">{{ detailEmployee.email || '—' }}</el-descriptions-item>
            <el-descriptions-item label="入职日期">{{ detailEmployee.hire_date || '—' }}</el-descriptions-item>
            <el-descriptions-item label="状态" :span="3">
              <el-tag size="small" :type="detailEmployee.status === '在职' ? 'success' : 'info'">
                {{ detailEmployee.status }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 劳动合同 -->
        <el-card class="contract-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>劳动合同（深圳市标准范本）</span>
              <el-button type="success" :icon="PlusIcon" @click="openNewContract">新建劳动合同</el-button>
            </div>
          </template>
          <el-table :data="detailContracts" v-loading="detailContractsLoading" border stripe empty-text="暂无合同">
            <el-table-column label="合同号" width="160">
              <template #default="{ row }">{{ contractNo(row) }}</template>
            </el-table-column>
            <el-table-column label="类型" prop="contract_type" width="100" />
            <el-table-column label="期限" prop="contract_term" width="180" />
            <el-table-column label="开始" prop="start_date" width="110" />
            <el-table-column label="结束" width="180">
              <template #default="{ row }">
                <span>{{ endDateText(row) }}</span>
                <el-tag v-if="remainingTag(row).show" :type="remainingTag(row).type" size="small" style="margin-left: 6px">
                  {{ remainingTag(row).text }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="基本工资" width="120" align="right">
              <template #default="{ row }">{{ fmt(row.salary) }}</template>
            </el-table-column>
            <el-table-column label="状态" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="statusTagType(row.status)" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="280" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openEditContract(row)">编辑</el-button>
                <el-button v-if="row.status === '草稿'" link type="success" @click="submitContract(row)">提交</el-button>
                <el-button v-if="row.status === '已生效' || row.status === '已到期' || row.status === '已终止'" link type="primary" @click="goPrintContract(row)">打印</el-button>
                <el-button v-if="row.status === '已生效' || row.status === '已到期'" link type="danger" @click="terminateContract(row)">终止</el-button>
                <el-button link type="danger" @click="deleteContract(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="contract-hint">
            合同填写说明：选择员工后姓名/身份证/部门/岗位/乙方自动带出；甲方（公司）自动取「公司设置」；
            新签合同无状态，保存即草稿，提交后一人公司自动审批生效，可按深圳市标准范本打印。
          </div>
        </el-card>
      </div>
    </el-drawer>

    <!-- 劳动合同新建/编辑弹窗（复用组件） -->
    <LaborContractDialog
      v-model="contractDialogVisible"
      :contract="editingContract"
      :locked-employee="editingContract ? null : detailEmployee?.id || null"
      @saved="onContractSaved"
    />
  </div>
</template>

<style scoped>
.emp-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.kw-input {
  width: 240px;
}
.emp-table {
  border-radius: 10px;
  overflow: hidden;
}
.acct-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.acct-preview {
  color: var(--el-color-primary);
}
.muted {
  color: var(--el-text-color-secondary);
}
.field-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.5;
  margin-top: 2px;
}
.tip-err {
  color: var(--el-color-danger);
}
.hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.6;
  background: var(--el-fill-color-light);
  border-radius: 8px;
  padding: 10px 14px;
}
.hint b {
  color: var(--el-color-primary);
}

/* 详情抽屉 */
.detail-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.info-card,
.contract-card {
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 10px;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.contract-hint {
  margin-top: 10px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.6;
  background: var(--el-fill-color-light);
  border-radius: 8px;
  padding: 10px 14px;
}
</style>
