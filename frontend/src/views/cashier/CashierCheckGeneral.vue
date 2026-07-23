<script setup lang="ts">
/** 出纳 · 核对总账：将现金/银行存款「日记账流水余额」与「总账期末余额」逐项比对。
 * 两者同源（均来自凭证分录），一致即说明账务无串户/漏记。零后端改动。
 */
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getJournal, getLedgerSummary } from '@/api/ledger'
import type { JournalLine, LedgerSummaryRow } from '@/types/ledger'

const period = ref<string>('')
const loading = ref(false)
const journalLines = ref<JournalLine[]>([])
const summary = ref<LedgerSummaryRow[]>([])

const CASH = '1001'
const BANK = '1002'

async function load() {
  loading.value = true
  try {
    const [j, s] = await Promise.all([
      getJournal(period.value || undefined),
      getLedgerSummary(period.value || undefined),
    ])
    journalLines.value = j.data.lines || []
    summary.value = s.data || []
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载核对数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(load)

/** 某科目日记账流水末笔余额（借正常向） */
function journalEnd(code: string): number {
  const lines = journalLines.value
    .filter((l) => l.subject_code === code)
    .sort((a, b) => (a.date + a.voucher_no).localeCompare(b.date + b.voucher_no))
  let bal = 0
  for (const l of lines) {
    const amt = Number(l.amount) || 0
    bal += l.direction === '借' ? amt : -amt
  }
  return bal
}

/** 某科目总账期末余额（借正常向） */
function ledgerEnd(code: string): number {
  const row = summary.value.find((r) => r.code === code)
  if (!row) return 0
  return row.ending_debit - row.ending_credit
}

const rows = computed(() => {
  return [CASH, BANK].map((code) => {
    const j = journalEnd(code)
    const g = ledgerEnd(code)
    return {
      code,
      name: summary.value.find((r) => r.code === code)?.name || (code === CASH ? '库存现金' : '银行存款'),
      journal: j,
      ledger: g,
      diff: +(j - g).toFixed(2),
      ok: Math.abs(j - g) < 0.005,
    }
  })
})

const allOk = computed(() => rows.value.every((r) => r.ok))
</script>

<template>
  <div style="padding: 16px;">
    <el-card shadow="never" style="margin-bottom: 12px;">
      <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
        <span style="color: #606266; font-size: 14px;">期间</span>
        <el-input v-model="period" placeholder="留空=累计；如 2026-07" style="width: 160px;" clearable @clear="load" />
        <el-button type="primary" @click="load">核对</el-button>
        <el-tag :type="allOk ? 'success' : 'danger'" style="margin-left: auto;">
          {{ allOk ? '✓ 现金类科目账账相符' : '✗ 存在差额，请检查凭证' }}
        </el-tag>
      </div>
    </el-card>

    <el-table :data="rows" v-loading="loading" border>
      <el-table-column prop="code" label="科目编码" width="120" />
      <el-table-column prop="name" label="科目名称" min-width="140" />
      <el-table-column label="日记账余额(流水)" width="180" align="right">
        <template #default="{ row }">{{ row.journal.toFixed(2) }}</template>
      </el-table-column>
      <el-table-column label="总账期末余额" width="180" align="right">
        <template #default="{ row }">{{ row.ledger.toFixed(2) }}</template>
      </el-table-column>
      <el-table-column label="差额" width="140" align="right">
        <template #default="{ row }">
          <span :style="row.ok ? 'color:#67c23a;font-weight:600' : 'color:#f56c6c;font-weight:600'">
            {{ row.diff.toFixed(2) }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="核对结果" width="140" align="center">
        <template #default="{ row }">
          <el-tag :type="row.ok ? 'success' : 'danger'">{{ row.ok ? '相符' : '不符' }}</el-tag>
        </template>
      </el-table-column>
    </el-table>

    <el-alert
      type="info"
      :closable="false"
      show-icon
      style="margin-top: 12px;"
      title="核对口径"
      description="日记账余额 = 现金/银行存款科目凭证分录逐笔滚动；总账余额 = 同一科目按期间汇总的期末数。两者同源，相符即账账一致。"
    />
  </div>
</template>
