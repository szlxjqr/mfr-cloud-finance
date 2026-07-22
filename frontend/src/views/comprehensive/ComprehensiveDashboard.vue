<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import VChart from '@/plugins/echarts'
import { getComprehensiveOverview } from '@/api/comprehensive'
import { formatCurrency } from '@/utils/format'
import { Refresh } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import type { ComprehensiveOverview, StatusMap } from '@/types/comprehensive'
import type { EChartsOption } from 'echarts'

const period = ref(dayjs().format('YYYY-MM'))
const loading = ref(false)
const data = ref<ComprehensiveOverview | null>(null)

const VAT_COLOR = '#E6A23C'
const CARRY_COLOR = '#909399'

async function load() {
  loading.value = true
  try {
    const res = await getComprehensiveOverview(period.value)
    data.value = res.data
  } finally {
    loading.value = false
  }
}

onMounted(load)

/** KPI 卡片 */
const kpis = computed(() => {
  const d = data.value
  if (!d) return []
  const vat = d.tax.vat_payable
  return [
    { label: '凭证总数', value: String(d.voucher.total), color: '#409EFF' },
    { label: '待审批业务单', value: String(d.business.pending_total), color: '#F56C6C' },
    { label: '本期进项税额', value: formatCurrency(d.tax.input_tax), color: '#67C23A' },
    {
      label: d.tax.carryforward ? '留抵税额' : '本期应交增值税',
      value: formatCurrency(Math.abs(vat)),
      color: d.tax.carryforward ? CARRY_COLOR : VAT_COLOR,
    },
  ]
})

/** 税务概况行 */
const taxRows = computed(() => {
  const t = data.value?.tax
  if (!t) return []
  return [
    { name: '进项税额', value: t.input_tax, color: '#409EFF' },
    { name: '销项税额', value: t.output_tax, color: '#67C23A' },
    { name: '应交增值税', value: Math.max(t.vat_payable, 0), color: VAT_COLOR },
    { name: '留抵税额', value: t.carryforward ? -t.vat_payable : 0, color: CARRY_COLOR },
  ]
})

/** 经营趋势图 */
const revenueOption = computed<EChartsOption>(() => {
  const trend = data.value?.revenue_trend ?? []
  return {
    grid: { left: 12, right: 20, top: 30, bottom: 10, containLabel: true },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: trend.map((d) => d.period),
      axisLine: { lineStyle: { color: '#dcdfe6' } },
      axisLabel: { color: '#909399' },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#909399' },
      splitLine: { lineStyle: { type: 'dashed', color: '#f0f0f0' } },
    },
    series: [
      {
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        data: trend.map((d) => d.revenue),
        itemStyle: { color: '#409EFF' },
        lineStyle: { width: 3, color: '#409EFF' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(64,158,255,0.30)' },
              { offset: 1, color: 'rgba(64,158,255,0.02)' },
            ],
          },
        },
      },
    ],
  }
})

/** 业务概况：把三个模块的状态摊平展示 */
function statusText(m: StatusMap | undefined): string {
  if (!m || Object.keys(m).length === 0) return '暂无单据'
  return Object.entries(m)
    .map(([k, v]) => `${k} ${v}`)
    .join(' / ')
}
</script>

<template>
  <div class="comprehensive" v-loading="loading">
    <!-- 顶部：期间 + 刷新 -->
    <div class="top-bar">
      <div class="section-title">
        <span class="triangle" />
        <span>综合报表看板</span>
        <span class="hint">（数据由 业务单 / 凭证 / 账务 / 税务 实时聚合）</span>
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
        <el-button :icon="Refresh" circle size="small" :loading="loading" @click="load" />
      </div>
    </div>

    <!-- KPI 卡片 -->
    <el-row :gutter="16" class="row-gap">
      <el-col v-for="k in kpis" :key="k.label" :xs="12" :sm="12" :md="6" :lg="6">
        <div class="kpi-card">
          <div class="kpi-label">{{ k.label }}</div>
          <div class="kpi-value" :style="{ color: k.color }">{{ k.value }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 资金情况 + 税务概况 -->
    <el-row :gutter="16" class="row-gap">
      <el-col :xs="24" :sm="24" :md="14" :lg="14">
        <el-card shadow="never" class="block">
          <template #header><span class="block-title">资金情况（关键科目真实余额）</span></template>
          <div class="fund-list">
            <div v-for="f in data?.funds" :key="f.code" class="fund-row">
              <span class="fund-name">{{ f.name }}</span>
              <span class="fund-amount">{{ formatCurrency(f.amount) }}</span>
            </div>
            <div v-if="!data?.funds?.length" class="empty">暂无科目余额数据</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="24" :md="10" :lg="10">
        <el-card shadow="never" class="block">
          <template #header><span class="block-title">税务概况</span></template>
          <div class="tax-list">
            <div v-for="t in taxRows" :key="t.name" class="tax-row">
              <span class="dot" :style="{ backgroundColor: t.color }" />
              <span class="tax-name">{{ t.name }}</span>
              <span class="tax-amount">{{ formatCurrency(t.value) }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 经营趋势 -->
    <el-row :gutter="16" class="row-gap">
      <el-col :span="24">
        <el-card shadow="never" class="block">
          <template #header><span class="block-title">经营趋势（主营业务收入 6001 按月）</span></template>
          <v-chart v-if="data?.revenue_trend?.length" class="chart" :option="revenueOption" autoresize />
          <div v-else class="empty">研发期暂无主营业务收入数据</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 业务概况 -->
    <el-row :gutter="16" class="row-gap">
      <el-col :span="24">
        <el-card shadow="never" class="block">
          <template #header><span class="block-title">业务概况（单据状态）</span></template>
          <el-descriptions :column="3" border>
            <el-descriptions-item label="报销单">{{ statusText(data?.business.reimburse) }}</el-descriptions-item>
            <el-descriptions-item label="采购申请">{{ statusText(data?.business.purchase) }}</el-descriptions-item>
            <el-descriptions-item label="差旅申请">{{ statusText(data?.business.travel) }}</el-descriptions-item>
            <el-descriptions-item label="待审批合计">
              <b style="color:#F56C6C">{{ data?.business.pending_total ?? 0 }}</b> 笔
            </el-descriptions-item>
            <el-descriptions-item label="凭证总数">{{ data?.voucher.total ?? 0 }} 张</el-descriptions-item>
            <el-descriptions-item label="所选期间凭证数">{{ data?.voucher.period_count ?? 0 }} 张</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.comprehensive { padding: 4px; }
.top-bar {
  display: flex; align-items: center; justify-content: space-between;
  background: #fff; border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  padding: 12px 16px; margin-bottom: 16px;
}
.section-title { display: flex; align-items: center; gap: 8px; font-size: 15px; font-weight: 600; color: #303133; }
.hint { font-size: 12px; font-weight: 400; color: #909399; }
.triangle { width: 0; height: 0; border-top: 6px solid transparent; border-bottom: 6px solid transparent; border-left: 10px solid #409eff; }
.tools { display: flex; align-items: center; gap: 8px; }
.row-gap { margin-top: 16px; }
.kpi-card {
  background: #fff; border-radius: 8px; padding: 18px 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}
.kpi-label { font-size: 13px; color: #909399; }
.kpi-value { margin-top: 8px; font-size: 24px; font-weight: 700; font-family: 'DIN', 'Helvetica Neue', Arial, sans-serif; }
.block { border-radius: 8px; }
.block-title { font-size: 15px; font-weight: 600; color: #303133; }
.fund-list, .tax-list { display: flex; flex-direction: column; gap: 4px; }
.fund-row, .tax-row { display: flex; align-items: center; gap: 10px; padding: 10px 6px; border-bottom: 1px dashed #f0f0f0; }
.fund-name, .tax-name { font-size: 14px; color: #606266; }
.fund-amount, .tax-amount { margin-left: auto; font-size: 14px; font-weight: 600; color: #303133; font-family: 'DIN', 'Helvetica Neue', Arial, sans-serif; }
.dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.chart { height: 280px; width: 100%; }
.empty { padding: 40px 0; text-align: center; color: #909399; font-size: 14px; }
@media (max-width: 768px) { .el-col { margin-bottom: 16px; } }
</style>
