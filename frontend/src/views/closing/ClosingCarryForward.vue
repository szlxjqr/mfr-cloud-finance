<script setup lang="ts">
/** 结账 · 期末结转预览：由科目汇总表实时计算损益类科目「本期发生额」，
 * 给出结转至「本年利润(3103)」的预览分录。
 * 仅预览——实际生成结转凭证请在「凭证管理」模块操作。零后端改动。
 */
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getLedgerSummary } from '@/api/ledger'
import type { LedgerSummaryRow } from '@/types/ledger'

const period = ref<string>('')
const loading = ref(false)
const summary = ref<LedgerSummaryRow[]>([])

// 损益类科目（与财务报表引擎口径一致）
const EXPENSE_CODES = [
  ['5401', '主营业务成本'],
  ['5501', '其他业务成本'],
  ['5601', '销售费用'],
  ['5602', '管理费用'],
  ['5603', '财务费用'],
  ['5801', '所得税费用'],
] as const
const REVENUE_CODES = [
  ['5001', '主营业务收入'],
  ['5051', '其他业务收入'],
] as const

async function load() {
  loading.value = true
  try {
    const res = await getLedgerSummary(period.value || undefined)
    summary.value = res.data || []
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载结转数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(load)

/** 本期净额（借正常向科目：借-贷；贷正常向科目：贷-借） */
function netOf(code: string): number {
  const r = summary.value.find((x) => x.code === code || x.code.startsWith(code + '.'))
  if (!r) return 0
  if (r.direction === '借') return +(r.period_debit - r.period_credit).toFixed(2)
  return +(r.period_credit - r.period_debit).toFixed(2)
}

// 结转分录 1：借 损益费用/成本(净额) ｜ 贷 本年利润(3103)
const expenseRows = computed(() =>
  EXPENSE_CODES.map(([code, name]) => ({ code, name, amount: netOf(code) }))
    .filter((r) => Math.abs(r.amount) > 0.005),
)
const expenseTotal = computed(() => +expenseRows.value.reduce((s, r) => s + r.amount, 0).toFixed(2))

// 结转分录 2：借 本年利润(3103) ｜ 贷 损益收入(净额)
const revenueRows = computed(() =>
  REVENUE_CODES.map(([code, name]) => ({ code, name, amount: netOf(code) }))
    .filter((r) => Math.abs(r.amount) > 0.005),
)
const revenueTotal = computed(() => +revenueRows.value.reduce((s, r) => s + r.amount, 0).toFixed(2))

// 净利润（收入-费用），与利润表一致
const netProfit = computed(() => +(revenueTotal.value - expenseTotal.value).toFixed(2))
const hasData = computed(() => expenseRows.value.length > 0 || revenueRows.value.length > 0)
</script>

<template>
  <div style="padding: 16px;">
    <el-card shadow="never" style="margin-bottom: 12px;">
      <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
        <span style="color: #606266; font-size: 14px;">结转期间</span>
        <el-input v-model="period" placeholder="留空=累计；如 2026-07" style="width: 170px;" clearable @clear="load" />
        <el-button type="primary" @click="load">计算结转</el-button>
        <el-tag :type="hasData ? 'warning' : 'info'" style="margin-left: auto;">
          {{ hasData ? '本期存在损益，可结转' : '本期无损益发生额' }}
        </el-tag>
      </div>
    </el-card>

    <el-empty v-if="!hasData && !loading" description="所选期间无损益类科目发生额，无需结转" />

    <template v-else>
      <!-- 结转分录 1：损益费用/成本 → 本年利润 -->
      <el-card shadow="never" style="margin-bottom: 12px;" header="结转分录（一）：结转成本费用">
        <el-table :data="expenseRows" v-loading="loading" border>
          <el-table-column label="方向" width="90" align="center">
            <template #default><el-tag type="danger">借</el-tag></template>
          </el-table-column>
          <el-table-column prop="code" label="科目编码" width="120" />
          <el-table-column prop="name" label="科目名称" min-width="160" />
          <el-table-column label="本期发生额" width="160" align="right">
            <template #default="{ row }">{{ row.amount.toFixed(2) }}</template>
          </el-table-column>
        </el-table>
        <div style="margin-top: 8px; color: #606266; font-size: 13px;">
          对应贷方：<b>本年利润 (3103)</b> ｜ 金额
          <b style="color: #f56c6c;">{{ expenseTotal.toFixed(2) }}</b>
        </div>
      </el-card>

      <!-- 结转分录 2：本年利润 → 损益收入 -->
      <el-card shadow="never" style="margin-bottom: 12px;" header="结转分录（二）：结转收入">
        <el-table :data="revenueRows" v-loading="loading" border>
          <el-table-column label="方向" width="90" align="center">
            <template #default><el-tag type="success">贷</el-tag></template>
          </el-table-column>
          <el-table-column prop="code" label="科目编码" width="120" />
          <el-table-column prop="name" label="科目名称" min-width="160" />
          <el-table-column label="本期发生额" width="160" align="right">
            <template #default="{ row }">{{ row.amount.toFixed(2) }}</template>
          </el-table-column>
        </el-table>
        <div style="margin-top: 8px; color: #606266; font-size: 13px;">
          对应借方：<b>本年利润 (3103)</b> ｜ 金额
          <b style="color: #67c23a;">{{ revenueTotal.toFixed(2) }}</b>
        </div>
      </el-card>

      <el-alert
        type="warning"
        :closable="false"
        show-icon
        title="结转结果预览"
        :description="`本期净利润 = 收入 ${revenueTotal.toFixed(2)} − 费用成本 ${expenseTotal.toFixed(2)} = ${netProfit.toFixed(2)}。此为预览，实际需在「凭证管理」生成结转凭证并记账后，资产负债表方体现本年利润。`"
      />
    </template>
  </div>
</template>
