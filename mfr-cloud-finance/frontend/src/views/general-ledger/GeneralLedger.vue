<script setup lang="ts">
import { ref, computed, watch } from 'vue'

/* ==================== 类型定义 ==================== */

/** 总账行（按科目汇总） */
interface GeneralLedgerRow {
  id: string
  accountCode: string     // 科目编码
  accountName: string     // 科目名称
  accountLevel: number    // 科目级别 1/2/3
  parentCode: string      // 上级科目编码
  openingDebit: number    // 期初借方余额
  openingCredit: number   // 期初贷方余额
  openingBalance: number  // 期初余额（正=借，负=贷）
  periodDebit: number     // 本期借方发生额
  periodCredit: number    // 本期贷方发生额
  endingDebit: number     // 期末借方余额
  endingCredit: number    // 期末贷方余额
  endingBalance: number   // 期末余额（正=借，负=贷）
  hasChildren: boolean    // 是否有下级科目
  expanded: boolean       // 展开状态
  children: GeneralLedgerRow[]
}

/* ==================== 状态 ==================== */

/** 会计期间 */
const period = ref('2026-05')

/** 科目级别筛选 */
const levelFilter = ref<number | null>(null)

/** 科目编码/名称搜索 */
const searchKeyword = ref('')

/** 显示无发生额科目 */
const showZero = ref(true)

/** 表格数据 */
const tableData = ref<GeneralLedgerRow[]>([])

/** 展开的行 ID 集合 */
const expandedRowKeys = ref<string[]>([])

/** 加载状态 */
const loading = ref(false)

/* ==================== Mock 数据 ==================== */

/** 会计科目表（标准企业会计科目） */
const mockAccountTree: GeneralLedgerRow[] = [
  {
    id: '1', accountCode: '1001', accountName: '库存现金', accountLevel: 1, parentCode: '',
    openingDebit: 50000, openingCredit: 0, openingBalance: 50000,
    periodDebit: 120000, periodCredit: 95000,
    endingDebit: 75000, endingCredit: 0, endingBalance: 75000,
    hasChildren: false, expanded: false, children: []
  },
  {
    id: '2', accountCode: '1002', accountName: '银行存款', accountLevel: 1, parentCode: '',
    openingDebit: 2580000, openingCredit: 0, openingBalance: 2580000,
    periodDebit: 3560000, periodCredit: 4120000,
    endingDebit: 2020000, endingCredit: 0, endingBalance: 2020000,
    hasChildren: true, expanded: false, children: [
      {
        id: '2-1', accountCode: '1002-01', accountName: '银行存款-基本户(工行)', accountLevel: 2, parentCode: '1002',
        openingDebit: 1800000, openingCredit: 0, openingBalance: 1800000,
        periodDebit: 2500000, periodCredit: 3000000,
        endingDebit: 1300000, endingCredit: 0, endingBalance: 1300000,
        hasChildren: false, expanded: false, children: []
      },
      {
        id: '2-2', accountCode: '1002-02', accountName: '银行存款-一般户(建行)', accountLevel: 2, parentCode: '1002',
        openingDebit: 780000, openingCredit: 0, openingBalance: 780000,
        periodDebit: 1060000, periodCredit: 1120000,
        endingDebit: 720000, endingCredit: 0, endingBalance: 720000,
        hasChildren: false, expanded: false, children: []
      }
    ]
  },
  {
    id: '3', accountCode: '1122', accountName: '应收账款', accountLevel: 1, parentCode: '',
    openingDebit: 960000, openingCredit: 0, openingBalance: 960000,
    periodDebit: 1850000, periodCredit: 1620000,
    endingDebit: 1190000, endingCredit: 0, endingBalance: 1190000,
    hasChildren: true, expanded: false, children: [
      {
        id: '3-1', accountCode: '1122-01', accountName: '应收账款-华宇科技', accountLevel: 2, parentCode: '1122',
        openingDebit: 560000, openingCredit: 0, openingBalance: 560000,
        periodDebit: 850000, periodCredit: 720000,
        endingDebit: 690000, endingCredit: 0, endingBalance: 690000,
        hasChildren: false, expanded: false, children: []
      },
      {
        id: '3-2', accountCode: '1122-02', accountName: '应收账款-明达集团', accountLevel: 2, parentCode: '1122',
        openingDebit: 400000, openingCredit: 0, openingBalance: 400000,
        periodDebit: 1000000, periodCredit: 900000,
        endingDebit: 500000, endingCredit: 0, endingBalance: 500000,
        hasChildren: false, expanded: false, children: []
      }
    ]
  },
  {
    id: '4', accountCode: '1403', accountName: '原材料', accountLevel: 1, parentCode: '',
    openingDebit: 680000, openingCredit: 0, openingBalance: 680000,
    periodDebit: 420000, periodCredit: 380000,
    endingDebit: 720000, endingCredit: 0, endingBalance: 720000,
    hasChildren: false, expanded: false, children: []
  },
  {
    id: '5', accountCode: '1405', accountName: '库存商品', accountLevel: 1, parentCode: '',
    openingDebit: 1250000, openingCredit: 0, openingBalance: 1250000,
    periodDebit: 860000, periodCredit: 920000,
    endingDebit: 1190000, endingCredit: 0, endingBalance: 1190000,
    hasChildren: false, expanded: false, children: []
  },
  {
    id: '6', accountCode: '1601', accountName: '固定资产', accountLevel: 1, parentCode: '',
    openingDebit: 4200000, openingCredit: 0, openingBalance: 4200000,
    periodDebit: 180000, periodCredit: 0,
    endingDebit: 4380000, endingCredit: 0, endingBalance: 4380000,
    hasChildren: false, expanded: false, children: []
  },
  {
    id: '7', accountCode: '1602', accountName: '累计折旧', accountLevel: 1, parentCode: '',
    openingDebit: 0, openingCredit: 860000, openingBalance: -860000,
    periodDebit: 0, periodCredit: 42000,
    endingDebit: 0, endingCredit: 902000, endingBalance: -902000,
    hasChildren: false, expanded: false, children: []
  },
  {
    id: '8', accountCode: '2001', accountName: '短期借款', accountLevel: 1, parentCode: '',
    openingDebit: 0, openingCredit: 1500000, openingBalance: -1500000,
    periodDebit: 500000, periodCredit: 0,
    endingDebit: 0, endingCredit: 1000000, endingBalance: -1000000,
    hasChildren: false, expanded: false, children: []
  },
  {
    id: '9', accountCode: '2202', accountName: '应付账款', accountLevel: 1, parentCode: '',
    openingDebit: 0, openingCredit: 780000, openingBalance: -780000,
    periodDebit: 650000, periodCredit: 920000,
    endingDebit: 0, endingCredit: 1050000, endingBalance: -1050000,
    hasChildren: true, expanded: false, children: [
      {
        id: '9-1', accountCode: '2202-01', accountName: '应付账款-鑫达原料', accountLevel: 2, parentCode: '2202',
        openingDebit: 0, openingCredit: 480000, openingBalance: -480000,
        periodDebit: 380000, periodCredit: 520000,
        endingDebit: 0, endingCredit: 620000, endingBalance: -620000,
        hasChildren: false, expanded: false, children: []
      },
      {
        id: '9-2', accountCode: '2202-02', accountName: '应付账款-恒通物流', accountLevel: 2, parentCode: '2202',
        openingDebit: 0, openingCredit: 300000, openingBalance: -300000,
        periodDebit: 270000, periodCredit: 400000,
        endingDebit: 0, endingCredit: 430000, endingBalance: -430000,
        hasChildren: false, expanded: false, children: []
      }
    ]
  },
  {
    id: '10', accountCode: '2221', accountName: '应交税费', accountLevel: 1, parentCode: '',
    openingDebit: 0, openingCredit: 156000, openingBalance: -156000,
    periodDebit: 132000, periodCredit: 168000,
    endingDebit: 0, endingCredit: 192000, endingBalance: -192000,
    hasChildren: false, expanded: false, children: []
  },
  {
    id: '11', accountCode: '4001', accountName: '实收资本', accountLevel: 1, parentCode: '',
    openingDebit: 0, openingCredit: 5000000, openingBalance: -5000000,
    periodDebit: 0, periodCredit: 0,
    endingDebit: 0, endingCredit: 5000000, endingBalance: -5000000,
    hasChildren: false, expanded: false, children: []
  },
  {
    id: '12', accountCode: '4103', accountName: '本年利润', accountLevel: 1, parentCode: '',
    openingDebit: 0, openingCredit: 0, openingBalance: 0,
    periodDebit: 0, periodCredit: 0,
    endingDebit: 0, endingCredit: 0, endingBalance: 0,
    hasChildren: false, expanded: false, children: []
  },
  {
    id: '13', accountCode: '5001', accountName: '生产成本', accountLevel: 1, parentCode: '',
    openingDebit: 320000, openingCredit: 0, openingBalance: 320000,
    periodDebit: 480000, periodCredit: 350000,
    endingDebit: 450000, endingCredit: 0, endingBalance: 450000,
    hasChildren: false, expanded: false, children: []
  },
  {
    id: '14', accountCode: '6001', accountName: '主营业务收入', accountLevel: 1, parentCode: '',
    openingDebit: 0, openingCredit: 0, openingBalance: 0,
    periodDebit: 0, periodCredit: 2850000,
    endingDebit: 0, endingCredit: 2850000, endingBalance: -2850000,
    hasChildren: false, expanded: false, children: []
  },
  {
    id: '15', accountCode: '6401', accountName: '主营业务成本', accountLevel: 1, parentCode: '',
    openingDebit: 0, openingCredit: 0, openingBalance: 0,
    periodDebit: 1680000, periodCredit: 0,
    endingDebit: 1680000, endingCredit: 0, endingBalance: 1680000,
    hasChildren: false, expanded: false, children: []
  },
  {
    id: '16', accountCode: '6601', accountName: '销售费用', accountLevel: 1, parentCode: '',
    openingDebit: 0, openingCredit: 0, openingBalance: 0,
    periodDebit: 256000, periodCredit: 0,
    endingDebit: 256000, endingCredit: 0, endingBalance: 256000,
    hasChildren: false, expanded: false, children: []
  },
  {
    id: '17', accountCode: '6602', accountName: '管理费用', accountLevel: 1, parentCode: '',
    openingDebit: 0, openingCredit: 0, openingBalance: 0,
    periodDebit: 382000, periodCredit: 0,
    endingDebit: 382000, endingCredit: 0, endingBalance: 382000,
    hasChildren: false, expanded: false, children: []
  }
]

/* ==================== 计算属性 ==================== */

/** 平铺后的显示数据（含子级展开） */
const flattenedData = computed<GeneralLedgerRow[]>(() => {
  const result: GeneralLedgerRow[] = []
  const flatten = (rows: GeneralLedgerRow[]) => {
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

/** 按条件筛选后的数据 */
const filteredData = computed(() => {
  let data = tableData.value

  // 按科目级别筛选
  if (levelFilter.value !== null) {
    data = data.filter(r => r.accountLevel === levelFilter.value)
  }

  // 按关键词搜索
  if (searchKeyword.value.trim()) {
    const kw = searchKeyword.value.trim().toLowerCase()
    data = data.filter(r =>
      r.accountCode.toLowerCase().includes(kw) ||
      r.accountName.toLowerCase().includes(kw)
    )
  }

  // 是否显示无发生额科目
  if (!showZero.value) {
    data = data.filter(r =>
      r.periodDebit !== 0 || r.periodCredit !== 0
    )
  }

  return data
})

/** 合计行 */
const totals = computed(() => {
  let sumOpeningDebit = 0, sumOpeningCredit = 0
  let sumPeriodDebit = 0, sumPeriodCredit = 0
  let sumEndingDebit = 0, sumEndingCredit = 0

  filteredData.value.forEach(r => {
    sumOpeningDebit += r.openingDebit
    sumOpeningCredit += r.openingCredit
    sumPeriodDebit += r.periodDebit
    sumPeriodCredit += r.periodCredit
    sumEndingDebit += r.endingDebit
    sumEndingCredit += r.endingCredit
  })

  return {
    openingDebit: sumOpeningDebit,
    openingCredit: sumOpeningCredit,
    periodDebit: sumPeriodDebit,
    periodCredit: sumPeriodCredit,
    endingDebit: sumEndingDebit,
    endingCredit: sumEndingCredit
  }
})

/* ==================== 方法 ==================== */

/** 加载数据 */
function loadData() {
  loading.value = true
  // 模拟异步加载
  setTimeout(() => {
    tableData.value = mockAccountTree
    loading.value = false
  }, 300)
}

/** 切换展开 */
function toggleExpand(row: GeneralLedgerRow) {
  const idx = expandedRowKeys.value.indexOf(row.id)
  if (idx > -1) {
    expandedRowKeys.value.splice(idx, 1)
  } else {
    expandedRowKeys.value.push(row.id)
  }
}

/** 展开全部 */
function expandAll() {
  const allIds: string[] = []
  const collect = (rows: GeneralLedgerRow[]) => {
    rows.forEach(r => {
      if (r.hasChildren) allIds.push(r.id)
      collect(r.children)
    })
  }
  collect(filteredData.value)
  expandedRowKeys.value = allIds
}

/** 收起全部 */
function collapseAll() {
  expandedRowKeys.value = []
}

/** 联查明细账 */
function viewDetail(row: GeneralLedgerRow) {
  // 跳转到明细账页面，携带科目参数
  const url = `/general-ledger/detail?accountCode=${row.accountCode}&accountName=${encodeURIComponent(row.accountName)}&period=${period.value}`
  window.open(url, '_blank')
}

/** 格式化金额 */
function formatAmount(val: number): string {
  if (val === 0) return ''
  return Math.abs(val).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

/** 余额方向标记 */
function getDirection(row: GeneralLedgerRow): string {
  // 资产/成本类借方余额，负债/权益/收入类贷方余额
  const code = row.accountCode
  if (code.startsWith('1') || code.startsWith('5')) return '借'
  if (code.startsWith('2') || code.startsWith('3') || code.startsWith('4') || code.startsWith('6')) return '贷'
  return row.endingBalance >= 0 ? '借' : '贷'
}

/** 科目级别样式类 */
function levelClass(level: number): string {
  return `level-${level}`
}

/* ==================== 生命周期 ==================== */

loadData()

/* ==================== 监听器 ==================== */

// 筛选条件变化时收起所有展开
watch([levelFilter, searchKeyword, showZero], () => {
  expandedRowKeys.value = []
})
</script>

<template>
  <div class="general-ledger-page">
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
          style="width: 140px"
          @change="loadData"
        />
        <el-divider direction="vertical" />
        <span class="toolbar-label">科目级别：</span>
        <el-select
          v-model="levelFilter"
          size="small"
          clearable
          placeholder="全部"
          style="width: 100px"
        >
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
          style="width: 220px"
          :prefix-icon="null"
        >
          <template #prefix>
            <span style="color:#909399;font-size:13px;">🔍</span>
          </template>
        </el-input>
        <el-button-group size="small" style="margin-left:8px">
          <el-button @click="expandAll">全部展开</el-button>
          <el-button @click="collapseAll">全部收起</el-button>
        </el-button-group>
        <el-button size="small" :icon="null" @click="loadData" style="margin-left:4px">
          🔄 刷新
        </el-button>
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
        :row-class-name="({ row }: { row: GeneralLedgerRow }) => levelClass(row.accountLevel)"
        style="width: 100%"
        max-height="calc(100vh - 220px)"
      >
        <!-- 固定列：科目编码 -->
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
              <span v-else style="display:inline-block;width:14px;"></span>
              {{ row.accountCode }}
            </span>
          </template>
        </el-table-column>

        <!-- 科目名称 -->
        <el-table-column prop="accountName" label="科目名称" min-width="180" fixed="left">
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
              <span class="amount" :class="{ highlight: row.periodDebit > 0 }">
                {{ formatAmount(row.periodDebit) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="贷方" width="130" align="right">
            <template #default="{ row }">
              <span class="amount" :class="{ highlight: row.periodCredit > 0 }">
                {{ formatAmount(row.periodCredit) }}
              </span>
            </template>
          </el-table-column>
        </el-table-column>

        <!-- 期末余额 -->
        <el-table-column label="期末余额" align="center">
          <el-table-column label="借方" width="130" align="right">
            <template #default="{ row }">
              <span class="amount" :class="{ 'ending-balance': row.endingBalance > 0 }">
                {{ formatAmount(row.endingDebit) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="贷方" width="130" align="right">
            <template #default="{ row }">
              <span class="amount" :class="{ 'ending-balance': row.endingBalance < 0 }">
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
        <el-table-column label="操作" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="viewDetail(row)">
              明细账
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- ===== 底部合计栏 ===== -->
    <div class="footer-bar">
      <div class="footer-left">
        <span>共 <b>{{ filteredData.length }}</b> 个科目</span>
        <el-divider direction="vertical" />
        <span>筛选：{{ flattenedData.length }} 行</span>
      </div>
      <div class="footer-right">
        <span class="total-item">
          期初借方合计：<b>¥{{ totals.openingDebit.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</b>
        </span>
        <span class="total-item">
          期初贷方合计：<b>¥{{ totals.openingCredit.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</b>
        </span>
        <span class="total-item">
          本期借方合计：<b>¥{{ totals.periodDebit.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</b>
        </span>
        <span class="total-item">
          本期贷方合计：<b>¥{{ totals.periodCredit.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</b>
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.general-ledger-page {
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

/* ===== 表格区域 ===== */
.table-wrapper {
  background: #fff;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  flex: 1;
  overflow: hidden;
}

/* 展开/折叠箭头 */
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

/* 科目名称层级样式 */
.account-name.level-1 {
  font-weight: 600;
  color: #303133;
}
.account-name.level-2 {
  color: #606266;
}

/* 金额样式 */
.amount {
  font-family: 'SF Mono', 'Menlo', 'Consolas', monospace;
  font-size: 13px;
  color: #606266;
}
.amount.highlight {
  color: #303133;
  font-weight: 500;
}
.amount.ending-balance {
  color: #409eff;
  font-weight: 600;
}

/* ===== 底部合计栏 ===== */
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

.footer-left {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #909399;
}

.footer-right {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.total-item {
  color: #606266;
  white-space: nowrap;
}

.total-item b {
  color: #303133;
  font-family: 'SF Mono', 'Menlo', 'Consolas', monospace;
}

/* ===== Element Plus 表格微调 ===== */
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
