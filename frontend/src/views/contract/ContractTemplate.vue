<template>
  <div class="page">
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索模板名" clearable style="width: 220px" @clear="load" />
      <el-button type="primary" @click="openCreate">新建模板</el-button>
    </div>
    <el-table :data="list" border stripe>
      <el-table-column type="index" label="#" width="50" />
      <el-table-column prop="name" label="模板名称" />
      <el-table-column prop="ctype" label="类型" />
      <el-table-column prop="remark" label="备注" />
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑模板' : '新建模板'" width="640px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.ctype">
            <el-option label="人事" value="hr" />
            <el-option label="销售" value="sales" />
            <el-option label="采购" value="purchase" />
          </el-select>
        </el-form-item>
        <el-form-item label="内容"><el-input v-model="form.content" type="textarea" :rows="6" /></el-form-item>
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
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { templateApi } from '@/api/contract'
import type { ContractTemplate } from '@/types/contract'

const props = defineProps<{ type: 'hr' | 'sales' | 'purchase' }>()
const ctypeMap: Record<string, string> = { hr: 'hr', sales: 'sales', purchase: 'purchase' }

const keyword = ref('')
const list = ref<ContractTemplate[]>([])
const dialogVisible = ref(false)
const editing = ref(false)
const editingId = ref<number | null>(null)

const emptyForm = () => ({ name: '', ctype: ctypeMap[props.type], content: '', remark: '' })
const form = reactive(emptyForm())

async function load() {
  const res = await templateApi.list({ ctype: ctypeMap[props.type], keyword: keyword.value || undefined })
  list.value = res.data
}
function openCreate() {
  Object.assign(form, emptyForm())
  editing.value = false
  editingId.value = null
  dialogVisible.value = true
}
function openEdit(row: ContractTemplate) {
  Object.assign(form, emptyForm(), row)
  editing.value = true
  editingId.value = row.id
  dialogVisible.value = true
}
async function save() {
  const payload = { ...form }
  if (editing.value && editingId.value != null) {
    await templateApi.update(editingId.value, payload)
    ElMessage.success('已更新')
  } else {
    await templateApi.create(payload)
    ElMessage.success('已创建')
  }
  dialogVisible.value = false
  load()
}
async function remove(row: ContractTemplate) {
  await ElMessageBox.confirm('确认删除？', '提示', { type: 'warning' })
  await templateApi.remove(row.id)
  ElMessage.success('已删除')
  load()
}

load()
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
</style>
