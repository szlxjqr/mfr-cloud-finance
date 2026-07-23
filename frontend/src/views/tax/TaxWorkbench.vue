<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getTaxWorkbench } from '@/api/tax'
import { formatNumber } from '@/utils/format'
import { Refresh } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import type { TaxWorkbench } from '@/types/tax'

/** 期间选择器（默认当前月） */
const period = ref(dayjs().format('YYYY-MM'))
const loading = ref(false)
const data = ref<TaxWorkbench | null>(null)

async function load() {
  loading.value = true
  try {
    const res = await getTaxWorkbench(period.value)
    data.value = res.data
  } finally {
    loading.value = false
  }
}

onMounted(load)

const emptyVat = { input_tax: 0, output_tax: 0, vat_payable: 0, carryforward: false }
const emptyInd = { total_tax: 0, total_gross: 0, headcount: 0 }
const emptyStamp = { total_tax: 0, total_amount: 0, contract_count: 0 }

const vat = computed(() => data.value?.vat ?? emptyVat)
const ind = computed(() => data.value?.individual ?? emptyInd)
const stamp = computed(() => data.value?.stamp ?? emptyStamp)
</script>

<template>
  <div class="tax-workbench">
    <!-- 期间选择 + 刷新 -->
    <el-card shadow="never" class="bar-card">
      <div class="bar">
        <div class="section-title">
          <span class="triangle" />
          <span>税务工作台</span>
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

    <div v-loading="loading" class="groups">
      <!-- 增值税 -->
      <el-card shadow="never" class="group">
        <template #header>
          <div class="group-title">增值税（{{ period }}）</div>
        </template>
        <div class="kpi-row">
          <div class="kpi">
            <div class="kpi-label">进项税额</div>
            <div class="kpi-value">{{ formatNumber(vat.input_tax ?? 0) }}</div>
          </div>
          <div class="kpi">
            <div class="kpi-label">销项税额</div>
            <div class="kpi-value">{{ formatNumber(vat.output_tax ?? 0) }}</div>
          </div>
          <div class="kpi" :class="{ warn: vat.carryforward }">
            <div class="kpi-label">{{ vat.carryforward ? '留抵税额' : '应交增值税' }}</div>
            <div class="kpi-value">{{ formatNumber(Math.abs(vat.vat_payable ?? 0)) }}</div>
          </div>
        </div>
      </el-card>

      <!-- 个人所得税 -->
      <el-card shadow="never" class="group">
        <template #header>
          <div class="group-title">个人所得税（代扣代缴）</div>
        </template>
        <div class="kpi-row">
          <div class="kpi">
            <div class="kpi-label">申报人数</div>
            <div class="kpi-value">{{ ind.headcount ?? 0 }}</div>
          </div>
          <div class="kpi">
            <div class="kpi-label">应发合计</div>
            <div class="kpi-value">{{ formatNumber(ind.total_gross ?? 0) }}</div>
          </div>
          <div class="kpi warn">
            <div class="kpi-label">本期应申报个税</div>
            <div class="kpi-value">{{ formatNumber(ind.total_tax ?? 0) }}</div>
          </div>
        </div>
      </el-card>

      <!-- 印花税 -->
      <el-card shadow="never" class="group">
        <template #header>
          <div class="group-title">印花税（累计有效合同）</div>
        </template>
        <div class="kpi-row">
          <div class="kpi">
            <div class="kpi-label">应税合同</div>
            <div class="kpi-value">{{ stamp.contract_count ?? 0 }}</div>
          </div>
          <div class="kpi">
            <div class="kpi-label">计税金额</div>
            <div class="kpi-value">{{ formatNumber(stamp.total_amount ?? 0) }}</div>
          </div>
          <div class="kpi warn">
            <div class="kpi-label">印花税合计</div>
            <div class="kpi-value">{{ formatNumber(stamp.total_tax ?? 0) }}</div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.tax-workbench {
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
.groups {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.group-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}
.kpi-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
.kpi {
  text-align: center;
  padding: 8px 4px;
  background: #fafafa;
  border-radius: 6px;
}
.kpi-label {
  font-size: 12px;
  color: #909399;
}
.kpi-value {
  font-size: 22px;
  font-weight: 700;
  color: #303133;
  margin-top: 4px;
}
.kpi.warn .kpi-value {
  color: #e6a23c;
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
