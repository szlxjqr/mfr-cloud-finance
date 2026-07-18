<script setup lang="ts">
import { useRouter } from 'vue-router'

interface ActionItem {
  /** 图标组件名（Element Plus 全局图标） */
  icon: string
  /** 显示文案 */
  label: string
  /** 跳转路由 */
  path: string
  /** 主题色 */
  color: string
}

const router = useRouter()

/** 12 个常用功能入口（3 行 4 列） */
const actions: ActionItem[] = [
  { icon: 'Document', label: '查看凭证', path: '/finance/voucher', color: '#409EFF' },
  { icon: 'Notebook', label: '日记账', path: '/finance/journal', color: '#00CED1' },
  { icon: 'DataAnalysis', label: '总账', path: '/finance/ledger', color: '#E6A23C' },
  { icon: 'List', label: '明细账', path: '/finance/detail-ledger', color: '#409EFF' },
  { icon: 'Coin', label: '余额表', path: '/finance/balance', color: '#9254DE' },
  { icon: 'Trophy', label: '资产负债表', path: '/report/balance-sheet', color: '#F56C6C' },
  { icon: 'Money', label: '利润表', path: '/report/income', color: '#F0B020' },
  { icon: 'TrendCharts', label: '现金流量表', path: '/report/cash-flow', color: '#409EFF' },
  { icon: 'Download', label: '进项发票', path: '/tax/input-invoice', color: '#00CED1' },
  { icon: 'Upload', label: '销项发票', path: '/tax/output-invoice', color: '#E6A23C' },
  { icon: 'DocumentCopy', label: '进销存基础资料', path: '/inventory/basic', color: '#9254DE' },
  { icon: 'Tickets', label: '费用发票', path: '/tax/expense-invoice', color: '#67C23A' },
]

/** 计算图标背景的浅色底（主题色 12% 透明度） */
function tint(color: string): string {
  return `${color}1f`
}

function handleClick(item: ActionItem) {
  router.push(item.path)
}
</script>

<template>
  <div class="quick-actions">
    <div class="section-title">
      <span class="triangle" />
      <span>常用功能</span>
    </div>

    <div class="action-grid">
      <div
        v-for="item in actions"
        :key="item.label"
        class="action-card"
        @click="handleClick(item)"
      >
        <div class="action-icon" :style="{ backgroundColor: tint(item.color) }">
          <el-icon :size="22" :color="item.color">
            <component :is="item.icon" />
          </el-icon>
        </div>
        <span class="action-label">{{ item.label }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.quick-actions {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  padding: 18px 20px 22px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 18px;
}

.triangle {
  width: 0;
  height: 0;
  border-top: 6px solid transparent;
  border-bottom: 6px solid transparent;
  border-left: 10px solid #409eff;
}

.action-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.action-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 16px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
}

.action-card:hover {
  transform: translateY(-4px);
  background: #f7faff;
  box-shadow: 0 6px 16px rgba(64, 158, 255, 0.18);
}

.action-icon {
  width: 46px;
  height: 46px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-label {
  font-size: 13px;
  color: #606266;
  text-align: center;
  line-height: 1.3;
}

@media (max-width: 768px) {
  .action-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
