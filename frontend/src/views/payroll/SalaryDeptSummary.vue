<template>
  <div class="page" ref="pageRef">
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
      <span class="tip">按「部门 + 工资月份」聚合应发/代扣/实发</span>
      <span class="spacer" />
      <el-button type="primary" plain size="small" :icon="Download" :disabled="!rows.length" @click="onExportExcel">导出Excel</el-button>
      <el-button plain size="small" :icon="Download" :disabled="!rows.length" @click="onExportPdf">导出PDF</el-button>
    </div>

    <el-table :data="rows" border stripe v-loading="loading" show-summary :summary-method="summaryMethod">
      <el-table-column prop="department" label="部门" min-width="120" />
      <el-table-column prop="period" label="工资月份" width="120" align="center" />
      <el-table-column prop="headcount" label="人数" width="90" align="center" />
      <el-table-column label="应发合计" align="right">
        <template #default="{ row }">{{ fmt(row.gross_total) }}</template>
      </el-table-column>
      <el-table-column label="社保(个人)" align="right">
        <template #default="{ row }">{{ fmt(row.social_total) }}</template>
      </el-table-column>
      <el-table-column label="公积金(个人)" align="right">
        <template #default="{ row }">{{ fmt(row.fund_total) }}</template>
      </el-table-column>
      <el-table-column label="个税" align="right">
        <template #default="{ row }">{{ fmt(row.tax_total) }}</template>
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
    <el-empty v-if="!loading && rows.length === 0" description="暂无工资数据" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Download } from '@element-plus/icons-vue'
import { exportXlsx, printReport } from '@/utils/exportReport'
import { salaryApi } from '@/api/salary'

const statusOptions = ['草稿', '待审批', '已通过', '已驳回', '已发放']

const period = ref<string | null>(null)
const statusFilter = ref<string | null>(null)
const rows = ref<Record<string, any>[]>([])
const loading = ref(false)
const pageRef = ref<HTMLElement>()

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
    if (['headcount', 'gross_total', 'social_total', 'fund_total', 'tax_total', 'deduct_total', 'net_total'].includes(col.property)) {
      const total = rows.value.reduce((acc, r) => acc + toNum(r[col.property]), 0)
      sums[idx] = col.property === 'headcount' ? String(Math.round(total)) : fmt(total)
    } else {
      sums[idx] = ''
    }
  })
  return sums
}

function xlsxRows(): (string | number | null)[][] {
  const out: (string | number | null)[][] = []
  out.push([`部门工资汇总表（${period.value || '全部月份'}）`])
  out.push([])
  out.push(['部门', '工资月份', '人数', '应发合计', '社保(个人)', '公积金(个人)', '个税', '代扣合计', '实发合计'])
  let h = 0, g = 0, so = 0, f = 0, t = 0, d = 0, n = 0
  for (const r of rows.value) {
    h += toNum(r.headcount); g += toNum(r.gross_total); so += toNum(r.social_total)
    f += toNum(r.fund_total); t += toNum(r.tax_total); d += toNum(r.deduct_total); n += toNum(r.net_total)
    out.push([r.department, r.period, toNum(r.headcount), r.gross_total, r.social_total, r.fund_total, r.tax_total, r.deduct_total, r.net_total])
  }
  out.push([])
  out.push(['合计', '', h, g, so, f, t, d, n])
  return out
}
function onExportExcel() {
  if (!rows.value.length) return
  void exportXlsx(`部门工资汇总_${period.value || '全部'}.xlsx`, [{ name: '部门工资汇总', rows: xlsxRows() }])
}
function onExportPdf() {
  printReport(`部门工资汇总（${period.value || '全部月份'}）`, pageRef.value)
}

async function load() {
  loading.value = true
  try {
    const params: { period?: string; status?: string } = {}
    if (period.value) params.period = period.value
    if (statusFilter.value) params.status = statusFilter.value
    const res = await salaryApi.deptSummary(params)
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
.spacer { flex: 1; }
</style>
