<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Edit, Delete } from '@element-plus/icons-vue'
import type { Employee } from '@/types/employee'
import {
  listEmployees,
  createEmployee,
  updateEmployee,
  deleteEmployee,
} from '@/api/employee'

const loading = ref(false)
const list = ref<Employee[]>([])
const keyword = ref('')
const statusFilter = ref<string>('')

async function load() {
  loading.value = true
  try {
    const { data } = await listEmployees({
      keyword: keyword.value || undefined,
      status: statusFilter.value || undefined,
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
  phone: '',
  email: '',
  status: '在职',
  hire_date: '',
})

function openCreate() {
  dialogMode.value = 'create'
  editingNo.value = ''
  Object.assign(form, {
    name: '',
    department: '',
    position: '',
    phone: '',
    email: '',
    status: '在职',
    hire_date: '',
  })
  dialogVisible.value = true
}

function openEdit(row: Employee) {
  dialogMode.value = 'edit'
  editingNo.value = row.employee_no
  Object.assign(form, {
    name: row.name,
    department: row.department || '',
    position: row.position || '',
    phone: row.phone || '',
    email: row.email || '',
    status: row.status || '在职',
    hire_date: row.hire_date || '',
  })
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.name.trim()) {
    ElMessage.warning('请输入员工姓名')
    return
  }
  saving.value = true
  try {
    if (dialogMode.value === 'create') {
      const { data } = await createEmployee({ ...form })
      ElMessage.success(`已新增员工 ${data.name}，登录账号「${data.username}」（初始密码 123456）`)
    } else {
      await updateEmployee(editingNo.value, { ...form })
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
        <el-select v-model="statusFilter" placeholder="全部状态" clearable class="st-select" @change="load">
          <el-option label="在职" value="在职" />
          <el-option label="离职" value="离职" />
        </el-select>
        <el-button @click="load">查询</el-button>
      </div>
      <el-button type="primary" :icon="Plus" @click="openCreate">新增员工</el-button>
    </div>

    <!-- 员工表格 -->
    <el-table :data="list" v-loading="loading" class="emp-table" border stripe>
      <el-table-column prop="employee_no" label="工号" width="110" />
      <el-table-column prop="name" label="姓名" width="120" />
      <el-table-column prop="department" label="部门" min-width="120" />
      <el-table-column prop="position" label="职位" min-width="120" />
      <el-table-column prop="username" label="登录账号（姓名全拼）" min-width="180">
        <template #default="{ row }">
          <el-tag v-if="row.username" type="primary" effect="light">{{ row.username }}</el-tag>
          <span v-else class="muted">—</span>
        </template>
      </el-table-column>
      <el-table-column prop="phone" label="手机号" width="140" />
      <el-table-column prop="hire_date" label="入职日期" width="130" />
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === '在职' ? 'success' : 'info'">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" :icon="Edit" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" :icon="Delete" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="hint">
      提示：新增员工时系统按「姓名全拼」自动创建登录账号（如 沈雷 → shenlei），初始密码统一为
      <b>123456</b>，请通知员工首次登录后自行修改。
    </div>

    <!-- 新增 / 编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '新增员工' : '编辑员工'"
      width="520px"
    >
      <el-form :model="form" label-width="90px">
        <el-form-item label="姓名" required>
          <el-input v-model="form.name" placeholder="如：沈雷" />
        </el-form-item>
        <el-form-item label="部门">
          <el-input v-model="form.department" placeholder="如：研发部" />
        </el-form-item>
        <el-form-item label="职位">
          <el-input v-model="form.position" placeholder="如：工程师" />
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
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio value="在职">在职</el-radio>
            <el-radio value="离职">离职</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-alert
          v-if="dialogMode === 'create'"
          type="info"
          :closable="false"
          title="保存后将自动生成登录账号（姓名全拼），初始密码 123456。"
        />
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
.st-select {
  width: 130px;
}
.emp-table {
  border-radius: 10px;
  overflow: hidden;
}
.muted {
  color: var(--el-text-color-secondary);
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
