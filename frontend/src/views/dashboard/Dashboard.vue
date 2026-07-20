<script setup lang="ts">
import { ref } from 'vue'
import QuickActions from './components/QuickActions.vue'
import VoucherCard from './components/VoucherCard.vue'
import FundOverview from './components/FundOverview.vue'
import BusinessChart from './components/BusinessChart.vue'
import TaxChart from './components/TaxChart.vue'

/** 顶部二级标签（当前激活项） */
const activeTab = ref('voucher')

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
  color: #409eff;
}

.top-tab.active {
  color: #409eff;
  font-weight: 600;
  border-bottom-color: #409eff;
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
