<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

/* ==================== 类型定义 ==================== */

/** 科目树节点 */
interface AccountNode {
  id: string
  code: string
  name: string
  level: number
  parentCode: string
  children: AccountNode[]
  hasChildren: boolean
}

/** 明细账分录行 */
interface DetailEntry {
  id: string
  date: string           // 日期
  voucherWord: string    // 凭证字
  voucherNumber: number  // 凭证号
  summary: string        // 摘要
  debitAmount: number    // 借方金额
  creditAmount: number   // 贷方金额
  direction: '借' | '贷' // 方向
  balance: number        // 余额
}

/* ==================== 状态 ==================== */

/** 会计期间 */
const period = ref('2026-05')

/** 科目搜索关键词 */
const searchKeyword = ref('')

/** 显示明细科目名称 */
const showDetailName = ref(false)

/** 不显示期初为0且无发生额 */
const hideZeroOpening = ref(true)

/** 当前选中的科目 */
const selectedAccount = ref<AccountNode | null>(null)

/** 科目树数据 */
const accountTree = ref<AccountNode[]>([])

/** 右侧表格数据 */
const tableData = ref<DetailEntry[]>([])

/** 加载状态 */
const loading = ref(false)

/* ==================== 科目树（复用总账的） ==================== */

const mockAccountTree: AccountNode[] = [
  { id: 'd1', code: '1001', name: '库存现金', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd2', code: '1002', name: '银行存款', level: 1, parentCode: '', hasChildren: true, children: [
    { id: 'd2-1', code: '1002-01', name: '基本户(工行)', level: 2, parentCode: '1002', hasChildren: false, children: [] },
    { id: 'd2-2', code: '1002-02', name: '一般户(建行)', level: 2, parentCode: '1002', hasChildren: false, children: [] }
  ]},
  { id: 'd3', code: '1012', name: '其他货币资金', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd4', code: '1101', name: '短期投资', level: 1, parentCode: '', hasChildren: true, children: [] },
  { id: 'd5', code: '1121', name: '应收票据', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd6', code: '1122', name: '应收账款', level: 1, parentCode: '', hasChildren: true, children: [
    { id: 'd6-1', code: '1122-01', name: '华宇科技', level: 2, parentCode: '1122', hasChildren: false, children: [] },
    { id: 'd6-2', code: '1122-02', name: '明达集团', level: 2, parentCode: '1122', hasChildren: false, children: [] }
  ]},
  { id: 'd7', code: '1123', name: '预付账款', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd8', code: '1131', name: '应收股利', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd9', code: '1132', name: '应收利息', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd10', code: '1221', name: '其他应收款', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd11', code: '1401', name: '材料采购', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd12', code: '1402', name: '在途物资', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd13', code: '1403', name: '原材料', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd14', code: '1404', name: '材料成本差异', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd15', code: '1405', name: '库存商品', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd16', code: '1407', name: '商品进销差价', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd17', code: '1408', name: '委托加工物资', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd18', code: '1411', name: '周转材料', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd19', code: '1421', name: '消耗性生物资产', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd20', code: '1501', name: '长期债券投资', level: 1, parentCode: '', hasChildren: true, children: [] },
  { id: 'd21', code: '1511', name: '长期股权投资', level: 1, parentCode: '', hasChildren: true, children: [] },
  { id: 'd22', code: '1601', name: '固定资产', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd23', code: '1602', name: '累计折旧', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd24', code: '1604', name: '在建工程', level: 1, parentCode: '', hasChildren: true, children: [] },
  { id: 'd25', code: '1605', name: '工程物资', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd26', code: '1701', name: '无形资产', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd27', code: '1801', name: '长期待摊费用', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd28', code: '1901', name: '待处理财产损溢', level: 1, parentCode: '', hasChildren: false, children: [] },
  // 负债类
  { id: 'd29', code: '2001', name: '短期借款', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd30', code: '2201', name: '应付票据', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd31', code: '2202', name: '应付账款', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd32', code: '2203', name: '预收账款', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd33', code: '2211', name: '应付职工薪酬', level: 1, parentCode: '', hasChildren: true, children: [] },
  { id: 'd34', code: '2221', name: '应交税费', level: 1, parentCode: '', hasChildren: true, children: [] },
  { id: 'd35', code: '2231', name: '应付利息', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd36', code: '2232', name: '应付利润', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd37', code: '2241', name: '其他应付款', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd38', code: '2401', name: '递延收益', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd39', code: '2501', name: '长期借款', level: 1, parentCode: '', hasChildren: false, children: [] },
  // 权益类
  { id: 'd40', code: '3001', name: '实收资本', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd41', code: '3002', name: '资本公积', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd42', code: '3101', name: '盈余公积', level: 1, parentCode: '', hasChildren: true, children: [] },
  { id: 'd43', code: '3103', name: '本年利润', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd44', code: '3104', name: '利润分配', level: 1, parentCode: '', hasChildren: true, children: [] },
  // 成本类
  { id: 'd45', code: '4001', name: '生产成本', level: 1, parentCode: '', hasChildren: true, children: [] },
  { id: 'd46', code: '4101', name: '制造费用', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd47', code: '4301', name: '研发支出', level: 1, parentCode: '', hasChildren: false, children: [] },
  // 损益类 — 收入
  { id: 'd48', code: '5001', name: '主营业务收入', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd49', code: '5051', name: '其他业务收入', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd50', code: '5111', name: '投资收益', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd51', code: '5301', name: '营业外收入', level: 1, parentCode: '', hasChildren: true, children: [] },
  // 损益类 — 成本费用
  { id: 'd52', code: '5401', name: '主营业务成本', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd53', code: '5402', name: '其他业务成本', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd54', code: '5403', name: '营业税金及附加', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'd55', code: '5601', name: '销售费用', level: 1, parentCode: '', hasChildren: true, children: [] },
  { id: 'd56', code: '5602', name: '管理费用', level: 1, parentCode: '', hasChildren: true, children: [] },
  { id: 'd57', code: '5603', name: '财务费用', level: 1, parentCode: '', hasChildren: true, children: [] },
  { id: 'd58', code: '5711', name: '营业外支出', level: 1, parentCode: '', hasChildren: true, children: [] },
  { id: 'd59', code: '5801', name: '所得税费用', level: 1, parentCode: '', hasChildren: false, children: [] }
]

/* ==================== 计算属性 ==================== */

const filteredAccounts = computed(() => {
  let data = accountTree.value
  if (searchKeyword.value.trim()) {
    const kw = searchKeyword.value.trim().toLowerCase()
    data = data.filter(a =>
      a.code.toLowerCase().includes(kw) ||
      a.name.toLowerCase().includes(kw)
    )
  }
  return data
})

const flatAccountList = computed(() => {
  const result: AccountNode[] = []
  const flatten = (nodes: AccountNode[]) => {
    nodes.forEach(n => {
      result.push(n)
      if (n.hasChildren && n.children.length > 0) flatten(n.children)
    })
  }
  flatten(accountTree.value)
  return result
})

const currentIndex = computed(() => {
  if (!selectedAccount.value) return -1
  return flatAccountList.value.findIndex(a => a.id === selectedAccount.value!.id)
})

const hasPrev = computed(() => currentIndex.value > 0)
const hasNext = computed(() => currentIndex.value >= 0 && currentIndex.value < flatAccountList.value.length - 1)

/* ==================== 方法 ==================== */

function loadAccountTree() {
  accountTree.value = mockAccountTree
}

function generateMockData(account: AccountNode): DetailEntry[] {
  const entries: DetailEntry[] = []

  const isDebit = !account.code.startsWith('2') && !account.code.startsWith('3') &&
                  !account.code.startsWith('4') || account.code.startsWith('6') && (
                    account.code === '5401' || account.code === '5402' ||
                    account.code === '5403' || account.code.startsWith('560') ||
                    account.code === '5711' || account.code === '5801'
                  )

  let balance = Math.floor(Math.random() * 500000) + 10000
  if (!isDebit) balance = -balance

  // 期初余额行（如果非零）
  if (Math.abs(balance) > 0) {
    entries.push({
      id: `e0`, date: '', voucherWord: '', voucherNumber: 0,
      summary: '期初余额',
      debitAmount: 0, creditAmount: 0,
      direction: balance >= 0 ? '借' : '贷',
      balance: Math.abs(balance)
    })
  }

  // 本期分录
  const count = Math.floor(Math.random() * 10) + 4
  const words = ['记', '收', '付', '转']
  const summaries = [
    '采购原材料入库', '支付供应商货款', '收到客户货款', '计提本月工资',
    '报销差旅费', '缴纳增值税', '计提固定资产折旧', '销售商品确认收入',
    '支付水电费', '结转销售成本', '收到银行利息', '归还短期借款',
    '购买办公用品', '支付房租', '预收客户定金', '支付广告费',
    '收到投资款', '结转本月损益'
  ]

  for (let i = 0; i < count; i++) {
    const day = Math.floor((i / count) * 28) + 1
    const date = `${period.value}-${String(day).padStart(2, '0')}`
    const word = words[Math.floor(Math.random() * words.length)]
    const vNum = Math.floor(Math.random() * 60) + 1
    const summary = summaries[Math.floor(Math.random() * summaries.length)]
    const isDebitEntry = Math.random() > 0.45
    const amount = Math.floor(Math.random() * 200000) + 500

    if (isDebitEntry) balance += amount
    else balance -= amount

    entries.push({
      id: `e${i + 1}`,
      date,
      voucherWord: word,
      voucherNumber: vNum,
      summary,
      debitAmount: isDebitEntry ? amount : 0,
      creditAmount: isDebitEntry ? 0 : amount,
      direction: balance >= 0 ? '借' : '贷',
      balance: Math.abs(balance)
    })
  }

  return entries
}

function selectAccount(account: AccountNode) {
  selectedAccount.value = account
  loading.value = true
  setTimeout(() => {
    tableData.value = generateMockData(account)
    loading.value = false
  }, 200)
}

function prevAccount() {
  if (hasPrev.value) selectAccount(flatAccountList.value[currentIndex.value - 1])
}

function nextAccount() {
  if (hasNext.value) selectAccount(flatAccountList.value[currentIndex.value + 1])
}

function formatAmount(val: number): string {
  if (val === 0) return ''
  return val.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function refresh() {
  if (selectedAccount.value) selectAccount(selectedAccount.value)
}

onMounted(() => {
  loadAccountTree()
})
</script>

<template>
  <div class="detail-ledger-page">
    <!-- ===== 顶部工具栏 ===== -->
    <div class="top-toolbar">
      <div class="toolbar-left">
        <span class="toolbar-label">期间</span>
        <el-date-picker
          v-model="period"
          type="month"
          format="YYYY年MM期"
          value-format="YYYY-MM"
          size="small"
          style="width: 160px"
          @change="refresh"
        />
        <el-button size="small" type="primary" plain style="margin-left: 8px">
          筛选 ▾
        </el-button>
        <el-button size="small" circle @click="refresh">
          <span style="font-size: 13px">🔄</span>
        </el-button>
      </div>
      <div class="toolbar-right">
        <el-checkbox v-model="showDetailName" size="small">
          显示明细科目名称
        </el-checkbox>
        <el-checkbox v-model="hideZeroOpening" size="small" style="margin-left: 12px">
          期初为0且无发生额不显示
        </el-checkbox>
        <el-button size="small" style="margin-left: 12px">打印</el-button>
        <el-dropdown style="margin-left: 4px">
          <el-button size="small">导出 ▾</el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item>导出Excel</el-dropdown-item>
              <el-dropdown-item>导出PDF</el-dropdown-item>
              <el-dropdown-item>打印预览</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- ===== 主体区域 ===== -->
    <div class="main-content">
      <!-- 左侧科目树面板 -->
      <div class="left-panel">
        <div class="panel-search">
          <el-input v-model="searchKeyword" size="small" placeholder="请输入要搜索的科目" clearable>
            <template #prefix><span style="color:#c0c4cc;font-size:13px">🔍</span></template>
          </el-input>
        </div>
        <div class="panel-tree">
          <div
            v-for="account in filteredAccounts"
            :key="account.id"
            class="account-item"
            :class="{ active: selectedAccount?.id === account.id, 'has-children': account.hasChildren }"
            @click="selectAccount(account)"
          >
            <span class="account-code">{{ account.code }}</span>
            <span class="account-name">{{ account.name }}</span>
            <span v-if="account.hasChildren" class="expand-icon">▶</span>
          </div>
        </div>
      </div>

      <!-- 中间拖拽条 -->
      <div class="resizer"><div class="resizer-handle">◀▶</div></div>

      <!-- 右侧表格 -->
      <div class="right-panel">
        <!-- 科目选择器 -->
        <div class="account-selector">
          <el-button size="small" :disabled="!hasPrev" @click="prevAccount" class="nav-btn">◀</el-button>
          <div class="selector-display">
            <span v-if="selectedAccount" class="selector-text">
              {{ selectedAccount.code }} {{ selectedAccount.name }}
            </span>
            <span v-else class="selector-placeholder">请选择科目</span>
          </div>
          <el-button size="small" :disabled="!hasNext" @click="nextAccount" class="nav-btn">▶</el-button>
        </div>

        <!-- 数据表格 -->
        <div class="table-area">
          <el-table
            v-if="selectedAccount"
            :data="tableData"
            v-loading="loading"
            border stripe size="small"
            :header-cell-style="{ background:'#f5f7fa', color:'#303133', fontWeight:600, fontSize:'13px' }"
            style="width:100%"
            max-height="calc(100vh - 240px)"
          >
            <el-table-column prop="date" label="日期" width="110" align="center" sortable />
            <el-table-column label="凭证号" width="110" align="center">
              <template #default="{ row }">
                <span v-if="row.voucherWord">
                  {{ row.voucherWord }}-{{ String(row.voucherNumber).padStart(3, '0') }}
                </span>
                <span v-else>—</span>
              </template>
            </el-table-column>
            <el-table-column prop="summary" label="摘要" min-width="180" />
            <el-table-column label="借方" width="130" align="right">
              <template #default="{ row }">
                <span class="amount debit">{{ formatAmount(row.debitAmount) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="贷方" width="130" align="right">
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
            <el-table-column label="余额" width="130" align="right">
              <template #default="{ row }">
                <span class="amount balance">{{ formatAmount(row.balance) }}</span>
              </template>
            </el-table-column>
          </el-table>

          <div v-else class="empty-state">
            <el-empty description="暂无数据" :image-size="200">
              <template #image><div style="font-size:80px;opacity:0.3">📊</div></template>
            </el-empty>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.detail-ledger-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f0f2f5;
}

/* ===== 顶部工具栏 ===== */
.top-toolbar {
  background: #fff;
  padding: 8px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e4e7ed;
  flex-shrink: 0;
}
.toolbar-left, .toolbar-right { display: flex; align-items: center; gap: 8px; }
.toolbar-label { font-size: 13px; color: #606266; white-space: nowrap; }

/* ===== 主体 ===== */
.main-content { display: flex; flex: 1; overflow: hidden; }

/* 左侧面板 */
.left-panel {
  width: 220px; background: #fff; border-right: 1px solid #e4e7ed;
  display: flex; flex-direction: column; flex-shrink: 0;
}
.panel-search { padding: 12px; border-bottom: 1px solid #e4e7ed; }
.panel-tree { flex: 1; overflow-y: auto; padding: 4px 0; }

.account-item {
  padding: 8px 12px; cursor: pointer; display: flex; align-items: center; gap: 6px;
  transition: background 0.15s; font-size: 13px;
}
.account-item:hover { background: #f5f7fa; }
.account-item.active { background: #ecf5ff; color: #409eff; }
.account-code { color: #909399; font-size: 12px; min-width: 50px; }
.account-name { flex: 1; color: #303133; }
.account-item.active .account-name { color: #409eff; font-weight: 500; }
.account-item.active .account-code { color: #409eff; }
.expand-icon { font-size: 10px; color: #909399; }

/* 拖拽条 */
.resizer { width: 6px; background: #e4e7ed; cursor: col-resize; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.resizer-handle { font-size: 10px; color: #c0c4cc; writing-mode: vertical-rl; letter-spacing: 2px; }

/* 右侧 */
.right-panel { flex: 1; display: flex; flex-direction: column; overflow: hidden; background: #fff; }

.account-selector {
  display: flex; align-items: center; padding: 10px 16px; border-bottom: 1px solid #e4e7ed; gap: 8px;
}
.nav-btn { padding: 4px 8px; font-size: 12px; }
.selector-display {
  flex: 1; background: #409eff; color: #fff; padding: 6px 16px; border-radius: 4px;
  text-align: center; font-size: 14px; font-weight: 500;
}
.selector-placeholder { opacity: 0.7; }

.table-area { flex: 1; overflow: hidden; }
.empty-state { display: flex; align-items: center; justify-content: center; height: 100%; }

.amount { font-family: 'SF Mono','Menlo','Consolas',monospace; font-size: 13px; color: #606266; }
.amount.debit { color: #303133; font-weight: 500; }
.amount.credit { color: #67c23a; }
.amount.balance { color: #409eff; font-weight: 600; }

:deep(.el-table){ font-size: 13px; }
:deep(.el-table th){ padding: 8px 0; }
:deep(.el-table td){ padding: 6px 0; }
:deep(.el-empty__description){ font-size:14px;color:#909399; }
</style>
