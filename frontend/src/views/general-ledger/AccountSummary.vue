<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listSubjects, getLedgerSummary } from '@/api/ledger'
import type { AccountSubject } from '@/types/ledger'

const router = useRouter()

/* ==================== 类型定义 ==================== */

interface SummaryRow {
  id: string
  accountCode: string
  accountName: string
  accountLevel: number
  parentCode: string
  periodDebit: number
  periodCredit: number
  cumDebit: number
  cumCredit: number
  hasChildren: boolean
  children: SummaryRow[]
}

/* ==================== 状态 ==================== */

const period = ref('2026-05')
const levelFilter = ref<number | null>(1)
const searchKeyword = ref('')
const loading = ref(false)
const tableData = ref<SummaryRow[]>([])
const expandedRowKeys = ref<string[]>([])

/* ==================== Mock 数据 ==================== */


/* ==================== 计算属性 ==================== */

const filteredData = computed(() => {
  let data = tableData.value
  if (levelFilter.value !== null) {
    data = data.filter(r => r.accountLevel === levelFilter.value)
  }
  if (searchKeyword.value.trim()) {
    const kw = searchKeyword.value.trim().toLowerCase()
    data = data.filter(r => r.accountCode.includes(kw) || r.accountName.toLowerCase().includes(kw))
  }
  return data
})

const flattenedData = computed(() => {
  const result: SummaryRow[] = []
  const flatten = (rows: SummaryRow[]) => {
    rows.forEach(row => {
      result.push(row)
      if (row.hasChildren && expandedRowKeys.value.includes(row.id)) {
        flatten(row.children)
      }
    })
  }
  flatten(filteredData.value)
  return result
})

const totals = computed(() => {
  let pd = 0, pc = 0, cd = 0, cc = 0
  filteredData.value.forEach(r => {
    pd += r.periodDebit
    pc += r.periodCredit
    cd += r.cumDebit
    cc += r.cumCredit
  })
  return { periodDebit: pd, periodCredit: pc, cumDebit: cd, cumCredit: cc }
})

/* ==================== 方法 ==================== */

/** 加载科目汇总表（真实数据，期间感知） */
async function loadData() {
  loading.value = true
  try {
    const [subsRes, balRes] = await Promise.all([
      listSubjects(),
      getLedgerSummary(period.value || undefined),
    ])
    const balMap = new Map(balRes.data.map(b => [b.code, b]))
    const nodes: SummaryRow[] = (subsRes.data as AccountSubject[]).map(s => {
      const b = balMap.get(s.code)
      return {
        id: s.code,
        accountCode: s.code,
        accountName: s.name,
        accountLevel: s.level,
        parentCode: s.parent_code || '',
        periodDebit: b?.period_debit || 0,
        periodCredit: b?.period_credit || 0,
        cumDebit: b?.cum_debit || 0,
        cumCredit: b?.cum_credit || 0,
        hasChildren: false,
        children: [],
      }
    })
    // 构建科目树
    const map = new Map(nodes.map(n => [n.accountCode, n]))
    const roots: SummaryRow[] = []
    map.forEach(n => {
      const parent = n.parentCode ? map.get(n.parentCode) : undefined
      if (parent) {
        parent.children.push(n)
        parent.hasChildren = true
      } else {
        roots.push(n)
      }
    })
    tableData.value = roots
  } finally {
    loading.value = false
  }
}

function toggleExpand(row: SummaryRow) {
  const idx = expandedRowKeys.value.indexOf(row.id)
  if (idx > -1) {
    expandedRowKeys.value.splice(idx, 1)
  } else {
    expandedRowKeys.value.push(row.id)
  }
}

function expandAll() {
  const allIds: string[] = []
  const collect = (rows: SummaryRow[]) => {
    rows.forEach(r => {
      if (r.hasChildren) allIds.push(r.id)
      collect(r.children)
    })
  }
  collect(filteredData.value)
  expandedRowKeys.value = allIds
}

function collapseAll() {
  expandedRowKeys.value = []
}

function viewDetail(row: SummaryRow) {
  router.push({
    path: '/general-ledger/detail',
    query: { accountCode: row.accountCode, accountName: row.accountName, period: period.value }
  })
}

function formatAmount(val: number): string {
  if (val === 0) return ''
  return val.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function accountClass(row: SummaryRow): string {
  const code = row.accountCode
  if (code.startsWith('1')) return 'asset'
  if (code.startsWith('2')) return 'liability'
  if (code.startsWith('4')) return 'equity'
  if (code.startsWith('5')) return 'cost'
  if (code.startsWith('6')) return 'profit-loss'
  return ''
}

onMounted(() => loadData())
</script>

<template>
  <div class="account-summary-page">
    <!-- ===== 顶部工具栏 ===== -->
    <div class="toolbar">
      <div class="toolbar-left">
        <span class="toolbar-label">会计期间：</span>
        <el-date-picker
          v-model="period"
          type="month"
          format="YYYY-MM"
          value-format="YYYY-MM"
          size="small"
          style="width:130px"
          @change="loadData"
        />
        <el-divider direction="vertical" />
        <span class="toolbar-label">科目级别：</span>
        <el-select v-model="levelFilter" size="small" clearable placeholder="全部" style="width:100px">
          <el-option label="一级科目" :value="1" />
          <el-option label="二级科目" :value="2" />
        </el-select>
      </div>
      <div class="toolbar-right">
        <el-input
          v-model="searchKeyword"
          size="small"
          placeholder="搜索科目编码/名称…"
          clearable
          style="width:200px"
        >
          <template #prefix>
            <span style="color:#909399;font-size:13px;">🔍</span>
          </template>
        </el-input>
        <el-button-group size="small" style="margin-left:8px">
          <el-button @click="expandAll">全部展开</el-button>
          <el-button @click="collapseAll">全部收起</el-button>
        </el-button-group>
        <el-button size="small" @click="loadData" style="margin-left:4px">🔄 刷新</el-button>
      </div>
    </div>

    <!-- ===== 数据表格 ===== -->
    <div class="table-wrapper">
      <el-table
        :data="flattenedData"
        v-loading="loading"
        border
        stripe
        size="small"
        :header-cell-style="{ background: '#f5f7fa', color: '#303133', fontWeight: 600, fontSize: '13px' }"
        :row-class-name="({ row }: { row: SummaryRow }) => accountClass(row)"
        style="width:100%"
        max-height="calc(100vh - 220px)"
      >
        <el-table-column prop="accountCode" label="科目编码" width="140" fixed="left">
          <template #default="{ row }">
            <span :style="{ paddingLeft: (row.accountLevel - 1) * 16 + 'px' }">
              <span
                v-if="row.hasChildren"
                class="expand-toggle"
                @click="toggleExpand(row)"
              >
                {{ expandedRowKeys.includes(row.id) ? '▼' : '▶' }}
              </span>
              <span v-else style="display:inline-block;width:14px;" />
              {{ row.accountCode }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="accountName" label="科目名称" min-width="180" fixed="left">
          <template #default="{ row }">
            <span
              :style="{
                paddingLeft: (row.accountLevel - 1) * 16 + 'px',
                fontWeight: row.accountLevel === 1 ? 600 : 400
              }"
            >
              {{ row.accountName }}
            </span>
          </template>
        </el-table-column>

        <!-- 本期发生额 -->
        <el-table-column label="本期发生额" align="center">
          <el-table-column label="借方" width="140" align="right">
            <template #default="{ row }">
              <span class="amount highlight">{{ formatAmount(row.periodDebit) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="贷方" width="140" align="right">
            <template #default="{ row }">
              <span class="amount highlight">{{ formatAmount(row.periodCredit) }}</span>
            </template>
          </el-table-column>
        </el-table-column>

        <!-- 本年累计 -->
        <el-table-column label="本年累计发生额" align="center">
          <el-table-column label="借方" width="140" align="right">
            <template #default="{ row }">
              <span class="amount">{{ formatAmount(row.cumDebit) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="贷方" width="140" align="right">
            <template #default="{ row }">
              <span class="amount">{{ formatAmount(row.cumCredit) }}</span>
            </template>
          </el-table-column>
        </el-table-column>

        <!-- 操作 -->
        <el-table-column label="操作" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="viewDetail(row)">
              明细账
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- ===== 底部合计 ===== -->
    <div class="footer-bar">
      <div class="footer-left">
        <span>共 <b>{{ filteredData.length }}</b> 个科目</span>
      </div>
      <div class="footer-right">
        <div class="total-cards">
          <div class="total-card">
            <div class="tc-label">本期借方合计</div>
            <div class="tc-value">¥{{ totals.periodDebit.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</div>
          </div>
          <div class="total-card">
            <div class="tc-label">本期贷方合计</div>
            <div class="tc-value">¥{{ totals.periodCredit.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</div>
          </div>
          <div class="total-card">
            <div class="tc-label">本年借方累计</div>
            <div class="tc-value">¥{{ totals.cumDebit.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</div>
          </div>
          <div class="total-card">
            <div class="tc-label">本年贷方累计</div>
            <div class="tc-value">¥{{ totals.cumCredit.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.account-summary-page {
  padding: 16px;
  background: #f0f2f5;
  min-height: 100%;
  display: flex;
  flex-direction: column;
}

/* ===== 工具栏 ===== */
.toolbar {
  background: #fff;
  padding: 12px 16px;
  border-radius: 6px;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.toolbar-label {
  font-size: 13px;
  color: #606266;
  white-space: nowrap;
}

/* ===== 表格 ===== */
.table-wrapper {
  background: #fff;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  flex: 1;
  overflow: hidden;
}

.expand-toggle {
  cursor: pointer;
  display: inline-block;
  width: 14px;
  font-size: 11px;
  color: #909399;
  user-select: none;
}
.expand-toggle:hover { color: #409eff; }

.amount {
  font-family: 'SF Mono', 'Menlo', 'Consolas', monospace;
  font-size: 13px;
  color: #909399;
}
.amount.highlight { color: #303133; font-weight: 500; }

/* ===== 底部 ===== */
.footer-bar {
  background: #fff;
  padding: 10px 16px;
  border-radius: 6px;
  margin-top: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  font-size: 13px;
}

.footer-left { color: #909399; }

.total-cards {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.total-card {
  background: #f5f7fa;
  padding: 8px 16px;
  border-radius: 6px;
  text-align: center;
}

.tc-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 2px;
}

.tc-value {
  font-family: 'SF Mono', 'Menlo', 'Consolas', monospace;
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

:deep(.el-table) { font-size: 13px; }
:deep(.el-table th) { padding: 8px 0; }
:deep(.el-table td) { padding: 6px 0; }
</style>
