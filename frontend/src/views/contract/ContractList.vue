<template>
  <div class="page">
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索" clearable style="width: 220px" @keyup.enter="load" @clear="load" />
      <el-button type="primary" @click="openCreate">新建</el-button>
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
        <el-table-column prop="salary" label="薪资" />
      </template>
      <template v-else>
        <el-table-column prop="contract_no" label="合同号" />
        <el-table-column :label="type === 'sales' ? '客户' : '供应商'">
          <template #default="{ row }">{{ partyName(row) }}</template>
        </el-table-column>
        <el-table-column prop="amount" label="金额" />
        <el-table-column prop="tax_rate" label="税率" />
        <el-table-column prop="tax_amount" label="税额" />
      </template>
      <el-table-column :prop="type === 'hr' ? 'start_date' : 'sign_date'" :label="type === 'hr' ? '开始' : '签立'" />
      <el-table-column prop="end_date" :label="type === 'hr' ? '结束' : '到期'">
        <template #default="{ row }">
          <span>{{ row.end_date }}</span>
          <el-tag v-if="daysLeftText(row)" :type="expireTag(row)" size="small" style="margin-left: 6px">
            {{ daysLeftText(row) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" />
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑' : '新建'" width="640px">
      <el-form :model="form" label-width="110px">
        <template v-if="type === 'hr'">
          <el-form-item label="员工姓名"><el-input v-model="form.employee_name" /></el-form-item>
          <el-form-item label="身份证"><el-input v-model="form.id_number" placeholder="脱敏*原样保留" /></el-form-item>
          <el-form-item label="合同类型">
            <el-select v-model="form.contract_type">
              <el-option label="劳动合同" value="劳动合同" />
              <el-option label="劳务" value="劳务" />
              <el-option label="实习" value="实习" />
              <el-option label="保密" value="保密" />
              <el-option label="竞业" value="竞业" />
            </el-select>
          </el-form-item>
          <el-form-item label="甲方(公司)"><el-input v-model="form.party_a" /></el-form-item>
          <el-form-item label="乙方(员工)"><el-input v-model="form.party_b" /></el-form-item>
          <el-form-item label="薪资"><el-input v-model.number="form.salary" type="number" /></el-form-item>
        </template>
        <template v-else>
          <el-form-item label="合同号"><el-input v-model="form.contract_no" /></el-form-item>
          <el-form-item :label="type === 'sales' ? '客户' : '供应商'">
            <el-select v-model="form.party_id" filterable placeholder="选择">
              <el-option v-for="p in partyOptions" :key="p.id" :label="p.name" :value="p.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="金额"><el-input v-model.number="form.amount" type="number" @input="calcTax" /></el-form-item>
          <el-form-item label="税率"><el-input v-model.number="form.tax_rate" type="number" @input="calcTax" /></el-form-item>
          <el-form-item label="税额"><el-input :model-value="form.tax_amount" disabled /></el-form-item>
        </template>
        <el-form-item :label="type === 'hr' ? '开始日期' : '签立日期'">
          <el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item :label="type === 'hr' ? '结束日期' : '到期日期'">
          <el-date-picker v-model="form.end_date" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status">
            <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
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
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { hrApi, partyApi, purchaseApi, salesApi } from '@/api/contract'
import type { Party } from '@/types/contract'

const props = defineProps<{ type: 'hr' | 'sales' | 'purchase' }>()

const keyword = ref('')
const onlyExpiring = ref(false)
const list = ref<any[]>([])
const partyOptions = ref<Party[]>([])
const dialogVisible = ref(false)
const editing = ref(false)
const editingId = ref<number | null>(null)

const statusOptions = computed(() =>
  props.type === 'hr' ? ['生效', '到期', '终止', '续签中'] : ['草稿', '执行中', '已完成', '终止', '纠纷'],
)

const emptyForm = () => ({
  employee_name: '',
  id_number: '',
  contract_type: '劳动合同',
  party_a: '',
  party_b: '',
  salary: null as number | null,
  contract_no: '',
  party_id: null as number | null,
  amount: null as number | null,
  tax_rate: null as number | null,
  tax_amount: null as number | null,
  start_date: '',
  end_date: '',
  status: props.type === 'hr' ? '生效' : '草稿',
  remark: '',
})
const form = reactive(emptyForm())

const api = computed(() =>
  props.type === 'hr' ? hrApi : props.type === 'sales' ? salesApi : purchaseApi,
)

function partyField() {
  return props.type === 'sales' ? 'customer_id' : 'supplier_id'
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

function openCreate() {
  Object.assign(form, emptyForm())
  editing.value = false
  editingId.value = null
  dialogVisible.value = true
}
function openEdit(row: any) {
  Object.assign(form, emptyForm(), row)
  form.party_id = row.customer_id ?? row.supplier_id ?? null
  editing.value = true
  editingId.value = row.id
  dialogVisible.value = true
}
async function save() {
  const payload: any = { ...form }
  if (props.type !== 'hr') {
    delete payload.customer_id
    delete payload.supplier_id
    payload[partyField()] = form.party_id
  }
  delete payload.party_id
  // 空字符串字段统一置 null，避免后端校验失败
  ;['salary', 'amount', 'tax_rate', 'start_date', 'end_date', 'sign_date', 'effective_date', 'expire_date'].forEach(
    (k) => {
      if (payload[k] === '') payload[k] = null
    },
  )
  if (editing.value && editingId.value != null) {
    await api.value.update(editingId.value, payload)
    ElMessage.success('已更新')
  } else {
    await api.value.create(payload)
    ElMessage.success('已创建')
  }
  dialogVisible.value = false
  load()
}
async function remove(row: any) {
  await ElMessageBox.confirm('确认删除该合同？', '提示', { type: 'warning' })
  await api.value.remove(row.id)
  ElMessage.success('已删除')
  load()
}
function toggleExpiring() {
  onlyExpiring.value = !onlyExpiring.value
}

onMounted(() => {
  load()
  loadParties()
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
