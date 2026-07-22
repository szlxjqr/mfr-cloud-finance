<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Edit, Delete } from '@element-plus/icons-vue'
import type { Employee } from '@/types/employee'
import {
  listEmployees,
  previewUsername,
  createEmployee,
  updateEmployee,
  deleteEmployee,
} from '@/api/employee'

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
    // 简易格式校验，详细校验后端做
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

// ===== 新增 / 编辑 =====
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
      <el-button type="primary" :icon="Plus" @click="openCreate">新增员工</el-button>
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
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
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
      提示：新增员工时系统按「姓名全拼」自动创建登录账号（如：沈雷 → shenlei），初始密码统一为
      <b>123456</b>，请通知员工首次登录后自行修改。工号 8 位数字自增（admin 固定 00000000）。
    </div>

    <!-- 新增 / 编辑弹窗 -->
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
</style>
