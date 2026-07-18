<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

/* ==================== 类型定义 ==================== */

interface ChronologicalEntry {
  id: string
  date: string
  voucherWord: string
  voucherNumber: number
  summary: string
  accountCode: string
  accountName: string
  debitAmount: number
  creditAmount: number
  direction: '借' | '贷'
  creator: string
  auditor: string
  status: 'draft' | 'audited' | 'posted'
}

/* ==================== 状态 ==================== */

const period = ref('2026-05')
const dateRange = ref<[string, string]>(['2026-05-01', '2026-05-31'])
const dateMode = ref<'period' | 'range'>('period')
const searchKeyword = ref('')
const filterStatus = ref<string | null>(null)
const loading = ref(false)
const tableData = ref<ChronologicalEntry[]>([])

/* ==================== Mock 数据 ==================== */

function generateMockData(): ChronologicalEntry[] {
  const entries: ChronologicalEntry[] = []
  const accounts = [
    { code: '1001', name: '库存现金' },
    { code: '1002', name: '银行存款' },
    { code: '1122', name: '应收账款' },
    { code: '1403', name: '原材料' },
    { code: '2202', name: '应付账款' },
    { code: '2221', name: '应交税费' },
    { code: '6001', name: '主营业务收入' },
    { code: '6401', name: '主营业务成本' },
    { code: '6602', name: '管理费用' },
    { code: '6601', name: '销售费用' }
  ]
  const summaries = [
    '采购原材料入库', '支付供应商货款', '收到客户货款', '计提本月工资',
    '报销差旅费', '缴纳增值税', '计提固定资产折旧', '销售商品确认收入',
    '支付水电费', '结转销售成本', '收到银行利息', '归还短期借款',
    '购买办公用品', '支付房租', '预收客户定金', '支付广告费',
    '收到投资款', '结转本月损益', '计提坏账准备', '支付运输费'
  ]
  const words = ['记', '收', '付', '转']
  const creators = ['张会计', '李会计', '王主管']
  const auditors = ['赵审核', '', '']
  const statuses: Array<'draft' | 'audited' | 'posted'> = ['draft', 'audited', 'posted', 'audited', 'audited']

  for (let i = 0; i < 45; i++) {
    const day = Math.floor(Math.random() * 28) + 1
    const date = `2026-05-${String(day).padStart(2, '0')}`
    const vNum = Math.floor(i / 2) + 1
    const word = words[Math.floor(Math.random() * words.length)]
    const acc = accounts[Math.floor(Math.random() * accounts.length)]
    const summary = summaries[Math.floor(Math.random() * summaries.length)]
    const isDebit = Math.random() > 0.45
    const amount = Math.floor(Math.random() * 800000) + 2000
    const status = statuses[Math.floor(Math.random() * statuses.length)]
    const creator = creators[Math.floor(Math.random() * creators.length)]
    const auditor = status === 'draft' ? '' : auditors[0]

    entries.push({
      id: `ce-${i}`,
      date,
      voucherWord: word,
      voucherNumber: vNum,
      summary,
      accountCode: acc.code,
      accountName: acc.name,
      debitAmount: isDebit ? amount : 0,
      creditAmount: isDebit ? 0 : amount,
      direction: isDebit ? '借' : '贷',
      creator,
      auditor,
      status
    })
  }

  // 按日期排序
  entries.sort((a, b) => {
    if (a.date !== b.date) return a.date.localeCompare(b.date)
    return a.voucherNumber - b.voucherNumber
  })

  return entries
}

/* ==================== 计算属性 ==================== */

const filteredData = computed(() => {
  let data = tableData.value

  if (searchKeyword.value.trim()) {
    const kw = searchKeyword.value.trim().toLowerCase()
    data = data.filter(e =>
      e.summary.toLowerCase().includes(kw) ||
      e.accountName.toLowerCase().includes(kw) ||
      e.accountCode.includes(kw)
    )
  }

  if (filterStatus.value) {
    data = data.filter(e => e.status === filterStatus.value)
  }

  return data
})

const totals = computed(() => {
  let debit = 0, credit = 0
  filteredData.value.forEach(e => {
    debit += e.debitAmount
    credit += e.creditAmount
  })
  return { debit, credit }
})

/* ==================== 方法 ==================== */

function loadData() {
  loading.value = true
  setTimeout(() => {
    tableData.value = generateMockData()
    loading.value = false
  }, 300)
}

function viewVoucher(row: ChronologicalEntry) {
  router.push({
    path: '/general-ledger/voucher-list',
    query: { date: row.date }
  })
}

function viewDetail(row: ChronologicalEntry) {
  router.push({
    path: '/general-ledger/detail',
    query: {
      accountCode: row.accountCode,
      accountName: row.accountName,
      period: period.value
    }
  })
}

function formatAmount(val: number): string {
  if (val === 0) return ''
  return val.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function getStatusType(status: string) {
  const map: Record<string, string> = { draft: 'info', audited: 'success', posted: '' }
  return map[status] || 'info'
}

function getStatusText(status: string) {
  const map: Record<string, string> = { draft: '草稿', audited: '已审', posted: '已记账' }
  return map[status] || status
}

onMounted(() => loadData())
</script>

<template>
  <div class="chronological-page">
    <!-- ===== 顶部工具栏 ===== -->
    <div class="toolbar">
      <div class="toolbar-left">
        <span class="toolbar-label">日期：</span>
        <el-radio-group v-model="dateMode" size="small">
          <el-radio-button value="period">会计期间</el-radio-button>
          <el-radio-button value="range">日期范围</el-radio-button>
        </el-radio-group>

        <template v-if="dateMode === 'period'">
          <el-date-picker
            v-model="period"
            type="month"
            format="YYYY-MM"
            value-format="YYYY-MM"
            size="small"
            style="width:130px;margin-left:8px"
            @change="loadData"
          />
        </template>
        <template v-else>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始"
            end-placeholder="结束"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            size="small"
            style="width:240px;margin-left:8px"
            @change="loadData"
          />
        </template>

        <el-divider direction="vertical" />

        <el-select v-model="filterStatus" size="small" clearable placeholder="全部状态" style="width:110px">
          <el-option label="草稿" value="draft" />
          <el-option label="已审核" value="audited" />
          <el-option label="已记账" value="posted" />
        </el-select>
      </div>

      <div class="toolbar-right">
        <el-input
          v-model="searchKeyword"
          size="small"
          placeholder="搜索摘要/科目…"
          clearable
          style="width:200px"
        >
          <template #prefix>
            <span style="color:#909399;font-size:13px;">🔍</span>
          </template>
        </el-input>
        <el-button size="small" @click="loadData" style="margin-left:4px">🔄 刷新</el-button>
        <el-button size="small">📥 导出</el-button>
      </div>
    </div>

    <!-- ===== 数据表格 ===== -->
    <div class="table-wrapper">
      <el-table
        :data="filteredData"
        v-loading="loading"
        border
        stripe
        size="small"
        :header-cell-style="{ background: '#f5f7fa', color: '#303133', fontWeight: 600, fontSize: '13px' }"
        style="width:100%"
        max-height="calc(100vh - 220px)"
        show-summary
        :summary-method="() => []"
      >
        <el-table-column prop="date" label="日期" width="110" align="center" fixed="left" sortable />
        <el-table-column label="凭证字号" width="120" align="center" fixed="left">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="viewVoucher(row)">
              {{ row.voucherWord }}-{{ String(row.voucherNumber).padStart(3, '0') }}
            </el-button>
          </template>
        </el-table-column>
        <el-table-column prop="summary" label="摘要" min-width="180" show-overflow-tooltip />
        <el-table-column label="科目" width="180" align="center">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="viewDetail(row)">
              {{ row.accountCode }} {{ row.accountName }}
            </el-button>
          </template>
        </el-table-column>
        <el-table-column label="借方金额" width="140" align="right" sortable>
          <template #default="{ row }">
            <span class="amount debit">{{ formatAmount(row.debitAmount) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="贷方金额" width="140" align="right" sortable>
          <template #default="{ row }">
            <span class="amount credit">{{ formatAmount(row.creditAmount) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="方向" width="60" align="center">
          <template #default="{ row }">
            <el-tag :type="row.direction === '借' ? '' : 'success'" size="small" effect="plain">
              {{ row.direction }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="creator" label="制单人" width="90" align="center" />
        <el-table-column prop="auditor" label="审核人" width="90" align="center">
          <template #default="{ row }">
            <span :style="{ color: row.auditor ? '#303133' : '#c0c4cc' }">
              {{ row.auditor || '—' }}
            </span>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- ===== 底部统计 ===== -->
    <div class="footer-bar">
      <div class="footer-left">
        <span>共 <b>{{ filteredData.length }}</b> 条分录</span>
        <el-divider direction="vertical" />
        <span>日期范围：{{ dateMode === 'period' ? period : dateRange.join(' ~ ') }}</span>
      </div>
      <div class="footer-right">
        <span class="total-item">借方合计：<b>¥{{ totals.debit.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</b></span>
        <span class="total-item">贷方合计：<b>¥{{ totals.credit.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</b></span>
        <span class="total-item" :class="{ balanced: totals.debit === totals.credit }">
          {{ totals.debit === totals.credit ? '✓ 借贷平衡' : '✗ 借贷不平' }}
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chronological-page {
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

.amount {
  font-family: 'SF Mono', 'Menlo', 'Consolas', monospace;
  font-size: 13px;
}

.amount.debit {
  color: #303133;
  font-weight: 500;
}

.amount.credit {
  color: #67c23a;
}

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

.footer-left {
  color: #909399;
}

.footer-right {
  display: flex;
  gap: 20px;
}

.total-item {
  color: #606266;
}

.total-item b {
  font-family: 'SF Mono', 'Menlo', 'Consolas', monospace;
  color: #303133;
}

.total-item.balanced {
  color: #67c23a;
  font-weight: 600;
}

:deep(.el-table) { font-size: 13px; }
:deep(.el-table th) { padding: 8px 0; }
:deep(.el-table td) { padding: 6px 0; }
</style>
