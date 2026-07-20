<template>
  <div class="page">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="客户" name="customer" />
      <el-tab-pane label="供应商" name="supplier" />
    </el-tabs>
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索名称" clearable style="width: 220px" @clear="load" />
      <el-button type="primary" @click="openCreate">新建</el-button>
    </div>
    <el-table :data="list" border stripe>
      <el-table-column type="index" label="#" width="50" />
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="tax_no" label="税号" />
      <el-table-column prop="contact" label="联系人" />
      <el-table-column prop="phone" label="电话" />
      <el-table-column prop="status" label="状态" />
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑' : '新建'" width="560px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="税号"><el-input v-model="form.tax_no" /></el-form-item>
        <el-form-item label="联系人"><el-input v-model="form.contact" /></el-form-item>
        <el-form-item label="电话"><el-input v-model="form.phone" /></el-form-item>
        <el-form-item label="地址"><el-input v-model="form.address" /></el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status">
            <el-option label="启用" value="enabled" />
            <el-option label="停用" value="disabled" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="form.remark" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { partyApi } from '@/api/contract'
import type { Party } from '@/types/contract'

const activeTab = ref<'customer' | 'supplier'>('customer')
const keyword = ref('')
const list = ref<Party[]>([])
const dialogVisible = ref(false)
const editing = ref(false)
const editingId = ref<number | null>(null)

const emptyForm = () => ({
  name: '',
  tax_no: '',
  contact: '',
  phone: '',
  address: '',
  status: 'enabled',
  remark: '',
})
const form = reactive(emptyForm())

async function load() {
  const res = await partyApi.list({ ptype: activeTab.value, keyword: keyword.value || undefined })
  list.value = res.data
}
function openCreate() {
  Object.assign(form, emptyForm())
  editing.value = false
  editingId.value = null
  dialogVisible.value = true
}
function openEdit(row: Party) {
  Object.assign(form, emptyForm(), row)
  editing.value = true
  editingId.value = row.id
  dialogVisible.value = true
}
async function save() {
  const payload = { ...form, ptype: activeTab.value }
  if (editing.value && editingId.value != null) {
    await partyApi.update(editingId.value, payload)
    ElMessage.success('已更新')
  } else {
    await partyApi.create(payload)
    ElMessage.success('已创建')
  }
  dialogVisible.value = false
  load()
}
async function remove(row: Party) {
  await ElMessageBox.confirm('确认删除？', '提示', { type: 'warning' })
  await partyApi.remove(row.id)
  ElMessage.success('已删除')
  load()
}

watch(activeTab, load)
load()
</script>

<style scoped>
.page {
  padding: 16px;
}
.toolbar {
  display: flex;
  gap: 12px;
  margin: 12px 0;
}
</style>
