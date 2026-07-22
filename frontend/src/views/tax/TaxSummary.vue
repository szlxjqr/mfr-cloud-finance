<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import VChart from '@/plugins/echarts'
import { getTaxSummary } from '@/api/tax'
import { formatNumber } from '@/utils/format'
import { Refresh } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import type { EChartsOption } from 'echarts'
import type { TaxSummaryDetail, TaxInputDetail } from '@/types/tax'

/** 期间选择器（默认当前月） */
const period = ref(dayjs().format('YYYY-MM'))
const loading = ref(false)
const data = ref<TaxSummaryDetail | null>(null)

/** KPI 卡片 */
const summary = computed(() => data.value?.summary ?? null)
/** 本年累计进项税额（月度趋势累计到所选期间） */
const ytdInput = computed(() => {
  if (!data.value) return 0
  const sel = period.value
  return data.value.monthly
    .filter((m) => !sel || m.period <= sel)
    .reduce((s, m) => s + (m.input_tax || 0), 0)
})

async function load() {
  loading.value = true
  try {
    const res = await getTaxSummary(period.value)
    data.value = res.data
  } finally {
    loading.value = false
  }
}

onMounted(load)

/** 进项税额明细 */
const details = computed<TaxInputDetail[]>(() => data.value?.details ?? [])
const totalDetail = computed(() =>
  details.value.reduce((s, d) => s + (d.amount || 0), 0),
)

/** 月度趋势图 */
const trendOption = computed<EChartsOption>(() => {
  const m = data.value?.monthly ?? []
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['进项税额', '销项税额'], bottom: 0 },
    grid: { left: 56, right: 16, top: 20, bottom: 36 },
    xAxis: {
      type: 'category',
      data: m.map((x) => x.period.slice(5) + '月'),
      axisLabel: { color: '#909399' },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#909399', formatter: (v: number) => formatNumber(v) },
    },
    series: [
      {
        name: '进项税额',
        type: 'bar',
        data: m.map((x) => x.input_tax),
        itemStyle: { color: '#409EFF' },
        barMaxWidth: 18,
      },
      {
        name: '销项税额',
        type: 'bar',
        data: m.map((x) => x.output_tax),
        itemStyle: { color: '#67C23A' },
        barMaxWidth: 18,
      },
    ],
  }
})
</script>

<template>
  <div class="tax-summary">
    <!-- 期间选择 + 刷新 -->
    <el-card shadow="never" class="bar-card">
      <div class="bar">
        <div class="section-title">
          <span class="triangle" />
          <span>发票税务汇总</span>
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
        </div>
      </div>
    </el-card>

    <!-- KPI 卡片 -->
    <div class="kpi-row" v-loading="loading">
      <el-card shadow="never" class="kpi">
        <div class="kpi-label">本期进项税额</div>
        <div class="kpi-value">{{ formatNumber(summary?.input_tax ?? 0) }}</div>
        <div class="kpi-unit">元</div>
      </el-card>
      <el-card shadow="never" class="kpi">
        <div class="kpi-label">本期销项税额</div>
        <div class="kpi-value">{{ formatNumber(summary?.output_tax ?? 0) }}</div>
        <div class="kpi-unit">元</div>
      </el-card>
      <el-card shadow="never" class="kpi" :class="{ warn: summary?.carryforward }">
        <div class="kpi-label">
          {{ summary?.carryforward ? '留抵税额' : '本期应交增值税' }}
        </div>
        <div class="kpi-value">{{ formatNumber(Math.abs(summary?.vat_payable ?? 0)) }}</div>
        <div class="kpi-unit">元</div>
      </el-card>
      <el-card shadow="never" class="kpi">
        <div class="kpi-label">本年累计进项税额</div>
        <div class="kpi-value">{{ formatNumber(ytdInput) }}</div>
        <div class="kpi-unit">元</div>
      </el-card>
    </div>

    <!-- 明细 + 趋势 -->
    <div class="grid">
      <el-card shadow="never" class="detail-card">
        <template #header>
          <div class="section-title">
            <span class="triangle" />
            <span>进项税额明细</span>
          </div>
        </template>
        <el-table :data="details" size="small" empty-text="本期无进项税额">
          <el-table-column prop="voucher_no" label="凭证号" min-width="140" />
          <el-table-column prop="date" label="日期" width="110" />
          <el-table-column prop="summary" label="摘要" min-width="200" show-overflow-tooltip />
          <el-table-column prop="source_no" label="来源单号" min-width="130" />
          <el-table-column label="税额(元)" width="120" align="right">
            <template #default="{ row }">{{ formatNumber(row.amount) }}</template>
          </el-table-column>
        </el-table>
        <div class="detail-total" v-if="details.length">
          合计进项税额：<b>{{ formatNumber(totalDetail) }}</b> 元
        </div>
      </el-card>

      <el-card shadow="never" class="trend-card">
        <template #header>
          <div class="section-title">
            <span class="triangle" />
            <span>月度趋势（{{ period.slice(0, 4) }} 年）</span>
          </div>
        </template>
        <v-chart class="trend" :option="trendOption" autoresize />
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.tax-summary {
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
.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
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
.grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 14px;
}
.detail-total {
  margin-top: 10px;
  text-align: right;
  font-size: 13px;
  color: #606266;
}
.trend {
  height: 300px;
  width: 100%;
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
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
