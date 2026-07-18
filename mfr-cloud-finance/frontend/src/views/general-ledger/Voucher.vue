<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

/* ==================== 类型定义 ==================== */

/** 凭证行数据 */
interface VoucherLine {
  id: number
  sequence: number        // 序号
  summary: string         // 摘要
  accountCode: string     // 科目编码（用于展示和提交）
  accountName: string     // 科目名称
  debitAmount: string     // 借方金额字符串（如 "10000.00"）
  creditAmount: string    // 贷方金额字符串
}

/** 凭证头部信息 */
interface VoucherHeader {
  word: string            // 凭证字：记 / 收 / 付 / 转
  number: number          // 凭证号
  date: string            // 凭证日期 YYYY-MM-DD
  period: string          // 会计期间，如 "2026年05期"
  attachmentCount: number // 附单据张数
  remark: string          // 备注
}

/* ==================== 状态 ==================== */

/** 凭证头 */
const header = reactive<VoucherHeader>({
  word: '记',
  number: 1,
  date: '2026-05-01',
  period: '2026年05期',
  attachmentCount: 0,
  remark: '',
})

/** 凭证行 — 默认4行空行 */
const lines = reactive<VoucherLine[]>(Array.from({ length: 4 }, (_, i) => ({
  id: i + 1,
  sequence: i + 1,
  summary: '',
  accountCode: '',
  accountName: '',
  debitAmount: '',
  creditAmount: '',
})))

/** 搜索关键字 */
const searchKeyword = ref('')

/* ==================== 计算属性 ==================== */

/** 借方合计 */
const totalDebit = computed(() => {
  return lines.reduce((sum, line) => {
    const val = parseFloat(line.debitAmount) || 0
    return sum + val
  }, 0).toFixed(2)
})

/** 贷方合计 */
const totalCredit = computed(() => {
  return lines.reduce((sum, line) => {
    const val = parseFloat(line.creditAmount) || 0
    return sum + val
  }, 0).toFixed(2)
})

/** 是否借贷平衡 */
const isBalanced = computed(() => totalDebit.value === totalCredit.value)

/** 金额列标题（借方/贷方共用）*/
const amountColumns = ['千', '百', '十', '亿', '千', '百', '十', '万', '千', '百', '十', '元', '角', '分']

/* ==================== 方法 ==================== */

/** 新增一行 */
function addLine() {
  const nextSeq = lines.length + 1
  lines.push({
    id: Date.now(),
    sequence: nextSeq,
    summary: '',
    accountCode: '',
    accountName: '',
    debitAmount: '',
    creditAmount: '',
  })
}

/** 删除最后一行（至少保留1行） */
function removeLastLine() {
  if (lines.length > 1) {
    lines.pop()
    renumberLines()
  }
}

/** 重编序号 */
function renumberLines() {
  lines.forEach((line, idx) => { line.sequence = idx + 1 })
}

/** 清空当前凭证 */
async function handleClear() {
  try {
    await ElMessageBox.confirm('确定要清空当前凭证内容吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    lines.forEach(line => {
      line.summary = ''
      line.accountCode = ''
      line.accountName = ''
      line.debitAmount = ''
      line.creditAmount = ''
    })
    ElMessage.success('已清空')
  } catch {
    // 取消操作
  }
}

/** 保存凭证 */
function handleSave() {
  if (!validateVoucher()) return
  ElMessage.success(`凭证已保存 — 记字第${String(header.number).padStart(3, '0')}号`)
}

/** 保存并新增 */
function handleSaveAndNew() {
  if (!validateVoucher()) return
  ElMessage.success(`凭证已保存，正在新建…`)
  // TODO: 调用保存API → 成功后清空表单、凭证号+1
}

/** 保存并打印 */
function handleSaveAndPrint() {
  if (!validateVoucher()) return
  ElMessage.info('正在生成打印预览…')
  // TODO: 打开打印窗口
}

/** 校验凭证 */
function validateVoucher(): boolean {
  // 至少有一行有内容
  const hasContent = lines.some(
    l => l.summary.trim() || l.accountName.trim() || l.debitAmount || l.creditAmount
  )
  if (!hasContent) {
    ElMessage.warning('请至少录入一条分录')
    return false
  }
  // 借贷检查
  if (totalDebit.value !== '0.00' && totalCredit.value !== '0.00' && !isBalanced.value) {
    ElMessage.error(`借贷不平衡！借方 ${totalDebit.value} ≠ 贷方 ${totalCredit.value}`)
    return false
  }
  return true
}

/** 科目选择弹窗（占位） */
function openAccountSelector() {
  ElMessage.info('科目选择器开发中…')
}
</script>

<template>
  <div class="voucher-page">
    <!-- ====== 顶部工具栏 ====== -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索凭证编号"
          clearable
          :prefix-icon="'Search'"
          size="default"
          class="search-input"
        />
        <el-button plain>更多凭证</el-button>
      </div>

      <div class="toolbar-right">
        <el-button type="primary" @click="handleSave">保存(Ctrl+S)</el-button>
        <el-button type="primary" plain @click="handleSaveAndNew">保存并新增(F5)</el-button>
        <el-button plain @click="handleSaveAndPrint">保存并打印</el-button>
        <el-button text @click="handleClear">清除</el-button>

        <el-dropdown trigger="click">
          <el-button text>更多<el-icon class="el-icon--right"><ArrowDown /></el-icon></el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="addLine">插入行</el-dropdown-item>
              <el-dropdown-item @click="removeLastLine" :disabled="lines.length <= 1">删除末行</el-dropdown-item>
              <el-dropdown-item divided>导入凭证</el-dropdown-item>
              <el-dropdown-item>导出凭证</el-dropdown-item>
              <el-dropdown-item divided>审核</el-dropdown-item>
              <el-dropdown-item>反审核</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <!-- 导航箭头 -->
        <el-button-group class="nav-arrows">
          <el-button text :icon="'ArrowLeft'" title="上一张"></el-button>
          <el-button text :icon="'ArrowRight'" title="下一张"></el-button>
        </el-button-group>

        <el-button text circle :icon="'Setting'" title="设置"></el-button>
      </div>
    </div>

    <!-- ====== 凭证主体 ====== -->
    <div class="voucher-body">
      <!-- 凭证头信息栏 -->
      <div class="voucher-header">
        <div class="header-left">
          <span class="header-label">凭证字：</span>
          <el-select v-model="header.word" size="small" style="width: 80px">
            <el-option label="记" value="记" />
            <el-option label="收" value="收" />
            <el-option label="付" value="付" />
            <el-option label="转" value="转" />
          </el-select>

          <span class="header-label" style="margin-left: 20px;">号</span>
          <el-input-number
            v-model="header.number"
            :min="1"
            :controls="false"
            size="small"
            style="width: 70px"
          />

          <span class="header-label" style="margin-left: 20px;">日期：</span>
          <el-date-picker
            v-model="header.date"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            size="small"
            style="width: 150px"
          />
        </div>

        <div class="header-center">
          <h2 class="voucher-title">
            记账凭证
            <el-icon class="title-edit-icon"><EditPen /></el-icon>
          </h2>
          <span class="period-text">{{ header.period }}</span>
        </div>

        <div class="header-right">
          <span class="header-label">附单据：</span>
          <el-input-number
            v-model="header.attachmentCount"
            :min="0"
            :controls="false"
            size="small"
            style="width: 60px"
          />
          <el-link :underline="false" class="attachment-link">
            <el-icon><Paperclip /></el-icon>
          </el-link>
        </div>
      </div>

      <!-- 分录表格 -->
      <div class="table-wrapper">
        <table class="voucher-table">
          <thead>
            <tr>
              <th class="col-seq">序号</th>
              <th class="col-summary">
                摘要
                <el-icon class="th-icon"><Grid /></el-icon>
              </th>
              <th class="col-account">会计科目</th>
              <th class="col-amount-header" colspan="14">
                <span class="amount-side">借方</span>
              </th>
              <th class="col-amount-header" colspan="14">
                <span class="amount-side">贷方</span>
              </th>
            </tr>
            <tr class="sub-header">
              <th></th><th></th><th></th>
              <!-- 借方金额子列 -->
              <template v-for="(unit, ui) in amountColumns" :key="`d-${ui}`">
                <th class="col-amount-unit">{{ unit }}</th>
              </template>
              <!-- 贷方金额子列 -->
              <template v-for="(unit, ui) in amountColumns" :key="`c-${ui}`">
                <th class="col-amount-unit">{{ unit }}</th>
              </template>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(line, idx) in lines" :key="line.id" :class="{ 'row-active': idx === 0 }">
              <td class="cell-seq">{{ line.sequence }}</td>
              <td class="cell-summary">
                <input
                  v-model="line.summary"
                  type="text"
                  class="inline-input"
                  placeholder=""
                />
              </td>
              <td class="cell-account">
                <div class="account-cell" @click="openAccountSelector">
                  <input
                    v-model="line.accountName"
                    type="text"
                    class="inline-input account-input"
                    placeholder="点击选择科目"
                    readonly
                  />
                  <el-icon class="account-search-icon"><Search /></el-icon>
                </div>
              </td>
              <!-- 借方金额格子 -->
              <template v-for="(unit, ui) in amountColumns" :key="`dv-${idx}-${ui}`">
                <td :class="['cell-amount', { 'amount-red-line': unit === '元' }]">
                  <input
                    v-if="ui === amountColumns.length - 8 /* 元位列 */"
                    v-model="line.debitAmount"
                    type="text"
                    class="inline-input amount-input"
                    inputmode="decimal"
                  />
                </td>
              </template>
              <!-- 贷方金额格子 -->
              <template v-for="(unit, ui) in amountColumns" :key="`cv-${idx}-${ui}`">
                <td :class="['cell-amount', { 'amount-red-line': unit === '元' }]">
                  <input
                    v-if="ui === amountColumns.length - 8 /* 元位列 */"
                    v-model="line.creditAmount"
                    type="text"
                    class="inline-input amount-input"
                    inputmode="decimal"
                  />
                </td>
              </template>
            </tr>
          </tbody>
          <tfoot>
            <tr class="row-total">
              <td colspan="3" class="total-label">合计：</td>
              <!-- 借方合计 -->
              <td
                v-for="(_, ui) in amountColumns"
                :key="`dt-${ui}`"
                :class="['cell-amount', 'cell-total', { 'amount-red-line': amountColumns[ui] === '元' }]"
              >
                <span v-if="ui === amountColumns.length - 8" class="total-value">{{ totalDebit }}</span>
              </td>
              <!-- 贷方合计 -->
              <td
                v-for="(_, ui) in amountColumns"
                :key="`ct-${ui}`"
                :class="['cell-amount', 'cell-total', { 'amount-red-line': amountColumns[ui] === '元' }]"
              >
                <span v-if="ui === amountColumns.length - 8" class="total-value">{{ totalCredit }}</span>
              </td>
            </tr>
          </tfoot>
        </table>
      </div>

      <!-- 底部状态栏 -->
      <div class="voucher-footer">
        <div class="footer-left">
          <span :class="['balance-status', { balanced: isBalanced }]">
            {{ isBalanced ? '✓ 借贷平衡' : `⚠ 借贷差额: ${(parseFloat(totalDebit) - parseFloat(totalCredit)).toFixed(2)}` }}
          </span>
        </div>
        <div class="footer-right">
          <span class="footer-info">制单人：<strong>管理员</strong></span>
          <span class="footer-info">审核人：<em style="color:#c0c4cc">待审核</em></span>
          <span class="footer-info">记账：<em style="color:#c0c4cc">待记账</em></span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.voucher-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f5f7fa;
  border-radius: 8px;
  overflow: hidden;
}

/* ====== 工具栏 ====== */
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  flex-shrink: 0;
  gap: 12px;
}
.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.search-input {
  width: 200px !important;
}
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.nav-arrows .el-button {
  padding: 5px 8px !important;
}

/* ====== 凭证主体 ====== */
.voucher-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: auto;
  background: #fff;
  margin: 12px;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

/* ---- 凭证头 ---- */
.voucher-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 16px 24px 8px;
  border-bottom: 1px solid #f0f0f0;
  flex-shrink: 0;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 4px;
}
.header-label {
  color: #606266;
  font-size: 14px;
  white-space: nowrap;
}
.header-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}
.voucher-title {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
  margin: 0;
  letter-spacing: 2px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.title-edit-icon {
  font-size: 16px;
  color: #409eff;
  cursor: pointer;
}
.period-text {
  font-size: 13px;
  color: #909399;
  margin-top: 2px;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 4px;
}
.attachment-link {
  margin-left: 4px;
  color: #909399;
  cursor: pointer;
}

/* ---- 表格区域 ---- */
.table-wrapper {
  flex: 1;
  overflow: auto;
  padding: 0 16px 12px;
}

.voucher-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  font-size: 13px;
}

/* 表头 */
.voucher-table thead th {
  background: #f7f9fc;
  border: 1px solid #e4e7ed;
  padding: 10px 6px;
  font-weight: 600;
  color: #303133;
  text-align: center;
  position: sticky;
  top: 0;
  z-index: 2;
}
.sub-header th {
  background: #eff2f7;
  padding: 6px 2px;
  font-weight: 500;
  font-size: 12px;
  color: #606266;
  position: sticky;
  top: 41px; /* 第一行表头高度 */
  z-index: 1;
}
.th-icon {
  margin-left: 4px;
  color: #409eff;
  cursor: pointer;
  font-size: 13px;
}

/* 列宽定义 */
.col-seq       { width: 50px; }
.col-summary   { width: 180px; min-width: 140px; }
.col-account   { width: 200px; min-width: 150px; }
.col-amount-header { text-align: center; letter-spacing: 1px; }
.col-amount-unit { width: 24px; padding: 4px 1px !important; font-size: 11px; }

.amount-side {
  font-size: 14px;
  font-weight: 700;
  color: #303133;
}

/* 数据单元格 */
.voucher-table tbody td {
  border: 1px solid #e4e7ed;
  padding: 0;
  vertical-align: middle;
  height: 42px;
}
.row-active td {
  background: #fafcff;
}
.cell-seq {
  text-align: center;
  color: #409eff;
  font-weight: 600;
  font-size: 14px;
}
.cell-summary,
.cell-account {
  padding: 2px 6px;
}

/* 行内输入框 */
.inline-input {
  width: 100%;
  border: none;
  outline: none;
  background: transparent;
  font-size: 13px;
  color: #303133;
  padding: 4px 0;
  box-sizing: border-box;
}
.inline-input:focus {
  background: #ecf5ff;
  border-radius: 3px;
}
.inline-input::placeholder {
  color: #c0c4cc;
}

/* 科目单元格 */
.account-cell {
  display: flex;
  align-items: center;
  gap: 2px;
  cursor: pointer;
  padding-right: 4px;
}
.account-cell:hover {
  background: #f5f7fa;
  border-radius: 3px;
}
.account-input {
  flex: 1;
  cursor: pointer;
}
.account-search-icon {
  color: #c0c4cc;
  font-size: 14px;
  flex-shrink: 0;
}

/* 金额单元格 */
.cell-amount {
  text-align: right;
  padding: 0 1px !important;
  border-color: #e4e7ed;
  position: relative;
}
.amount-red-line::after {
  content: '';
  position: absolute;
  left: 0;
  top: 25%;
  bottom: 25%;
  width: 1px;
  background: #f56c6c;
}
.amount-input {
  text-align: right;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  color: #303133;
  padding-right: 4px;
}

/* 合计行 */
.row-total td {
  background: #fdfaf0;
  border-color: #f0e6ce;
  padding: 10px 4px;
  height: 38px;
  font-weight: 600;
}
.total-label {
  text-align: left !important;
  padding-left: 12px !important;
  color: #606266;
  font-size: 14px;
}
.cell-total {
  text-align: right;
}
.total-value {
  color: #e6a23c;
  font-weight: 700;
  font-size: 13px;
  font-family: 'Consolas', monospace;
}

/* ---- 底部状态栏 ---- */
.voucher-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 24px 12px;
  border-top: 1px solid #f0f0f0;
  font-size: 13px;
  flex-shrink: 0;
}
.balance-status {
  color: #f56c6c;
  font-weight: 600;
  font-size: 13px;
}
.balance-status.balanced {
  color: #67c23a;
}
.footer-right {
  display: flex;
  gap: 20px;
}
.footer-info {
  color: #909399;
}

/* 响应式 */
@media (max-width: 1200px) {
  .col-summary { width: 140px; }
  .col-account { width: 160px; }
}
@media (max-width: 900px) {
  .toolbar { flex-direction: column; align-items: stretch; }
  .toolbar-left, .toolbar-right { justify-content: flex-start; }
  .search-input { width: 100% !important; }
}
</style>
