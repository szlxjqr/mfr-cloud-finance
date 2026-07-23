<template>
  <div class="page">
    <div class="toolbar">
      <el-date-picker
        v-model="period"
        type="month"
        value-format="YYYY-MM"
        placeholder="全部月份"
        clearable
        style="width: 180px"
        @change="load"
      />
      <el-select v-model="statusFilter" placeholder="全部状态" clearable style="width: 140px" @change="load">
        <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
      </el-select>
      <el-button type="primary" @click="load">查询</el-button>
      <span class="tip">按部门归集工资成本，ratio = 部门应发 ÷ 工资总额</span>
    </div>

    <div class="kpis" v-loading="loading">
      <el-card shadow="never" class="kpi">
        <div class="k-label">工资总额（应发）</div>
        <div class="k-value">{{ fmt(data.total_gross) }}</div>
      </el-card>
      <el-card shadow="never" class="kpi">
        <div class="k-label">人均工资</div>
        <div class="k-value">{{ fmt(data.avg_gross) }}</div>
      </el-card>
      <el-card shadow="never" class="kpi">
        <div class="k-label">研发投入人力成本占比</div>
        <div class="k-value" style="color: var(--el-color-primary)">{{ (data.rd_ratio * 100).toFixed(1) }}%</div>
      </el-card>
      <el-card shadow="never" class="kpi">
        <div class="k-label">归集部门数</div>
        <div class="k-value">{{ data.rows.length }}</div>
      </el-card>
    </div>

    <el-table :data="data.rows" border stripe v-loading="loading" show-summary :summary-method="summaryMethod">
      <el-table-column prop="department" label="部门" min-width="140" />
      <el-table-column prop="headcount" label="人数" width="90" align="center" />
      <el-table-column label="应发合计" align="right">
        <template #default="{ row }">{{ fmt(row.gross_total) }}</template>
      </el-table-column>
      <el-table-column label="分摊占比" min-width="200">
        <template #default="{ row }">
          <div class="ratio-cell">
            <el-progress :percentage="Math.round(row.ratio * 100)" :stroke-width="14" />
            <span class="ratio-num">{{ (row.ratio * 100).toFixed(1) }}%</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="代扣合计" align="right">
        <template #default="{ row }">{{ fmt(row.deduct_total) }}</template>
      </el-table-column>
      <el-table-column label="实发合计" align="right">
        <template #default="{ row }">
          <span style="font-weight: 600; color: var(--el-color-success)">{{ fmt(row.net_total) }}</span>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!loading && data.rows.length === 0" description="暂无工资数据" />

    <el-alert
      class="note"
      type="info"
      :closable="false"
      show-icon
      title="分摊口径说明"
      description="当前按「部门」归集工资成本（部门应发 ÷ 工资总额 = 分摊权重）。若需进一步按产品线 / 研发项目二次分摊，需在工资设置中配置分摊规则。"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { salaryApi } from '@/api/salary'
import type { SalaryAllocation } from '@/types/salary'

const statusOptions = ['草稿', '待审批', '已通过', '已驳回', '已发放']
const period = ref<string | null>(null)
const statusFilter = ref<string | null>(null)
const loading = ref(false)
const data = ref<SalaryAllocation>({
  total_gross: 0,
  total_headcount: 0,
  avg_gross: 0,
  rd_ratio: 0,
  rows: [],
})

function toNum(v: any): number {
  const n = Number(v)
  return Number.isFinite(n) ? n : 0
}
function fmt(v: any): string {
  return '¥' + toNum(v).toFixed(2)
}
function summaryMethod({ columns }: any) {
  const sums: string[] = []
  columns.forEach((col: any, idx: number) => {
    if (idx === 0) {
      sums[idx] = '合计'
      return
    }
    if (['headcount', 'gross_total', 'deduct_total', 'net_total'].includes(col.property)) {
      const total = data.value.rows.reduce((acc, r) => acc + toNum((r as any)[col.property]), 0)
      sums[idx] = col.property === 'headcount' ? String(Math.round(total)) : fmt(total)
    } else if (col.property === 'ratio') {
      sums[idx] = '100%'
    } else {
      sums[idx] = ''
    }
  })
  return sums
}

async function load() {
  loading.value = true
  try {
    const params: { period?: string; status?: string } = {}
    if (period.value) params.period = period.value
    if (statusFilter.value) params.status = statusFilter.value
    const res = await salaryApi.allocation(params)
    data.value = res.data
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
.kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
.kpi { text-align: center; }
.k-label { color: var(--el-text-color-secondary); font-size: 13px; margin-bottom: 6px; }
.k-value { font-size: 22px; font-weight: 700; }
.ratio-cell { display: flex; align-items: center; gap: 8px; }
.ratio-cell .el-progress { flex: 1; }
.ratio-num { font-size: 13px; color: var(--el-text-color-secondary); min-width: 48px; text-align: right; }
.note { margin-top: 12px; }
@media (max-width: 900px) { .kpis { grid-template-columns: repeat(2, 1fr); } }
</style>
