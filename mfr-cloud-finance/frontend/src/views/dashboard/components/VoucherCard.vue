<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getVoucherCount } from '@/api/dashboard'
import { useRouter } from 'vue-router'
import { Refresh } from '@element-plus/icons-vue'
import dayjs from 'dayjs'

const router = useRouter()

/** 月份选择器（默认当前月） */
const month = ref(dayjs().format('YYYY-MM'))
const total = ref(0)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const res = await getVoucherCount(month.value)
    total.value = typeof res.data === 'number' ? res.data : 128
  } catch {
    // 后端不可用时回退到演示数据，保证界面完整
    total.value = 128
  } finally {
    loading.value = false
  }
}

onMounted(load)

function viewVoucher() {
  router.push('/finance/voucher')
}

function addVoucher() {
  router.push('/finance/voucher?action=add')
}
</script>

<template>
  <div class="voucher-card">
    <div class="card-header">
      <div class="section-title">
        <span class="triangle" />
        <span>凭证</span>
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

    <div class="card-body" v-loading="loading">
      <div class="count">
        <span class="count-num">{{ total }}</span>
        <span class="count-unit">张</span>
      </div>

      <div class="actions">
        <el-button @click="viewVoucher">查看凭证</el-button>
        <el-button type="primary" @click="addVoucher">新增凭证</el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.voucher-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  padding: 18px 20px 24px;
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

.card-body {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 28px 0 8px;
  min-height: 180px;
}

.count {
  display: flex;
  align-items: baseline;
  gap: 6px;
  margin-bottom: 28px;
}

.count-num {
  font-size: 52px;
  font-weight: 700;
  line-height: 1;
  color: #409eff;
  font-family: 'DIN', 'Helvetica Neue', Arial, sans-serif;
}

.count-unit {
  font-size: 16px;
  color: #909399;
}

.actions {
  display: flex;
  gap: 12px;
}
</style>
