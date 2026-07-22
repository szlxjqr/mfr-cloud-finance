<template>
  <div class="page">
    <el-card shadow="never">
      <div class="toolbar">
        <span class="title">季报（{{ data ? data.as_of : '—' }}）</span>
        <el-select v-model="year" style="width: 110px" @change="load">
          <el-option v-for="y in years" :key="y" :label="y + '年'" :value="y" />
        </el-select>
        <el-select v-model="quarter" style="width: 110px" @change="load">
          <el-option v-for="q in [1,2,3,4]" :key="q" :label="q + '季度'" :value="q" />
        </el-select>
        <el-tag v-if="data && data.months.length" type="info" size="small">涵盖期间：{{ data.months.join('、') }}</el-tag>
      </div>

      <el-alert
        v-if="data && data.note"
        type="info"
        :closable="false"
        :title="data.note"
        style="margin: 12px 0"
      />

      <el-tabs v-model="tab">
        <el-tab-pane label="资产负债表" name="balance">
          <el-table :data="bsRows" border size="small" :show-header="false">
            <el-table-column prop="name" label="项目" min-width="220">
              <template #default="{ row }">
                <span :class="{ sec: row.type === 'section', tot: row.type === 'total' }">{{ row.name }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="amount" label="金额（元）" width="180" align="right">
              <template #default="{ row }">
                <span :class="{ neg: row.amount < 0, tot: row.type === 'total' }">{{ fmt(row.amount) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="利润表（季度累计）" name="income">
          <el-table :data="incRows" border size="small">
            <el-table-column prop="name" label="项目" min-width="240">
              <template #default="{ row }">
                <span :class="{ sec: row.type === 'sec', tot: row.type === 'tot' }">{{ row.name }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="current" label="季度金额（元）" width="180" align="right">
              <template #default="{ row }">
                <span :class="{ neg: row.current < 0, tot: row.type === 'tot' }">{{ fmt(row.current) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="cumulative" label="本年累计（元）" width="180" align="right">
              <template #default="{ row }">
                <span :class="{ neg: row.cumulative < 0, tot: row.type === 'tot' }">{{ fmt(row.cumulative) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="现金流量表" name="cash">
          <el-alert
            v-if="cfData && cfData.net_increase === 0 && cfData.note"
            type="info"
            :closable="false"
            :title="cfData.note"
            style="margin-bottom: 10px"
          />
          <el-table :data="cfRows" border size="small" :show-header="false">
            <el-table-column prop="name" label="项目" min-width="260">
              <template #default="{ row }">
                <span :class="{ sec: row.type === 'sec', tot: row.type === 'tot' }">{{ row.name }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="amount" label="金额（元）" width="180" align="right">
              <template #default="{ row }">
                <span :class="{ neg: row.amount < 0, tot: row.type === 'tot' }">{{ fmt(row.amount) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
      <p class="hint">注：季报资产负债表取季末月份快照，利润表/现金流量表为该季度内各月汇总。数据均由凭证实时派生。</p>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getQuarterly } from '@/api/financial_statement'
import type { QuarterOut } from '@/types/financial_statement'

const route = useRoute()
const years = [2025, 2026, 2027]
const year = ref<number>(2026)
const quarter = ref<number>(3)
const data = ref<QuarterOut | null>(null)

const tab = ref<string>(
  route.name === 'IncomeStatementQuarterly' ? 'income'
  : route.name === 'CashFlowStatementQuarterly' ? 'cash'
  : 'balance'
)

const fmt = (n?: number) =>
  (n ?? 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

const bsData = computed(() => data.value?.balance_sheet ?? null)
const incData = computed(() => data.value?.income ?? null)
const cfData = computed(() => data.value?.cash_flow ?? null)

const bsRows = computed(() => {
  const d = bsData.value
  if (!d) return []
  const out: any[] = []
  for (const sec of d.sections) {
    out.push({ type: 'section', name: sec.name, amount: '' })
    for (const it of sec.items) out.push({ type: 'item', name: `　${it.name}`, amount: it.amount })
    out.push({ type: 'total', name: `${sec.name}合计`, amount: sec.total })
  }
  return out
})

const incRows = computed(() => {
  const d = incData.value
  if (!d) return []
  const out: any[] = []
  const sec = (name: string, lines: any[], cur: number, cum: number) => {
    out.push({ type: 'sec', name, current: '', cumulative: '' })
    for (const l of lines) out.push({ type: 'line', name: `　${l.name}`, current: l.current, cumulative: l.cumulative })
    out.push({ type: 'tot', name: `${name}小计`, current: cur, cumulative: cum })
  }
  sec('营业收入', d.revenue, d.total_revenue_cur, d.total_revenue_cum)
  sec('期间费用', d.expense, d.total_expense_cur, d.total_expense_cum)
  out.push({ type: 'tot', name: '营业利润', current: d.operating_profit_cur, cumulative: d.operating_profit_cum })
  out.push({ type: 'tot', name: '净利润', current: d.net_profit_cur, cumulative: d.net_profit_cum })
  return out
})

const cfRows = computed(() => {
  const d = cfData.value
  if (!d) return []
  const out: any[] = []
  const push = (s: any) => {
    out.push({ type: 'sec', name: s.name, amount: '' })
    for (const it of s.items) out.push({ type: 'line', name: `　${it.name}`, amount: it.amount })
    out.push({ type: 'tot', name: `${s.name}小计`, amount: s.total })
  }
  push(d.operating)
  push(d.investing)
  push(d.financing)
  return out
})

async function load() {
  const res = await getQuarterly(year.value, quarter.value)
  data.value = res.data
}

onMounted(load)
</script>

<style scoped>
.page { padding: 16px; }
.toolbar { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.title { font-size: 18px; font-weight: 600; }
.sec { font-weight: 600; }
.tot { font-weight: 600; background: #fafafa; }
.neg { color: #f56c6c; }
.hint { color: #909399; font-size: 12px; margin-top: 12px; line-height: 1.6; }
</style>
