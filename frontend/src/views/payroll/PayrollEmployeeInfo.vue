<template>
  <div class="page">
    <div class="toolbar">
      <el-input
        v-model="keyword"
        placeholder="姓名 / 部门 / 工号"
        clearable
        style="width: 220px"
        @keyup.enter="load"
      />
      <el-select v-model="statusFilter" placeholder="全部状态" clearable style="width: 140px" @change="load">
        <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
      </el-select>
      <el-button type="primary" @click="load">查询</el-button>
      <span class="tip">工资模块视角的员工档案（新增 / 编辑在「人员管理」）</span>
    </div>

    <el-table :data="rows" border stripe v-loading="loading">
      <el-table-column prop="employee_no" label="工号" width="110" />
      <el-table-column prop="name" label="姓名" width="120" />
      <el-table-column prop="department" label="部门" min-width="120" />
      <el-table-column prop="position" label="职位" min-width="140" />
      <el-table-column prop="gender" label="性别" width="80" align="center" />
      <el-table-column prop="phone" label="手机号" width="140" />
      <el-table-column label="状态" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="row.status === '在职' ? 'success' : 'info'" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="角色" width="100" align="center">
        <template #default="{ row }">
          <el-tag
            :type="row.role === 'admin' ? 'danger' : row.role === 'gm' ? 'warning' : ''"
            size="small"
          >{{ roleLabel(row.role) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="username" label="登录账号" width="140" />
    </el-table>
    <el-empty v-if="!loading && rows.length === 0" description="暂无员工档案" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { listEmployees } from '@/api/employee'
import type { Employee } from '@/types/employee'

const statusOptions = ['在职', '离职']
const keyword = ref('')
const statusFilter = ref<string | null>(null)
const rows = ref<Employee[]>([])
const loading = ref(false)

function roleLabel(r?: string): string {
  return r === 'admin' ? '管理员' : r === 'gm' ? '总经理' : r === 'employee' ? '员工' : (r || '—')
}

async function load() {
  loading.value = true
  try {
    const params: { keyword?: string; status?: string } = {}
    if (keyword.value.trim()) params.keyword = keyword.value.trim()
    if (statusFilter.value) params.status = statusFilter.value
    const res = await listEmployees(params)
    rows.value = res.data
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.page { padding: 16px; }
.toolbar { display: flex; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; align-items: center; }
.tip { color: var(--el-text-color-secondary); font-size: 13px; }
</style>
