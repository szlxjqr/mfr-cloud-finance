<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getFundsOverview } from '@/api/dashboard'
import { formatCurrency } from '@/utils/format'
import { Refresh } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import type { FundItem } from '@/types/dashboard'

/** 月份选择器（默认当前月） */
const month = ref(dayjs().format('YYYY-MM'))
const loading = ref(false)
const funds = ref<FundItem[]>([])

/** 后端不可用时的演示数据（与接口结构一致） */
const fallback: FundItem[] = [
  { name: '现金', amount: 156820.5, color: '#E6A23C', unit: '元' },
  { name: '银行存款', amount: 842310.75, color: '#67C23A', unit: '元' },
  { name: '应收账款', amount: 312500, color: '#409EFF', unit: '元' },
  { name: '应付账款', amount: 198640, color: '#909399', unit: '元' },
  { name: '主营业务收入', amount: 1256000, color: '#F56C6C', unit: '元' },
  { name: '管理费用', amount: 86420.3, color: '#00CED1', unit: '元' },
]

async function load() {
  loading.value = true
  try {
    const res = await getFundsOverview()
    funds.value = res.data?.length ? res.data : fallback
  } catch {
    funds.value = fallback
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="fund-overview">
    <div class="card-header">
      <div class="section-title">
        <span class="triangle" />
        <span>资金情况</span>
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

    <div class="fund-grid" v-loading="loading">
      <div v-for="item in funds" :key="item.name" class="fund-item">
        <span class="dot" :style="{ backgroundColor: item.color }" />
        <span class="fund-name">{{ item.name }}</span>
        <span class="fund-amount">{{ formatCurrency(item.amount) }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.fund-overview {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  padding: 18px 20px 22px;
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

.fund-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px 24px;
  margin-top: 18px;
  min-height: 160px;
}

.fund-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 6px;
  border-bottom: 1px dashed #f0f0f0;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.fund-name {
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
}

.fund-amount {
  margin-left: auto;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  text-align: right;
  font-family: 'DIN', 'Helvetica Neue', Arial, sans-serif;
}
</style>
