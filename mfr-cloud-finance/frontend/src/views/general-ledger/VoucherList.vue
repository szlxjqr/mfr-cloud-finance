<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'

const router = useRouter()

/* ==================== 类型定义 ==================== */

/** 凭证分录行 */
interface VoucherLine {
  summary: string
  accountName: string
  accountCode: string
  debitAmount: number
  creditAmount: number
}

/** 凭证列表项 */
interface VoucherItem {
  id: string               // 凭证ID
  word: string             // 凭证字：记/收/付/转
  number: number           // 凭证号
  date: string             // 凭证日期 YYYY-MM-DD
  period: string           // 会计期间
  attachmentCount: number  // 附单据数
  lines: VoucherLine[]     // 分录行
  totalDebit: number       // 借方合计
  totalCredit: number      // 贷方合计
  status: 'draft' | 'audited' | 'posted' // 草稿/已审核/已记账
  creator: string          // 制单人
  auditor: string          // 审核人
  remark: string           // 备注
  expanded: boolean        // 是否展开显示分录
}

/* ==================== 状态 ==================== */

/** 日期筛选模式 */
const dateMode = ref<'date' | 'period'>('date')

/** 日期范围 */
const dateRange = ref<[string, string]>(['2026-05-01', '2026-05-31'])

/** 搜索关键字 */
const searchKeyword = ref('')

/** 是否展开显示分录明细 */
const showDetailLines = ref(true)

/** 是否取消分页（一次性加载全部）*/
const noPagination = ref(false)

/** 表格选中项 ID 集合 */
const selectedIds = ref<string[]>([])

/** 加载状态 */
const loading = ref(false)

/** Mock 数据 — 凭证列表 */
const vouchers = ref<VoucherItem[]>([
  {
    id: 'V-2026-05-001', word: '记', number: 1, date: '2026-05-03',
    period: '2026年05期', attachmentCount: 2,
    status: 'audited', creator: '张会计', auditor: '李主管', remark: '',
    expanded: false, totalDebit: 50000, totalCredit: 50000,
    lines: [
      { summary: '收到客户A货款', accountName: '银行存款', accountCode: '1002', debitAmount: 50000, creditAmount: 0 },
      { summary: '收到客户A货款', accountName: '应收账款—客户A', accountCode: '112201', debitAmount: 0, creditAmount: 50000 },
    ],
  },
  {
    id: 'V-2026-05-002', word: '记', number: 2, date: '2026-05-06',
    period: '2026年05期', attachmentCount: 1,
    status: 'audited', creator: '张会计', auditor: '李主管', remark: '',
    expanded: false, totalDebit: 15000, totalCredit: 15000,
    lines: [
      { summary: '采购办公用品', accountName: '管理费用—办公费', accountCode: '660203', debitAmount: 3000, creditAmount: 0 },
      { summary: '采购办公用品', accountName: '库存现金', accountCode: '1001', debitAmount: 12000, creditAmount: 0 },
      { summary: '采购办公用品', accountName: '应付账款—供应商B', accountCode: '220201', debitAmount: 0, creditAmount: 15000 },
    ],
  },
  {
    id: 'V-2026-05-003', word: '付', number: 3, date: '2026-05-10',
    period: '2026年05期', attachmentCount: 3,
    status: 'draft', creator: '张会计', auditor: '', remark: '',
    expanded: false, totalDebit: 8000, totalCredit: 8000,
    lines: [
      { summary: '支付房租', accountName: '管理费用—租赁费', accountCode: '660204', debitAmount: 8000, creditAmount: 0 },
      { summary: '支付房租', accountName: '银行存款', accountCode: '1002', debitAmount: 0, creditAmount: 8000 },
    ],
  },
  {
    id: 'V-2026-05-004', word: '收', number: 4, date: '2026-05-15',
    period: '2026年05期', attachmentCount: 1,
    status: 'draft', creator: '王出纳', auditor: '', remark: '预收款',
    expanded: false, totalDebit: 20000, totalCredit: 20000,
    lines: [
      { summary: '收到预付款', accountName: '银行存款', accountCode: '1002', debitAmount: 20000, creditAmount: 0 },
      { summary: '收到预付款', accountName: '合同负债—预收账款', accountCode: '224101', debitAmount: 0, creditAmount: 20000 },
    ],
  },
  {
    id: 'V-2026-05-005', word: '记', number: 5, date: '2026-05-20',
    period: '2026年05期', attachmentCount: 4,
    status: 'draft', creator: '张会计', auditor: '', remark: '',
    expanded: false, totalDebit: 358000, totalCredit: 358000,
    lines: [
      { summary: '销售产品一批', accountName: '应收账款—客户C', accountCode: '112202', debitAmount: 358000, creditAmount: 0 },
      { summary: '销售产品一批', accountName: '主营业务收入', accountCode: '600101', debitAmount: 0, creditAmount: 310000 },
      { summary: '销售产品一批', accountName: '应交税费—增值税(销)', accountCode: '22210101', debitAmount: 0, creditAmount: 48000 },
    ],
  },
])

/* ==================== 计算属性 ==================== */

/** 选中的数量 */
const selectedCount = computed(() => selectedIds.value.length)

/* ==================== 方法 ==================== */

/** 单行选择 */
function toggleExpand(item: VoucherItem) {
  item.expanded = !item.expanded
}

/** 新增凭证 → 跳转到录入页 */
function goNew() {
  router.push('/general-ledger/voucher')
}

/** 搜索 */
function handleSearch() {
  loading.value = true
  setTimeout(() => {
    loading.value = false
    ElMessage.info(`搜索完成，关键词："${searchKeyword.value || '（空）'}"`)
  }, 600)
}

/** 刷新 */
function handleRefresh() {
  loading.value = true
  setTimeout(() => { loading.value = false; ElMessage.success('数据已刷新') }, 500)
}

/** 审核 */
async function handleAudit(action: 'audit' | 'unaudit' | 'batch') {
  if (selectedCount.value === 0 && action !== 'batch') {
    ElMessage.warning('请先选择凭证')
    return
  }
  const actionText = action === 'audit' ? '审核' : action === 'unaudit' ? '反审核' : '批量审核'
  await ElMessageBox.confirm(`确定对 ${selectedCount.value} 张凭证执行${actionText}操作？`, '确认', { type: 'warning' })
  ElMessage.success(`${actionText}成功`)
}

/** 打印 */
function handlePrint(mode: 'current' | 'selected' | 'preview') {
  ElMessage.info(`${mode === 'preview' ? '打印预览' : `打印${mode === 'selected' ? '所选' : '当前'}凭证`}…`)
}

/** 导出 */
function handleExport(format: 'excel' | 'pdf' | 'csv') {
  ElMessage.success(`正在导出为 ${format.toUpperCase()} 格式…`)
}

/** 删除 */
async function handleDelete() {
  if (selectedCount.value === 0) {
    ElMessage.warning('请先选择要删除的凭证')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确定删除选中的 ${selectedCount.value} 条凭证？此操作不可恢复！`,
      '警告',
      { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'error', confirmButtonClass: 'el-button--danger' }
    )
    ElMessage.success('已删除')
  } catch {
    // 取消
  }
}

/** 整理编号 */
function handleRenumber() {
  ElMessage.info('正在重新编排凭证号…')
}

/** 导入 */
function handleImport(type?: string) {
  ElMessage.info(type ? `导入${type}` : '打开导入选项…')
}

onMounted(() => {
  // 默认加载第一页数据
})
</script>

<template>
  <div class="voucher-list-page">
    <!-- ====== 顶部工具栏 ====== -->
    <div class="toolbar">
      <!-- 左侧：日期 + 搜索 -->
      <div class="toolbar-left">
        <!-- 日期模式切换 -->
        <el-radio-group v-model="dateMode" size="small" class="mode-group">
          <el-radio-button value="date">日期</el-radio-button>
          <el-radio-button value="period">期间</el-radio-button>
        </el-radio-group>

        <!-- 日期范围选择 -->
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="-"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY/MM/DD"
          value-format="YYYY-MM-DD"
          size="default"
          class="date-picker"
        />

        <!-- 搜索框 -->
        <el-input
          v-model="searchKeyword"
          placeholder="搜索凭证编号/摘要/金额等"
          clearable
          :prefix-icon="'Search'"
          size="default"
          class="search-box"
          @keyup.enter="handleSearch"
        />

        <!-- 筛选 -->
        <el-dropdown trigger="click">
          <el-button plain>筛选<el-icon class="el-icon--right"><ArrowDown /></el-icon></el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item>全部状态</el-dropdown-item>
              <el-dropdown-item>草稿</el-dropdown-item>
              <el-dropdown-item>已审核</el-dropdown-item>
              <el-dropdown-item>已记账</el-dropdown-item>
              <el-dropdown-item divided>自定义筛选</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <!-- 刷新 -->
        <el-button text circle :icon="'Refresh'" title="刷新" @click="handleRefresh" />
      </div>

      <!-- 右侧：操作按钮 -->
      <div class="toolbar-right">
        <el-checkbox v-model="showDetailLines">展开分录</el-checkbox>
        <el-checkbox v-model="noPagination">取消分页</el-checkbox>

        <el-button type="primary" @click="goNew">新增</el-button>

        <el-dropdown trigger="click" @command="handleImport">
          <el-button plain>导入<el-icon class="el-icon--right"><ArrowDown /></el-icon></el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="excel">Excel导入</el-dropdown-item>
              <el-dropdown-item command="txt">文本导入</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <el-button text @click="handleImport">电子账簿</el-button>
        <el-button text @click="handleRenumber">整理编号</el-button>
      </div>
    </div>

    <!-- ====== 第二行：批量操作栏 ====== -->
    <div class="batch-bar">
      <span class="select-count">已选中 <strong>{{ selectedCount }}</strong> 条</span>

      <el-dropdown trigger="click" @command="(cmd: string) => handleAudit(cmd as any)">
        <el-button text size="small">
          审核<el-icon class="el-icon--right"><ArrowDown /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="audit">审核通过</el-dropdown-item>
            <el-dropdown-item command="unaudit">反审核</el-dropdown-item>
            <el-dropdown-item command="batch">批量审核</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <el-dropdown trigger="click" @command="(cmd: string) => handlePrint(cmd as any)">
        <el-button text size="small">
          打印<el-icon class="el-icon--right"><ArrowDown /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="current">打印当前页</el-dropdown-item>
            <el-dropdown-item command="selected">打印所选</el-dropdown-item>
            <el-dropdown-item command="preview">打印预览</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <el-dropdown trigger="click" @command="(cmd: string) => handleExport(cmd as any)">
        <el-button text size="small">
          导出<el-icon class="el-icon--right"><ArrowDown /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="excel">导出 Excel</el-dropdown-item>
            <el-dropdown-item command="pdf">导出 PDF</el-dropdown-item>
            <el-dropdown-item command="csv">导出 CSV</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <el-button text size="small" danger :disabled="selectedCount === 0" @click="handleDelete">
        <el-icon style="margin-right:2px"><Delete /></el-icon>删除
      </el-button>
    </div>

    <!-- ====== 数据表格 ====== -->
    <div class="table-area">
      <el-table
        :data="vouchers"
        v-loading="loading"
        row-key="id"
        border
        stripe
        header-cell-class-name="table-header"
        :default-expand-all="false"
        class="voucher-table"
        :row-class-name="(row: VoucherItem) => row.expanded ? 'row-expanded' : ''"
        @selection-change="(rows: VoucherItem[]) => { selectedIds = rows.map(r => r.id) }"
      >
        <!-- 选择列 -->
        <el-table-column type="selection" width="44" align="center" />

        <!-- 展开/折叠图标列 -->
        <el-table-column width="48" align="center" label="">
          <template #default="{ row }">
            <el-icon
              class="expand-toggle"
              :class="{ 'is-open': row.expanded }"
              @click.stop="toggleExpand(row)"
            >
              <component is="ArrowRight" />
            </el-icon>
          </template>
        </el-table-column>

        <!-- 摘要列（主信息） -->
        <el-table-column min-width="280" label="摘要">
          <template #default="{ row }: { row: VoucherItem }">
            <div class="summary-cell">
              <div class="voucher-info">
                <!-- 凭证字+号 + 日期 -->
                <span class="voucher-tag" :class="`tag-${row.word.toLowerCase()}`">{{ row.word }}字第{{ String(row.number).padStart(3, '0') }}号</span>
                <span class="voucher-date">{{ row.date }}</span>
                <!-- 状态标签 -->
                <el-tag
                  v-if="row.status === 'audited'"
                  size="small"
                  type="success"
                  effect="light"
                  round
                  class="status-tag"
                >已审</el-tag>
                <el-tag
                  v-else-if="row.status === 'posted'"
                  size="small"
                  type="info"
                  effect="light"
                  round
                  class="status-tag"
                >记账</el-tag>
                <el-tag
                  v-else
                  size="small"
                  type="warning"
                  effect="light"
                  round
                  class="status-tag"
                >草稿</el-tag>
              </div>
              <!-- 分录摘要文字 -->
              <div class="line-summary" :title="row.lines.map(l => l.summary).join('; ')">
                {{ row.lines.map(l => l.summary).join('；') }}
              </div>
            </div>
          </template>
        </el-table-column>

        <!-- 科目列 -->
        <el-table-column min-width="180" label="科目">
          <template #default="{ row }: { row: VoucherItem }">
            <div class="account-cell">
              <p
                v-for="(line, li) in row.lines"
                :key="li"
                :class="['account-line', { 'first-line': li === 0 }]"
              >
                {{ line.accountName }}
                <span class="account-code">{{ line.accountCode }}</span>
              </p>
            </div>
          </template>
        </el-table-column>

        <!-- 借方金额 -->
        <el-table-column width="140" label="借方金额" align="right">
          <template #default="{ row }: { row: VoucherItem }">
            <div class="amount-col">
              <p v-for="(line, li) in row.lines" :key="li" class="amount-line" :class="{ 'has-value': line.debitAmount > 0 }">
                {{ line.debitAmount > 0 ? line.debitAmount.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) : '' }}
              </p>
              <p class="amount-total debit-total">{{ row.totalDebit.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</p>
            </div>
          </template>
        </el-table-column>

        <!-- 贷方金额 -->
        <el-table-column width="140" label="贷方金额" align="right">
          <template #default="{ row }: { row: VoucherItem }">
            <div class="amount-col">
              <p v-for="(line, li) in row.lines" :key="li" class="amount-line" :class="{ 'has-value': line.creditAmount > 0 }">
                {{ line.creditAmount > 0 ? line.creditAmount.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) : '' }}
              </p>
              <p class="amount-total credit-total">{{ row.totalCredit.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</p>
            </div>
          </template>
        </el-table-column>

        <!-- 展开的分录明细行（子表格） -->
        <el-table-column type="expand" width="1" v-if="showDetailLines">
          <template #default="{ row }: { row: VoucherItem }">
            <div class="detail-panel" v-show="row.expanded || showDetailLines">
              <table class="detail-table">
                <thead>
                  <tr>
                    <th style="width:50px">#</th>
                    <th style="min-width:160px">摘要</th>
                    <th style="min-width:180px">科目编码</th>
                    <th style="min-width:160px">科目名称</th>
                    <th style="width:130px;text-align:right">借方金额</th>
                    <th style="width:130px;text-align:right">贷方金额</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(line, di) in row.lines" :key="di">
                    <td class="dt-seq">{{ di + 1 }}</td>
                    <td>{{ line.summary }}</td>
                    <td><code class="code-text">{{ line.accountCode }}</code></td>
                    <td>{{ line.accountName }}</td>
                    <td align="right" :class="{ 'amt-debit': line.debitAmount > 0 }">
                      {{ line.debitAmount > 0 ? line.debitAmount.toFixed(2) : '' }}
                    </td>
                    <td align="right" :class="{ 'amt-credit': line.creditAmount > 0 }">
                      {{ line.creditAmount > 0 ? line.creditAmount.toFixed(2) : '' }}
                    </td>
                  </tr>
                  <tr class="detail-total-row">
                    <td colspan="4" class="dt-label">合计：</td>
                    <td align="right" class="dt-debit-total">{{ row.totalDebit.toFixed(2) }}</td>
                    <td align="right" class="dt-credit-total">{{ row.totalCredit.toFixed(2) }}</td>
                  </tr>
                </tbody>
              </table>
              <div class="detail-footer">
                <span>制单人：<strong>{{ row.creator }}</strong></span>
                <span>审核人：<strong>{{ row.auditor || '-' }}</strong></span>
                <span>附单据：<strong>{{ row.attachmentCount }}</strong> 张</span>
                <span v-if="row.remark">备注：{{ row.remark }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页（当未取消分页时） -->
    <div class="pagination-bar" v-if="!noPagination">
      <el-pagination
        background
        layout="total, sizes, prev, pager, next, jumper"
        :total="128"
        :page-sizes="[20, 50, 100, 200]"
        :page-size="20"
        :current-page="1"
        small
      />
    </div>
  </div>
</template>

<style scoped>
.voucher-list-page {
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
  flex-wrap: wrap;
  flex-shrink: 0;
}
.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.mode-group {
  margin-right: 2px;
}
.date-picker {
  width: 260px !important;
}
.search-box {
  width: 240px !important;
}

/* 批量操作栏 */
.batch-bar {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  background: #fafbfc;
  border-bottom: 1px solid #f0f0f0;
  gap: 4px;
  font-size: 13px;
  color: #606266;
  flex-shrink: 0;
}
.select-count strong {
  color: #409eff;
  margin: 0 2px;
}
.batch-bar .el-button {
  font-size: 13px !important;
}

/* ====== 表格区域 ====== */
.table-area {
  flex: 1;
  overflow: auto;
}
.voucher-table {
  --el-table-border-color: #eef0f3;
  --el-table-header-bg-color: #f7f9fc;
}
.voucher-table :deep(.table-header) {
  background: #f7f9fc !important;
  color: #303133;
  font-weight: 600;
  font-size: 13px;
}
.voucher-table :deep(.el-table__row:hover > td) {
  background: #ecf5ff !important;
}
.row-expanded > td {
  background: #fafcff !important;
}

/* 展开/折叠箭头 */
.expand-toggle {
  cursor: pointer;
  color: #909399;
  transition: transform 0.2s;
  font-size: 14px;
}
.expand-toggle.is-open {
  transform: rotate(90deg);
  color: #409eff;
}

/* ---- 摘要单元格 ---- */
.summary-cell {
  padding: 4px 0;
}
.voucher-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 3px;
}
.voucher-tag {
  font-size: 12px;
  font-weight: 700;
  padding: 1px 7px;
  border-radius: 3px;
  white-space: nowrap;
}
.tag-记 { background: #ecf5ff; color: #409eff; border: 1px solid #b3d8ff; }
.tag-收 { background: #fdf6ec; color: #e6a23c; border: 1px solid #f5dab1; }
.tag-付 { background: #fef0f0; color: #f56c6c; border: 1px solid #fbc4c4; }
.tag-转 { background: #f4f4f5; color: #909399; border: 1px solid #dcdfe6; }
.voucher-date {
  font-size: 12px;
  color: #909399;
}
.status-tag {
  transform: scale(0.88);
  margin-left: auto;
}
.line-summary {
  font-size: 13px;
  color: #606266;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 260px;
}

/* ---- 科目单元格 ---- */
.account-cell {
  padding: 0;
}
.account-line {
  margin: 0;
  padding: 3px 0;
  font-size: 13px;
  color: #303133;
  line-height: 1.5;
}
.first-line {
  /* 第一行无特殊样式 */
}
.account-code {
  font-family: Consolas, monospace;
  font-size: 11px;
  color: #909399;
  margin-left: 6px;
}

/* ---- 金额单元格 ---- */
.amount-col {
  font-family: 'Consolas', 'Monaco', monospace;
}
.amount-line {
  margin: 0;
  padding: 3px 0;
  font-size: 13px;
  color: #c0c4cc;
}
.amount-line.has-value {
  color: #303133;
  font-weight: 500;
}
.amount-total {
  margin: 6px 0 2px;
  padding-top: 4px;
  border-top: 1px dashed #ebeef5;
  font-weight: 700;
  font-size: 13px;
}
.debit-total { color: #e6a23c; }
.credit-total { color: #67c23a; }

/* ====== 展开详情面板 ====== */
.detail-panel {
  background: #fbfdff;
  padding: 0 24px 12px;
}
.detail-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  margin-top: 8px;
}
.detail-table thead th {
  background: #f2f5fa;
  border: 1px solid #e4e7ed;
  padding: 8px 10px;
  font-weight: 600;
  color: #606266;
  text-align: left;
  font-size: 12px;
}
.detail-table tbody td {
  border: 1px solid #eef0f3;
  padding: 8px 10px;
  color: #303133;
  vertical-align: middle;
}
.dt-seq {
  text-align: center;
  color: #909399;
  font-size: 12px;
}
.code-text {
  font-family: Consolas, monospace;
  font-size: 12px;
  color: #909399;
  background: #f5f7fa;
  padding: 1px 5px;
  border-radius: 3px;
}
.amt-debit { color: #e6a23c; font-weight: 500; }
.amt-credit { color: #67c23a; font-weight: 500; }

.detail-total-row td {
  background: #fffbf0;
  border-color: #f5e6c8;
  font-weight: 700;
  padding: 8px 10px;
}
.dt-label { color: #606266; }
.dt-debit-total { color: #e6a23c; }
.dt-credit-total { color: #67c23a; }

.detail-footer {
  display: flex;
  gap: 20px;
  padding: 8px 0 4px;
  font-size: 12px;
  color: #909399;
  border-top: 1px dashed #e4e7ed;
  margin-top: 8px;
}
.detail-footer strong {
  color: #303133;
}

/* 分页 */
.pagination-bar {
  display: flex;
  justify-content: flex-end;
  padding: 12px 16px;
  border-top: 1px solid #ebeef5;
  flex-shrink: 0;
}

/* 响应式 */
@media (max-width: 900px) {
  .toolbar { flex-direction: column; align-items: stretch; }
  .toolbar-left, .toolbar-right { justify-content: flex-start; flex-wrap: wrap; }
  .search-box { width: 100% !important; }
  .date-picker { width: 100% !important; }
}
</style>
