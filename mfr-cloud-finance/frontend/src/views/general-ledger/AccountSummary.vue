<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

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

const mockData: SummaryRow[] = [
  // 资产类
  {
    id: 's1', accountCode: '1001', accountName: '库存现金', accountLevel: 1, parentCode: '',
    periodDebit: 120000, periodCredit: 95000, cumDebit: 680000, cumCredit: 655000,
    hasChildren: false, children: []
  },
  {
    id: 's2', accountCode: '1002', accountName: '银行存款', accountLevel: 1, parentCode: '',
    periodDebit: 3560000, periodCredit: 4120000, cumDebit: 18250000, cumCredit: 17530000,
    hasChildren: true, children: [
      {
        id: 's2-1', accountCode: '1002-01', accountName: '基本户(工行)', accountLevel: 2, parentCode: '1002',
        periodDebit: 2500000, periodCredit: 3000000, cumDebit: 12800000, cumCredit: 12100000,
        hasChildren: false, children: []
      },
      {
        id: 's2-2', accountCode: '1002-02', accountName: '一般户(建行)', accountLevel: 2, parentCode: '1002',
        periodDebit: 1060000, periodCredit: 1120000, cumDebit: 5450000, cumCredit: 5430000,
        hasChildren: false, children: []
      }
    ]
  },
  {
    id: 's3', accountCode: '1122', accountName: '应收账款', accountLevel: 1, parentCode: '',
    periodDebit: 1850000, periodCredit: 1620000, cumDebit: 8520000, cumCredit: 7330000,
    hasChildren: false, children: []
  },
  {
    id: 's4', accountCode: '1123', accountName: '预付账款', accountLevel: 1, parentCode: '',
    periodDebit: 150000, periodCredit: 180000, cumDebit: 960000, cumCredit: 860000,
    hasChildren: false, children: []
  },
  {
    id: 's5', accountCode: '1403', accountName: '原材料', accountLevel: 1, parentCode: '',
    periodDebit: 420000, periodCredit: 380000, cumDebit: 2850000, cumCredit: 2430000,
    hasChildren: false, children: []
  },
  {
    id: 's6', accountCode: '1405', accountName: '库存商品', accountLevel: 1, parentCode: '',
    periodDebit: 860000, periodCredit: 920000, cumDebit: 5230000, cumCredit: 5040000,
    hasChildren: false, children: []
  },
  {
    id: 's7', accountCode: '1601', accountName: '固定资产', accountLevel: 1, parentCode: '',
    periodDebit: 180000, periodCredit: 0, cumDebit: 580000, cumCredit: 0,
    hasChildren: false, children: []
  },
  // 负债类
  {
    id: 's8', accountCode: '2001', accountName: '短期借款', accountLevel: 1, parentCode: '',
    periodDebit: 500000, periodCredit: 0, cumDebit: 1500000, cumCredit: 1000000,
    hasChildren: false, children: []
  },
  {
    id: 's9', accountCode: '2202', accountName: '应付账款', accountLevel: 1, parentCode: '',
    periodDebit: 650000, periodCredit: 920000, cumDebit: 3820000, cumCredit: 4500000,
    hasChildren: false, children: []
  },
  {
    id: 's10', accountCode: '2211', accountName: '应付职工薪酬', accountLevel: 1, parentCode: '',
    periodDebit: 380000, periodCredit: 420000, cumDebit: 2280000, cumCredit: 2320000,
    hasChildren: false, children: []
  },
  {
    id: 's11', accountCode: '2221', accountName: '应交税费', accountLevel: 1, parentCode: '',
    periodDebit: 132000, periodCredit: 168000, cumDebit: 780000, cumCredit: 972000,
    hasChildren: false, children: []
  },
  // 权益类
  {
    id: 's12', accountCode: '4001', accountName: '实收资本', accountLevel: 1, parentCode: '',
    periodDebit: 0, periodCredit: 0, cumDebit: 0, cumCredit: 0,
    hasChildren: false, children: []
  },
  // 成本类
  {
    id: 's13', accountCode: '5001', accountName: '生产成本', accountLevel: 1, parentCode: '',
    periodDebit: 480000, periodCredit: 350000, cumDebit: 2560000, cumCredit: 2210000,
    hasChildren: false, children: []
  },
  // 损益类
  {
    id: 's14', accountCode: '6001', accountName: '主营业务收入', accountLevel: 1, parentCode: '',
    periodDebit: 0, periodCredit: 2850000, cumDebit: 0, cumCredit: 16820000,
    hasChildren: false, children: []
  },
  {
    id: 's15', accountCode: '6401', accountName: '主营业务成本', accountLevel: 1, parentCode: '',
    periodDebit: 1680000, periodCredit: 0, cumDebit: 9850000, cumCredit: 0,
    hasChildren: false, children: []
  },
  {
    id: 's16', accountCode: '6601', accountName: '销售费用', accountLevel: 1, parentCode: '',
    periodDebit: 256000, periodCredit: 0, cumDebit: 1520000, cumCredit: 0,
    hasChildren: false, children: []
  },
  {
    id: 's17', accountCode: '6602', accountName: '管理费用', accountLevel: 1, parentCode: '',
    periodDebit: 382000, periodCredit: 0, cumDebit: 2230000, cumCredit: 0,
    hasChildren: false, children: []
  },
  {
    id: 's18', accountCode: '6603', accountName: '财务费用', accountLevel: 1, parentCode: '',
    periodDebit: 18000, periodCredit: 5200, cumDebit: 96000, cumCredit: 32000,
    hasChildren: false, children: []
  }
]

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

function loadData() {
  loading.value = true
  setTimeout(() => {
    tableData.value = mockData
    loading.value = false
  }, 300)
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
