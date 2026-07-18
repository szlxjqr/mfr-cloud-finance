<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

/* ==================== 类型定义 ==================== */

/** 明细账分录行 */
interface DetailLine {
  id: string
  date: string           // 日期
  voucherWord: string    // 凭证字
  voucherNumber: number  // 凭证号
  summary: string        // 摘要
  counterpartyAccount: string // 对方科目
  debitAmount: number    // 借方金额
  creditAmount: number   // 贷方金额
  direction: '借' | '贷' // 方向
  balance: number        // 余额
}

/** 明细账页面对应的科目 */
interface AccountInfo {
  code: string
  name: string
}

/* ==================== 状态 ==================== */

/** 会计期间 */
const period = ref(route.query.period as string || '2026-05')

/** 当前科目（可从路由参数获取，也可手动切换） */
const currentAccount = ref<AccountInfo>({
  code: (route.query.accountCode as string) || '1002',
  name: (route.query.accountName as string) || '银行存款'
})

/** 科目搜索关键词 */
const accountSearchKeyword = ref('')

/** 科目选择器可见 */
const accountPickerVisible = ref(false)

/** 是否包含未记账凭证 */
const includeUnposted = ref(true)

/** 表格数据 */
const tableData = ref<DetailLine[]>([])

/** 加载状态 */
const loading = ref(false)

/* ==================== 科目列表 ==================== */

const accountList = ref<AccountInfo[]>([
  { code: '1001', name: '库存现金' },
  { code: '1002', name: '银行存款' },
  { code: '1002-01', name: '银行存款-基本户(工行)' },
  { code: '1002-02', name: '银行存款-一般户(建行)' },
  { code: '1122', name: '应收账款' },
  { code: '1122-01', name: '应收账款-华宇科技' },
  { code: '1122-02', name: '应收账款-明达集团' },
  { code: '1403', name: '原材料' },
  { code: '1405', name: '库存商品' },
  { code: '1601', name: '固定资产' },
  { code: '1602', name: '累计折旧' },
  { code: '2001', name: '短期借款' },
  { code: '2202', name: '应付账款' },
  { code: '2221', name: '应交税费' },
  { code: '4001', name: '实收资本' },
  { code: '6001', name: '主营业务收入' },
  { code: '6401', name: '主营业务成本' },
  { code: '6601', name: '销售费用' },
  { code: '6602', name: '管理费用' }
])

/** 筛选后的科目列表 */
const filteredAccounts = computed(() => {
  if (!accountSearchKeyword.value.trim()) return accountList.value
  const kw = accountSearchKeyword.value.trim().toLowerCase()
  return accountList.value.filter(a =>
    a.code.toLowerCase().includes(kw) ||
    a.name.toLowerCase().includes(kw)
  )
})

/* ==================== Mock 数据生成 ==================== */

function generateMockData(code: string, name: string): DetailLine[] {
  // 根据科目不同生成不同特征的数据
  const isAsset = code.startsWith('1')
  const isLiability = code.startsWith('2')
  const isEquity = code.startsWith('4')
  const isRevenue = code.startsWith('6') && name.includes('收入')
  const isExpense = code.startsWith('6') && !name.includes('收入')

  const lines: DetailLine[] = []
  const startDay = 1
  const endDay = 28
  const count = 8 + Math.floor(Math.random() * 12)

  let balance = 0

  // 期初余额
  if (isAsset || isExpense) {
    balance = Math.floor(Math.random() * 2000000) + 50000
  } else if (isLiability || isEquity || isRevenue) {
    balance = -(Math.floor(Math.random() * 2000000) + 50000)
  }

  for (let i = 0; i < count; i++) {
    const day = startDay + Math.floor((i / count) * endDay)
    const date = `2026-05-${String(day).padStart(2, '0')}`
    const vNum = Math.floor(Math.random() * 80) + 1
    const words = ['记', '收', '付', '转']
    const word = words[Math.floor(Math.random() * words.length)]

    const summaries = [
      '采购原材料', '支付货款', '收到销售款', '支付工资',
      '报销差旅费', '缴纳税费', '计提折旧', '收到投资款',
      '支付水电费', '销售商品', '购买办公用品', '银行利息收入',
      '支付租金', '收到应收账款', '归还借款', '结转成本'
    ]
    const summary = summaries[Math.floor(Math.random() * summaries.length)]

    const counterparties = [
      '银行存款', '库存现金', '应付账款', '应收账款',
      '管理费用', '主营业务收入', '应交税费', '固定资产'
    ]
    const counterparty = counterparties[Math.floor(Math.random() * counterparties.length)]

    const isDebit = Math.random() > 0.4
    const amount = Math.floor(Math.random() * 500000) + 5000

    const debit = isDebit ? amount : 0
    const credit = isDebit ? 0 : amount

    balance = balance + debit - credit

    lines.push({
      id: `dl-${i}`,
      date,
      voucherWord: word,
      voucherNumber: vNum,
      summary,
      counterpartyAccount: counterparty,
      debitAmount: debit,
      creditAmount: credit,
      direction: balance >= 0 ? '借' : '贷',
      balance: Math.abs(balance)
    })
  }

  return lines
}

/* ==================== 计算属性 ==================== */

/** 本期合计 */
const periodTotals = computed(() => {
  let debit = 0, credit = 0
  tableData.value.forEach(l => {
    debit += l.debitAmount
    credit += l.creditAmount
  })
  return { debit, credit }
})

/* ==================== 方法 ==================== */

function loadData() {
  loading.value = true
  setTimeout(() => {
    tableData.value = generateMockData(currentAccount.value.code, currentAccount.value.name)
    loading.value = false
  }, 300)
}

/** 选择科目 */
function selectAccount(acc: AccountInfo) {
  currentAccount.value = { ...acc }
  accountPickerVisible.value = false
  accountSearchKeyword.value = ''
  loadData()
}

/** 联查凭证 */
function viewVoucher(row: DetailLine) {
  router.push({
    path: '/general-ledger/voucher-list',
    query: { date: row.date, keyword: row.voucherNumber.toString() }
  })
}

/** 格式化金额 */
function formatAmount(val: number): string {
  if (val === 0) return ''
  return val.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

/** 切换期间 */
function prevPeriod() {
  const [y, m] = period.value.split('-').map(Number)
  if (m === 1) {
    period.value = `${y - 1}-12`
  } else {
    period.value = `${y}-${String(m - 1).padStart(2, '0')}`
  }
  loadData()
}

function nextPeriod() {
  const [y, m] = period.value.split('-').map(Number)
  if (m === 12) {
    period.value = `${y + 1}-01`
  } else {
    period.value = `${y}-${String(m + 1).padStart(2, '0')}`
  }
  loadData()
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="detail-ledger-page">
    <!-- ===== 顶部工具栏 ===== -->
    <div class="toolbar">
      <div class="toolbar-left">
        <!-- 科目选择 -->
        <span class="toolbar-label">科目：</span>
        <el-popover
          v-model:visible="accountPickerVisible"
          placement="bottom-start"
          :width="320"
          trigger="click"
        >
          <template #reference>
            <el-button size="small" style="min-width:200px;text-align:left;">
              <b>{{ currentAccount.code }}</b>&nbsp;{{ currentAccount.name }}
              <span style="float:right;color:#909399;">▾</span>
            </el-button>
          </template>
          <div class="account-picker">
            <el-input
              v-model="accountSearchKeyword"
              size="small"
              placeholder="搜索科目…"
              clearable
              style="margin-bottom:8px"
            />
            <div class="account-list">
              <div
                v-for="acc in filteredAccounts"
                :key="acc.code"
                class="account-item"
                :class="{ active: acc.code === currentAccount.code }"
                @click="selectAccount(acc)"
              >
                <span class="acc-code">{{ acc.code }}</span>
                <span class="acc-name">{{ acc.name }}</span>
              </div>
            </div>
          </div>
        </el-popover>

        <el-divider direction="vertical" />

        <!-- 期间切换 -->
        <el-button size="small" @click="prevPeriod">◀</el-button>
        <el-date-picker
          v-model="period"
          type="month"
          format="YYYY-MM"
          value-format="YYYY-MM"
          size="small"
          style="width:130px"
          @change="loadData"
        />
        <el-button size="small" @click="nextPeriod">▶</el-button>

        <el-divider direction="vertical" />

        <el-checkbox v-model="includeUnposted" size="small" @change="loadData">
          含未记账
        </el-checkbox>
      </div>

      <div class="toolbar-right">
        <el-button size="small" @click="loadData">🔄 刷新</el-button>
        <el-button size="small">📥 导出</el-button>
        <el-button size="small">🖨 打印</el-button>
      </div>
    </div>

    <!-- ===== 科目信息头 ===== -->
    <div class="account-header">
      <div class="header-left">
        <span class="header-title">
          明细账 — {{ currentAccount.name }}
          <el-tag size="small" style="margin-left:8px">{{ currentAccount.code }}</el-tag>
        </span>
      </div>
      <div class="header-right">
        <span class="header-period">会计期间：{{ period }}</span>
      </div>
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
        max-height="calc(100vh - 280px)"
        show-summary
        :summary-method="() => []"
      >
        <el-table-column prop="date" label="日期" width="110" align="center" fixed="left" />
        <el-table-column label="凭证字号" width="120" align="center" fixed="left">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="viewVoucher(row)">
              {{ row.voucherWord }}-{{ String(row.voucherNumber).padStart(3, '0') }}
            </el-button>
          </template>
        </el-table-column>
        <el-table-column prop="summary" label="摘要" min-width="180" />
        <el-table-column prop="counterpartyAccount" label="对方科目" width="130" align="center" />
        <el-table-column label="借方金额" width="140" align="right">
          <template #default="{ row }">
            <span class="amount debit">{{ formatAmount(row.debitAmount) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="贷方金额" width="140" align="right">
          <template #default="{ row }">
            <span class="amount credit">{{ formatAmount(row.creditAmount) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="方向" width="60" align="center">
          <template #default="{ row }">
            <el-tag
              :type="row.direction === '借' ? '' : 'success'"
              size="small"
              effect="plain"
            >
              {{ row.direction }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="余额" width="140" align="right">
          <template #default="{ row }">
            <span class="amount balance">{{ formatAmount(row.balance) }}</span>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- ===== 底部统计 ===== -->
    <div class="footer-bar">
      <div class="footer-left">
        <span>共 <b>{{ tableData.length }}</b> 笔分录</span>
      </div>
      <div class="footer-right">
        <div class="total-group">
          <div class="total-label">本期合计</div>
          <div class="total-values">
            <span class="total-item">
              借方：<b>¥{{ periodTotals.debit.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</b>
            </span>
            <span class="total-item">
              贷方：<b>¥{{ periodTotals.credit.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</b>
            </span>
          </div>
        </div>
        <div class="total-group" v-if="tableData.length > 0">
          <div class="total-label">期末余额</div>
          <div class="total-values">
            <span class="total-item">
              {{ tableData[tableData.length - 1].direction }}：
              <b>¥{{ tableData[tableData.length - 1].balance.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</b>
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.detail-ledger-page {
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

/* ===== 科目信息头 ===== */
.account-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 16px 20px;
  border-radius: 6px;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #fff;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.header-title {
  font-size: 16px;
  font-weight: 600;
}

.header-period {
  font-size: 13px;
  opacity: 0.85;
}

/* ===== 科目选择器 ===== */
.account-picker {
  max-height: 320px;
  display: flex;
  flex-direction: column;
}

.account-list {
  overflow-y: auto;
  max-height: 260px;
}

.account-item {
  padding: 8px 12px;
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background 0.15s;
}

.account-item:hover {
  background: #f0f2f5;
}

.account-item.active {
  background: #ecf5ff;
  color: #409eff;
}

.acc-code {
  font-size: 12px;
  color: #909399;
  min-width: 70px;
}

.acc-name {
  font-size: 13px;
}

/* ===== 表格 ===== */
.table-wrapper {
  background: #fff;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  flex: 1;
  overflow: hidden;
}

.amount {
  font-family: 'SF Mono', 'Menlo', 'Consolas', monospace;
  font-size: 13px;
  color: #606266;
}

.amount.debit {
  color: #303133;
}

.amount.credit {
  color: #67c23a;
}

.amount.balance {
  color: #409eff;
  font-weight: 600;
}

/* ===== 底部统计 ===== */
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

.footer-right {
  display: flex;
  gap: 24px;
}

.total-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.total-label {
  font-size: 12px;
  color: #909399;
}

.total-values {
  display: flex;
  gap: 16px;
}

.total-item {
  color: #606266;
  white-space: nowrap;
}

.total-item b {
  color: #303133;
  font-family: 'SF Mono', 'Menlo', 'Consolas', monospace;
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
</style>
