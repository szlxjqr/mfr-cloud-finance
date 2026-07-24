<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import QuickActions from './components/QuickActions.vue'
import VoucherCard from './components/VoucherCard.vue'
import FundOverview from './components/FundOverview.vue'
import BusinessChart from './components/BusinessChart.vue'
import TaxChart from './components/TaxChart.vue'
import { getVoucherCount, getFundsOverview, getDashboardSummary } from '@/api/dashboard'
import { formatCurrency } from '@/utils/format'

/** 顶部二级标签（当前激活项） */
const activeTab = ref('voucher')

/** 关键指标（KpiTile 示范，接已有接口 + 兜底演示值） */
const kpi = reactive({ voucher: 128, fund: 1000000, tax: 0 })

async function loadKpi() {
  try {
    const [vc, funds, sum] = await Promise.all([
      getVoucherCount(),
      getFundsOverview(),
      getDashboardSummary(),
    ])
    const fundSum = Array.isArray(funds.data)
      ? funds.data.reduce((a: number, b: any) => a + (b.amount || 0), 0)
      : 1000000
    const taxItem = Array.isArray(sum.data?.taxItems)
      ? sum.data.taxItems.find((t: any) => String(t.name).includes('应交'))
      : null
    kpi.voucher = typeof vc.data === 'number' ? vc.data : 128
    kpi.fund = fundSum
    kpi.tax = taxItem?.value ?? 0
  } catch {
    kpi.voucher = 128
    kpi.fund = 1000000
    kpi.tax = 0
  }
}

onMounted(loadKpi)

interface TopTab {
  label: string
  key: string
}

const topTabs: TopTab[] = [
  { label: '凭证', key: 'voucher' },
  { label: '查看凭证', key: 'view' },
  { label: '费用发票', key: 'expense' },
]
</script>

<template>
  <div class="dashboard">
    <!-- 顶部二级标签 -->
    <div class="top-tabs">
      <div
        v-for="tab in topTabs"
        :key="tab.key"
        class="top-tab"
        :class="{ active: activeTab === tab.key }"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </div>
    </div>

    <!-- 关键指标（KpiTile 示范） -->
    <el-row :gutter="16" class="row-gap">
      <el-col :xs="24" :sm="8" :md="8">
        <KpiTile label="本月凭证" :value="kpi.voucher" delta-label="张" icon="Document" accent="brand" />
      </el-col>
      <el-col :xs="24" :sm="8" :md="8">
        <KpiTile label="资金总额" :value="formatCurrency(kpi.fund)" icon="Wallet" accent="success" />
      </el-col>
      <el-col :xs="24" :sm="8" :md="8">
        <KpiTile label="应交税费" :value="formatCurrency(kpi.tax)" icon="Money" accent="warning" />
      </el-col>
    </el-row>

    <!-- 常用功能（全宽） -->
    <el-row :gutter="16">
      <el-col :span="24">
        <QuickActions />
      </el-col>
    </el-row>

    <!-- 凭证中心 + 资金情况 -->
    <el-row :gutter="16" class="row-gap">
      <el-col :xs="24" :sm="24" :md="8" :lg="8">
        <VoucherCard />
      </el-col>
      <el-col :xs="24" :sm="24" :md="16" :lg="16">
        <FundOverview />
      </el-col>
    </el-row>

    <!-- 经营数据 + 应交税费 -->
    <el-row :gutter="16" class="row-gap">
      <el-col :xs="24" :sm="24" :md="14" :lg="14">
        <BusinessChart />
      </el-col>
      <el-col :xs="24" :sm="24" :md="10" :lg="10">
        <TaxChart />
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.dashboard {
  padding: 4px;
}

/* 顶部二级标签 */
.top-tabs {
  display: flex;
  gap: 4px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  padding: 0 8px;
  margin-bottom: 16px;
}

.top-tab {
  padding: 12px 18px;
  font-size: 14px;
  color: #606266;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: color 0.18s ease;
}

.top-tab:hover {
  color: var(--el-color-primary);
}

.top-tab.active {
  color: var(--el-color-primary);
  font-weight: 600;
  border-bottom-color: var(--el-color-primary);
}

.row-gap {
  margin-top: 16px;
}

/* 小屏堆叠时给卡片增加下边距 */
@media (max-width: 768px) {
  .el-col {
    margin-bottom: 16px;
  }
}
</style>
