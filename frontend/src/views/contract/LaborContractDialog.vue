<template>
  <el-dialog
    v-model="visible"
    :title="editing ? '编辑劳动合同' : '新建劳动合同'"
    width="880px"
    :close-on-click-modal="false"
  >
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
              :disabled="lockedEmployee"
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
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="saving" @click="save">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { hrApi } from '@/api/contract'
import { listEmployees } from '@/api/employee'
import { companyApi } from '@/api/company'
import type { HRContract } from '@/types/contract'
import type { Employee } from '@/types/employee'

/**
 * 劳动合同新建/编辑对话框（可复用）
 *
 * Props:
 *  - modelValue: boolean 弹窗可见性（v-model）
 *  - contract: HRContract | null 编辑时传入；null = 新建
 *  - lockedEmployee: number | null 锁定员工 ID（用于「从员工详情新建」场景，不可改员工）
 *  - onSaved: () => void 保存成功后回调（父组件刷新列表）
 */
const props = defineProps<{
  modelValue: boolean
  contract?: HRContract | null
  lockedEmployee?: number | null
}>()
const emit = defineEmits<{
  'update:modelValue': [val: boolean]
  saved: []
}>()

const visible = ref(props.modelValue)
watch(() => props.modelValue, (v) => (visible.value = v))
watch(visible, (v) => emit('update:modelValue', v))

const editing = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const employeeOptions = ref<Employee[]>([])
const empLoading = ref(false)

const emptyForm = () => ({
  employee_id: null as number | null,
  employee_no: '' as string | null,
  employee_name: '',
  id_number: '' as string | null,
  department: '' as string | null,
  position: '' as string | null,
  phone: '' as string | null,
  contract_type: '劳动合同',
  contract_term: '有固定期限' as string | null,
  sign_date: new Date().toISOString().slice(0, 10) as string | null,
  start_date: new Date().toISOString().slice(0, 10) as string | null,
  end_date: '' as string | null,
  probation_months: 3 as number | null,
  probation_salary: 0 as number | null,
  pay_day: 15 as number | null,
  work_content: '' as string | null,
  work_location: '深圳市' as string | null,
  work_hours_type: '标准工时制' as string | null,
  salary: 0 as number | null,
  pay_method: '计时工资' as string | null,
  benefits: '' as string | null,
  party_a: '' as string | null,
  party_b: '' as string | null,
  status: '草稿',
  remark: '' as string | null,
})
const form = reactive(emptyForm())

async function searchEmployees(q: string) {
  empLoading.value = true
  try {
    const res = await listEmployees({ keyword: q || undefined, status: '在职' })
    employeeOptions.value = res.data
  } finally {
    empLoading.value = false
  }
}

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

async function init() {
  Object.assign(form, emptyForm())
  editing.value = !!props.contract
  editingId.value = props.contract?.id || null
  if (props.contract) {
    // 编辑：填充现有合同
    const c = props.contract
    form.employee_id = c.employee_id || null
    form.employee_no = c.employee_no || ''
    form.employee_name = c.employee_name || ''
    form.id_number = c.id_number || ''
    form.department = c.department || ''
    form.position = c.position || ''
    form.phone = c.phone || ''
    form.contract_type = c.contract_type || '劳动合同'
    form.contract_term = c.contract_term || '有固定期限'
    form.sign_date = c.sign_date || form.sign_date
    form.start_date = c.start_date || form.start_date
    form.end_date = c.end_date || ''
    form.probation_months = c.probation_months ?? 3
    form.probation_salary = c.probation_salary ?? 0
    form.pay_day = c.pay_day ?? 15
    form.work_content = c.work_content || ''
    form.work_location = c.work_location || '深圳市'
    form.work_hours_type = c.work_hours_type || '标准工时制'
    form.salary = c.salary ?? 0
    form.pay_method = c.pay_method || '计时工资'
    form.benefits = c.benefits || ''
    form.party_a = c.party_a || ''
    form.party_b = c.party_b || ''
    form.remark = c.remark || ''
  } else if (props.lockedEmployee) {
    // 从员工详情新建：锁定员工 + 自动带出
    form.employee_id = props.lockedEmployee
  }
  // 加载员工列表（用于 select 选项）
  await searchEmployees('')
  // 甲方自动取公司设置
  try {
    const res = await companyApi.get()
    form.party_a = res.data.company_name || '深圳市流形机器人科技有限公司'
  } catch {
    form.party_a = '深圳市流形机器人科技有限公司'
  }
}

async function save() {
  if (!form.employee_id) {
    ElMessage.warning('请选择员工')
    return
  }
  // 空字符串字段统一置 null
  const payload: Record<string, unknown> = { ...form }
  ;['sign_date', 'start_date', 'end_date', 'salary', 'probation_salary'].forEach((k) => {
    if (payload[k] === '') payload[k] = null
  })
  // 新签合同无状态：保存即草稿
  if (!editing.value) payload.status = '草稿'
  saving.value = true
  try {
    if (editing.value && editingId.value != null) {
      await hrApi.update(editingId.value, payload)
      ElMessage.success('已保存')
    } else {
      await hrApi.create(payload)
      ElMessage.success('已创建')
    }
    visible.value = false
    emit('saved')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

watch(
  () => [props.modelValue, props.contract, props.lockedEmployee],
  ([mv]) => {
    if (mv) init()
  },
  { immediate: true },
)

onMounted(() => {
  if (visible.value) init()
})
</script>
