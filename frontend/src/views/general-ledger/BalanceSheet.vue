<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getSubjectBalance } from '@/api/ledger'
import type { SubjectBalance } from '@/types/ledger'

const period = ref('')
const searchKeyword = ref('')
const hideZero = ref(false)
const loading = ref(false)
const rows = ref<SubjectBalance[]>([])

const catLabel: Record<string, string> = {
  资产: '资产', 负债: '负债', 权益: '权益', 成本: '成本', 损益: '损益',
}

const filtered = computed(() => {
  let data = rows.value
  if (hideZero.value) {
    data = data.filter(r => r.ending_debit !== 0 || r.ending_credit !== 0)
  }
  const kw = searchKeyword.value.trim().toLowerCase()
  if (kw) {
    data = data.filter(r => r.code.includes(kw) || r.name.toLowerCase().includes(kw))
  }
  return data
})

const totals = computed(() => {
  return filtered.value.reduce(
    (a, r) => {
      a.debit += r.ending_debit
      a.credit += r.ending_credit
      return a
    },
    { debit: 0, credit: 0 },
  )
})

function fmt(v: number): string {
  if (!v) return ''
  return v.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

async function loadData() {
  loading.value = true
  try {
    const res = await getSubjectBalance(period.value || undefined)
    rows.value = res.data
  } catch (e) {
    ElMessage.error('加载科目余额失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <div class="balance-page">
    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-date-picker
          v-model="period"
          type="month"
          format="YYYY年MM期"
          value-format="YYYY-MM"
          placeholder="全部期间"
          size="small"
          style="width: 160px"
          @change="loadData"
        />
        <el-input
          v-model="searchKeyword"
          placeholder="搜索科目编码 / 名称"
          clearable
          size="small"
          style="width: 240px"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-checkbox v-model="hideZero" size="small" @change="() => {}">隐藏余额为 0</el-checkbox>
        <el-button size="small" circle title="刷新" @click="loadData">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
      <div class="toolbar-right">
        <span class="hint">科目余额由凭证分录自动汇总</span>
      </div>
    </div>

    <!-- 余额表 -->
    <div class="table-area">
      <el-table
        :data="filtered"
        v-loading="loading"
        border
        stripe
        size="small"
        :header-cell-style="{ background: '#f5f7fa', color: '#303133', fontWeight: 600 }"
        style="width: 100%"
        max-height="calc(100vh - 180px)"
      >
        <el-table-column prop="code" label="科目编码" width="120" align="center" fixed />
        <el-table-column prop="name" label="科目名称" min-width="180" fixed />
        <el-table-column label="类别" width="84" align="center">
          <template #default="{ row }">
            <span class="cat-tag">{{ catLabel[row.category] || row.category }}</span>
          </template>
        </el-table-column>
        <el-table-column label="方向" width="72" align="center">
          <template #default="{ row }">
            <span :class="['dir-tag', row.direction]">{{ row.direction }}</span>
          </template>
        </el-table-column>
        <el-table-column label="本期发生额" align="center">
          <el-table-column label="借方" width="130" align="right">
            <template #default="{ row }"><span class="amt">{{ fmt(row.period_debit) }}</span></template>
          </el-table-column>
          <el-table-column label="贷方" width="130" align="right">
            <template #default="{ row }"><span class="amt">{{ fmt(row.period_credit) }}</span></template>
          </el-table-column>
        </el-table-column>
        <el-table-column label="期末余额" align="center">
          <el-table-column label="借方" width="130" align="right">
            <template #default="{ row }"><span class="amt end">{{ fmt(row.ending_debit) }}</span></template>
          </el-table-column>
          <el-table-column label="贷方" width="130" align="right">
            <template #default="{ row }"><span class="amt end">{{ fmt(row.ending_credit) }}</span></template>
          </el-table-column>
        </el-table-column>
      </el-table>
    </div>

    <!-- 合计 -->
    <div class="total-bar" v-if="filtered.length">
      共 {{ filtered.length }} 个科目 · 期末余额借方合计
      <strong class="end">{{ fmt(totals.debit) }}</strong>
      · 贷方合计
      <strong class="end">{{ fmt(totals.credit) }}</strong>
    </div>
  </div>
</template>

<style scoped>
.balance-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #ebeef5;
  gap: 10px;
  flex-wrap: wrap;
  flex-shrink: 0;
}
.toolbar-left { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.hint { font-size: 12px; color: #909399; }
.table-area { flex: 1; overflow: auto; }

.cat-tag {
  display: inline-block;
  padding: 1px 10px;
  border-radius: 10px;
  font-size: 12px;
  background: #f4f4f5;
  color: #606266;
}
.dir-tag {
  display: inline-block;
  padding: 1px 10px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 500;
}
.dir-tag.借 { color: #409eff; background: rgba(64, 158, 255, .1); }
.dir-tag.贷 { color: #e6a23c; background: rgba(230, 162, 60, .12); }

.amt { font-family: 'SF Mono', 'Menlo', 'Consolas', monospace; font-size: 13px; color: #909399; }
.amt.end { color: #409eff; font-weight: 600; }

.total-bar {
  padding: 10px 16px;
  border-top: 1px solid #ebeef5;
  font-size: 13px;
  color: #606266;
  flex-shrink: 0;
}
.total-bar .end { color: #409eff; margin: 0 4px; }
</style>
