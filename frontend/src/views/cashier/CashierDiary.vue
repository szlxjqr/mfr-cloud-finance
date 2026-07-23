<script setup lang="ts">
/** 出纳 · 日记账：由序时账实时过滤现金(1001)/银行存款(1002) 生成。
 * 数据来自凭证分录（ledgerApi.getJournal），与账务始终一致，零后端改动。
 */
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getJournal } from '@/api/ledger'
import type { JournalLine } from '@/types/ledger'

const CASH = '1001' // 库存现金
const BANK = '1002' // 银行存款

const period = ref<string>('')
const loading = ref(false)
const allLines = ref<JournalLine[]>([])

async function load() {
  loading.value = true
  try {
    const res = await getJournal(period.value || undefined)
    allLines.value = res.data.lines || []
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载日记账失败')
  } finally {
    loading.value = false
  }
}

onMounted(load)

/** 取某科目的日记账流水（含逐笔余额，借正常向） */
function diaryOf(code: string) {
  const lines = allLines.value
    .filter((l) => l.subject_code === code)
    .slice()
    .sort((a, b) => (a.date + a.voucher_no).localeCompare(b.date + b.voucher_no))
  let bal = 0
  return lines.map((l) => {
    const amt = Number(l.amount) || 0
    if (l.direction === '借') bal += amt
    else bal -= amt
    return {
      date: l.date,
      voucher_no: l.voucher_no,
      summary: l.summary || '',
      debit: l.direction === '借' ? amt : 0,
      credit: l.direction === '贷' ? amt : 0,
      balance: bal,
    }
  })
}

const cashRows = computed(() => diaryOf(CASH))
const bankRows = computed(() => diaryOf(BANK))
const cashEnd = computed(() => (cashRows.value.length ? cashRows.value[cashRows.value.length - 1].balance : 0))
const bankEnd = computed(() => (bankRows.value.length ? bankRows.value[bankRows.value.length - 1].balance : 0))
</script>

<template>
  <div style="padding: 16px;">
    <el-card shadow="never" style="margin-bottom: 12px;">
      <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
        <span style="color: #606266; font-size: 14px;">期间</span>
        <el-input v-model="period" placeholder="留空=累计；如 2026-07" style="width: 160px;" clearable @clear="load" />
        <el-button type="primary" @click="load">查询</el-button>
        <el-tag type="info" style="margin-left: auto;">
          现金余额 {{ cashEnd.toFixed(2) }} ｜ 银行存款余额 {{ bankEnd.toFixed(2) }}
        </el-tag>
      </div>
    </el-card>

    <el-tabs>
      <el-tab-pane label="库存现金日记账 (1001)">
        <el-table :data="cashRows" v-loading="loading" border height="520">
          <el-table-column prop="date" label="日期" width="120" />
          <el-table-column prop="voucher_no" label="凭证号" width="120" />
          <el-table-column prop="summary" label="摘要" min-width="160" />
          <el-table-column prop="debit" label="借方" width="130" align="right">
            <template #default="{ row }">{{ row.debit ? row.debit.toFixed(2) : '' }}</template>
          </el-table-column>
          <el-table-column prop="credit" label="贷方" width="130" align="right">
            <template #default="{ row }">{{ row.credit ? row.credit.toFixed(2) : '' }}</template>
          </el-table-column>
          <el-table-column prop="balance" label="余额" width="130" align="right">
            <template #default="{ row }">{{ row.balance.toFixed(2) }}</template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="银行存款日记账 (1002)">
        <el-table :data="bankRows" v-loading="loading" border height="520">
          <el-table-column prop="date" label="日期" width="120" />
          <el-table-column prop="voucher_no" label="凭证号" width="120" />
          <el-table-column prop="summary" label="摘要" min-width="160" />
          <el-table-column prop="debit" label="借方" width="130" align="right">
            <template #default="{ row }">{{ row.debit ? row.debit.toFixed(2) : '' }}</template>
          </el-table-column>
          <el-table-column prop="credit" label="贷方" width="130" align="right">
            <template #default="{ row }">{{ row.credit ? row.credit.toFixed(2) : '' }}</template>
          </el-table-column>
          <el-table-column prop="balance" label="余额" width="130" align="right">
            <template #default="{ row }">{{ row.balance.toFixed(2) }}</template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <el-alert
      type="success"
      :closable="false"
      show-icon
      style="margin-top: 12px;"
      title="数据说明"
      description="日记账由序时账（凭证分录）实时过滤现金/银行存款科目生成，与总账、明细账同源，借贷余额恒一致。"
    />
  </div>
</template>
