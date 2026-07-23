<script setup lang="ts">
import { computed, reactive, ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  QuestionFilled,
  ArrowDown,
  Setting,
  Search,
  CircleCheckFilled,
  CircleCloseFilled,
} from '@element-plus/icons-vue'
import { listSubjects } from '@/api/ledger'
import type { AccountSubject } from '@/types/ledger'

/** 单个科目的期初余额数据 */
interface OpeningBalance {
  beginQty: number
  beginForeign: number
  beginBase: number
  debitQty: number
  debitForeign: number
  debitBase: number
  creditQty: number
  creditForeign: number
  creditBase: number
  yearBeginQty: number
  yearBeginForeign: number
  yearBeginBase: number
  rate: number
}
type BalanceField = keyof OpeningBalance

/** 表格行：原始科目 + 期初余额 */
interface OpeningRow {
  id: string
  code: string
  name: string
  category: string
  direction: '借' | '贷'
  foreignCurrency?: string
  unit?: string
  isLeaf: boolean
  balance: OpeningBalance
}

/** 分类顺序（界面显示） */
const CATEGORY_ORDER = ['资产', '负债', '权益', '成本', '损益'] as const

/** 演示用：部分资产科目的期初本位币预填，便于直观预览 */
const DEMO_SEED: Record<string, number> = {
  '1001': 5000,
  '1002': 200000,
  '1122': 30000,
  '1601': 120000,
}

/** 后端科目 → 期初余额行 */
function toRow(s: AccountSubject): OpeningRow {
  const seeded = DEMO_SEED[s.code] ?? 0
  return {
    id: String(s.id),
    code: s.code,
    name: s.name,
    category: s.category,
    direction: s.direction as '借' | '贷',
    foreignCurrency: undefined,
    unit: undefined,
    isLeaf: s.is_leaf,
    balance: {
      beginQty: 0,
      beginForeign: 0,
      beginBase: seeded,
      debitQty: 0,
      debitForeign: 0,
      debitBase: 0,
      creditQty: 0,
      creditForeign: 0,
      creditBase: 0,
      yearBeginQty: 0,
      yearBeginForeign: 0,
      yearBeginBase: 0,
      rate: 0,
    },
  }
}

const allRows = reactive<OpeningRow[]>([])
const loading = ref(false)

/** 拉取后端权威科目，初始化期初余额行（统一到后端单一数据源） */
async function loadSubjects() {
  loading.value = true
  try {
    const res = await listSubjects()
    const rows = res.data.map(toRow)
    allRows.splice(0, allRows.length, ...rows)
  } catch (e) {
    ElMessage.error('加载科目失败')
  } finally {
    loading.value = false
  }
}

/** 当前选中的分类（中文 label） */
const activeCategory = ref<string>('资产')
/** 搜索关键字 */
const keyword = ref('')
/** 启用期间 */
const period = ref<string>('2026-05')

/** 当前分类下的筛选行 */
const filteredRows = computed<OpeningRow[]>(() => {
  const kw = keyword.value.trim().toLowerCase()
  return allRows.filter((r) => {
    if (r.category !== activeCategory.value) return false
    if (!kw) return true
    return r.code.toLowerCase().includes(kw) || r.name.toLowerCase().includes(kw)
  })
})

/** 金额分组（表头第二层） */
const amountGroups = [
  { key: 'begin', label: '期初余额' },
  { key: 'debit', label: '借方累计' },
  { key: 'credit', label: '贷方累计' },
  { key: 'yearBegin', label: '年初余额' },
] as const

/** 金额子列（数量 / 原币 / 本位币） */
const subCols = [
  { label: '数量', sub: 'Qty', needField: 'unit' as const },
  { label: '原币', sub: 'Foreign', needField: 'foreignCurrency' as const },
  { label: '本位币', sub: 'Base', needField: undefined },
] as const

function fieldName(g: (typeof amountGroups)[number], s: (typeof subCols)[number]): BalanceField {
  return (g.key + s.sub) as BalanceField
}

/** 数字格式化（千分位，保留两位小数） */
function fmt(n: number): string {
  return n.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

/* ====== 试算平衡 ====== */
const trialVisible = ref(false)
interface TrialLine {
  category: string
  debit: number
  credit: number
}
const trialLines = ref<TrialLine[]>([])
const trialBalanced = ref(false)

function openTrial() {
  const lines: TrialLine[] = CATEGORY_ORDER.map((label) => {
    let debit = 0
    let credit = 0
    for (const r of allRows) {
      if (r.category !== label) continue
      const v = r.balance.beginBase
      if (r.direction === '借') debit += v
      else credit += v
    }
    return { category: label, debit, credit }
  })
  const totalDebit = lines.reduce((s, l) => s + l.debit, 0)
  const totalCredit = lines.reduce((s, l) => s + l.credit, 0)
  trialLines.value = lines
  // 浮点容差比较
  trialBalanced.value = Math.abs(totalDebit - totalCredit) < 0.005
  trialVisible.value = true
}

/** 试算平衡表格合计行 */
function trialSummary(param: { columns: any[]; data: any[] }): string[] {
  const { columns, data } = param
  const sums: string[] = []
  columns.forEach((col, i) => {
    if (i === 0) {
      sums[i] = '合计'
      return
    }
    const total = data.reduce((s, row) => s + (Number(row[col.property]) || 0), 0)
    sums[i] = total.toLocaleString('zh-CN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })
  })
  return sums
}

/* ====== 导出（当前分类 CSV） ====== */
function exportCsv() {
  const header = [
    '科目编号',
    '科目名称',
    '方向',
    '汇率',
    '外币名称',
    '期初数量',
    '期初原币',
    '期初本位币',
    '借方数量',
    '借方原币',
    '借方本位币',
    '贷方数量',
    '贷方原币',
    '贷方本位币',
    '年初数量',
    '年初原币',
    '年初本位币',
  ]
  const rows = filteredRows.value.map((r) => [
    r.code,
    r.name,
    r.direction,
    r.balance.rate,
    r.foreignCurrency ?? '',
    r.balance.beginQty,
    r.balance.beginForeign,
    r.balance.beginBase,
    r.balance.debitQty,
    r.balance.debitForeign,
    r.balance.debitBase,
    r.balance.creditQty,
    r.balance.creditForeign,
    r.balance.creditBase,
    r.balance.yearBeginQty,
    r.balance.yearBeginForeign,
    r.balance.yearBeginBase,
  ])
  const csv = [header, ...rows]
    .map((row) => row.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(','))
    .join('\n')
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `期初余额_${activeCategory.value}_${period.value}.csv`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('已导出当前分类期初余额')
}

/* ====== 帮助 / 设置 ====== */
function showHelp() {
  ElMessageBox.alert(
    '期初余额用于录入科目在启用期间的期初数据：\n\n' +
      '• 期初余额：科目启用时的结余（数量 / 原币 / 本位币）\n' +
      '• 借方累计 / 贷方累计：启用期间之前的累计发生额\n' +
      '• 年初余额：本会计年度初的结余\n\n' +
      '方向为「借」的科目余额填在借方，方向为「贷」的科目填在贷方。填完后点击「试算平衡」校验借贷是否相等。',
    '期初余额说明',
    { confirmButtonText: '知道了' },
  )
}
function showSetting() {
  ElMessage.info('列显示设置功能开发中')
}

onMounted(loadSubjects)
</script>

<template>
  <div class="opening-page">
    <!-- 顶部操作栏 -->
    <div class="toolbar">
      <el-tabs v-model="activeCategory" class="cat-tabs">
        <el-tab-pane v-for="c in CATEGORY_ORDER" :key="c" :label="c" :name="c" />
      </el-tabs>

      <div class="toolbar-right">
        <el-date-picker
          v-model="period"
          type="month"
          format="YYYY年MM月"
          value-format="YYYY-MM"
          placeholder="启用期间"
          class="period-picker"
        />
        <el-tooltip content="期初余额说明" placement="top">
          <el-button circle @click="showHelp">
            <el-icon><QuestionFilled /></el-icon>
          </el-button>
        </el-tooltip>
        <el-button type="primary" @click="openTrial">试算平衡</el-button>
        <el-dropdown trigger="click" @command="exportCsv">
          <el-button>
            导出<el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="csv">导出当前分类 (CSV)</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-tooltip content="列显示设置" placement="top">
          <el-button circle @click="showSetting">
            <el-icon><Setting /></el-icon>
          </el-button>
        </el-tooltip>
      </div>
    </div>

    <!-- 搜索栏 -->
    <div class="search-bar">
      <el-input
        v-model="keyword"
        placeholder="请输入科目编号或名称"
        clearable
        class="search-input"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <span class="count-tip">共 {{ filteredRows.length }} 条科目</span>
    </div>

    <!-- 主表格 -->
    <div class="table-wrap">
      <el-table
        :data="filteredRows"
        v-loading="loading"
        border
        stripe
        :max-height="'calc(100vh - 280px)'"
        :header-cell-style="{ background: '#f5f7fa', color: '#303133', fontWeight: 600 }"
        size="small"
      >
        <el-table-column prop="code" label="科目编号" width="100" fixed />
        <el-table-column prop="name" label="科目名称" min-width="160" fixed />
        <el-table-column prop="direction" label="方向" width="64" align="center" />
        <el-table-column label="汇率" width="92" align="center">
          <template #default="{ row }">
            <el-input-number
              v-model="row.balance.rate"
              :min="0"
              :max="9999"
              :precision="4"
              :controls="false"
              :disabled="!row.foreignCurrency"
              style="width: 100%"
            />
          </template>
        </el-table-column>
        <el-table-column prop="foreignCurrency" label="外币名称" width="96" align="center">
          <template #default="{ row }">
            <span v-if="row.foreignCurrency">{{ row.foreignCurrency }}</span>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>

        <el-table-column
          v-for="g in amountGroups"
          :key="g.key"
          :label="g.label"
          align="center"
        >
          <el-table-column
            v-for="s in subCols"
            :key="s.sub"
            :label="s.label"
            width="116"
            align="right"
          >
            <template #default="{ row }">
              <el-input-number
                v-model="row.balance[fieldName(g, s)]"
                :min="-1e12"
                :max="1e12"
                :precision="2"
                :controls="false"
                :disabled="s.needField ? !row[s.needField] : false"
                style="width: 100%"
              />
            </template>
          </el-table-column>
        </el-table-column>
      </el-table>
    </div>

    <!-- 试算平衡弹窗 -->
    <el-dialog v-model="trialVisible" title="试算平衡" width="520px">
      <el-table
        :data="trialLines"
        border
        size="small"
        :show-summary="true"
        :summary-method="trialSummary"
      >
        <el-table-column prop="category" label="分类" />
        <el-table-column prop="debit" label="期初借方" align="right">
          <template #default="{ row }">{{ fmt(row.debit) }}</template>
        </el-table-column>
        <el-table-column prop="credit" label="期初贷方" align="right">
          <template #default="{ row }">{{ fmt(row.credit) }}</template>
        </el-table-column>
      </el-table>
      <div class="trial-result" :class="trialBalanced ? 'ok' : 'bad'">
        <el-icon v-if="trialBalanced"><CircleCheckFilled /></el-icon>
        <el-icon v-else><CircleCloseFilled /></el-icon>
        <span v-if="trialBalanced">借贷平衡，期初数据正确。</span>
        <span v-else>借贷不平衡，请检查各科目期初余额。</span>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.opening-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 12px 16px 0;
  box-sizing: border-box;
}
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}
.cat-tabs {
  flex: 1;
  min-width: 320px;
}
.cat-tabs :deep(.el-tabs__header) {
  margin-bottom: 0;
}
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.period-picker {
  width: 140px;
}
.search-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 12px 0;
}
.search-input {
  width: 320px;
}
.count-tip {
  color: #909399;
  font-size: 13px;
}
.table-wrap {
  flex: 1;
  min-height: 0;
}
.muted {
  color: #c0c4cc;
}
.trial-result {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 14px;
  padding: 10px 14px;
  border-radius: 6px;
  font-weight: 600;
}
.trial-result.ok {
  color: #67c23a;
  background: #f0f9eb;
}
.trial-result.bad {
  color: #f56c6c;
  background: #fef0f0;
}
</style>
