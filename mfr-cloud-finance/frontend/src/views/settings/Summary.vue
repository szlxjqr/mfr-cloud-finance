<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Refresh,
  Setting,
  QuestionFilled,
  Document,
  Delete,
} from '@element-plus/icons-vue'

/** 凭证摘要记录 */
interface SummaryRecord {
  id: string
  code: string   // 编号
  name: string   // 名称
}

let _seq = 0
function genId(): string {
  _seq += 1
  return `sum_${Date.now().toString(36)}_${_seq}`
}

/** 默认数据：与截图一致 */
const rows = reactive<SummaryRecord[]>([
  { id: genId(), code: '01', name: '提取现金' },
  { id: genId(), code: '02', name: '发放工资' },
  { id: genId(), code: '03', name: '付材料款' },
  { id: genId(), code: '04', name: '销售收入' },
  { id: genId(), code: '05', name: '提取费用' },
  { id: genId(), code: '06', name: '差旅费' },
  { id: genId(), code: '07', name: '电话费' },
  { id: genId(), code: '08', name: '交通费' },
  { id: genId(), code: '09', name: '收到沈雷实缴资本金' },
])

/** 搜索关键字 */
const keyword = ref('')
const filteredRows = computed<SummaryRecord[]>(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return rows
  return rows.filter(
    (r) =>
      r.code.toLowerCase().includes(kw) ||
      r.name.toLowerCase().includes(kw),
  )
})

/** 计算下一个编号（按最大数字补 2 位） */
const nextCode = computed<string>(() => {
  let max = 0
  rows.forEach((r) => {
    const n = Number.parseInt(r.code, 10)
    if (!Number.isNaN(n) && n > max) max = n
  })
  return String(max + 1).padStart(2, '0')
})

/** 新增行模型 */
const newRow = reactive<SummaryRecord>({ id: '', code: nextCode.value, name: '' })
function resetNewRow() {
  newRow.code = nextCode.value
  newRow.name = ''
  newRow.id = ''
}

/** 表格显示的数据：现有记录 + 最后一行新增空行 */
const tableRows = computed<SummaryRecord[]>(() => [...filteredRows.value, { id: '__new__', code: '', name: '' }])

function addRow() {
  const code = newRow.code.trim()
  const name = newRow.name.trim()
  if (!code && !name) return
  if (!name) {
    ElMessage.warning('请输入摘要名称')
    return
  }
  rows.push({ id: genId(), code: code || nextCode.value, name })
  ElMessage.success('已新增')
  resetNewRow()
}

function deleteRow(row: SummaryRecord) {
  ElMessageBox.confirm(`确定删除摘要「${row.name}」吗？`, '删除确认', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(() => {
      const idx = rows.findIndex((r) => r.id === row.id)
      if (idx >= 0) rows.splice(idx, 1)
      ElMessage.success('已删除')
    })
    .catch(() => {})
}

function handleNewRowNameEnter(e: KeyboardEvent) {
  e.preventDefault()
  addRow()
}

function handleNewRowNameBlur() {
  if (newRow.name.trim()) addRow()
}

function handleNewRowCodeEnter(e: KeyboardEvent) {
  e.preventDefault()
  if (newRow.name.trim()) addRow()
}

function handleNewRowCodeBlur() {
  if (!newRow.code.trim()) newRow.code = nextCode.value
}

function handleRefresh() {
  keyword.value = ''
  ElMessage.success('已刷新')
}

function showHelp() {
  ElMessageBox.alert(
    '凭证摘要用于维护凭证中常用的摘要短语，便于录入凭证时快速选择：\n\n' +
      '• 编号：摘要顺序号，自动递增\n' +
      '• 名称：凭证摘要内容，如「提取现金」「发放工资」\n\n' +
      '在最后一行空白处输入编号和名称，按回车或失焦即可新增；点击行内删除按钮可删除对应摘要。',
    '凭证摘要说明',
    { confirmButtonText: '知道了' },
  )
}
</script>

<template>
  <div class="summary-page">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <div class="page-title">
          <el-icon><Document /></el-icon>
          <span>凭证摘要</span>
        </div>
        <el-input
          v-model="keyword"
          placeholder="请输入编号或摘要名称"
          clearable
          class="search-input"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <span class="count-tip">共 {{ filteredRows.length }} 条</span>
      </div>
      <div class="toolbar-right">
        <el-button text circle title="帮助" @click="showHelp">
          <el-icon><QuestionFilled /></el-icon>
        </el-button>
        <el-button text circle title="刷新" @click="handleRefresh">
          <el-icon><Refresh /></el-icon>
        </el-button>
        <el-button text circle title="设置">
          <el-icon><Setting /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 摘要表格 -->
    <div class="table-wrap">
      <el-table
        :data="tableRows"
        border
        size="small"
        :header-cell-style="{ background: '#f5f7fa', color: '#303133', fontWeight: 600 }"
        height="100%"
      >
        <el-table-column label="编号" width="120" align="center">
          <template #default="{ row }">
            <template v-if="row.id === '__new__'">
              <el-input
                v-model="newRow.code"
                placeholder="编号"
                size="small"
                @keyup.enter="handleNewRowCodeEnter"
                @blur="handleNewRowCodeBlur"
              />
            </template>
            <span v-else class="cell-text">{{ row.code }}</span>
          </template>
        </el-table-column>

        <el-table-column label="名称" min-width="240">
          <template #default="{ row }">
            <template v-if="row.id === '__new__'">
              <el-input
                v-model="newRow.name"
                placeholder="请输入摘要名称"
                size="small"
                @keyup.enter="handleNewRowNameEnter"
                @blur="handleNewRowNameBlur"
              />
            </template>
            <span v-else class="cell-text">{{ row.name }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="100" align="center">
          <template #default="{ row }">
            <el-button
              v-if="row.id !== '__new__'"
              text
              type="danger"
              size="small"
              @click="deleteRow(row)"
            >
              <el-icon><Delete /></el-icon>删除
            </el-button>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>

        <template #empty>
          <el-empty description="暂无凭证摘要" :image-size="80" />
        </template>
      </el-table>
    </div>
  </div>
</template>

<style scoped>
.summary-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 12px 16px 0;
  box-sizing: border-box;
  background: #fff;
  overflow: hidden;
}
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 0 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  gap: 12px;
  flex-wrap: wrap;
}
.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}
.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}
.page-title .el-icon {
  color: var(--el-color-primary);
}
.search-input {
  width: 280px;
}
.count-tip {
  color: #909399;
  font-size: 13px;
}
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.table-wrap {
  flex: 1;
  min-height: 0;
}
.cell-text {
  color: var(--el-text-color-primary);
}
.muted {
  color: #c0c4cc;
}
:deep(.el-table .el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--el-input-border-color) inset;
}
</style>
