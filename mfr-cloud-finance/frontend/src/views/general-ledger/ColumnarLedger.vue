<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

/* ==================== 类型定义 ==================== */

/** 多栏账栏目（按科目分列） */
interface ColumnDef {
  code: string
  name: string
  key: string
}

/** 多栏账行 */
interface ColumnarRow {
  id: string
  date: string
  voucherWord: string
  voucherNumber: number
  summary: string
  totalDebit: number
  totalCredit: number
  balance: number
  direction: '借' | '贷'
  columns: Record<string, number>  // key → amount
}

/* ==================== 状态 ==================== */

const period = ref('2026-05')
const parentAccount = ref('6602')  // 默认管理费用
const loading = ref(false)
const tableData = ref<ColumnarRow[]>([])
const columnDefs = ref<ColumnDef[]>([])

/* ==================== 科目模板配置 ==================== */

const templates: Record<string, { name: string; columns: ColumnDef[] }> = {
  '6602': {
    name: '管理费用',
    columns: [
      { code: '6602-01', name: '工资', key: 'c1' },
      { code: '6602-02', name: '办公费', key: 'c2' },
      { code: '6602-03', name: '差旅费', key: 'c3' },
      { code: '6602-04', name: '折旧费', key: 'c4' },
      { code: '6602-05', name: '水电费', key: 'c5' },
      { code: '6602-06', name: '业务招待费', key: 'c6' },
      { code: '6602-07', name: '其他', key: 'c7' }
    ]
  },
  '6601': {
    name: '销售费用',
    columns: [
      { code: '6601-01', name: '广告费', key: 'c1' },
      { code: '6601-02', name: '运输费', key: 'c2' },
      { code: '6601-03', name: '包装费', key: 'c3' },
      { code: '6601-04', name: '销售人员工资', key: 'c4' },
      { code: '6601-05', name: '其他', key: 'c5' }
    ]
  },
  '5001': {
    name: '生产成本',
    columns: [
      { code: '5001-01', name: '直接材料', key: 'c1' },
      { code: '5001-02', name: '直接人工', key: 'c2' },
      { code: '5001-03', name: '制造费用', key: 'c3' },
      { code: '5001-04', name: '其他', key: 'c4' }
    ]
  }
}

const templateList = [
  { code: '6602', name: '管理费用' },
  { code: '6601', name: '销售费用' },
  { code: '5001', name: '生产成本' }
]

/* ==================== Mock 数据 ==================== */

function generateMockData(): ColumnarRow[] {
  const template = templates[parentAccount.value]
  if (!template) return []
  columnDefs.value = template.columns

  const rows: ColumnarRow[] = []
  const summaries = [
    '计提本月工资', '购买办公用品', '报销差旅费', '计提折旧',
    '支付水电费', '招待客户餐费', '支付快递费', '支付房租物业',
    '计提社保公积金', '报销通讯费'
  ]

  for (let i = 0; i < 15; i++) {
    const day = Math.floor(Math.random() * 27) + 1
    const date = `2026-05-${String(day).padStart(2, '0')}`
    const words = ['记', '付']
    const word = words[Math.floor(Math.random() * words.length)]
    const vNum = Math.floor(Math.random() * 40) + 1

    // 随机分配到几个栏目
    const columns: Record<string, number> = {}
    let totalDebit = 0
    const activeCols = Math.floor(Math.random() * 3) + 1
    const shuffled = [...template.columns].sort(() => Math.random() - 0.5)
    for (let c = 0; c < activeCols && c < shuffled.length; c++) {
      const amount = Math.floor(Math.random() * 50000) + 500
      columns[shuffled[c].key] = amount
      totalDebit += amount
    }

    rows.push({
      id: `cr-${i}`,
      date,
      voucherWord: word,
      voucherNumber: vNum,
      summary: summaries[Math.floor(Math.random() * summaries.length)],
      totalDebit,
      totalCredit: 0,
      balance: totalDebit,
      direction: '借',
      columns
    })
  }

  rows.sort((a, b) => a.date.localeCompare(b.date) || a.voucherNumber - b.voucherNumber)
  return rows
}

/* ==================== 计算属性 ==================== */

const columnTotals = computed(() => {
  const totals: Record<string, number> = {}
  columnDefs.value.forEach(col => { totals[col.key] = 0 })
  tableData.value.forEach(row => {
    Object.entries(row.columns).forEach(([key, val]) => {
      totals[key] = (totals[key] || 0) + val
    })
  })
  return totals
})

const grandTotal = computed(() => {
  let t = 0
  Object.values(columnTotals.value).forEach(v => { t += v })
  return t
})

/* ==================== 方法 ==================== */

function loadData() {
  loading.value = true
  setTimeout(() => {
    tableData.value = generateMockData()
    loading.value = false
  }, 300)
}

function switchTemplate(code: string) {
  parentAccount.value = code
  loadData()
}

function viewVoucher(row: ColumnarRow) {
  router.push({
    path: '/general-ledger/voucher-list',
    query: { date: row.date }
  })
}

function formatAmount(val: number): string {
  if (val === 0) return ''
  return val.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

onMounted(() => loadData())
</script>

<template>
  <div class="columnar-page">
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

        <span class="toolbar-label">多栏科目：</span>
        <el-select
          :model-value="parentAccount"
          size="small"
          style="width:160px"
          @change="switchTemplate"
        >
          <el-option
            v-for="tpl in templateList"
            :key="tpl.code"
            :label="`${tpl.code} ${tpl.name}`"
            :value="tpl.code"
          />
        </el-select>
      </div>

      <div class="toolbar-right">
        <el-button size="small" @click="loadData">🔄 刷新</el-button>
        <el-button size="small">📥 导出</el-button>
        <el-button size="small">🖨 打印</el-button>
      </div>
    </div>

    <!-- ===== 标题栏 ===== -->
    <div class="title-bar">
      <span class="title-text">
        {{ templates[parentAccount]?.name || '' }} — 多栏明细账
      </span>
      <span class="title-period">{{ period }}</span>
    </div>

    <!-- ===== 数据表格 ===== -->
    <div class="table-wrapper">
      <el-table
        :data="tableData"
        v-loading="loading"
        border
        stripe
        size="small"
        :header-cell-style="{ background: '#f5f7fa', color: '#303133', fontWeight: 600, fontSize: '13px' }"
        style="width:100%"
        max-height="calc(100vh - 260px)"
      >
        <el-table-column prop="date" label="日期" width="110" align="center" fixed="left" />
        <el-table-column label="凭证字号" width="120" align="center" fixed="left">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="viewVoucher(row)">
              {{ row.voucherWord }}-{{ String(row.voucherNumber).padStart(3, '0') }}
            </el-button>
          </template>
        </el-table-column>
        <el-table-column prop="summary" label="摘要" min-width="150" fixed="left" show-overflow-tooltip />

        <!-- 动态分栏 -->
        <el-table-column
          v-for="col in columnDefs"
          :key="col.key"
          :label="col.name"
          :width="130"
          align="right"
        >
          <template #default="{ row }">
            <span class="amount">{{ formatAmount(row.columns[col.key] || 0) }}</span>
          </template>
        </el-table-column>

        <!-- 合计列 -->
        <el-table-column label="借方合计" width="130" align="right">
          <template #default="{ row }">
            <span class="amount total-col">{{ formatAmount(row.totalDebit) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="贷方合计" width="130" align="right">
          <template #default="{ row }">
            <span class="amount total-col">{{ formatAmount(row.totalCredit) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="方向" width="60" align="center">
          <template #default="{ row }">
            <el-tag :type="row.direction === '借' ? '' : 'success'" size="small" effect="plain">
              {{ row.direction }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="余额" width="130" align="right">
          <template #default="{ row }">
            <span class="amount balance">{{ formatAmount(row.balance) }}</span>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- ===== 底部栏目合计 ===== -->
    <div class="footer-bar">
      <div class="footer-left">
        <span>共 <b>{{ tableData.length }}</b> 笔记录</span>
      </div>
      <div class="footer-right">
        <div class="column-total-row">
          <span class="col-total-label">栏目合计：</span>
          <span
            v-for="col in columnDefs"
            :key="col.key"
            class="col-total-item"
          >
            {{ col.name }} <b>¥{{ (columnTotals[col.key] || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</b>
          </span>
          <el-divider direction="vertical" />
          <span class="col-total-grand">
            总计：<b>¥{{ grandTotal.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</b>
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.columnar-page {
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

/* ===== 标题栏 ===== */
.title-bar {
  background: linear-gradient(135deg, #409eff 0%, #337ecc 100%);
  padding: 12px 20px;
  border-radius: 6px;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #fff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}

.title-text {
  font-size: 16px;
  font-weight: 600;
}

.title-period {
  font-size: 13px;
  opacity: 0.85;
}

/* ===== 表格 ===== */
.table-wrapper {
  background: #fff;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  flex: 1;
  overflow-x: auto;
  overflow-y: hidden;
}

.amount {
  font-family: 'SF Mono', 'Menlo', 'Consolas', monospace;
  font-size: 13px;
  color: #606266;
}

.amount.total-col {
  font-weight: 600;
  color: #303133;
}

.amount.balance {
  color: #409eff;
  font-weight: 600;
}

/* ===== 底部栏目合计 ===== */
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
  color: #909399;
}

.column-total-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.col-total-label {
  color: #909399;
  font-size: 12px;
}

.col-total-item {
  color: #606266;
  font-size: 12px;
  white-space: nowrap;
}

.col-total-item b {
  color: #303133;
  font-family: 'SF Mono', 'Menlo', 'Consolas', monospace;
}

.col-total-grand {
  color: #303133;
  font-weight: 600;
}

.col-total-grand b {
  color: #409eff;
  font-family: 'SF Mono', 'Menlo', 'Consolas', monospace;
}

:deep(.el-table) { font-size: 13px; }
:deep(.el-table th) { padding: 8px 0; }
:deep(.el-table td) { padding: 6px 0; }
</style>
