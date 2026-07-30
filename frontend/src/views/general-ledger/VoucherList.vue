<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { listVouchers, syncVouchers } from '@/api/ledger'
import { auditVoucher, postVoucher, unpostVoucher, unauditVoucher } from '@/api/voucher'
import type { Voucher } from '@/types/ledger'

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

/** 凭证列表（来自后端，业务单审批通过自动生成） */
const vouchers = ref<VoucherItem[]>([])

/** 后端 Voucher → 前端 VoucherItem 映射 */
function toItem(v: Voucher): VoucherItem {
  const lines = (v.entries || []).map(e => ({
    summary: e.summary || '',
    accountName: e.subject_name,
    accountCode: e.subject_code,
    debitAmount: e.direction === '借' ? e.amount : 0,
    creditAmount: e.direction === '贷' ? e.amount : 0,
  }))
  const totalDebit = lines.reduce((s, l) => s + l.debitAmount, 0)
  const totalCredit = lines.reduce((s, l) => s + l.creditAmount, 0)
  const statusMap: Record<string, 'draft' | 'audited' | 'posted'> = {
    '未审核': 'draft', '已审核': 'audited', '已记账': 'posted',
  }
  return {
    id: String(v.id),
    word: v.voucher_word,
    number: v.seq,
    date: v.date,
    period: v.period,
    attachmentCount: v.attach_count,
    status: statusMap[v.status] || 'draft',
    creator: v.maker || '',
    auditor: '',
    remark: v.summary || '',
    expanded: false,
    totalDebit,
    totalCredit,
    lines,
  }
}

async function loadData() {
  loading.value = true
  try {
    const res = await listVouchers()
    vouchers.value = res.data.map(toItem)
  } catch (e) {
    ElMessage.error('加载凭证失败')
  } finally {
    loading.value = false
  }
}

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
  loadData()
}

/** 一键联动：把「已通过」的报销单/采购申请补生成凭证 */
async function handleSync() {
  try {
    const r = await syncVouchers()
    const res = r.data
    ElMessage.success(`联动生成凭证 ${res.generated} 张，跳过 ${res.skipped} 张`)
    if (res.detail.length) console.log('[凭证联动]', res.detail)
    await loadData()
  } catch (e) {
    ElMessage.error('联动生成失败')
  }
}

/** 单行审核：未审核 → 已审核 */
async function handleRowAudit(row: VoucherItem) {
  try {
    await auditVoucher(Number(row.id))
    ElMessage.success(`凭证 ${row.word}字${String(row.number).padStart(3, '0')}号 已审核`)
    await loadData()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '审核失败')
  }
}

/** 单行记账：已审核 → 已记账 */
async function handleRowPost(row: VoucherItem) {
  try {
    await postVoucher(Number(row.id))
    ElMessage.success(`凭证 ${row.word}字${String(row.number).padStart(3, '0')}号 已记账`)
    await loadData()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '记账失败（请先审核）')
  }
}

/** 单行反记账：已记账 → 已审核（释放记账锁定，仍在账簿） */
async function handleRowUnpost(row: VoucherItem) {
  try {
    await unpostVoucher(Number(row.id))
    ElMessage.success(`凭证 ${row.word}字${String(row.number).padStart(3, '0')}号 已反记账`)
    await loadData()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '反记账失败')
  }
}

/** 单行反审核：已审核 → 未审核（拉出账簿） */
async function handleRowUnaudit(row: VoucherItem) {
  try {
    await unauditVoucher(Number(row.id))
    ElMessage.success(`凭证 ${row.word}字${String(row.number).padStart(3, '0')}号 已反审核（移出账簿）`)
    await loadData()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '反审核失败（已记账请先反记账）')
  }
}

/** 批量审核选中的凭证（已审核/已记账幂等跳过） */
async function batchAudit() {
  if (selectedCount.value === 0) {
    ElMessage.warning('请先选择凭证')
    return
  }
  try {
    await ElMessageBox.confirm(`确定审核选中的 ${selectedCount.value} 张凭证？`, '批量审核', { type: 'warning' })
  } catch {
    return
  }
  let ok = 0
  for (const id of selectedIds.value) {
    try {
      await auditVoucher(Number(id))
      ok++
    } catch (e: any) {
      ElMessage.error((e?.response?.data?.detail || '审核失败') + '：#' + id)
    }
  }
  if (ok) ElMessage.success(`已审核 ${ok} 张`)
  await loadData()
}

/** 批量记账选中的凭证（仅已审核生效，未审核会被后端拦截） */
async function batchPost() {
  if (selectedCount.value === 0) {
    ElMessage.warning('请先选择凭证')
    return
  }
  try {
    await ElMessageBox.confirm(`确定记选中 ${selectedCount.value} 张凭证的账？`, '批量记账', { type: 'warning' })
  } catch {
    return
  }
  let ok = 0
  for (const id of selectedIds.value) {
    try {
      await postVoucher(Number(id))
      ok++
    } catch (e: any) {
      ElMessage.error((e?.response?.data?.detail || '记账失败') + '：#' + id)
    }
  }
  if (ok) ElMessage.success(`已记账 ${ok} 张`)
  await loadData()
}

/** 批量反记账选中的凭证（仅已记账生效） */
async function batchUnpost() {
  if (selectedCount.value === 0) {
    ElMessage.warning('请先选择凭证')
    return
  }
  try {
    await ElMessageBox.confirm(`确定反记账选中的 ${selectedCount.value} 张凭证？`, '批量反记账', { type: 'warning' })
  } catch {
    return
  }
  let ok = 0
  for (const id of selectedIds.value) {
    try {
      await unpostVoucher(Number(id))
      ok++
    } catch (e: any) {
      ElMessage.error((e?.response?.data?.detail || '反记账失败') + '：#' + id)
    }
  }
  if (ok) ElMessage.success(`已反记账 ${ok} 张`)
  await loadData()
}

/** 批量反审核选中的凭证（已记账须先反记账） */
async function batchUnaudit() {
  if (selectedCount.value === 0) {
    ElMessage.warning('请先选择凭证')
    return
  }
  try {
    await ElMessageBox.confirm(`确定反审核选中的 ${selectedCount.value} 张凭证？`, '批量反审核', { type: 'warning' })
  } catch {
    return
  }
  let ok = 0
  for (const id of selectedIds.value) {
    try {
      await unauditVoucher(Number(id))
      ok++
    } catch (e: any) {
      ElMessage.error((e?.response?.data?.detail || '反审核失败') + '：#' + id)
    }
  }
  if (ok) ElMessage.success(`已反审核 ${ok} 张（移出账簿）`)
  await loadData()
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
  loadData()
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
          <el-button plain>筛选<AppIcon class="el-icon--right" name="ArrowDown" /></el-button>
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

        <el-button type="success" @click="handleSync" title="把已通过的报销单/采购单补生成凭证">一键联动生成</el-button>
        <el-button type="primary" @click="goNew">新增</el-button>

        <el-dropdown trigger="click" @command="handleImport">
          <el-button plain>导入<AppIcon class="el-icon--right" name="ArrowDown" /></el-button>
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

      <el-button text size="small" @click="batchAudit">
        <AppIcon style="margin-right:2px" name="Select" />审核
      </el-button>
      <el-button text size="small" @click="batchPost">
        <AppIcon style="margin-right:2px" name="Stamp" />记账
      </el-button>
      <el-button text size="small" @click="batchUnpost">
        <AppIcon style="margin-right:2px" name="Back" />反记账
      </el-button>
      <el-button text size="small" @click="batchUnaudit">
        <AppIcon style="margin-right:2px" name="RefreshLeft" />反审核
      </el-button>

      <el-dropdown trigger="click" @command="(cmd: string) => handlePrint(cmd as any)">
        <el-button text size="small">
          打印<AppIcon class="el-icon--right" name="ArrowDown" />
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
          导出<AppIcon class="el-icon--right" name="ArrowDown" />
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
        <AppIcon style="margin-right:2px" name="Delete" />删除
      </el-button>
    </div>

    <!-- ====== 数据表格 ====== -->
    <div class="table-area">
      <DataLoader :loading="loading" :is-empty="!vouchers.length">
        <el-table
          :data="vouchers"
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
            <AppIcon
              class="expand-toggle"
              :class="{ 'is-open': row.expanded }"
              @click.stop="toggleExpand(row)"
             name="component" />
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

        <!-- 操作列：状态感知的审核 / 记账 / 反向 -->
        <el-table-column label="操作" width="170" fixed="right">
          <template #default="{ row }: { row: VoucherItem }">
            <el-button
              v-if="row.status === 'draft'"
              size="small"
              type="primary"
              @click="handleRowAudit(row)"
            >审核</el-button>
            <template v-else-if="row.status === 'audited'">
              <el-button size="small" type="success" @click="handleRowPost(row)">记账</el-button>
              <el-button size="small" plain @click="handleRowUnaudit(row)">反审核</el-button>
            </template>
            <el-button
              v-else
              size="small"
              type="warning"
              plain
              @click="handleRowUnpost(row)"
            >反记账</el-button>
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
      </DataLoader>
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
  border-bottom: 1px solid var(--border-soft);
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
  border-bottom: 1px solid var(--bg-subtle);
  gap: 4px;
  font-size: 13px;
  color: var(--text-base);
  flex-shrink: 0;
}
.select-count strong {
  color: var(--el-color-primary);
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
  color: var(--text-strong);
  font-weight: 600;
  font-size: 13px;
}
.voucher-table :deep(.el-table__row:hover > td) {
  background: var(--el-color-primary-light-9) !important;
}
.row-expanded > td {
  background: #fafcff !important;
}

/* 展开/折叠箭头 */
.expand-toggle {
  cursor: pointer;
  color: var(--text-muted);
  transition: transform 0.2s;
  font-size: 14px;
}
.expand-toggle.is-open {
  transform: rotate(90deg);
  color: var(--el-color-primary);
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
.tag-记 { background: var(--el-color-primary-light-9); color: var(--el-color-primary); border: 1px solid var(--el-color-primary-light-5); }
.tag-收 { background: #fdf6ec; color: var(--warning); border: 1px solid #f5dab1; }
.tag-付 { background: #fef0f0; color: var(--danger); border: 1px solid #fbc4c4; }
.tag-转 { background: #f4f4f5; color: var(--text-muted); border: 1px solid var(--border-soft); }
.voucher-date {
  font-size: 12px;
  color: var(--text-muted);
}
.status-tag {
  transform: scale(0.88);
  margin-left: auto;
}
.line-summary {
  font-size: 13px;
  color: var(--text-base);
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
  color: var(--text-strong);
  line-height: 1.5;
}
.first-line {
  /* 第一行无特殊样式 */
}
.account-code {
  font-family: Consolas, monospace;
  font-size: 11px;
  color: var(--text-muted);
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
  color: var(--border-soft);
}
.amount-line.has-value {
  color: var(--text-strong);
  font-weight: 500;
}
.amount-total {
  margin: 6px 0 2px;
  padding-top: 4px;
  border-top: 1px dashed var(--border-soft);
  font-weight: 700;
  font-size: 13px;
}
.debit-total { color: var(--warning); }
.credit-total { color: var(--success); }

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
  border: 1px solid var(--border-soft);
  padding: 8px 10px;
  font-weight: 600;
  color: var(--text-base);
  text-align: left;
  font-size: 12px;
}
.detail-table tbody td {
  border: 1px solid #eef0f3;
  padding: 8px 10px;
  color: var(--text-strong);
  vertical-align: middle;
}
.dt-seq {
  text-align: center;
  color: var(--text-muted);
  font-size: 12px;
}
.code-text {
  font-family: Consolas, monospace;
  font-size: 12px;
  color: var(--text-muted);
  background: #f5f7fa;
  padding: 1px 5px;
  border-radius: 3px;
}
.amt-debit { color: var(--warning); font-weight: 500; }
.amt-credit { color: var(--success); font-weight: 500; }

.detail-total-row td {
  background: #fffbf0;
  border-color: #f5e6c8;
  font-weight: 700;
  padding: 8px 10px;
}
.dt-label { color: var(--text-base); }
.dt-debit-total { color: var(--warning); }
.dt-credit-total { color: var(--success); }

.detail-footer {
  display: flex;
  gap: 20px;
  padding: 8px 0 4px;
  font-size: 12px;
  color: var(--text-muted);
  border-top: 1px dashed var(--border-soft);
  margin-top: 8px;
}
.detail-footer strong {
  color: var(--text-strong);
}

/* 分页 */
.pagination-bar {
  display: flex;
  justify-content: flex-end;
  padding: 12px 16px;
  border-top: 1px solid var(--border-soft);
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
