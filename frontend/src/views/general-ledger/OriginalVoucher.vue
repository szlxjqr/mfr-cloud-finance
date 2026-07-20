<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

/* ==================== 类型定义 ==================== */

interface AttachmentItem {
  id: string
  name: string           // 附件名称
  description: string    // 附件说明
  remark: string         // 备注
  voucherId: string      // 关联凭证编号
  voucherStatus: 'draft' | 'audited' | 'posted' | '' // 凭证状态
  category: 'attachment' | 'invoice' | 'bank' // 分类
  fileType: string       // 文件类型
  fileSize: string       // 文件大小
  date: string           // 日期
  creator: string        // 上传人
}

/* ==================== 状态 ==================== */

/** 日期模式 */
const dateMode = ref<'date' | 'period'>('date')

/** 日期范围 */
const dateRange = ref<[string, string]>(['2026-05-01', '2026-05-31'])

/** 搜索关键字 */
const searchKeyword = ref('')

/** 当前选中的分类 */
const activeCategory = ref<'all' | 'attachment' | 'invoice' | 'bank'>('all')

/** 加载状态 */
const loading = ref(false)

/** 表格选中项 */
const selectedIds = ref<string[]>([])

/** Mock 数据 — 原始凭证附件列表 */
const attachments = ref<AttachmentItem[]>([
  {
    id: 'ATT-001', name: '2026-05-03-收款回单.pdf', description: '客户A货款收款回单',
    remark: '银行转账', voucherId: '记字第001号', voucherStatus: 'audited',
    category: 'bank', fileType: 'PDF', fileSize: '245KB', date: '2026-05-03', creator: '张会计',
  },
  {
    id: 'ATT-002', name: '办公用品采购发票.jpg', description: '办公用品采购发票',
    remark: '增值税普通发票', voucherId: '记字第002号', voucherStatus: 'audited',
    category: 'invoice', fileType: 'JPG', fileSize: '1.2MB', date: '2026-05-06', creator: '张会计',
  },
  {
    id: 'ATT-003', name: '房租支付回单.pdf', description: '5月房租支付银行回单',
    remark: '对公转账', voucherId: '付字第003号', voucherStatus: 'draft',
    category: 'bank', fileType: 'PDF', fileSize: '189KB', date: '2026-05-10', creator: '王出纳',
  },
  {
    id: 'ATT-004', name: '预付款收据.jpg', description: '客户预付款收据',
    remark: '预收账款', voucherId: '收字第004号', voucherStatus: 'draft',
    category: 'attachment', fileType: 'JPG', fileSize: '856KB', date: '2026-05-15', creator: '王出纳',
  },
  {
    id: 'ATT-005', name: '销售合同.pdf', description: '产品销售合同附件',
    remark: '合同编号 HT-2026-005', voucherId: '记字第005号', voucherStatus: 'draft',
    category: 'attachment', fileType: 'PDF', fileSize: '3.5MB', date: '2026-05-20', creator: '张会计',
  },
])

/* ==================== 计算属性 ==================== */

/** 按分类过滤后的列表 */
const filteredList = computed(() => {
  let list = attachments.value
  if (activeCategory.value !== 'all') {
    list = list.filter(item => item.category === activeCategory.value)
  }
  if (searchKeyword.value) {
    const kw = searchKeyword.value.toLowerCase()
    list = list.filter(item =>
      item.name.toLowerCase().includes(kw) ||
      item.description.toLowerCase().includes(kw) ||
      item.voucherId.toLowerCase().includes(kw)
    )
  }
  return list
})

/** 选中的数量 */
const selectedCount = computed(() => selectedIds.value.length)

/** 分类统计 */
const categoryCount = computed(() => ({
  all: attachments.value.length,
  attachment: attachments.value.filter(i => i.category === 'attachment').length,
  invoice: attachments.value.filter(i => i.category === 'invoice').length,
  bank: attachments.value.filter(i => i.category === 'bank').length,
}))

/* ==================== 方法 ==================== */

/** 搜索 */
function handleSearch() {
  loading.value = true
  setTimeout(() => { loading.value = false }, 400)
}

/** 刷新 */
function handleRefresh() {
  loading.value = true
  setTimeout(() => { loading.value = false; ElMessage.success('数据已刷新') }, 500)
}

/** 上传附件 */
function handleUpload() {
  ElMessage.info('打开上传附件对话框…')
}

/** 生成凭证 */
function handleGenerateVoucher() {
  if (selectedCount.value === 0) {
    ElMessage.warning('请先选择要生成凭证的附件')
    return
  }
  ElMessage.success(`已为 ${selectedCount.value} 个附件生成凭证`)
}

/** 关联凭证 */
function handleLinkVoucher() {
  if (selectedCount.value === 0) {
    ElMessage.warning('请先选择要关联的附件')
    return
  }
  ElMessage.info('打开关联凭证对话框…')
}

/** 修改 */
function handleEdit() {
  if (selectedCount.value === 0) {
    ElMessage.warning('请先选择要修改的附件')
    return
  }
  ElMessage.info('打开修改对话框…')
}

/** 删除 */
async function handleDelete() {
  if (selectedCount.value === 0) {
    ElMessage.warning('请先选择要删除的附件')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确定删除选中的 ${selectedCount.value} 个附件？此操作不可恢复！`,
      '警告',
      { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'error' }
    )
    ElMessage.success('已删除')
  } catch { /* 取消 */ }
}

/** 下载 */
function handleDownload() {
  if (selectedCount.value === 0) {
    ElMessage.warning('请先选择要下载的附件')
    return
  }
  ElMessage.success(`正在打包下载 ${selectedCount.value} 个附件…`)
}

/** 表格行选择变化 */
function handleSelectionChange(rows: AttachmentItem[]) {
  selectedIds.value = rows.map(r => r.id)
}

/** 获取文件类型图标颜色 */
function getFileTypeColor(type: string): string {
  const map: Record<string, string> = {
    'PDF': '#f56c6c', 'JPG': '#67c23a', 'PNG': '#67c23a', 'DOC': '#409eff',
    'XLS': '#67c23a', 'ZIP': '#e6a23c',
  }
  return map[type.toUpperCase()] || '#909399'
}

/** 状态标签 */
function getStatusTag(status: string) {
  const map: Record<string, { type: string; label: string }> = {
    'draft': { type: 'warning', label: '草稿' },
    'audited': { type: 'success', label: '已审核' },
    'posted': { type: 'info', label: '已记账' },
    '': { type: 'info', label: '未关联' },
  }
  return map[status] || { type: 'info', label: status }
}
</script>

<template>
  <div class="original-voucher-page">
    <!-- ====== 顶部工具栏 ====== -->
    <div class="toolbar">
      <div class="toolbar-left">
        <!-- 日期/期间切换 -->
        <el-radio-group v-model="dateMode" size="small" class="mode-group">
          <el-radio-button value="date">日期</el-radio-button>
          <el-radio-button value="period">期间</el-radio-button>
        </el-radio-group>

        <!-- 日期范围 -->
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="-"
          start-placeholder="开始期间"
          end-placeholder="结束期间"
          format="YYYY/MM/DD"
          value-format="YYYY-MM-DD"
          size="default"
          class="date-picker"
        />

        <!-- 搜索 -->
        <el-input
          v-model="searchKeyword"
          placeholder="搜索附件名称"
          clearable
          :prefix-icon="'Search'"
          size="default"
          class="search-box"
          @keyup.enter="handleSearch"
        />

        <!-- 筛选 -->
        <el-dropdown trigger="click">
          <el-button type="primary">筛选<el-icon class="el-icon--right"><ArrowDown /></el-icon></el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item>全部状态</el-dropdown-item>
              <el-dropdown-item>已关联凭证</el-dropdown-item>
              <el-dropdown-item>未关联凭证</el-dropdown-item>
              <el-dropdown-item divided>按文件类型</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <!-- 刷新 -->
        <el-button text circle :icon="'Refresh'" title="刷新" @click="handleRefresh" />
      </div>

      <!-- 右侧：上传 -->
      <div class="toolbar-right">
        <el-button type="primary" @click="handleUpload">上传附件</el-button>
      </div>
    </div>

    <!-- ====== 主体区域：左侧分类 + 右侧表格 ====== -->
    <div class="main-body">
      <!-- 左侧分类树 -->
      <div class="category-panel">
        <div class="category-title">全部分类</div>
        <div
          class="category-item"
          :class="{ active: activeCategory === 'all' }"
          @click="activeCategory = 'all'"
        >
          <span class="cat-name">凭证附件</span>
          <span class="cat-count">{{ categoryCount.all }}</span>
        </div>
        <div
          class="category-item"
          :class="{ active: activeCategory === 'invoice' }"
          @click="activeCategory = 'invoice'"
        >
          <span class="cat-name">发票</span>
          <span class="cat-count">{{ categoryCount.invoice }}</span>
        </div>
        <div
          class="category-item"
          :class="{ active: activeCategory === 'bank' }"
          @click="activeCategory = 'bank'"
        >
          <span class="cat-name">银行回单</span>
          <span class="cat-count">{{ categoryCount.bank }}</span>
        </div>
      </div>

      <!-- 右侧表格区域 -->
      <div class="table-area">
        <!-- 批量操作栏 -->
        <div class="batch-bar">
          <span class="select-count">已选中 <strong>{{ selectedCount }}</strong> 条</span>

          <el-button text size="small" @click="handleGenerateVoucher">
            <el-icon style="margin-right:4px"><Document /></el-icon>生成凭证
          </el-button>

          <el-button text size="small" @click="handleLinkVoucher">
            <el-icon style="margin-right:4px"><Link /></el-icon>关联凭证
          </el-button>

          <el-button text size="small" @click="handleEdit">
            <el-icon style="margin-right:4px"><Edit /></el-icon>修改
          </el-button>

          <el-button text size="small" @click="handleDelete">
            <el-icon style="margin-right:4px"><Delete /></el-icon>删除
          </el-button>

          <el-button text size="small" @click="handleDownload">
            <el-icon style="margin-right:4px"><Download /></el-icon>下载
          </el-button>
        </div>

        <!-- 数据表格 -->
        <el-table
          :data="filteredList"
          v-loading="loading"
          row-key="id"
          border
          stripe
          header-cell-class-name="table-header"
          @selection-change="handleSelectionChange"
          class="attachment-table"
        >
          <el-table-column type="selection" width="44" align="center" />

          <el-table-column label="附件" min-width="240">
            <template #default="{ row }">
              <div class="file-cell">
                <span
                  class="file-type-badge"
                  :style="{ background: getFileTypeColor(row.fileType) + '15', color: getFileTypeColor(row.fileType) }"
                >
                  {{ row.fileType }}
                </span>
                <span class="file-name" :title="row.name">{{ row.name }}</span>
                <span class="file-size">{{ row.fileSize }}</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="附件说明及备注" min-width="280">
            <template #default="{ row }">
              <div class="desc-cell">
                <p class="desc-text">{{ row.description }}</p>
                <p v-if="row.remark" class="remark-text">备注：{{ row.remark }}</p>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="凭证编号" width="140" align="center">
            <template #default="{ row }">
              <span v-if="row.voucherId" class="voucher-link">{{ row.voucherId }}</span>
              <span v-else class="text-muted">—</span>
            </template>
          </el-table-column>

          <el-table-column label="凭证状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag
                v-if="row.voucherStatus"
                size="small"
                :type="getStatusTag(row.voucherStatus).type"
                effect="light"
                round
              >
                {{ getStatusTag(row.voucherStatus).label }}
              </el-tag>
              <span v-else class="text-muted">—</span>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="100" align="center" fixed="right">
            <template #default>
              <el-button text size="small" type="primary">查看</el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div class="pagination-bar">
          <el-pagination
            background
            layout="total, sizes, prev, pager, next, jumper"
            :total="filteredList.length"
            :page-sizes="[20, 50, 100]"
            :page-size="20"
            :current-page="1"
            small
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.original-voucher-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}

/* ====== 工具栏 ====== */
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #ebeef5;
  gap: 10px;
  flex-shrink: 0;
}
.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.date-picker {
  width: 260px !important;
}
.search-box {
  width: 200px !important;
}

/* ====== 主体区域 ====== */
.main-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* ---- 左侧分类面板 ---- */
.category-panel {
  width: 180px;
  flex-shrink: 0;
  border-right: 1px solid #ebeef5;
  padding: 12px 0;
  background: #fafbfc;
  overflow-y: auto;
}
.category-title {
  font-size: 14px;
  font-weight: 700;
  color: #303133;
  padding: 8px 16px 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
}
.category-title::before {
  content: '▾';
  font-size: 10px;
  color: #909399;
}
.category-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 9px 16px 9px 28px;
  font-size: 13px;
  color: #606266;
  cursor: pointer;
  transition: all 0.15s;
  border-radius: 0 6px 6px 0;
  margin-right: 8px;
}
.category-item:hover {
  background: #ecf5ff;
  color: #409eff;
}
.category-item.active {
  background: #ecf5ff;
  color: #409eff;
  font-weight: 600;
}
.cat-name {
  flex: 1;
}
.cat-count {
  font-size: 12px;
  color: #909399;
  background: #f0f2f5;
  padding: 1px 7px;
  border-radius: 10px;
  min-width: 20px;
  text-align: center;
}
.category-item.active .cat-count {
  background: #409eff;
  color: #fff;
}

/* ---- 右侧表格区域 ---- */
.table-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0 16px 12px;
}

/* 批量操作栏 */
.batch-bar {
  display: flex;
  align-items: center;
  padding: 10px 0;
  gap: 4px;
  font-size: 13px;
  color: #606266;
  flex-shrink: 0;
  border-bottom: 1px solid #f0f0f0;
}
.select-count strong {
  color: #409eff;
  margin: 0 2px;
}
.batch-bar .el-button {
  font-size: 13px !important;
}

/* 表格 */
.attachment-table {
  flex: 1;
  overflow: auto;
  --el-table-border-color: #eef0f3;
  --el-table-header-bg-color: #f7f9fc;
}
.attachment-table :deep(.table-header) {
  background: #f7f9fc !important;
  color: #303133;
  font-weight: 600;
  font-size: 13px;
}
.attachment-table :deep(.el-table__row:hover > td) {
  background: #ecf5ff !important;
}

/* 文件单元格 */
.file-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}
.file-type-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 4px;
  white-space: nowrap;
  flex-shrink: 0;
}
.file-name {
  font-size: 13px;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}
.file-size {
  font-size: 12px;
  color: #c0c4cc;
  white-space: nowrap;
  flex-shrink: 0;
}

/* 描述单元格 */
.desc-cell {
  padding: 2px 0;
}
.desc-text {
  margin: 0;
  font-size: 13px;
  color: #303133;
  line-height: 1.5;
}
.remark-text {
  margin: 2px 0 0;
  font-size: 12px;
  color: #909399;
}

/* 凭证编号链接 */
.voucher-link {
  color: #409eff;
  cursor: pointer;
  font-size: 13px;
}
.voucher-link:hover {
  text-decoration: underline;
}
.text-muted {
  color: #c0c4cc;
  font-size: 13px;
}

/* 分页 */
.pagination-bar {
  display: flex;
  justify-content: flex-end;
  padding: 12px 0 0;
  flex-shrink: 0;
}

/* 响应式 */
@media (max-width: 900px) {
  .main-body { flex-direction: column; }
  .category-panel { width: 100%; display: flex; gap: 8px; padding: 8px 12px; border-right: none; border-bottom: 1px solid #ebeef5; }
  .category-title { display: none; }
  .category-item { margin: 0; border-radius: 6px; padding: 6px 12px; }
}
</style>
