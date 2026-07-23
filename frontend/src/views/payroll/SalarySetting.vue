<template>
  <div class="page">
    <el-row :gutter="16">
      <!-- 社保及公积金设置 -->
      <el-col :span="12">
        <el-card shadow="never" header="社保及公积金设置">
          <el-form :model="form" label-width="140px">
            <el-form-item label="社保个人比例(%)">
              <el-input-number v-model="form.social_personal_rate" :min="0" :max="100" :precision="2" :controls="false" style="width: 100%" />
              <div class="hint">应发 × 该比例 = 社保个人部分</div>
            </el-form-item>
            <el-form-item label="公积金个人比例(%)">
              <el-input-number v-model="form.fund_personal_rate" :min="0" :max="100" :precision="2" :controls="false" style="width: 100%" />
              <div class="hint">应发 × 该比例 = 公积金个人部分</div>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 工资计算设置（个税） -->
      <el-col :span="12">
        <el-card shadow="never" header="工资计算设置（个税）">
          <el-form :model="form" label-width="140px">
            <el-form-item label="个税起征点">
              <el-input-number v-model="form.tax_threshold" :min="0" :max="100000" :precision="2" :controls="false" style="width: 100%" />
              <div class="hint">基本减除费用，默认 5000</div>
            </el-form-item>
            <el-form-item label="个税计算方式">
              <el-radio-group v-model="form.tax_method">
                <el-radio value="月度税率表">月度税率表</el-radio>
                <el-radio value="固定比例">固定比例</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item v-if="form.tax_method === '固定比例'" label="固定税率(%)">
              <el-input-number v-model="form.tax_flat_rate" :min="0" :max="100" :precision="2" :controls="false" style="width: 100%" />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <!-- 试算 -->
    <el-card shadow="never" style="margin-top: 16px" header="设置试算">
      <el-row :gutter="12" align="middle">
        <el-col :span="4">
          <el-input-number v-model="trial.base" :min="0" :precision="2" :controls="false" style="width: 100%" placeholder="应发试算" />
        </el-col>
        <el-col :span="2" style="text-align:center">→</el-col>
        <el-col :span="14">
          <el-descriptions :column="4" border size="small">
            <el-descriptions-item label="社保">{{ fmt(trial.res.social_personal) }}</el-descriptions-item>
            <el-descriptions-item label="公积金">{{ fmt(trial.res.fund_personal) }}</el-descriptions-item>
            <el-descriptions-item label="个税">{{ fmt(trial.res.tax_personal) }}</el-descriptions-item>
            <el-descriptions-item label="实发">{{ fmt(trial.res.net_pay) }}</el-descriptions-item>
          </el-descriptions>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" @click="runTrial">试算</el-button>
        </el-col>
      </el-row>
    </el-card>

    <div style="margin-top: 16px; text-align: right">
      <el-button @click="load">重置</el-button>
      <el-button type="primary" :loading="saving" @click="save">保存设置</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { salaryApi } from '@/api/salary'
import type { SalarySetting } from '@/types/salary'

const defaultForm: SalarySetting = {
  social_personal_rate: 10.5,
  fund_personal_rate: 12,
  tax_threshold: 5000,
  tax_method: '月度税率表',
  tax_flat_rate: 3,
}

const form = reactive<SalarySetting>({ ...defaultForm })
const saving = ref(false)

const trial = reactive({
  base: 25000,
  res: { gross_pay: 0, social_personal: 0, fund_personal: 0, tax_personal: 0, deduct_total: 0, net_pay: 0 },
})

function toNum(v: any): number {
  const n = Number(v)
  return Number.isFinite(n) ? n : 0
}
function fmt(v: any): string {
  return '¥' + toNum(v).toFixed(2)
}

async function load() {
  try {
    const res = await salaryApi.getSetting()
    Object.assign(form, res.data)
  } catch (e: any) {
    ElMessage.warning(e?.response?.data?.detail || '读取设置失败，已载入默认')
    Object.assign(form, defaultForm)
  }
}

async function save() {
  saving.value = true
  try {
    await salaryApi.saveSetting({ ...form })
    ElMessage.success('工资设置已生效')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function runTrial() {
  try {
    const res = await salaryApi.calcDeductions({ base_salary: trial.base })
    Object.assign(trial.res, res.data)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '试算失败')
  }
}

onMounted(load)
</script>

<style scoped>
.page { padding: 16px; }
.hint { font-size: 12px; color: var(--el-text-color-secondary); margin-top: 2px; }
</style>
