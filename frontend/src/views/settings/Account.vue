<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { accountData, type AccountItem } from './accountData'

/** 科目类别 Tab */
const tabs = [
  { key: 'asset', label: '资产' },
  { key: 'liability', label: '负债' },
  { key: 'equity', label: '权益' },
  { key: 'cost', label: '成本' },
  { key: 'pnl', label: '损益' },
]
const activeTab = ref('asset')

/* ---- 科目数据：来自 accountData.ts（由 Excel 完整科目表初始化）---- */

/** 当前 tab 对应的一级科目 */
const currentRoots = computed<AccountItem[]>(() => accountData[activeTab.value] ?? [])

/* ---- 展开/折叠（用 id 集合记录已展开节点）---- */
const expandedIds = ref<Set<string>>(new Set())

function toggleExpand(node: AccountItem) {
  if (expandedIds.value.has(node.id)) expandedIds.value.delete(node.id)
  else expandedIds.value.add(node.id)
}

function isExpanded(id: string): boolean {
  return expandedIds.value.has(id)
}

/* ---- 扁平化为可见行（带层级 depth）---- */
interface VisibleRow { node: AccountItem; depth: number }

function flatten(nodes: AccountItem[], depth: number, out: VisibleRow[]) {
  for (const n of nodes) {
    out.push({ node: n, depth })
    if (n.children?.length && isExpanded(n.id)) {
      flatten(n.children, depth + 1, out)
    }
  }
}

/* ---- 搜索 ---- */
const searchKey = ref('')

const visibleRows = computed<VisibleRow[]>(() => {
  const out: VisibleRow[] = []
  const key = searchKey.value.trim().toLowerCase()
  if (!key) {
    flatten(currentRoots.value, 0, out)
    return out
  }
  // 搜索：忽略层级折叠，跨全树匹配
  const flatAll: VisibleRow[] = []
  flatten(currentRoots.value, 0, flatAll)
  return flatAll.filter(r =>
    r.node.code.includes(key) || r.node.name.toLowerCase().includes(key),
  )
})

/* ---- 选中 ---- */
const selectedIds = ref<Set<string>>(new Set(['1122'])) // 默认选中"应收账款"

function toggleSelect(node: AccountItem, e: Event) {
  e.stopPropagation()
  if (selectedIds.value.has(node.id)) {
    selectedIds.value.delete(node.id)
  } else {
    selectedIds.value.add(node.id)
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
            v-for="row in visibleRows"
            :key="row.node.id"
            :class="['data-row', { selected: isRowSelected(row.node.id) }]"
            @click="toggleSelect(row.node, $event as unknown as Event)"
          >
            <!-- 复选框 -->
            <td class="col-check" @click.stop>
              <el-checkbox
                :model-value="isRowSelected(row.node.id)"
                @change="toggleSelect(row.node, $event as unknown as Event)"
              />
            </td>
            <!-- 展开 + 编码（按层级缩进） -->
            <td class="col-code" :style="{ paddingLeft: (12 + row.depth * 22) + 'px' }">
              <span v-if="row.node.children?.length" class="expand-btn" @click.stop="toggleExpand(row.node)">
                <el-icon :size="12"><component :is="isExpanded(row.node.id) ? 'ArrowDown' : 'ArrowRight'" /></el-icon>
              </span>
              <span v-else class="expand-placeholder"></span>
              {{ row.node.code }}
            </td>
            <!-- 名称 + 选中操作图标 -->
            <td class="col-name">
              {{ row.node.name }}
              <span v-if="isRowSelected(row.node.id)" class="row-actions">
                <el-icon class="action-icon" size="14" title="删除" @click.stop="handleDelete(row.node)">
                  <Close />
                </el-icon>
                <el-icon class="action-icon edit" size="14" title="编辑" @click.stop="handleEdit(row.node)">
                  <EditPen />
                </el-icon>
              </span>
            </td>
            <td class="col-cat">{{ row.node.category }}</td>
            <td class="col-unit">{{ row.node.unit || '' }}</td>
            <td class="col-dir">
              <span :class="['dir-tag', row.node.direction]">{{ row.node.direction }}</span>
            </td>
            <td class="col-aux">{{ row.node.auxCalc || '' }}</td>
            <td class="col-fx">{{ row.node.foreignCurrency || '' }}</td>
          </tr>
          <tr v-if="visibleRows.length === 0">
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
.col-code    { width: 150px; }
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
