<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import VChart from '@/plugins/echarts'
import { getTaxOverview } from '@/api/dashboard'
import { formatNumber } from '@/utils/format'
import { Refresh } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import type { TaxItem } from '@/types/dashboard'
import type { EChartsOption } from 'echarts'

/** 月份选择器（默认当前月） */
const month = ref(dayjs().format('YYYY-MM'))
const loading = ref(false)
const data = ref<TaxItem[]>([])

/** 后端不可用时的演示数据 */
const fallback: TaxItem[] = [
  { name: '增值税', value: 12000, color: '#409EFF' },
  { name: '企业所得税', value: 8000, color: '#67C23A' },
  { name: '城建税', value: 3000, color: '#E6A23C' },
  { name: '其他税费', value: 1500, color: '#909399' },
]

async function load() {
  loading.value = true
  try {
    const res = await getTaxOverview()
    data.value = res.data?.length ? res.data : fallback
  } catch {
    data.value = fallback
  } finally {
    loading.value = false
  }
}

onMounted(load)

/** 合计税额 */
const total = computed(() => data.value.reduce((sum, d) => sum + (d.value || 0), 0))

const option = computed<EChartsOption>(() => ({
  tooltip: {
    trigger: 'item',
    formatter: (params: any) =>
      `${params.name}<br/>税额：<b>${formatNumber(params.value)}</b> 元（${params.percent}%）`,
  },
  legend: {
    orient: 'vertical',
    right: 12,
    top: 'center',
    itemWidth: 10,
    itemHeight: 10,
    icon: 'circle',
    textStyle: { color: '#606266' },
    formatter: (name: string) => {
      const item = data.value.find((d) => d.name === name)
      return item ? `${name}  ${formatNumber(item.value)}` : name
    },
  },
  title: {
    text: '合计税额',
    subtext: `${formatNumber(total.value)} 元`,
    left: '38%',
    top: '40%',
    textAlign: 'center',
    textStyle: { fontSize: 13, color: '#909399', fontWeight: 'normal' },
    subtextStyle: { fontSize: 16, color: '#303133', fontWeight: 'bold' },
  },
  series: [
    {
      type: 'pie',
      radius: ['55%', '75%'],
      center: ['38%', '50%'],
      avoidLabelOverlap: false,
      label: { show: false },
      labelLine: { show: false },
      data: data.value.map((d) => ({
        name: d.name,
        value: d.value,
        itemStyle: { color: d.color },
      })),
    },
  ],
}))
</script>

<template>
  <div class="tax-chart">
    <div class="card-header">
      <div class="section-title">
        <span class="triangle" />
        <span>应交税费</span>
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
.tax-chart {
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
