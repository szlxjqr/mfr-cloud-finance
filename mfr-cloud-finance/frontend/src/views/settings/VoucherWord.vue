<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Refresh,
  Setting,
  QuestionFilled,
  DocumentChecked,
  Delete,
} from '@element-plus/icons-vue'

/** 凭证字记录 */
interface VoucherWordRecord {
  id: string
  code: string   // 编号
  word: string   // 凭证字
  name: string   // 名称
  enabled: boolean // 是否启用
}

let _seq = 0
function genId(): string {
  _seq += 1
  return `vw_${Date.now().toString(36)}_${_seq}`
}

/** 默认数据：与截图一致 */
const rows = reactive<VoucherWordRecord[]>([
  { id: genId(), code: '01', word: '记', name: '记账凭证', enabled: true },
  { id: genId(), code: '02', word: '收', name: '收款凭证', enabled: true },
  { id: genId(), code: '03', word: '付', name: '付款凭证', enabled: true },
  { id: genId(), code: '04', word: '现收', name: '现金收款凭证', enabled: true },
  { id: genId(), code: '05', word: '现付', name: '现金付款凭证', enabled: true },
  { id: genId(), code: '06', word: '银收', name: '银行收款凭证', enabled: true },
  { id: genId(), code: '07', word: '银付', name: '银行付款凭证', enabled: true },
  { id: genId(), code: '08', word: '现', name: '现金凭证', enabled: true },
  { id: genId(), code: '09', word: '银', name: '银行凭证', enabled: true },
  { id: genId(), code: '10', word: '转', name: '转账凭证', enabled: true },
])

/** 搜索关键字 */
const keyword = ref('')
const filteredRows = computed<VoucherWordRecord[]>(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return rows
  return rows.filter(
    (r) =>
      r.code.toLowerCase().includes(kw) ||
      r.word.toLowerCase().includes(kw) ||
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
const newRow = reactive<VoucherWordRecord>({
  id: '',
  code: nextCode.value,
  word: '',
  name: '',
  enabled: true,
})
function resetNewRow() {
  newRow.code = nextCode.value
  newRow.word = ''
  newRow.name = ''
  newRow.enabled = true
  newRow.id = ''
}

/** 表格显示的数据：现有记录 + 最后一行新增空行 */
const tableRows = computed<VoucherWordRecord[]>(() => [
  ...filteredRows.value,
  { id: '__new__', code: '', word: '', name: '', enabled: true },
])

function addRow() {
  const code = newRow.code.trim()
  const word = newRow.word.trim()
  const name = newRow.name.trim()
  if (!code && !word && !name) return
  if (!word || !name) {
    ElMessage.warning('请输入凭证字和名称')
    return
  }
  rows.push({
    id: genId(),
    code: code || nextCode.value,
    word,
    name,
    enabled: newRow.enabled,
  })
  ElMessage.success('已新增')
  resetNewRow()
}

function deleteRow(row: VoucherWordRecord) {
  ElMessageBox.confirm(`确定删除凭证字「${row.word} ${row.name}」吗？`, '删除确认', {
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

function handleNewRowEnter(e: KeyboardEvent) {
  e.preventDefault()
  addRow()
}

function handleNewRowBlur() {
  if (newRow.word.trim() || newRow.name.trim()) addRow()
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
    '凭证字用于维护凭证的类别前缀，如「记」「收」「付」「转」等：\n\n' +
      '• 编号：顺序号，自动递增\n' +
      '• 凭证字：凭证类别简称，通常 1~2 个汉字\n' +
      '• 名称：凭证字全称，如「记账凭证」「收款凭证」\n' +
      '• 是否启用：启用后可在凭证录入时选择该凭证字\n\n' +
      '在最后一行空白处输入编号、凭证字和名称，按回车或失焦即可新增；点击行内删除按钮可删除。',
    '凭证字说明',
    { confirmButtonText: '知道了' },
  )
}
</script>

<template>
  <div class="voucher-word-page">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <div class="page-title">
          <el-icon><DocumentChecked /></el-icon>
          <span>凭证字</span>
        </div>
        <el-input
          v-model="keyword"
          placeholder="请输入编号、凭证字或名称"
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

    <!-- 凭证字表格 -->
    <div class="table-wrap">
      <el-table
        :data="tableRows"
        border
        size="small"
        :header-cell-style="{ background: '#f5f7fa', color: '#303133', fontWeight: 600 }"
        height="100%"
      >
        <el-table-column label="编号" width="90" align="center">
          <template #default="{ row }">
            <template v-if="row.id === '__new__'">
              <el-input
                v-model="newRow.code"
                placeholder="编号"
                size="small"
                @keyup.enter="handleNewRowEnter"
                @blur="handleNewRowCodeBlur"
              />
            </template>
            <span v-else class="cell-text">{{ row.code }}</span>
          </template>
        </el-table-column>

        <el-table-column label="凭证字" width="120" align="center">
          <template #default="{ row }">
            <template v-if="row.id === '__new__'">
              <el-input
                v-model="newRow.word"
                placeholder="凭证字"
                size="small"
                @keyup.enter="handleNewRowEnter"
                @blur="handleNewRowBlur"
              />
            </template>
            <span v-else class="cell-text">{{ row.word }}</span>
          </template>
        </el-table-column>

        <el-table-column label="名称" min-width="240">
          <template #default="{ row }">
            <template v-if="row.id === '__new__'">
              <el-input
                v-model="newRow.name"
                placeholder="请输入名称"
                size="small"
                @keyup.enter="handleNewRowEnter"
                @blur="handleNewRowBlur"
              />
            </template>
            <span v-else class="cell-text">{{ row.name }}</span>
          </template>
        </el-table-column>

        <el-table-column label="是否启用" width="100" align="center">
          <template #default="{ row }">
            <template v-if="row.id === '__new__'">
              <el-switch
                v-model="newRow.enabled"
                active-text="开"
                inactive-text="关"
                inline-prompt
              />
            </template>
            <el-switch v-else v-model="row.enabled" inline-prompt />
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
          <el-empty description="暂无凭证字数据" :image-size="80" />
        </template>
      </el-table>
    </div>
  </div>
</template>

<style scoped>
.voucher-word-page {
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
