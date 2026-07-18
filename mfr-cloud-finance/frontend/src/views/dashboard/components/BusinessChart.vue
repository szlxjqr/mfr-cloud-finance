<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import VChart from '@/plugins/echarts'
import { getRevenueTrend } from '@/api/dashboard'
import { Refresh } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import type { RevenueDataPoint } from '@/types/dashboard'
import type { EChartsOption } from 'echarts'

/** 月份选择器（默认当前月） */
const month = ref(dayjs().format('YYYY-MM'))
const loading = ref(false)
const data = ref<RevenueDataPoint[]>([])

/** 后端不可用时的演示数据（全年 12 个月，数值 0-700） */
const fallback: RevenueDataPoint[] = [
  { month: '1月', value: 320 },
  { month: '2月', value: 410 },
  { month: '3月', value: 380 },
  { month: '4月', value: 460 },
  { month: '5月', value: 520 },
  { month: '6月', value: 480 },
  { month: '7月', value: 560 },
  { month: '8月', value: 610 },
  { month: '9月', value: 540 },
  { month: '10月', value: 590 },
  { month: '11月', value: 640 },
  { month: '12月', value: 680 },
]

async function load() {
  loading.value = true
  try {
    const res = await getRevenueTrend()
    data.value = res.data?.length ? res.data : fallback
  } catch {
    data.value = fallback
  } finally {
    loading.value = false
  }
}

onMounted(load)

const option = computed<EChartsOption>(() => ({
  grid: { left: 12, right: 20, top: 30, bottom: 10, containLabel: true },
  tooltip: {
    trigger: 'axis',
    formatter: (params: any) => {
      const p = Array.isArray(params) ? params[0] : params
      return `${p.axisValue}<br/>经营数据：<b>${p.data}</b>`
    },
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: data.value.map((d) => d.month),
    axisLine: { lineStyle: { color: '#dcdfe6' } },
    axisLabel: { color: '#909399' },
  },
  yAxis: {
    type: 'value',
    min: 0,
    max: 700,
    axisLabel: { color: '#909399' },
    splitLine: { lineStyle: { type: 'dashed', color: '#f0f0f0' } },
  },
  series: [
    {
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      data: data.value.map((d) => d.value),
      itemStyle: { color: '#409EFF' },
      lineStyle: { width: 3, color: '#409EFF' },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(64,158,255,0.30)' },
            { offset: 1, color: 'rgba(64,158,255,0.02)' },
          ],
        },
      },
    },
  ],
}))
</script>

<template>
  <div class="business-chart">
    <div class="card-header">
      <div class="section-title">
        <span class="triangle" />
        <span>经营数据</span>
      </div>
      <div class="header-tools">
        <el-date-picker
          v-model="month"
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

    <v-chart class="chart" :option="option" :loading="loading" autoresize />
  </div>
</template>

<style scoped>
.business-chart {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  padding: 18px 20px 12px;
  height: 100%;
  box-sizing: border-box;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
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

.header-tools {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chart {
  height: 280px;
  width: 100%;
}
</style>
