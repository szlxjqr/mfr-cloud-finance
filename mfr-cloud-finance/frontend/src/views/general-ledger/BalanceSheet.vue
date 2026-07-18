<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

/* ==================== 类型定义 ==================== */

/** 余额表行 */
interface BalanceRow {
  id: string
  accountCode: string
  accountName: string
  accountLevel: number
  parentCode: string
  openingDebit: number
  openingCredit: number
  openingBalance: number      // 正=借余, 负=贷余
  periodDebit: number
  periodCredit: number
  cumDebit: number            // 本年累计借方
  cumCredit: number           // 本年累计贷方
  endingDebit: number
  endingCredit: number
  endingBalance: number
  hasChildren: boolean
  children: BalanceRow[]
}

/* ==================== 状态 ==================== */

const period = ref('2026-05')
const levelFilter = ref<number | null>(null)
const searchKeyword = ref('')
const showZero = ref(true)
const loading = ref(false)
const tableData = ref<BalanceRow[]>([])
const expandedRowKeys = ref<string[]>([])

/* ==================== Mock 数据 ==================== */

const mockBalanceData: BalanceRow[] = [
  // --- 资产类 ---
  {
    id: 'b1', accountCode: '1001', accountName: '库存现金', accountLevel: 1, parentCode: '',
    openingDebit: 50000, openingCredit: 0, openingBalance: 50000,
    periodDebit: 120000, periodCredit: 95000,
    cumDebit: 680000, cumCredit: 655000,
    endingDebit: 75000, endingCredit: 0, endingBalance: 75000,
    hasChildren: false, children: []
  },
  {
    id: 'b2', accountCode: '1002', accountName: '银行存款', accountLevel: 1, parentCode: '',
    openingDebit: 2580000, openingCredit: 0, openingBalance: 2580000,
    periodDebit: 3560000, periodCredit: 4120000,
    cumDebit: 18250000, cumCredit: 17530000,
    endingDebit: 2020000, endingCredit: 0, endingBalance: 2020000,
    hasChildren: true, children: [
      {
        id: 'b2-1', accountCode: '1002-01', accountName: '银行存款-基本户(工行)', accountLevel: 2, parentCode: '1002',
        openingDebit: 1800000, openingCredit: 0, openingBalance: 1800000,
        periodDebit: 2500000, periodCredit: 3000000,
        cumDebit: 12800000, cumCredit: 12100000,
        endingDebit: 1300000, endingCredit: 0, endingBalance: 1300000,
        hasChildren: false, children: []
      },
      {
        id: 'b2-2', accountCode: '1002-02', accountName: '银行存款-一般户(建行)', accountLevel: 2, parentCode: '1002',
        openingDebit: 780000, openingCredit: 0, openingBalance: 780000,
        periodDebit: 1060000, periodCredit: 1120000,
        cumDebit: 5450000, cumCredit: 5430000,
        endingDebit: 720000, endingCredit: 0, endingBalance: 720000,
        hasChildren: false, children: []
      }
    ]
  },
  {
    id: 'b3', accountCode: '1122', accountName: '应收账款', accountLevel: 1, parentCode: '',
    openingDebit: 960000, openingCredit: 0, openingBalance: 960000,
    periodDebit: 1850000, periodCredit: 1620000,
    cumDebit: 8520000, cumCredit: 7330000,
    endingDebit: 1190000, endingCredit: 0, endingBalance: 1190000,
    hasChildren: true, children: [
      {
        id: 'b3-1', accountCode: '1122-01', accountName: '应收账款-华宇科技', accountLevel: 2, parentCode: '1122',
        openingDebit: 560000, openingCredit: 0, openingBalance: 560000,
        periodDebit: 850000, periodCredit: 720000,
        cumDebit: 4200000, cumCredit: 3510000,
        endingDebit: 690000, endingCredit: 0, endingBalance: 690000,
        hasChildren: false, children: []
      },
      {
        id: 'b3-2', accountCode: '1122-02', accountName: '应收账款-明达集团', accountLevel: 2, parentCode: '1122',
        openingDebit: 400000, openingCredit: 0, openingBalance: 400000,
        periodDebit: 1000000, periodCredit: 900000,
        cumDebit: 4320000, cumCredit: 3820000,
        endingDebit: 500000, endingCredit: 0, endingBalance: 500000,
        hasChildren: false, children: []
      }
    ]
  },
  {
    id: 'b4', accountCode: '1123', accountName: '预付账款', accountLevel: 1, parentCode: '',
    openingDebit: 280000, openingCredit: 0, openingBalance: 280000,
    periodDebit: 150000, periodCredit: 180000,
    cumDebit: 960000, cumCredit: 860000,
    endingDebit: 250000, endingCredit: 0, endingBalance: 250000,
    hasChildren: false, children: []
  },
  {
    id: 'b5', accountCode: '1221', accountName: '其他应收款', accountLevel: 1, parentCode: '',
    openingDebit: 85000, openingCredit: 0, openingBalance: 85000,
    periodDebit: 42000, periodCredit: 38000,
    cumDebit: 380000, cumCredit: 333000,
    endingDebit: 89000, endingCredit: 0, endingBalance: 89000,
    hasChildren: false, children: []
  },
  {
    id: 'b6', accountCode: '1403', accountName: '原材料', accountLevel: 1, parentCode: '',
    openingDebit: 680000, openingCredit: 0, openingBalance: 680000,
    periodDebit: 420000, periodCredit: 380000,
    cumDebit: 2850000, cumCredit: 2430000,
    endingDebit: 720000, endingCredit: 0, endingBalance: 720000,
    hasChildren: false, children: []
  },
  {
    id: 'b7', accountCode: '1405', accountName: '库存商品', accountLevel: 1, parentCode: '',
    openingDebit: 1250000, openingCredit: 0, openingBalance: 1250000,
    periodDebit: 860000, periodCredit: 920000,
    cumDebit: 5230000, cumCredit: 5040000,
    endingDebit: 1190000, endingCredit: 0, endingBalance: 1190000,
    hasChildren: false, children: []
  },
  {
    id: 'b8', accountCode: '1601', accountName: '固定资产', accountLevel: 1, parentCode: '',
    openingDebit: 4200000, openingCredit: 0, openingBalance: 4200000,
    periodDebit: 180000, periodCredit: 0,
    cumDebit: 580000, cumCredit: 0,
    endingDebit: 4380000, endingCredit: 0, endingBalance: 4380000,
    hasChildren: false, children: []
  },
  {
    id: 'b9', accountCode: '1602', accountName: '累计折旧', accountLevel: 1, parentCode: '',
    openingDebit: 0, openingCredit: 860000, openingBalance: -860000,
    periodDebit: 0, periodCredit: 42000,
    cumDebit: 0, cumCredit: 252000,
    endingDebit: 0, endingCredit: 902000, endingBalance: -902000,
    hasChildren: false, children: []
  },

  // --- 负债类 ---
  {
    id: 'b10', accountCode: '2001', accountName: '短期借款', accountLevel: 1, parentCode: '',
    openingDebit: 0, openingCredit: 1500000, openingBalance: -1500000,
    periodDebit: 500000, periodCredit: 0,
    cumDebit: 1500000, cumCredit: 1000000,
    endingDebit: 0, endingCredit: 1000000, endingBalance: -1000000,
    hasChildren: false, children: []
  },
  {
    id: 'b11', accountCode: '2202', accountName: '应付账款', accountLevel: 1, parentCode: '',
    openingDebit: 0, openingCredit: 780000, openingBalance: -780000,
    periodDebit: 650000, periodCredit: 920000,
    cumDebit: 3820000, cumCredit: 4500000,
    endingDebit: 0, endingCredit: 1050000, endingBalance: -1050000,
    hasChildren: false, children: []
  },
  {
    id: 'b12', accountCode: '2203', accountName: '预收账款', accountLevel: 1, parentCode: '',
    openingDebit: 0, openingCredit: 320000, openingBalance: -320000,
    periodDebit: 180000, periodCredit: 250000,
    cumDebit: 960000, cumCredit: 1230000,
    endingDebit: 0, endingCredit: 390000, endingBalance: -390000,
    hasChildren: false, children: []
  },
  {
    id: 'b13', accountCode: '2211', accountName: '应付职工薪酬', accountLevel: 1, parentCode: '',
    openingDebit: 0, openingCredit: 420000, openingBalance: -420000,
    periodDebit: 380000, periodCredit: 420000,
    cumDebit: 2280000, cumCredit: 2320000,
    endingDebit: 0, endingCredit: 460000, endingBalance: -460000,
    hasChildren: false, children: []
  },
  {
    id: 'b14', accountCode: '2221', accountName: '应交税费', accountLevel: 1, parentCode: '',
    openingDebit: 0, openingCredit: 156000, openingBalance: -156000,
    periodDebit: 132000, periodCredit: 168000,
    cumDebit: 780000, cumCredit: 972000,
    endingDebit: 0, endingCredit: 192000, endingBalance: -192000,
    hasChildren: false, children: []
  },

  // --- 权益类 ---
  {
    id: 'b15', accountCode: '4001', accountName: '实收资本', accountLevel: 1, parentCode: '',
    openingDebit: 0, openingCredit: 5000000, openingBalance: -5000000,
    periodDebit: 0, periodCredit: 0,
    cumDebit: 0, cumCredit: 0,
    endingDebit: 0, endingCredit: 5000000, endingBalance: -5000000,
    hasChildren: false, children: []
  },
  {
    id: 'b16', accountCode: '4103', accountName: '本年利润', accountLevel: 1, parentCode: '',
    openingDebit: 0, openingCredit: 0, openingBalance: 0,
    periodDebit: 0, periodCredit: 0,
    cumDebit: 0, cumCredit: 0,
    endingDebit: 0, endingCredit: 0, endingBalance: 0,
    hasChildren: false, children: []
  },
  {
    id: 'b17', accountCode: '4104', accountName: '利润分配', accountLevel: 1, parentCode: '',
    openingDebit: 0, openingCredit: 1820000, openingBalance: -1820000,
    periodDebit: 0, periodCredit: 0,
    cumDebit: 0, cumCredit: 0,
    endingDebit: 0, endingCredit: 1820000, endingBalance: -1820000,
    hasChildren: false, children: []
  },

  // --- 成本类 ---
  {
    id: 'b18', accountCode: '5001', accountName: '生产成本', accountLevel: 1, parentCode: '',
    openingDebit: 320000, openingCredit: 0, openingBalance: 320000,
    periodDebit: 480000, periodCredit: 350000,
    cumDebit: 2560000, cumCredit: 2210000,
    endingDebit: 450000, endingCredit: 0, endingBalance: 450000,
    hasChildren: false, children: []
  },

  // --- 损益类 ---
  {
    id: 'b19', accountCode: '6001', accountName: '主营业务收入', accountLevel: 1, parentCode: '',
    openingDebit: 0, openingCredit: 0, openingBalance: 0,
    periodDebit: 0, periodCredit: 2850000,
    cumDebit: 0, cumCredit: 16820000,
    endingDebit: 0, endingCredit: 2850000, endingBalance: -2850000,
    hasChildren: false, children: []
  },
  {
    id: 'b20', accountCode: '6401', accountName: '主营业务成本', accountLevel: 1, parentCode: '',
    openingDebit: 0, openingCredit: 0, openingBalance: 0,
    periodDebit: 1680000, periodCredit: 0,
    cumDebit: 9850000, cumCredit: 0,
    endingDebit: 1680000, endingCredit: 0, endingBalance: 1680000,
    hasChildren: false, children: []
  },
  {
    id: 'b21', accountCode: '6601', accountName: '销售费用', accountLevel: 1, parentCode: '',
    openingDebit: 0, openingCredit: 0, openingBalance: 0,
    periodDebit: 256000, periodCredit: 0,
    cumDebit: 1520000, cumCredit: 0,
    endingDebit: 256000, endingCredit: 0, endingBalance: 256000,
    hasChildren: false, children: []
  },
  {
    id: 'b22', accountCode: '6602', accountName: '管理费用', accountLevel: 1, parentCode: '',
    openingDebit: 0, openingCredit: 0, openingBalance: 0,
    periodDebit: 382000, periodCredit: 0,
    cumDebit: 2230000, cumCredit: 0,
    endingDebit: 382000, endingCredit: 0, endingBalance: 382000,
    hasChildren: false, children: []
  },
  {
    id: 'b23', accountCode: '6603', accountName: '财务费用', accountLevel: 1, parentCode: '',
    openingDebit: 0, openingCredit: 0, openingBalance: 0,
    periodDebit: 18000, periodCredit: 5200,
    cumDebit: 96000, cumCredit: 32000,
    endingDebit: 12800, endingCredit: 0, endingBalance: 12800,
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
    data = data.filter(r =>
      r.accountCode.toLowerCase().includes(kw) ||
      r.accountName.toLowerCase().includes(kw)
    )
  }

  if (!showZero.value) {
    data = data.filter(r =>
      r.periodDebit !== 0 || r.periodCredit !== 0 ||
      r.openingBalance !== 0 || r.endingBalance !== 0
    )
  }

  return data
})

const flattenedData = computed(() => {
  const result: BalanceRow[] = []
  const flatten = (rows: BalanceRow[]) => {
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
  let od = 0, oc = 0, pd = 0, pc = 0, cd = 0, cc = 0, ed = 0, ec = 0
  filteredData.value.forEach(r => {
    od += r.openingDebit
    oc += r.openingCredit
    pd += r.periodDebit
    pc += r.periodCredit
    cd += r.cumDebit
    cc += r.cumCredit
    ed += r.endingDebit
    ec += r.endingCredit
  })
  return { openingDebit: od, openingCredit: oc, periodDebit: pd, periodCredit: pc, cumDebit: cd, cumCredit: cc, endingDebit: ed, endingCredit: ec }
})

/* ==================== 方法 ==================== */

function loadData() {
  loading.value = true
  setTimeout(() => {
    tableData.value = mockBalanceData
    loading.value = false
  }, 300)
}

function toggleExpand(row: BalanceRow) {
  const idx = expandedRowKeys.value.indexOf(row.id)
  if (idx > -1) {
    expandedRowKeys.value.splice(idx, 1)
  } else {
    expandedRowKeys.value.push(row.id)
  }
}

function expandAll() {
  const allIds: string[] = []
  const collect = (rows: BalanceRow[]) => {
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

function viewDetail(row: BalanceRow) {
  router.push({
    path: '/general-ledger/detail',
    query: {
      accountCode: row.accountCode,
      accountName: row.accountName,
      period: period.value
    }
  })
}

function viewGeneral(row: BalanceRow) {
  router.push({
    path: '/general-ledger/general',
    query: {
      accountCode: row.accountCode,
      period: period.value
    }
  })
}

function formatAmount(val: number): string {
  if (val === 0) return ''
  return val.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function getDirection(row: BalanceRow): string {
  const code = row.accountCode
  if (code.startsWith('1') || code.startsWith('5')) return '借'
  if (code.startsWith('2') || code.startsWith('3') || code.startsWith('4') || code.startsWith('6')) return '贷'
  return row.endingBalance >= 0 ? '借' : '贷'
}

function levelClass(level: number): string {
  return `level-${level}`
}

function accountClass(row: BalanceRow): string {
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
  <div class="balance-sheet-page">
    <!-- ===== 顶部工具栏 ===== -->
    <div class="toolbar">
      <div class="toolbar-left">
        <span class="toolbar-label">会计期间：</span>
        <el-date-picker
          v-model="period"
          type="month"
          placeholder="选择期间"
          format="YYYY-MM"
          value-format="YYYY-MM"
          size="small"
          style="width:140px"
          @change="loadData"
        />
        <el-divider direction="vertical" />
        <span class="toolbar-label">科目级别：</span>
        <el-select v-model="levelFilter" size="small" clearable placeholder="全部" style="width:100px">
          <el-option label="一级科目" :value="1" />
          <el-option label="二级科目" :value="2" />
        </el-select>
        <el-checkbox v-model="showZero" size="small" style="margin-left:12px">
          含无发生额
        </el-checkbox>
      </div>
      <div class="toolbar-right">
        <el-input
          v-model="searchKeyword"
          size="small"
          placeholder="搜索科目编码/名称…"
          clearable
          style="width:220px"
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
        <el-dropdown style="margin-left:4px">
          <el-button size="small">
            更多 ▾
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item>📥 导出Excel</el-dropdown-item>
              <el-dropdown-item>🖨 打印</el-dropdown-item>
              <el-dropdown-item>📊 按科目类别汇总</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
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
        :row-class-name="({ row }: { row: BalanceRow }) => [levelClass(row.accountLevel), accountClass(row)]"
        style="width:100%"
        max-height="calc(100vh - 220px)"
      >
        <!-- 科目编码 -->
        <el-table-column prop="accountCode" label="科目编码" width="130" fixed="left">
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

        <!-- 科目名称 -->
        <el-table-column prop="accountName" label="科目名称" min-width="170" fixed="left">
          <template #default="{ row }">
            <span
              :class="['account-name', levelClass(row.accountLevel)]"
              :style="{ paddingLeft: (row.accountLevel - 1) * 16 + 'px' }"
            >
              {{ row.accountName }}
            </span>
          </template>
        </el-table-column>

        <!-- 期初余额 -->
        <el-table-column label="期初余额" align="center">
          <el-table-column label="借方" width="130" align="right">
            <template #default="{ row }">
              <span class="amount">{{ formatAmount(row.openingDebit) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="贷方" width="130" align="right">
            <template #default="{ row }">
              <span class="amount">{{ formatAmount(row.openingCredit) }}</span>
            </template>
          </el-table-column>
        </el-table-column>

        <!-- 本期发生额 -->
        <el-table-column label="本期发生额" align="center">
          <el-table-column label="借方" width="130" align="right">
            <template #default="{ row }">
              <span class="amount highlight">{{ formatAmount(row.periodDebit) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="贷方" width="130" align="right">
            <template #default="{ row }">
              <span class="amount highlight">{{ formatAmount(row.periodCredit) }}</span>
            </template>
          </el-table-column>
        </el-table-column>

        <!-- 本年累计 -->
        <el-table-column label="本年累计" align="center">
          <el-table-column label="借方" width="130" align="right">
            <template #default="{ row }">
              <span class="amount">{{ formatAmount(row.cumDebit) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="贷方" width="130" align="right">
            <template #default="{ row }">
              <span class="amount">{{ formatAmount(row.cumCredit) }}</span>
            </template>
          </el-table-column>
        </el-table-column>

        <!-- 期末余额 -->
        <el-table-column label="期末余额" align="center">
          <el-table-column label="借方" width="130" align="right">
            <template #default="{ row }">
              <span class="amount ending" :class="{ 'debit-end': row.endingBalance > 0 }">
                {{ formatAmount(row.endingDebit) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="贷方" width="130" align="right">
            <template #default="{ row }">
              <span class="amount ending" :class="{ 'credit-end': row.endingBalance < 0 }">
                {{ formatAmount(row.endingCredit) }}
              </span>
            </template>
          </el-table-column>
        </el-table-column>

        <!-- 方向 -->
        <el-table-column label="方向" width="60" align="center">
          <template #default="{ row }">
            <el-tag
              :type="getDirection(row) === '借' ? '' : 'success'"
              size="small"
              effect="plain"
            >
              {{ getDirection(row) }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 操作 -->
        <el-table-column label="操作" width="110" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="viewDetail(row)">明细账</el-button>
            <el-button link type="primary" size="small" @click="viewGeneral(row)">总账</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- ===== 底部合计栏 ===== -->
    <div class="footer-bar">
      <div class="footer-left">
        <span>共 <b>{{ filteredData.length }}</b> 个科目</span>
        <el-divider direction="vertical" />
        <span>其中展开 {{ flattenedData.length }} 行</span>
      </div>
      <div class="footer-right">
        <div class="total-grid">
          <div class="total-block">
            <div class="total-block-title">期初余额</div>
            <div class="total-block-values">
              <span>借 ¥{{ totals.openingDebit.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</span>
              <span>贷 ¥{{ totals.openingCredit.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</span>
            </div>
          </div>
          <div class="total-block">
            <div class="total-block-title">本期发生</div>
            <div class="total-block-values">
              <span>借 ¥{{ totals.periodDebit.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</span>
              <span>贷 ¥{{ totals.periodCredit.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</span>
            </div>
          </div>
          <div class="total-block">
            <div class="total-block-title">本年累计</div>
            <div class="total-block-values">
              <span>借 ¥{{ totals.cumDebit.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</span>
              <span>贷 ¥{{ totals.cumCredit.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</span>
            </div>
          </div>
          <div class="total-block highlight-block">
            <div class="total-block-title">期末余额</div>
            <div class="total-block-values">
              <span>借 ¥{{ totals.endingDebit.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</span>
              <span>贷 ¥{{ totals.endingCredit.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.balance-sheet-page {
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
  transition: color 0.2s;
  user-select: none;
}

.expand-toggle:hover {
  color: #409eff;
}

.account-name.level-1 {
  font-weight: 600;
  color: #303133;
}

.account-name.level-2 {
  color: #606266;
}

.amount {
  font-family: 'SF Mono', 'Menlo', 'Consolas', monospace;
  font-size: 13px;
  color: #909399;
}

.amount.highlight {
  color: #303133;
  font-weight: 500;
}

.amount.ending {
  font-weight: 600;
}

.amount.ending.debit-end {
  color: #409eff;
}

.amount.ending.credit-end {
  color: #67c23a;
}

/* ===== 底部合计栏 ===== */
.footer-bar {
  background: #fff;
  padding: 12px 16px;
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

.footer-left {
  color: #909399;
}

.total-grid {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.total-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 6px 12px;
  background: #f5f7fa;
  border-radius: 6px;
}

.total-block.highlight-block {
  background: #ecf5ff;
}

.total-block-title {
  font-size: 12px;
  color: #909399;
  text-align: center;
}

.total-block-values {
  display: flex;
  gap: 12px;
  font-family: 'SF Mono', 'Menlo', 'Consolas', monospace;
  font-size: 13px;
  color: #303133;
}

/* ===== Element Plus 微调 ===== */
:deep(.el-table) {
  font-size: 13px;
}

:deep(.el-table th) {
  padding: 8px 0;
}

:deep(.el-table td) {
  padding: 6px 0;
}

:deep(.el-table .cell) {
  padding: 0 8px;
}
</style>
