<template>
  <div class="page">
    <el-card shadow="never">
      <div class="toolbar">
        <span class="title">利润表</span>
        <el-date-picker
          v-model="period"
          type="month"
          value-format="YYYY-MM"
          placeholder="选择期间（留空=累计）"
          clearable
          style="width: 220px"
        />
        <span class="as-of">期间：{{ data?.period || '累计' }}</span>
      </div>

      <el-table :data="rows" border size="small" style="margin-top: 8px">
        <el-table-column prop="name" label="项目" min-width="240">
          <template #default="{ row }">
            <span :class="{ sec: row.type === 'sec', tot: row.type === 'tot' }">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="current" label="本期金额（元）" width="170" align="right">
          <template #default="{ row }">
            <span :class="{ neg: row.current < 0, tot: row.type === 'tot' }">{{ fmt(row.current) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="cumulative" label="本年累计（元）" width="170" align="right">
          <template #default="{ row }">
            <span :class="{ neg: row.cumulative < 0, tot: row.type === 'tot' }">{{ fmt(row.cumulative) }}</span>
          </template>
        </el-table-column>
      </el-table>
      <p class="hint">注：数据由凭证分录实时汇总；本期金额取「本期发生额」，本年累计取「累计发生额」。</p>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getIncomeStatement } from '@/api/financial_statement'
import type { IncomeStatementOut } from '@/types/financial_statement'

const period = ref<string>('')
const data = ref<IncomeStatementOut | null>(null)

const fmt = (n?: number) =>
  (n ?? 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

const rows = computed(() => {
  if (!data.value) return []
  const d = data.value
  const out: any[] = []
  const pushSec = (name: string, lines: any[], subtotalCur: number, subtotalCum: number) => {
    out.push({ type: 'sec', name, current: '', cumulative: '' })
    for (const l of lines) out.push({ type: 'line', name: `　${l.name}`, current: l.current, cumulative: l.cumulative })
    out.push({ type: 'tot', name: `${name}小计`, current: subtotalCur, cumulative: subtotalCum })
  }
  pushSec('营业收入', d.revenue, d.total_revenue_cur, d.total_revenue_cum)
  pushSec('营业成本', d.cost, d.total_expense_cur * 0, d.total_expense_cum * 0)
  pushSec('期间费用', d.expense, d.total_expense_cur, d.total_expense_cum)
  out.push({ type: 'tot', name: '营业利润', current: d.operating_profit_cur, cumulative: d.operating_profit_cum })
  out.push({ type: 'tot', name: '利润总额', current: d.total_profit_cur, cumulative: d.total_profit_cum })
  out.push({ type: 'tot', name: '净利润', current: d.net_profit_cur, cumulative: d.net_profit_cum })
  return out
})

async function load() {
  const res = await getIncomeStatement(period.value || undefined)
  data.value = res.data
}

onMounted(load)
</script>

<style scoped>
.page { padding: 16px; }
.toolbar { display: flex; align-items: center; gap: 16px; }
.title { font-size: 18px; font-weight: 600; }
.as-of { color: #909399; font-size: 13px; }
.sec { font-weight: 600; }
.tot { font-weight: 600; background: #fafafa; }
.neg { color: #f56c6c; }
.hint { color: #909399; font-size: 12px; margin-top: 12px; }
</style>
