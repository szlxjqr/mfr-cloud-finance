<template>
  <div class="page">
    <el-card shadow="never">
      <div class="toolbar">
        <span class="title">现金流量表</span>
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

      <el-alert
        v-if="data && data.net_increase === 0 && data.note"
        type="info"
        :closable="false"
        :title="data.note"
        style="margin: 12px 0"
      />

      <el-table :data="rows" border size="small" :show-header="false" style="margin-top: 8px">
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

      <el-descriptions :column="1" border size="small" style="margin-top: 16px">
        <el-descriptions-item label="现金及现金等价物净增加额">
          <span :class="{ neg: (data?.net_increase ?? 0) < 0 }">{{ fmt(data?.net_increase) }}</span>
        </el-descriptions-item>
      </el-descriptions>
      <p class="hint">注：以库存现金/银行存款的分录为入口，按对方科目类别归类 经营 / 投资 / 筹资 活动。本期无现金类凭证时表为空。</p>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getCashFlow } from '@/api/financial_statement'
import type { CashFlowOut } from '@/types/financial_statement'

const period = ref<string>('')
const data = ref<CashFlowOut | null>(null)

const fmt = (n?: number) =>
  (n ?? 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

const rows = computed(() => {
  if (!data.value) return []
  const out: any[] = []
  const push = (sec: any) => {
    out.push({ type: 'sec', name: sec.name, amount: '' })
    for (const it of sec.items) out.push({ type: 'line', name: `　${it.name}`, amount: it.amount })
    out.push({ type: 'tot', name: `${sec.name}小计`, amount: sec.total })
  }
  push(data.value.operating)
  push(data.value.investing)
  push(data.value.financing)
  return out
})

async function load() {
  const res = await getCashFlow(period.value || undefined)
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
.hint { color: #909399; font-size: 12px; margin-top: 12px; line-height: 1.6; }
</style>
