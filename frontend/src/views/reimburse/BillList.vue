<template>
  <div class="page">
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索单号/申请人/事由" clearable style="width: 240px" @keyup.enter="load" @clear="load" />
      <el-select v-model="statusFilter" placeholder="全部状态" clearable style="width: 140px" @change="load">
        <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
      </el-select>
      <el-button type="primary" @click="openCreate">新建报销单</el-button>
    </div>

    <el-table :data="list" border stripe>
      <el-table-column prop="bill_no" label="单号" width="160" />
      <el-table-column prop="applicant" label="申请人" width="110" />
      <el-table-column prop="department" label="部门" width="120" />
      <el-table-column prop="amount" label="金额" width="120" align="right">
        <template #default="{ row }">{{ row.amount != null ? '¥' + Number(row.amount).toFixed(2) : '-' }}</template>
      </el-table-column>
      <el-table-column prop="reason" label="事由" show-overflow-tooltip />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTag(row.status)" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="submit_date" label="提交日期" width="120" />
      <el-table-column prop="approve_date" label="审批日期" width="120" />
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button
            v-for="act in transformActions(row)"
            :key="act.action"
            link
            :type="act.type"
            @click="runAction(act.action, row)"
          >{{ act.label }}</el-button>
          <el-button link type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑报销单' : '新建报销单'" width="640px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="单号" v-if="editing">
          <el-input :model-value="form.bill_no ?? ''" disabled />
        </el-form-item>
        <el-form-item label="申请人">
          <el-input v-model="form.applicant" placeholder="必填" />
        </el-form-item>
        <el-form-item label="部门">
          <el-input v-model="form.department" />
        </el-form-item>
        <el-form-item label="金额">
          <el-input v-model.number="form.amount" type="number" placeholder="0.00" />
        </el-form-item>
        <el-form-item label="事由">
          <el-input v-model="form.reason" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { reimburseApi } from '@/api/reimburse'
import type { ReimbursementBill } from '@/types/reimburse'

const statusOptions = ['草稿', '待审批', '已通过', '已驳回', '已支付']

const keyword = ref('')
const statusFilter = ref<string | null>(null)
const list = ref<ReimbursementBill[]>([])
const dialogVisible = ref(false)
const editing = ref(false)
const editingId = ref<number | null>(null)

const emptyForm = () => ({
  bill_no: null as string | null,
  applicant: '',
  department: '',
  amount: null as number | null,
  reason: '',
  remark: '',
})
const form = reactive(emptyForm())

function statusTag(status: string): '' | 'success' | 'warning' | 'danger' | 'info' | 'primary' {
  switch (status) {
    case '待审批':
      return 'warning'
    case '已通过':
      return 'success'
    case '已驳回':
      return 'danger'
    case '已支付':
      return 'primary'
    default:
      return 'info'
  }
}

interface RowAction {
  action: 'submit' | 'approve' | 'reject' | 'pay'
  label: string
  type: 'warning' | 'success' | 'danger' | 'primary'
}

function transformActions(row: ReimbursementBill): RowAction[] {
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
      return [{ action: 'pay', label: '支付', type: 'primary' }]
    default:
      return []
  }
}

async function load() {
  const params: { keyword?: string; status?: string } = {}
  if (keyword.value) params.keyword = keyword.value
  if (statusFilter.value) params.status = statusFilter.value
  const res = await reimburseApi.list(params)
  list.value = res.data
}

function openCreate() {
  Object.assign(form, emptyForm())
  editing.value = false
  editingId.value = null
  dialogVisible.value = true
}
function openEdit(row: ReimbursementBill) {
  Object.assign(form, emptyForm(), row)
  editing.value = true
  editingId.value = row.id
  dialogVisible.value = true
}
async function save() {
  const payload: Record<string, unknown> = { ...form }
  if (payload.amount === '' || payload.amount === null) payload.amount = null
  if (editing.value && editingId.value != null) {
    await reimburseApi.update(editingId.value, payload)
    ElMessage.success('已更新')
  } else {
    await reimburseApi.create(payload)
    ElMessage.success('已创建')
  }
  dialogVisible.value = false
  load()
}
async function runAction(action: RowAction['action'], row: ReimbursementBill) {
  const map = {
    submit: reimburseApi.submit,
    approve: reimburseApi.approve,
    reject: reimburseApi.reject,
    pay: reimburseApi.pay,
  }
  await map[action](row.id)
  ElMessage.success('操作成功')
  load()
}
async function remove(row: ReimbursementBill) {
  await ElMessageBox.confirm(`确认删除报销单 ${row.bill_no ?? row.id}？`, '提示', { type: 'warning' })
  await reimburseApi.remove(row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
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
