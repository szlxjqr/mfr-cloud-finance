<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getIndividualTax } from '@/api/tax'
import { formatNumber } from '@/utils/format'
import { Refresh, Download } from '@element-plus/icons-vue'
import { exportXlsx, printReport } from '@/utils/exportReport'
import dayjs from 'dayjs'
import type { IndividualTax } from '@/types/tax'

/** 期间选择器（默认当前月） */
const period = ref(dayjs().format('YYYY-MM'))
const loading = ref(false)
const data = ref<IndividualTax | null>(null)

async function load() {
  loading.value = true
  try {
    const res = await getIndividualTax(period.value)
    data.value = res.data
  } finally {
    loading.value = false
  }
}

onMounted(load)

const rows = computed(() => data.value?.rows ?? [])
const totalTax = computed(() => data.value?.total_tax ?? 0)
const totalGross = computed(() => data.value?.total_gross ?? 0)
const headcount = computed(() => data.value?.headcount ?? 0)

const pageRef = ref<HTMLElement>()
function xlsxRows(): (string | number | null)[][] {
  const out: (string | number | null)[][] = []
  out.push([`个税申报明细（${period.value}）`])
  out.push([])
  out.push(['员工', '工号', '部门', '工资月份', '应发', '社保(个人)', '公积金(个人)', '个人所得税'])
  for (const r of rows.value) {
    out.push([
      r.employee_name,
      r.employee_no,
      r.department,
      r.period,
      r.gross_pay,
      r.social_personal,
      r.fund_personal,
      r.tax_personal,
    ])
  }
  out.push([])
  out.push(['合计', '', '', '', totalGross.value, '', '', totalTax.value])
  return out
}
function onExportExcel() {
  if (!rows.value.length) return
  void exportXlsx(`个税申报_${period.value}.xlsx`, [{ name: '个税申报', rows: xlsxRows() }])
}
function onExportPdf() {
  printReport(`个税申报（${period.value}）`, pageRef.value)
}
</script>

<template>
  <div class="tax-individual" ref="pageRef">
    <!-- 期间选择 + 刷新 -->
    <el-card shadow="never" class="bar-card">
      <div class="bar">
        <div class="section-title">
          <span class="triangle" />
          <span>个税申报（工资代扣代缴）</span>
        </div>
        <div class="tools">
          <el-date-picker
            v-model="period"
            type="month"
            value-format="YYYY-MM"
            placeholder="选择月份"
            size="small"
            @change="load"
          />
          <el-button
            :icon="Refresh"
            circle
            size="small"
            :loading="loading"
            @click="load"
          />
          <span class="spacer" />
          <el-button
            type="primary"
            plain
            size="small"
            :icon="Download"
            :disabled="!rows.length"
            @click="onExportExcel"
          >导出Excel</el-button>
          <el-button
            plain
            size="small"
            :icon="Download"
            :disabled="!rows.length"
            @click="onExportPdf"
          >导出PDF</el-button>
        </div>
      </div>
    </el-card>

    <!-- KPI 卡片 -->
    <div class="kpi-row" v-loading="loading">
      <el-card shadow="never" class="kpi">
        <div class="kpi-label">申报人数</div>
        <div class="kpi-value">{{ headcount }}</div>
        <div class="kpi-unit">人</div>
      </el-card>
      <el-card shadow="never" class="kpi">
        <div class="kpi-label">应发合计</div>
        <div class="kpi-value">{{ formatNumber(totalGross) }}</div>
        <div class="kpi-unit">元</div>
      </el-card>
      <el-card shadow="never" class="kpi warn">
        <div class="kpi-label">{{ period }} 应申报个税</div>
        <div class="kpi-value">{{ formatNumber(totalTax) }}</div>
        <div class="kpi-unit">元</div>
      </el-card>
    </div>

    <!-- 明细表 -->
    <el-card shadow="never" class="table-card">
      <template #header>
        <div class="section-title">
          <span class="triangle" />
          <span>个税明细（按员工 × 期间聚合，仅统计已通过/已发放工资单）</span>
        </div>
      </template>
      <el-table :data="rows" size="small" empty-text="本期无工资个税数据">
        <el-table-column prop="employee_name" label="员工" width="110" />
        <el-table-column prop="employee_no" label="工号" width="110" />
        <el-table-column prop="department" label="部门" width="130" />
        <el-table-column prop="period" label="工资月份" width="110" align="center" />
        <el-table-column label="应发" width="130" align="right">
          <template #default="{ row }">{{ formatNumber(row.gross_pay) }}</template>
        </el-table-column>
        <el-table-column label="社保(个人)" width="130" align="right">
          <template #default="{ row }">{{ formatNumber(row.social_personal) }}</template>
        </el-table-column>
        <el-table-column label="公积金(个人)" width="130" align="right">
          <template #default="{ row }">{{ formatNumber(row.fund_personal) }}</template>
        </el-table-column>
        <el-table-column label="个人所得税" width="140" align="right">
          <template #default="{ row }">
            <span style="font-weight: 600; color: #e6a23c">{{ formatNumber(row.tax_personal) }}</span>
          </template>
        </el-table-column>
      </el-table>
      <div class="detail-total" v-if="rows.length">
        合计：应发 <b>{{ formatNumber(totalGross) }}</b> 元 ｜ 个人所得税
        <b style="color: #e6a23c">{{ formatNumber(totalTax) }}</b> 元（共 {{ headcount }} 人）
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.tax-individual {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.tools {
  display: flex;
  align-items: center;
  gap: 8px;
}
.spacer {
  flex: 1;
}
.kpi-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}
.kpi {
  text-align: center;
}
.kpi-label {
  font-size: 13px;
  color: #909399;
}
.kpi-value {
  font-size: 26px;
  font-weight: 700;
  color: #303133;
  margin: 6px 0 2px;
}
.kpi-unit {
  font-size: 12px;
  color: #c0c4cc;
}
.kpi.warn .kpi-value {
  color: #e6a23c;
}
.detail-total {
  margin-top: 10px;
  text-align: right;
  font-size: 13px;
  color: #606266;
}
.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}
.triangle {
  width: 0;
  height: 0;
  border-top: 6px solid transparent;
  border-bottom: 6px solid transparent;
  border-left: 10px solid #409eff;
}
@media (max-width: 980px) {
  .kpi-row {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
