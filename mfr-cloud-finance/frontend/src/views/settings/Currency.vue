<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  Plus,
  Edit,
  Delete,
  Download,
  Upload,
  Search,
  Refresh,
  Setting,
  QuestionFilled,
  ArrowDown,
  Money,
} from '@element-plus/icons-vue'

/** 币别记录 */
interface CurrencyRecord {
  id: string
  code: string        // 编码
  name: string        // 名称
  rate: number        // 汇率
  isBase: boolean     // 是否本位币
  isSealed: boolean   // 是否封存
}

let _seq = 0
function genId(): string {
  _seq += 1
  return `cur_${Date.now().toString(36)}_${_seq}`
}

/** 默认数据：与截图一致 */
const rows = reactive<CurrencyRecord[]>([
  { id: genId(), code: 'RMB', name: '人民币', rate: 1, isBase: true, isSealed: false },
  { id: genId(), code: 'USD', name: '美元', rate: 6.2655, isBase: false, isSealed: false },
])

/** 搜索关键字 */
const keyword = ref('')
const filteredRows = computed<CurrencyRecord[]>(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return rows
  return rows.filter(
    (r) =>
      r.code.toLowerCase().includes(kw) ||
      r.name.toLowerCase().includes(kw) ||
      r.rate.toString().includes(kw),
  )
})

/** 选中行 */
const selectedIds = ref<Set<string>>(new Set())
function isSelected(id: string): boolean {
  return selectedIds.value.has(id)
}
function toggleSelect(row: CurrencyRecord, e: Event) {
  e.stopPropagation()
  if (selectedIds.value.has(row.id)) selectedIds.value.delete(row.id)
  else selectedIds.value.add(row.id)
}
function onRowClick(row: CurrencyRecord) {
  if (selectedIds.value.has(row.id)) selectedIds.value.delete(row.id)
  else selectedIds.value.add(row.id)
}

/* ============ 新增 / 编辑 弹窗 ============ */
const dialogVisible = ref(false)
const dialogMode = ref<'add' | 'edit'>('add')
const formRef = ref<FormInstance>()
const formModel = reactive<CurrencyRecord>({
  id: '',
  code: '',
  name: '',
  rate: 1,
  isBase: false,
  isSealed: false,
})

const rules: FormRules = {
  code: [{ required: true, message: '请输入编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
}

function resetForm() {
  Object.assign(formModel, { id: '', code: '', name: '', rate: 1, isBase: false, isSealed: false })
}

function openAdd() {
  dialogMode.value = 'add'
  resetForm()
  dialogVisible.value = true
  formRef.value?.clearValidate()
}

function openEdit(row?: CurrencyRecord) {
  const target =
    row ?? (selectedIds.value.size === 1 ? rows.find((r) => r.id === [...selectedIds.value][0]) : undefined)
  if (!target) {
    ElMessage.warning('请先勾选一条币别记录再编辑')
    return
  }
  dialogMode.value = 'edit'
  Object.assign(formModel, JSON.parse(JSON.stringify(target)))
  dialogVisible.value = true
  formRef.value?.clearValidate()
}

/** 保存：确保只有一个本位币 */
function submitForm() {
  formRef.value?.validate((valid) => {
    if (!valid) return
    const rec = JSON.parse(JSON.stringify(formModel)) as CurrencyRecord
    if (dialogMode.value === 'add') {
      rec.id = genId()
      rows.push(rec)
    } else {
      const idx = rows.findIndex((r) => r.id === rec.id)
      if (idx >= 0) rows[idx] = rec
    }
    if (rec.isBase) {
      rows.forEach((r) => {
        if (r.id !== rec.id && r.isBase) r.isBase = false
      })
    }
    ElMessage.success(dialogMode.value === 'add' ? '已新增' : '已保存')
    dialogVisible.value = false
  })
}

/* ============ 删除 ============ */
function deleteRows(row?: CurrencyRecord) {
  const ids = row ? new Set([row.id]) : selectedIds.value
  if (ids.size === 0) {
    ElMessage.warning('请先勾选要删除的币别记录')
    return
  }
  ElMessageBox.confirm(`确定要删除选中的 ${ids.size} 条币别记录吗？`, '删除确认', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(() => {
      for (let i = rows.length - 1; i >= 0; i--) {
        if (ids.has(rows[i].id)) rows.splice(i, 1)
      }
      selectedIds.value.clear()
      ElMessage.success(`已删除 ${ids.size} 条记录`)
    })
    .catch(() => {})
}

/* ============ ��出 CSV ============ */
function exportCsv() {
  const header = ['编码', '名称', '汇率', '是否本位币', '是否封存']
  const dataRows = rows.map((r) => [
    r.code,
    r.name,
    r.rate,
    r.isBase ? '是' : '否',
    r.isSealed ? '已封存' : '未封存',
  ])
  const csv = [header, ...dataRows]
    .map((row) => row.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(','))
    .join('\n')
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = '币别列表.csv'
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('已导出币别列表')
}

/* ============ 导入 CSV ============ */
const fileInput = ref<HTMLInputElement>()
function triggerImport() {
  fileInput.value?.click()
}
function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => {
    try {
      const text = String(reader.result || '')
      const parsed = parseCsv(text)
      if (parsed.length === 0) {
        ElMessage.warning('文件中没有数据行')
        return
      }
      const header = parsed[0]
      const idxByLabel: Record<string, number> = {}
      header.forEach((h, i) => (idxByLabel[h.trim()] = i))
      let added = 0
      for (let i = 1; i < parsed.length; i++) {
        const cells = parsed[i]
        const code = (cells[idxByLabel['编码']] || '').trim()
        const name = (cells[idxByLabel['名称']] || '').trim()
        if (!code && !name) continue
        const rate = Number.parseFloat(cells[idxByLabel['汇率']] || '1') || 1
        const isBase = (cells[idxByLabel['是否本位币']] || '').trim() === '是'
        const isSealed = (cells[idxByLabel['是否封存']] || '').trim() === '已封存'
        rows.push({ id: genId(), code, name, rate, isBase, isSealed })
        added++
      }
      // 导入后统一本位币唯一性
      const base = rows.find((r) => r.isBase)
      if (base) rows.forEach((r) => { if (r.id !== base.id) r.isBase = false })
      ElMessage.success(`已导入 ${added} 条币别记录`)
    } catch (err) {
      ElMessage.error('导入失败：文件解析出错')
    } finally {
      input.value = ''
    }
  }
  reader.readAsText(file, 'utf-8')
}

/** 简易 CSV 解析 */
function parseCsv(text: string): string[][] {
  const rows: string[][] = []
  let row: string[] = []
  let field = ''
  let inQuotes = false
  for (let i = 0; i < text.length; i++) {
    const ch = text[i]
    if (inQuotes) {
      if (ch === '"') {
        if (text[i + 1] === '"') {
          field += '"'
          i++
        } else inQuotes = false
      } else field += ch
    } else {
      if (ch === '"') inQuotes = true
      else if (ch === ',') {
        row.push(field)
        field = ''
      } else if (ch === '\n' || ch === '\r') {
        if (ch === '\r' && text[i + 1] === '\n') i++
        row.push(field)
        rows.push(row)
        row = []
        field = ''
      } else field += ch
    }
  }
  if (field.length > 0 || row.length > 0) {
    row.push(field)
    rows.push(row)
  }
  return rows.filter((r) => r.some((c) => c.trim() !== ''))
}

function downloadTemplate() {
  const header = ['编码', '名称', '汇率', '是否本位币', '是否封存']
  const csv = ['﻿' + header.map((c) => `"${c}"`).join(',')]
  const blob = new Blob([csv.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = '币别导入模板.csv'
  a.click()
  URL.revokeObjectURL(url)
}

function handleRefresh() {
  keyword.value = ''
  selectedIds.value.clear()
  ElMessage.success('已刷新')
}

function showHelp() {
  ElMessageBox.alert(
    '币别用于维护账套核算中涉及的外币档案：\n\n' +
      '• 编码：币别代码，如 RMB、USD\n' +
      '• 汇率：折算为本位币的比率，本位币通常为 1\n' +
      '• 是否本位币：一个账套只允许一个本位币；设置新的本位币时，其余自动取消\n' +
      '• 是否封存：封存后该币别不再用于新增凭证，但历史数据仍可查询\n\n' +
      '删除本位币前请先在编辑中将另一币别设为本位币。',
    '币别说明',
    { confirmButtonText: '知道了' },
  )
}
</script>

<template>
  <div class="currency-page">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <div class="page-title">
          <el-icon><Money /></el-icon>
          <span>币别</span>
        </div>
        <el-input
          v-model="keyword"
          placeholder="请输入编码、名称或汇率"
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
        <el-button type="primary" @click="openAdd">
          <el-icon><Plus /></el-icon>新增
        </el-button>
        <el-button @click="openEdit()">
          <el-icon><Edit /></el-icon>编辑
        </el-button>
        <el-button @click="deleteRows()">
          <el-icon><Delete /></el-icon>删除
        </el-button>
        <el-dropdown trigger="click" @command="(c: string) => c === 'tpl' ? downloadTemplate() : triggerImport()">
          <el-button>
            导入<el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="tpl">下载导入模板</el-dropdown-item>
              <el-dropdown-item command="file">
                <el-icon><Upload /></el-icon>选择 CSV 文件导入
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button @click="exportCsv">
          <el-icon><Download /></el-icon>导出
        </el-button>
        <el-button text circle title="刷新" @click="handleRefresh">
          <el-icon><Refresh /></el-icon>
        </el-button>
        <el-button text circle title="设置">
          <el-icon><Setting /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 主表格 -->
    <div class="table-wrap">
      <el-table
        :data="filteredRows"
        border
        stripe
        size="small"
        height="100%"
        :header-cell-style="{ background: '#f5f7fa', color: '#303133', fontWeight: 600 }"
        @row-click="onRowClick"
      >
        <el-table-column width="48" align="center">
          <template #header>
            <el-checkbox
              :model-value="selectedIds.size > 0 && selectedIds.size === filteredRows.length"
              @change="(val: any) => {
                if (val) filteredRows.forEach(r => selectedIds.add(r.id))
                else selectedIds.clear()
              }"
            />
          </template>
          <template #default="{ row }">
            <el-checkbox :model-value="isSelected(row.id)" @change="toggleSelect(row, $event as unknown as Event)" />
          </template>
        </el-table-column>

        <el-table-column prop="code" label="编码" width="120" show-overflow-tooltip />
        <el-table-column prop="name" label="名称" width="180" show-overflow-tooltip />
        <el-table-column prop="rate" label="汇率" width="140" align="right">
          <template #default="{ row }">
            <span>{{ row.rate.toFixed(4) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="是否本位币" width="120" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.isBase" type="success" size="small">是</el-tag>
            <span v-else class="muted">否</span>
          </template>
        </el-table-column>
        <el-table-column label="是否封存" width="120" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.isSealed" type="info" size="small">已封存</el-tag>
            <span v-else>未封存</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="140" fixed="right" align="center">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click.stop="openEdit(row)">
              <el-icon><Edit /></el-icon>修改
            </el-button>
            <el-button text type="danger" size="small" @click.stop="deleteRows(row)">
              <el-icon><Delete /></el-icon>删除
            </el-button>
          </template>
        </el-table-column>

        <template #empty>
          <el-empty description="暂无币别数据，点击「新增」添加" :image-size="80" />
        </template>
      </el-table>
    </div>

    <!-- 隐藏文件输入 -->
    <input ref="fileInput" type="file" accept=".csv" style="display: none" @change="onFileChange" />

    <!-- 新增 / 编辑 弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="`${dialogMode === 'add' ? '新增' : '编辑'}币别`"
      width="480px"
      @closed="formRef?.clearValidate()"
    >
      <el-form ref="formRef" :model="formModel" :rules="rules" label-width="100px">
        <el-form-item label="编码" prop="code">
          <el-input v-model="formModel.code" placeholder="如 RMB / USD" />
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="formModel.name" placeholder="如人民币 / 美元" />
        </el-form-item>
        <el-form-item label="汇率">
          <el-input-number
            v-model="formModel.rate"
            :min="0"
            :max="999999"
            :precision="4"
            :controls="false"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="是否本位币">
          <el-switch v-model="formModel.isBase" active-text="是" inactive-text="否" />
        </el-form-item>
        <el-form-item label="是否封存">
          <el-switch v-model="formModel.isSealed" active-text="已封存" inactive-text="未封存" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.currency-page {
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
  flex-wrap: wrap;
}
.table-wrap {
  flex: 1;
  min-height: 0;
}
.muted {
  color: #909399;
}
</style>
