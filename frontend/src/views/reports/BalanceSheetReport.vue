<template>
  <div class="page" ref="cardRef">
    <el-card shadow="never">
      <div class="toolbar">
        <span class="title">资产负债表</span>
        <el-date-picker
          v-model="period"
          type="month"
          value-format="YYYY-MM"
          placeholder="选择期间（留空=累计）"
          clearable
          style="width: 220px"
        />
        <span class="as-of">编制：{{ data?.as_of || '—' }}</span>
        <span class="spacer" />
        <el-button type="primary" plain size="small" :icon="Download" :disabled="!data" @click="onExportExcel">导出Excel</el-button>
        <el-button plain size="small" :disabled="!data" @click="onExportPdf">导出PDF</el-button>
      </div>

      <el-alert
        v-if="data && !data.balanced"
        type="error"
        :closable="false"
        :title="data.note || '资产与负债+权益不平衡'"
        style="margin-bottom: 12px"
      />

      <el-table :data="rows" border size="small" :show-header="false" style="margin-top: 8px">
        <el-table-column prop="name" label="项目" min-width="220">
          <template #default="{ row }">
            <span :class="{ 'sec': row.type === 'section', 'tot': row.type === 'total' }">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="金额（元）" width="180" align="right">
          <template #default="{ row }">
            <span :class="{ neg: row.amount < 0, tot: row.type === 'total' }">{{ fmt(row.amount) }}</span>
          </template>
        </el-table-column>
      </el-table>

      <el-descriptions :column="3" border size="small" style="margin-top: 16px">
        <el-descriptions-item label="资产总计">{{ fmt(data?.total_assets) }}</el-descriptions-item>
        <el-descriptions-item label="负债总计">{{ fmt(data?.total_liabilities) }}</el-descriptions-item>
        <el-descriptions-item label="所有者权益总计">{{ fmt(data?.total_equity) }}</el-descriptions-item>
      </el-descriptions>
      <p class="hint">注：损益类科目按「表结法」自动结转至「本年利润」，使 资产 = 负债 + 所有者权益 恒等。应交税费为负表示留抵税额。</p>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Download } from '@element-plus/icons-vue'
import { getBalanceSheet } from '@/api/financial_statement'
import type { BalanceSheetOut } from '@/types/financial_statement'
import { exportXlsx, printReport } from '@/utils/exportReport'

const period = ref<string>('')
const data = ref<BalanceSheetOut | null>(null)
const cardRef = ref<HTMLElement>()

const fmt = (n?: number) =>
  (n ?? 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

const rows = computed(() => {
  if (!data.value) return []
  const out: any[] = []
  for (const sec of data.value.sections) {
    out.push({ type: 'section', name: sec.name, amount: '' })
    for (const it of sec.items) {
      out.push({ type: 'item', name: `　${it.name}`, amount: it.amount })
    }
    out.push({ type: 'total', name: `${sec.name}合计`, amount: sec.total })
  }
  return out
})

async function load() {
  const res = await getBalanceSheet(period.value || undefined)
  data.value = res.data
}

function xlsxRows(): (string | number | null)[][] {
  const out: (string | number | null)[][] = []
  out.push(['资产负债表', data.value?.as_of || '累计'])
  out.push([])
  out.push(['项目', '金额（元）'])
  for (const r of rows.value) {
    out.push([r.name, typeof r.amount === 'number' ? r.amount : null])
  }
  out.push([])
  out.push(['资产总计', data.value?.total_assets ?? null])
  out.push(['负债总计', data.value?.total_liabilities ?? null])
  out.push(['所有者权益总计', data.value?.total_equity ?? null])
  return out
}

async function onExportExcel() {
  if (!data.value) return
  await exportXlsx(`资产负债表_${data.value.as_of || '累计'}.xlsx`, [
    { name: '资产负债表', rows: xlsxRows() },
  ])
}

function onExportPdf() {
  if (!data.value) return
  printReport(`资产负债表（${data.value.as_of || '累计'}）`, cardRef.value)
}

onMounted(load)
</script>

<style scoped>
.page { padding: 16px; }
.toolbar { display: flex; align-items: center; gap: 16px; }
.title { font-size: 18px; font-weight: 600; }
.as-of { color: #909399; font-size: 13px; }
.sec { font-weight: 600; }
.tot { font-weight: 600; }
.neg { color: #f56c6c; }
.hint { color: #909399; font-size: 12px; margin-top: 12px; line-height: 1.6; }
.spacer { flex: 1; }
</style>
