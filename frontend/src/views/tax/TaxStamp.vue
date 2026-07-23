<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getStampTax } from '@/api/tax'
import { formatNumber } from '@/utils/format'
import { Refresh } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import type { StampTax } from '@/types/tax'

/** 年度选择器（默认当前年） */
const year = ref(dayjs().format('YYYY'))
const loading = ref(false)
const data = ref<StampTax | null>(null)

async function load() {
  loading.value = true
  try {
    const res = await getStampTax(year.value)
    data.value = res.data
  } finally {
    loading.value = false
  }
}

onMounted(load)

const rows = computed(() => data.value?.rows ?? [])
const totalTax = computed(() => data.value?.total_tax ?? 0)
const totalAmount = computed(() => data.value?.total_amount ?? 0)
const contractCount = computed(() => data.value?.contract_count ?? 0)
/** 印花税率展示（0.0003 → 0.03%） */
const rateText = computed(() => {
  const r = rows.value[0]?.rate ?? 0.0003
  return (r * 100).toFixed(2) + '%'
})
</script>

<template>
  <div class="tax-stamp">
    <!-- 年度选择 + 刷新 -->
    <el-card shadow="never" class="bar-card">
      <div class="bar">
        <div class="section-title">
          <span class="triangle" />
          <span>印花税（买卖合同 0.03%）</span>
        </div>
        <div class="tools">
          <el-date-picker
            v-model="year"
            type="year"
            value-format="YYYY"
            placeholder="选择年度"
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

    <el-alert
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 14px"
      title="计税口径：销售合同 + 采购合同按金额 0.03% 计征；劳动合同依法免征印花税已自动排除。"
    />

    <!-- KPI 卡片 -->
    <div class="kpi-row" v-loading="loading">
      <el-card shadow="never" class="kpi">
        <div class="kpi-label">应税合同数</div>
        <div class="kpi-value">{{ contractCount }}</div>
        <div class="kpi-unit">份</div>
      </el-card>
      <el-card shadow="never" class="kpi">
        <div class="kpi-label">计税金额合计</div>
        <div class="kpi-value">{{ formatNumber(totalAmount) }}</div>
        <div class="kpi-unit">元</div>
      </el-card>
      <el-card shadow="never" class="kpi warn">
        <div class="kpi-label">印花税合计（{{ rateText }}）</div>
        <div class="kpi-value">{{ formatNumber(totalTax) }}</div>
        <div class="kpi-unit">元</div>
      </el-card>
    </div>

    <!-- 明细表 -->
    <el-card shadow="never" class="table-card">
      <template #header>
        <div class="section-title">
          <span class="triangle" />
          <span>印花税明细（执行中/已完成合同）</span>
        </div>
      </template>
      <el-table :data="rows" size="small" empty-text="暂无应税合同（劳动合同免税不计入）">
        <el-table-column prop="contract_no" label="合同号" width="150" />
        <el-table-column prop="type" label="类型" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="row.type === '销售合同' ? 'success' : 'warning'" size="small">{{ row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="party" label="对方单位" min-width="160" show-overflow-tooltip />
        <el-table-column prop="sign_date" label="签约日期" width="120" />
        <el-table-column label="合同金额" width="150" align="right">
          <template #default="{ row }">{{ formatNumber(row.amount) }}</template>
        </el-table-column>
        <el-table-column label="税率" width="90" align="center">
          <template #default="{ row }">{{ (row.rate * 100).toFixed(2) }}%</template>
        </el-table-column>
        <el-table-column label="应纳税额" width="140" align="right">
          <template #default="{ row }">
            <span style="font-weight: 600; color: #e6a23c">{{ formatNumber(row.tax) }}</span>
          </template>
        </el-table-column>
      </el-table>
      <div class="detail-total" v-if="rows.length">
        合计：计税金额 <b>{{ formatNumber(totalAmount) }}</b> 元 ｜ 印花税
        <b style="color: #e6a23c">{{ formatNumber(totalTax) }}</b> 元（共 {{ contractCount }} 份合同）
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.tax-stamp {
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
  grid-template-columns: repeat(3, 1fr);
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
.detail-total {
  margin-top: 10px;
  text-align: right;
  font-size: 13px;
  color: #606266;
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
}
</style>
