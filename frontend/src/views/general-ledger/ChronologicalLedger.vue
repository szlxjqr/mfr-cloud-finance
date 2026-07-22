<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getJournal } from '@/api/ledger'

/* ==================== 类型定义 ==================== */

interface ChronoEntry {
  id: string
  date: string
  voucherWord: string
  voucherNumber: number
  summary: string
  accountCode: string
  accountName: string
  quantity: number | null      // 数量（辅助核算）
  foreignAmount: number | null // 外币金额
  debitAmount: number
  creditAmount: number
}

/* ==================== 状态 ==================== */

const period = ref('2026-05')
const showAuxItems = ref(false)   // 展示辅助项（数量/外币列）
const loading = ref(false)
const tableData = ref<ChronoEntry[]>([])

/* ==================== Mock 数据 ==================== */


/* ==================== 计算属性 ==================== */

/** 按凭证分组显示时，合并同行 */
const displayData = computed(() => tableData.value)

const totals = computed(() => {
  let debit = 0, credit = 0
  tableData.value.forEach(e => { debit += e.debitAmount; credit += e.creditAmount })
  return { debit, credit }
})

/* ==================== 方法 ==================== */

/** 加载序时账（真实数据，全部凭证分录流水） */
async function loadData() {
  loading.value = true
  try {
    const res = await getJournal(period.value || undefined)
    tableData.value = res.data.lines
      .map((l, i) => {
        const parts = l.voucher_no.split('-')
        const word = parts[0]
        const num = parseInt(parts[parts.length - 1], 10) || 0
        return {
          id: `c-${i}`,
          date: l.date,
          voucherWord: word,
          voucherNumber: num,
          summary: l.summary || '',
          accountCode: l.subject_code,
          accountName: l.subject_name,
          quantity: null,
          foreignAmount: null,
          debitAmount: l.direction === '借' ? l.amount : 0,
          creditAmount: l.direction === '贷' ? l.amount : 0,
        }
      })
      .sort((a, b) =>
        a.date < b.date ? -1 : a.date > b.date ? 1 : a.voucherNumber - b.voucherNumber
      )
  } finally {
    loading.value = false
  }
}

function fmt(v: number): string { if (!v) return ''; return v.toLocaleString('zh-CN',{minimumFractionDigits:2,maximumFractionDigits:2}) }

onMounted(() => loadData())
</script>

<template>
  <div class="chrono-page">
    <!-- ===== 顶部工具栏 ===== -->
    <div class="top-toolbar">
      <div class="toolbar-left">
        <span class="label">期间</span>
        <el-date-picker
          v-model="period" type="month" format="YYYY年MM期"
          value-format="YYYY-MM" size="small" style="width:160px" @change="loadData"
        />
        <el-button size="small" type="primary" plain style="margin-left:8px">筛选 ▾</el-button>
        <el-button size="small" circle @click="loadData"><span style="font-size:13px">🔄</span></el-button>
      </div>
      <div class="toolbar-right">
        <el-checkbox v-model="showAuxItems" size="small" @change="loadData">展示辅助项</el-checkbox>
        <el-button size="small" style="margin-left:12px">打印</el-button>
        <el-button size="small">导出</el-button>
      </div>
    </div>

    <!-- ===== 数据表格 ===== -->
    <div class="table-area">
      <el-table
        :data="displayData" v-loading="loading" border stripe size="small"
        :header-cell-style="{ background:'#f5f7fa', color:'#303133', fontWeight:600, fontSize:'13px' }"
        style="width:100%" max-height="calc(100vh - 120px)"
      >
        <el-table-column prop="date" label="日期" width="110" align="center" sortable fixed />
        <el-table-column label="凭证号" width="110" align="center" fixed>
          <template #default="{ row }">
            <span>{{ row.voucherWord }}-{{ String(row.voucherNumber).padStart(3,'0') }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="summary" label="摘要" min-width="180" show-overflow-tooltip fixed />
        <el-table-column prop="accountCode" label="科目编码" width="110" align="center" />
        <el-table-column prop="accountName" label="科目名称" min-width="140" />
        <el-table-column v-if="showAuxItems" label="数量" width="90" align="right">
          <template #default="{ row }">
            <span v-if="row.quantity !== null">{{ row.quantity.toLocaleString('zh-CN') }}</span>
          </template>
        </el-table-column>
        <el-table-column v-if="showAuxItems" label="外币" width="130" align="right">
          <template #default="{ row }">
            <span v-if="row.foreignAmount !== null" class="amt-fc">{{ row.foreignAmount.toLocaleString('zh-CN',{minimumFractionDigits:2,maximumFractionDigits:2}) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="借方" width="140" align="right">
          <template #default="{ row }">
            <span class="amt debit">{{ fmt(row.debitAmount) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="贷方" width="140" align="right">
          <template #default="{ row }">
            <span class="amt credit">{{ fmt(row.creditAmount) }}</span>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- ===== 底部合计 ===== -->
    <div class="footer-bar">
      <span>共 <b>{{ tableData.length }}</b> 条分录</span>
      <el-divider direction="vertical" />
      <span>借方合计：<b>¥{{ totals.debit.toLocaleString('zh-CN',{minimumFractionDigits:2}) }}</b></span>
      <el-divider direction="vertical" />
      <span>贷方合计：<b>¥{{ totals.credit.toLocaleString('zh-CN',{minimumFractionDigits:2}) }}</b></span>
      <el-divider direction="vertical" />
      <span :class="{'balanced':totals.debit===totals.credit}">
        {{ totals.debit === totals.credit ? '✓ 借贷平衡' : '✗ 借贷不平' }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.chrono-page{ padding:16px; background:#f0f2f5; min-height:100%; display:flex; flex-direction:column; }

.top-toolbar{
  background:#fff; padding:10px 16px; border-radius:6px;
  display:flex; align-items:center; justify-content:space-between;
  flex-wrap:wrap; gap:8px; margin-bottom:12px; box-shadow:0 1px 3px rgba(0,0,0,.06);
}
.toolbar-left,.toolbar-right{ display:flex; align-items:center; gap:8px; }
.label{ font-size:13px; color:#606266; white-space:nowrap; }

.table-area{
  background:#fff; border-radius:6px; box-shadow:0 1px 3px rgba(0,0,0,.06);
  flex:1; overflow:hidden;
}

.amt{ font-family:'SF Mono','Menlo','Consolas',monospace; font-size:13px; color:#606266; }
.amt.debit{ color:#303133; font-weight:500; }
.amt.credit{ color:#67c23a; }
.amt-fc{ font-family:'SF Mono','Menlo','Consolas',monospace; font-size:13px; color:#e6a23c; }

.footer-bar{
  background:#fff; padding:10px 16px; border-radius:6px; margin-top:12px;
  display:flex; align-items:center; gap:12px; flex-wrap:wrap;
  box-shadow:0 1px 3px rgba(0,0,0,.06); font-size:13px; color:#606266;
}
.footer-bar b{ font-family:'SF Mono','Menlo','Consolas',monospace; color:#303133; }
.balanced{ color:#67c23a; font-weight:600; }

:deep(.el-table){ font-size:13px; }
:deep(.el-table th){ padding:8px 0; }
:deep(.el-table td){ padding:6px 0; }
</style>
