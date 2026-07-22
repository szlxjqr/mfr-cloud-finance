<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { listSubjects, getGeneralLedger } from '@/api/ledger'
import type { AccountSubject, GeneralLedgerOut } from '@/types/ledger'

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

/** 总账分录行 */
interface GeneralLedgerEntry {
  id: string
  period: string
  summary: string
  openingDebit: number
  openingCredit: number
  periodDebit: number
  periodCredit: number
  endingDebit: number
  endingCredit: number
  direction: string
  balance: number
}

/* ==================== 状态 ==================== */

/** 会计期间 */
const period = ref('2026-05')

/** 科目搜索关键词 */
const searchKeyword = ref('')

/** 只显示一级科目 */
const showLevel1Only = ref(false)

/** 不显示无发生额且余额为0 */
const hideZeroBalance = ref(true)

/** 当前选中的科目 */
const selectedAccount = ref<AccountNode | null>(null)

/** 科目树数据 */
const accountTree = ref<AccountNode[]>([])

/** 右侧表格数据 */
const tableData = ref<GeneralLedgerEntry[]>([])

/** 加载状态 */
const loading = ref(false)

/* ==================== 科目树数据 ==================== */


/* ==================== 计算属性 ==================== */

/** 筛选后的科目列表 */
const filteredAccounts = computed(() => {
  let data = accountTree.value

  // 只显示一级科目
  if (showLevel1Only.value) {
    data = data.filter(a => a.level === 1)
  }

  // 关键词搜索
  if (searchKeyword.value.trim()) {
    const kw = searchKeyword.value.trim().toLowerCase()
    data = data.filter(a =>
      a.code.toLowerCase().includes(kw) ||
      a.name.toLowerCase().includes(kw)
    )
  }

  return data
})

/** 扁平化的科目列表（用于上一个/下一个导航） */
const flatAccountList = computed(() => {
  const result: AccountNode[] = []
  const flatten = (nodes: AccountNode[]) => {
    nodes.forEach(n => {
      if (!showLevel1Only.value || n.level === 1) {
        result.push(n)
      }
      if (n.hasChildren && n.children.length > 0) {
        flatten(n.children)
      }
    })
  }
  flatten(accountTree.value)
  return result
})

/** 当前选中科目的索引 */
const currentIndex = computed(() => {
  if (!selectedAccount.value) return -1
  return flatAccountList.value.findIndex(a => a.id === selectedAccount.value!.id)
})

/** 是否有上一个科目 */
const hasPrev = computed(() => currentIndex.value > 0)

/** 是否有下一个科目 */
const hasNext = computed(() => currentIndex.value >= 0 && currentIndex.value < flatAccountList.value.length - 1)

/** 表格展示数据（可隐藏「无发生额且余额为0」的期间行） */
const displayData = computed(() => {
  if (!hideZeroBalance.value) return tableData.value
  return tableData.value.filter(r =>
    !(r.periodDebit === 0 && r.periodCredit === 0 && r.endingDebit === 0 && r.endingCredit === 0)
  )
})

/* ==================== 方法 ==================== */

/** 由后端科目列表实时构建科目树 */
function buildAccountTree(subs: AccountSubject[]): AccountNode[] {
  const map = new Map<string, AccountNode>()
  subs.forEach(s => {
    map.set(s.code, {
      id: s.code,
      code: s.code,
      name: s.name,
      level: s.level,
      parentCode: s.parent_code || '',
      children: [],
      hasChildren: false,
    })
  })
  const roots: AccountNode[] = []
  map.forEach(n => {
    const parent = n.parentCode ? map.get(n.parentCode) : undefined
    if (parent) {
      parent.children.push(n)
      parent.hasChildren = true
    } else {
      roots.push(n)
    }
  })
  return roots
}

/** 加载科目树（真实数据） */
async function loadAccountTree() {
  const res = await listSubjects()
  accountTree.value = buildAccountTree(res.data)
}

/** 加载选中科目的总账（真实数据，按期间汇总） */
async function loadLedger(account: AccountNode) {
  loading.value = true
  try {
    const res = await getGeneralLedger(account.code, period.value || undefined)
    const out: GeneralLedgerOut = res.data
    tableData.value = out.rows.map(r => ({
      id: `p-${r.period}`,
      period: r.period,
      summary: '',
      openingDebit: r.opening_debit,
      openingCredit: r.opening_credit,
      periodDebit: r.period_debit,
      periodCredit: r.period_credit,
      endingDebit: r.ending_debit,
      endingCredit: r.ending_credit,
      direction: r.direction,
      balance: r.balance,
    }))
  } finally {
    loading.value = false
  }
}

/** 选择科目 */
function selectAccount(account: AccountNode) {
  selectedAccount.value = account
  loadLedger(account)
}

/** 上一个科目 */
function prevAccount() {
  if (hasPrev.value) {
    selectAccount(flatAccountList.value[currentIndex.value - 1])
  }
}

/** 下一个科目 */
function nextAccount() {
  if (hasNext.value) {
    selectAccount(flatAccountList.value[currentIndex.value + 1])
  }
}

/** 格式化金额 */
function formatAmount(val: number): string {
  if (val === 0) return ''
  return val.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

/** 刷新 */
function refresh() {
  if (selectedAccount.value) {
    selectAccount(selectedAccount.value)
  }
}

/** 打印 */
function printLedger() {
  window.print()
}

/** 导出 */
function exportLedger() {
  // 占位
}

onMounted(() => {
  loadAccountTree()
})
</script>

<template>
  <div class="general-ledger-page">
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
        <el-checkbox v-model="showLevel1Only" size="small">
          只显示一级科目
        </el-checkbox>
        <el-checkbox v-model="hideZeroBalance" size="small" style="margin-left: 12px">
          无发生额且余额为0不显示
        </el-checkbox>
        <el-button size="small" style="margin-left: 12px" @click="printLedger">
          打印
        </el-button>
        <el-button size="small" @click="exportLedger">
          导出
        </el-button>
      </div>
    </div>

    <!-- ===== 主体区域：左侧科目树 + 右侧表格 ===== -->
    <div class="main-content">
      <!-- 左侧科目树面板 -->
      <div class="left-panel">
        <div class="panel-search">
          <el-input
            v-model="searchKeyword"
            size="small"
            placeholder="请输入要搜索的科目"
            clearable
          >
            <template #prefix>
              <span style="color: #c0c4cc; font-size: 13px">🔍</span>
            </template>
          </el-input>
        </div>
        <div class="panel-tree">
          <div
            v-for="account in filteredAccounts"
            :key="account.id"
            class="account-item"
            :class="{
              active: selectedAccount?.id === account.id,
              'has-children': account.hasChildren
            }"
            @click="selectAccount(account)"
          >
            <span class="account-code">{{ account.code }}</span>
            <span class="account-name">{{ account.name }}</span>
            <span v-if="account.hasChildren" class="expand-icon">▶</span>
          </div>
        </div>
      </div>

      <!-- 中间拖拽条 -->
      <div class="resizer">
        <div class="resizer-handle">◀▶</div>
      </div>

      <!-- 右侧表格区域 -->
      <div class="right-panel">
        <!-- 科目选择器 -->
        <div class="account-selector">
          <el-button
            size="small"
            :disabled="!hasPrev"
            @click="prevAccount"
            class="nav-btn"
          >
            ◀
          </el-button>
          <div class="selector-display">
            <span v-if="selectedAccount" class="selector-text">
              {{ selectedAccount.code }} {{ selectedAccount.name }}
            </span>
            <span v-else class="selector-placeholder">请选择科目</span>
          </div>
          <el-button
            size="small"
            :disabled="!hasNext"
            @click="nextAccount"
            class="nav-btn"
          >
            ▶
          </el-button>
        </div>

        <!-- 数据表格 -->
        <div class="table-area">
          <el-table
            v-if="selectedAccount"
            :data="displayData"
            v-loading="loading"
            border
            stripe
            size="small"
            :header-cell-style="{ background: '#f5f7fa', color: '#303133', fontWeight: 600, fontSize: '13px' }"
            style="width: 100%"
            max-height="calc(100vh - 240px)"
          >
            <el-table-column prop="period" label="期间" width="110" align="center" />
            <el-table-column label="期初借方" width="140" align="right">
              <template #default="{ row }">
                <span class="amount">{{ formatAmount(row.openingDebit) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="期初贷方" width="140" align="right">
              <template #default="{ row }">
                <span class="amount">{{ formatAmount(row.openingCredit) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="本期借方" width="140" align="right">
              <template #default="{ row }">
                <span class="amount">{{ formatAmount(row.periodDebit) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="本期贷方" width="140" align="right">
              <template #default="{ row }">
                <span class="amount">{{ formatAmount(row.periodCredit) }}</span>
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
            <el-table-column label="期末余额" width="140" align="right">
              <template #default="{ row }">
                <span class="amount balance">{{ formatAmount(row.endingDebit || row.endingCredit) }}</span>
              </template>
            </el-table-column>
          </el-table>

          <!-- 空状态 -->
          <div v-else class="empty-state">
            <el-empty description="暂无数据" :image-size="200">
              <template #image>
                <div style="font-size: 80px; opacity: 0.3">📊</div>
              </template>
            </el-empty>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.general-ledger-page {
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

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar-label {
  font-size: 13px;
  color: #606266;
  white-space: nowrap;
}

/* ===== 主体区域 ===== */
.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* ===== 左侧科目树面板 ===== */
.left-panel {
  width: 220px;
  background: #fff;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.panel-search {
  padding: 12px;
  border-bottom: 1px solid #e4e7ed;
}

.panel-tree {
  flex: 1;
  overflow-y: auto;
  padding: 4px 0;
}

.account-item {
  padding: 8px 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: background 0.15s;
  font-size: 13px;
}

.account-item:hover {
  background: #f5f7fa;
}

.account-item.active {
  background: #ecf5ff;
  color: #409eff;
}

.account-item.active .account-code {
  color: #409eff;
}

.account-code {
  color: #909399;
  font-size: 12px;
  min-width: 50px;
}

.account-name {
  flex: 1;
  color: #303133;
}

.account-item.active .account-name {
  color: #409eff;
  font-weight: 500;
}

.expand-icon {
  font-size: 10px;
  color: #909399;
}

/* ===== 中间拖拽条 ===== */
.resizer {
  width: 6px;
  background: #e4e7ed;
  cursor: col-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.resizer-handle {
  font-size: 10px;
  color: #c0c4cc;
  writing-mode: vertical-rl;
  letter-spacing: 2px;
}

/* ===== 右侧表格区域 ===== */
.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #fff;
}

/* 科目选择器 */
.account-selector {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  border-bottom: 1px solid #e4e7ed;
  gap: 8px;
}

.nav-btn {
  padding: 4px 8px;
  font-size: 12px;
}

.selector-display {
  flex: 1;
  background: #409eff;
  color: #fff;
  padding: 6px 16px;
  border-radius: 4px;
  text-align: center;
  font-size: 14px;
  font-weight: 500;
}

.selector-placeholder {
  opacity: 0.7;
}

/* 表格区域 */
.table-area {
  flex: 1;
  overflow: hidden;
  padding: 0;
}

/* 空状态 */
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

/* 金额样式 */
.amount {
  font-family: 'SF Mono', 'Menlo', 'Consolas', monospace;
  font-size: 13px;
  color: #606266;
}

.amount.balance {
  color: #409eff;
  font-weight: 600;
}

/* Element Plus 微调 */
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

:deep(.el-empty__description) {
  font-size: 14px;
  color: #909399;
}
</style>
