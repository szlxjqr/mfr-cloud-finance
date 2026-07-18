<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

/** 科目类别 Tab */
const tabs = [
  { key: 'asset', label: '资产' },
  { key: 'liability', label: '负债' },
  { key: 'equity', label: '权益' },
  { key: 'cost', label: '成本' },
  { key: 'pnl', label: '损益' },
]
const activeTab = ref('asset')

/* ---- 数据类型 ---- */
interface AccountItem {
  id: string
  code: string
  name: string
  category: string
  unit?: string
  direction: '借' | '贷'
  auxCalc?: string
  foreignCurrency?: string
  children?: AccountItem[]
  level: number
  expanded?: boolean
}

/* ---- Mock 数据：按截图还原 ---- */
const assetAccounts = ref<AccountItem[]>([
  { id: '1', code: '1001', name: '库存现金', category: '资产', direction: '借', level: 1, expanded: false },
  { id: '2', code: '1002', name: '银行存款', category: '资产', direction: '借', level: 1, expanded: false },
  { id: '3', code: '1012', name: '其他货币资金', category: '资产', direction: '借', level: 1, expanded: false },
  {
    id: '4', code: '1101', name: '短期投资', category: '资产', direction: '借', level: 1,
    expanded: false, children: [],
  },
  { id: '5', code: '1121', name: '应收票据', category: '资产', direction: '借', level: 1, expanded: false },
  { id: '6', code: '1122', name: '应收账款', category: '资产', direction: '借', level: 1, expanded: false },
  { id: '7', code: '1123', name: '预付账款', category: '资产', direction: '借', level: 1, expanded: false },
  { id: '8', code: '1131', name: '应收股利', category: '资产', direction: '借', level: 1, expanded: false },
  { id: '9', code: '1132', name: '应收利息', category: '资产', direction: '借', level: 1, expanded: false },
  { id: '10', code: '1221', name: '其他应收款', category: '资产', direction: '借', level: 1, expanded: false },
  { id: '11', code: '1401', name: '材料采购', category: '资产', direction: '借', level: 1, expanded: false },
  { id: '12', code: '1402', name: '在途物资', category: '资产', direction: '借', level: 1, expanded: false },
  { id: '13', code: '1403', name: '原材料', category: '资产', direction: '借', level: 1, expanded: false },
  { id: '14', code: '1404', name: '材料成本差异', category: '资产', direction: '借', level: 1, expanded: false },
  { id: '15', code: '1405', name: '库存商品', category: '资产', direction: '借', level: 1, expanded: false },
  { id: '16', code: '1407', name: '商品进销差价', category: '资产', direction: '贷', level: 1, expanded: false },
  { id: '17', code: '1408', name: '委托加工物资', category: '资产', direction: '借', level: 1, expanded: false },
  { id: '18', code: '1411', name: '周转材料', category: '资产', direction: '借', level: 1, expanded: false },
])

const liabilityAccounts = ref<AccountItem[]>([
  { id: 'l1', code: '2001', name: '短期借款', category: '负债', direction: '贷', level: 1, expanded: false },
  { id: 'l2', code: '2201', name: '应付票据', category: '负债', direction: '贷', level: 1, expanded: false },
  { id: 'l3', code: '2202', name: '应付账款', category: '负债', direction: '贷', level: 1, expanded: false },
  { id: 'l4', code: '2203', name: '预收账款', category: '负债', direction: '贷', level: 1, expanded: false },
  { id: 'l5', code: '2211', name: '应付职工薪酬', category: '负债', direction: '贷', level: 1, expanded: false },
  { id: 'l6', code: '2221', name: '应交税费', category: '负债', direction: '贷', level: 1, expanded: false },
  { id: 'l7', code: '2231', name: '应付利息', category: '负债', direction: '贷', level: 1, expanded: false },
  { id: 'l8', code: '2232', name: '应付股利', category: '负债', direction: '贷', level: 1, expanded: false },
  { id: 'l9', code: '2241', name: '其他应付款', category: '负债', direction: '贷', level: 1, expanded: false },
  { id: 'l10', code: '2501', name: '长期借款', category: '负债', direction: '贷', level: 1, expanded: false },
])

const equityAccounts = ref<AccountItem[]>([
  { id: 'e1', code: '3001', name: '实收资本(或股本)', category: '权益', direction: '贷', level: 1, expanded: false },
  { id: 'e2', code: '3002', name: '资本公积', category: '权益', direction: '贷', level: 1, expanded: false },
  { id: 'e3', code: '3101', name: '盈余公积', category: '权益', direction: '贷', level: 1, expanded: false },
  { id: 'e4', code: '3103', name: '本年利润', category: '权益', direction: '贷', level: 1, expanded: false },
  { id: 'e5', code: '3104', name: '利润分配', category: '权益', direction: '贷', level: 1, expanded: false },
])

const costAccounts = ref<AccountItem[]>([
  { id: 'c1', code: '4001', name: '生产成本', category: '成本', direction: '借', level: 1, expanded: false },
  { id: 'c2', code: '4002', name: '制造费用', category: '成本', direction: '借', level: 1, expanded: false },
  { id: 'c3', code: '4101', name: '劳务成本', category: '成本', direction: '借', level: 1, expanded: false },
  { id: 'c4', code: '4301', name: '研发支出', category: '成本', direction: '借', level: 1, expanded: false },
])

const pnlAccounts = ref<AccountItem[]>([
  { id: 'p1', code: '5001', name: '主营业务收入', category: '损益', direction: '贷', level: 1, expanded: false },
  { id: 'p2', code: '5051', name: '其他业务收入', category: '损益', direction: '贷', level: 1, expanded: false },
  { id: 'p3', code: '5111', name: '投资收益', category: '损益', direction: '贷', level: 1, expanded: false },
  { id: 'p4', code: '5301', name: '营业外收入', category: '损益', direction: '贷', level: 1, expanded: false },
  { id: 'p5', code: '5401', name: '主营业务成本', category: '损益', direction: '借', level: 1, expanded: false },
  { id: 'p6', code: '5402', name: '其他业务成本', category: '损益', direction: '借', level: 1, expanded: false },
  { id: 'p7', code: '5601', name: '销售费用', category: '损益', direction: '借', level: 1, expanded: false },
  { id: 'p8', code: '5602', name: '管理费用', category: '损益', direction: '借', level: 1, expanded: false },
  { id: 'p9', code: '5603', name: '财务费用', category: '损益', direction: '借', level: 1, expanded: false },
  { id: 'p10', code: '5711', name: '营业外支出', category: '损益', direction: '借', level: 1, expanded: false },
  { id: 'p11', code: '5801', name: '所得税费用', category: '损益', direction: '借', level: 1, expanded: false },
])

/** 当前 tab 对应数据 */
const currentData = computed(() => {
  switch (activeTab.value) {
    case 'asset': return assetAccounts.value
    case 'liability': return liabilityAccounts.value
    case 'equity': return equityAccounts.value
    case 'cost': return costAccounts.value
    case 'pnl': return pnlAccounts.value
    default: return assetAccounts.value
  }
})

/* ---- 搜索 / 筛选 ---- */
const searchKey = ref('')

const filteredData = computed(() => {
  const key = searchKey.value.trim().toLowerCase()
  if (!key) return currentData.value
  return currentData.value.filter(
    item => item.code.includes(key) || item.name.toLowerCase().includes(key),
  )
})

/* ---- 展开/折叠 / 选中 ---- */
function toggleExpand(row: AccountItem) {
  row.expanded = !row.expanded
}

const selectedIds = ref<Set<string>>(new Set(['6'])) // 默认选中"应收账款"

function toggleSelect(row: AccountItem, e: Event) {
  e.stopPropagation()
  if (selectedIds.value.has(row.id)) {
    selectedIds.value.delete(row.id)
  } else {
    selectedIds.value.add(row.id)
  }
}

function isRowSelected(id: string): boolean {
  return selectedIds.value.has(id)
}

/* ---- 操作 ---- */
function handleAdd() {
  ElMessage.info('打开新增科目弹窗...')
}

function handleBatchDelete() {
  if (selectedIds.value.size === 0) {
    ElMessage.warning('请先选择要删除的科目')
    return
  }
  ElMessageBox.confirm(`确定要删除选中的 ${selectedIds.value.size} 个科目吗？`, '批量删除', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(() => {
    ElMessage.success(`已删除 ${selectedIds.value.size} 个科目`)
    selectedIds.value.clear()
  }).catch(() => {})
}

function handleEdit(row: AccountItem) {
  ElMessage.info(`编辑科目：${row.code} ${row.name}`)
}

function handleDelete(row: AccountItem) {
  ElMessageBox.confirm(`确定删除科目「${row.name}」吗？`, '删除确认', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(() => {
    ElMessage.success(`已删除 ${row.name}`)
  }).catch(() => {})
}

function handleImport(cmd: string) {
  ElMessage.info(`导入${cmd}`)
}

function handleExport() {
  ElMessage.success('导出科目列表')
}

function handleRefresh() {
  ElMessage.success('已刷新')
}
</script>

<template>
  <div class="account-page">
    <!-- ====== Tab 栏 ====== -->
    <div class="tab-bar">
      <div class="tab-list">
        <div
          v-for="tab in tabs"
          :key="tab.key"
          :class="['tab-item', { active: activeTab === tab.key }]"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
          <span v-if="activeTab === tab.key" class="tab-dot"></span>
        </div>
      </div>
      <el-icon class="tab-collapse"><ArrowDown /></el-icon>
    </div>

    <!-- ====== 工具栏 ====== -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="searchKey"
          placeholder="请输入科目编号或名称"
          clearable
          class="search-input"
        >
          <template #suffix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button text circle @click="handleRefresh">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>

      <div class="toolbar-right">
        <span class="level-hint">
          <el-icon color="#67C23A"><Document /></el-icon>
          级次说明：0001 001 001 01 01
        </span>
        <el-button text circle title="帮助">
          <el-icon><QuestionFilled /></el-icon>
        </el-button>
        <el-button type="primary" @click="handleAdd">新增</el-button>
        <el-button @click="handleBatchDelete">批量删除</el-button>
        <el-dropdown @command="handleImport" trigger="click">
          <el-button>导入<el-icon class="el-icon--right"><ArrowDown /></el-icon></el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="Excel">从 Excel 导入</el-dropdown-item>
              <el-dropdown-item command="模板">下载导入模板</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button @click="handleExport">导出</el-button>
        <el-button text circle title="设置">
          <el-icon><Setting /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- ====== 表格 ====== -->
    <div class="table-wrap">
      <table class="account-table">
        <thead>
          <tr>
            <th class="col-check"></th>
            <th class="col-code">科目编码</th>
            <th class="col-name">科目名称</th>
            <th class="col-cat">类别</th>
            <th class="col-unit">计量单位</th>
            <th class="col-dir">方向</th>
            <th class="col-aux">辅助核算</th>
            <th class="col-fx">外币名称</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in filteredData"
            :key="row.id"
            :class="['data-row', { selected: isRowSelected(row.id) }]"
            @click="toggleSelect(row, $event as unknown as Event)"
          >
            <!-- 复选框 -->
            <td class="col-check" @click.stop>
              <el-checkbox
                :model-value="isRowSelected(row.id)"
                @change="toggleSelect(row, $event as unknown as Event)"
              />
            </td>
            <!-- 展开 + 编码 -->
            <td class="col-code">
              <span v-if="row.children?.length" class="expand-btn" @click.stop="toggleExpand(row)">
                <el-icon :size="12"><component :is="row.expanded ? 'ArrowDown' : 'ArrowRight'" /></el-icon>
              </span>
              <span v-else class="expand-placeholder"></span>
              {{ row.code }}
            </td>
            <!-- 名称 + 选中操作图标 -->
            <td class="col-name">
              {{ row.name }}
              <span v-if="isRowSelected(row.id)" class="row-actions">
                <el-icon class="action-icon" size="14" title="删除" @click.stop="handleDelete(row)">
                  <Close />
                </el-icon>
                <el-icon class="action-icon edit" size="14" title="编辑" @click.stop="handleEdit(row)">
                  <EditPen />
                </el-icon>
              </span>
            </td>
            <td class="col-cat">{{ row.category }}</td>
            <td class="col-unit">{{ row.unit || '' }}</td>
            <td class="col-dir">
              <span :class="['dir-tag', row.direction]">{{ row.direction }}</span>
            </td>
            <td class="col-aux">{{ row.auxCalc || '' }}</td>
            <td class="col-fx">{{ row.foreignCurrency || '' }}</td>
          </tr>
          <tr v-if="filteredData.length === 0">
            <td colspan="8" class="empty-cell">
              <el-empty description="暂无科目数据" :image-size="80" />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.account-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fff;
  overflow: hidden;
}

/* ====== Tab 栏 ====== */
.tab-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  border-bottom: 1px solid var(--el-border-color-light);
  flex-shrink: 0;
  background: #fff;
}
.tab-list {
  display: flex;
  gap: 0;
}
.tab-item {
  position: relative;
  padding: 14px 18px;
  font-size: 14px;
  cursor: pointer;
  color: var(--el-text-color-secondary);
  transition: all .2s;
}
.tab-item:hover {
  color: var(--el-color-primary);
}
.tab-item.active {
  color: var(--el-color-primary);
  font-weight: 600;
}
.tab-dot {
  position: absolute;
  bottom: 6px;
  left: 50%;
  transform: translateX(-50%);
  width: 16px;
  height: 3px;
  border-radius: 2px;
  background: var(--el-color-primary);
}
.tab-collapse {
  color: var(--el-text-color-placeholder);
  cursor: pointer;
  transform: rotate(-90deg);
  transition: transform .2s;
}

/* ====== 工具栏 ====== */
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 20px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  flex-shrink: 0;
  gap: 12px;
  flex-wrap: wrap;
}
.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.search-input {
  width: 260px;
}
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.level-hint {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #67C23A;
  margin-right: 4px;
}

/* ====== 表格区域 ====== */
.table-wrap {
  flex: 1;
  min-height: 0;
  overflow: auto;
}
.account-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}
.account-table thead th {
  position: sticky;
  top: 0;
  z-index: 5;
  padding: 10px 12px;
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  background: #fafafa;
  border-bottom: 1px solid var(--el-border-color-lighter);
  text-align: left;
  white-space: nowrap;
}
.col-check   { width: 44px; text-align: center; }
.col-code    { width: 110px; }
.col-name    { width: auto; }
.col-cat     { width: 72px; }
.col-unit    { width: 88px; }
.col-dir     { width: 64px; text-align: center; }
.col-aux     { width: 120px; }
.col-fx      { width: 120px; }

/* 行 */
.data-row {
  transition: background .15s;
  cursor: pointer;
}
.data-row:hover {
  background: var(--el-fill-color-light);
}
.data-row.selected {
  background: #ecf5ff;
}
.data-row td {
  padding: 9px 12px;
  font-size: 13.5px;
  border-bottom: 1px solid var(--el-border-color-extra-light);
  vertical-align: middle;
  white-space: nowrap;
}
.data-row td.col-check {
  text-align: center;
  vertical-align: middle;
}

/* 展开箭头 */
.expand-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  margin-right: 4px;
  cursor: pointer;
  color: var(--el-text-color-secondary);
}
.expand-placeholder {
  display: inline-block;
  width: 18px;
  margin-right: 4px;
}

/* 方向标签 */
.dir-tag {
  display: inline-block;
  padding: 1px 10px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 500;
}
.dir-tag.借 {
  color: #409eff;
  background: rgba(64,158,255,.1);
}
.dir-tag.贷 {
  color: #e6a23c;
  background: rgba(230,162,60,.12);
}

/* 选中行操作图标 */
.row-actions {
  margin-left: 8px;
  display: inline-flex;
  align-items: center;
  gap: 2px;
}
.action-icon {
  cursor: pointer;
  color: var(--el-text-color-placeholder);
  transition: color .15s;
}
.action-icon:hover {
  color: var(--el-color-danger);
}
.action-icon.edit:hover {
  color: var(--el-color-primary);
}

/* 空状态 */
.empty-cell {
  text-align: center;
  padding: 48px 0 !important;
}
</style>
