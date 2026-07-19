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
  User,
  OfficeBuilding,
  Goods,
  Collection,
  More,
} from '@element-plus/icons-vue'

/** 单条辅助字典记录：编号/名称为通用字段，其余字段按类别动态扩展 */
interface AuxRecord {
  id: string
  code: string
  name: string
  [key: string]: string
}

/** 字段定义 */
interface FieldDef {
  key: string
  label: string
  type: 'text' | 'date'
  width?: number
  required?: boolean
  placeholder?: string
}

/** 类别定义：key 对应路由/存储键，label 为界面显示 */
const CATEGORY_DEFS: {
  key: string
  label: string
  icon: any
  fields: FieldDef[]
}[] = [
  {
    key: 'customer',
    label: '客户',
    icon: User,
    fields: [
      { key: 'taxNo', label: '税号', type: 'text', width: 160, placeholder: '纳税人识别号' },
      { key: 'contact', label: '联系人', type: 'text', width: 110 },
      { key: 'phone', label: '联系电话', type: 'text', width: 140 },
      { key: 'bankAccount', label: '银行账号', type: 'text', width: 200 },
    ],
  },
  {
    key: 'supplier',
    label: '供应商',
    icon: OfficeBuilding,
    fields: [
      { key: 'taxNo', label: '税号', type: 'text', width: 160, placeholder: '纳税人识别号' },
      { key: 'contact', label: '联系人', type: 'text', width: 110 },
      { key: 'phone', label: '联系电话', type: 'text', width: 140 },
      { key: 'bankAccount', label: '银行账号', type: 'text', width: 200 },
    ],
  },
  {
    key: 'dept',
    label: '部门',
    icon: OfficeBuilding,
    fields: [],
  },
  {
    key: 'employee',
    label: '员工',
    icon: User,
    fields: [
      { key: 'mobile', label: '手机号', type: 'text', width: 140 },
      { key: 'hireDate', label: '入职时间', type: 'date', width: 130 },
      { key: 'leaveDate', label: '离职时间', type: 'date', width: 130 },
    ],
  },
  {
    key: 'project',
    label: '专项',
    icon: Collection,
    fields: [],
  },
  {
    key: 'inventory',
    label: '存货',
    icon: Goods,
    fields: [{ key: 'unit', label: '计量单位', type: 'text', width: 120 }],
  },
  {
    key: 'other',
    label: '其他',
    icon: More,
    fields: [],
  },
]

/** 当前选中类别 */
const activeKey = ref<string>('customer')

/** 各分类数据容器 */
const store: Record<string, AuxRecord[]> = reactive({})
CATEGORY_DEFS.forEach((c) => (store[c.key] = []))

/** 按数据字典预填部门示例数据 */
store.dept.push(
  { id: genId(), code: '0001', name: '总经办' },
  { id: genId(), code: '0002', name: '人力资源部' },
)

let _seq = 0
function genId(): string {
  _seq += 1
  return `aux_${Date.now().toString(36)}_${_seq}`
}

/** 当前类别定义与字段 */
const currentDef = computed(() => CATEGORY_DEFS.find((c) => c.key === activeKey.value)!)
/** 表格列：编号 + 名称 + 类别动态字段 */
const columns = computed(() => [
  { key: 'code', label: '编号', type: 'text' as const, width: 110, required: true },
  { key: 'name', label: '名称', type: 'text' as const, width: 180, required: true },
  ...currentDef.value.fields,
])

/** 当前类别数据 */
const rows = computed<AuxRecord[]>(() => store[activeKey.value] ?? [])

/** 搜索关键字 */
const keyword = ref('')
const filteredRows = computed<AuxRecord[]>(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return rows.value
  return rows.value.filter(
    (r) =>
      r.code.toLowerCase().includes(kw) ||
      r.name.toLowerCase().includes(kw) ||
      currentDef.value.fields.some((f) => (r[f.key] || '').toLowerCase().includes(kw)),
  )
})

/** 选中行（按 id） */
const selectedIds = ref<Set<string>>(new Set())
function isSelected(id: string): boolean {
  return selectedIds.value.has(id)
}
function toggleSelect(row: AuxRecord, e: Event) {
  e.stopPropagation()
  if (selectedIds.value.has(row.id)) selectedIds.value.delete(row.id)
  else selectedIds.value.add(row.id)
}
function onRowClick(row: AuxRecord) {
  // 点击行切换选中（与复选框一致）
  if (selectedIds.value.has(row.id)) selectedIds.value.delete(row.id)
  else selectedIds.value.add(row.id)
}

/* ============ 新增 / 编辑 弹窗 ============ */
const dialogVisible = ref(false)
const dialogMode = ref<'add' | 'edit'>('add')
const formRef = ref<FormInstance>()
const formModel = reactive<AuxRecord>({ id: '', code: '', name: '' })

function emptyForm(): AuxRecord {
  const base: AuxRecord = { id: '', code: '', name: '' }
  currentDef.value.fields.forEach((f) => (base[f.key] = ''))
  return base
}

const rules = computed<FormRules>(() => {
  const r: FormRules = {
    code: [{ required: true, message: '请输入编号', trigger: 'blur' }],
    name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  }
  return r
})

function openAdd() {
  dialogMode.value = 'add'
  Object.assign(formModel, emptyForm())
  dialogVisible.value = true
  formRef.value?.clearValidate()
}

function openEdit(row?: AuxRecord) {
  const target =
    row ?? (selectedIds.value.size === 1 ? rows.value.find((r) => r.id === [...selectedIds.value][0]) : undefined)
  if (!target) {
    ElMessage.warning('请先勾选一条记录再编辑')
    return
  }
  dialogMode.value = 'edit'
  Object.assign(formModel, emptyForm(), JSON.parse(JSON.stringify(target)))
  dialogVisible.value = true
  formRef.value?.clearValidate()
}

function submitForm() {
  formRef.value?.validate((valid) => {
    if (!valid) return
    if (dialogMode.value === 'add') {
      store[activeKey.value].push({ ...emptyForm(), ...formModel, id: genId() })
      ElMessage.success('已新增')
    } else {
      const idx = store[activeKey.value].findIndex((r) => r.id === formModel.id)
      if (idx >= 0) store[activeKey.value][idx] = { ...store[activeKey.value][idx], ...formModel }
      ElMessage.success('已保存')
    }
    dialogVisible.value = false
  })
}

/* ============ 删除 ============ */
function deleteRows(row?: AuxRecord) {
  const ids = row ? new Set([row.id]) : selectedIds.value
  if (ids.size === 0) {
    ElMessage.warning('请先勾选要删除的记录')
    return
  }
  ElMessageBox.confirm(`确定要删除选中的 ${ids.size} 条记录吗？`, '删除确认', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(() => {
      store[activeKey.value] = store[activeKey.value].filter((r) => !ids.has(r.id))
      selectedIds.value.clear()
      ElMessage.success(`已删除 ${ids.size} 条记录`)
    })
    .catch(() => {})
}

/* ============ 导出 CSV ============ */
function exportCsv() {
  const cols = columns.value
  const header = cols.map((c) => c.label)
  const dataRows = rows.value.map((r) => cols.map((c) => r[c.key] ?? ''))
  const csv = [header, ...dataRows]
    .map((row) => row.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(','))
    .join('\n')
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `辅助字典_${currentDef.value.label}.csv`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success(`已导出「${currentDef.value.label}」辅助字典`)
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
      // 按表头标签映射字段
      const keyByLabel: Record<string, string> = {}
      columns.value.forEach((c) => (keyByLabel[c.label] = c.key))
      let added = 0
      for (let i = 1; i < parsed.length; i++) {
        const cells = parsed[i]
        const rec: AuxRecord = { id: genId(), code: '', name: '' }
        header.forEach((h, idx) => {
          const key = keyByLabel[h.trim()]
          if (key) rec[key] = (cells[idx] ?? '').trim()
        })
        if (!rec.code && !rec.name) continue
        store[activeKey.value].push(rec)
        added++
      }
      ElMessage.success(`已导入 ${added} 条记录`)
    } catch (err) {
      ElMessage.error('导入失败：文件解析出错')
    } finally {
      input.value = ''
    }
  }
  reader.readAsText(file, 'utf-8')
}

/** 简易 CSV 解析（支持双引号包裹与转义） */
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

/* ============ 模板下载 ============ */
function downloadTemplate() {
  const header = columns.value.map((c) => c.label)
  const csv = ['﻿' + header.map((c) => `"${c}"`).join(',')]
  const blob = new Blob([csv.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `辅助字典_${currentDef.value.label}_导入模板.csv`
  a.click()
  URL.revokeObjectURL(url)
}

function showHelp() {
  ElMessageBox.alert(
    '辅助字典用于维护核算所需的各类基础档案：\n\n' +
      '• 客户 / 供应商：往来单位档案（税号、联系人、银行账号等）\n' +
      '• 部门 / 员工：组织架构与人员档案\n' +
      '• 专项：项目辅助核算档案\n' +
      '• 存货：存货档案（含计量单位）\n' +
      '• 其他：未归入上述分类的辅助项\n\n' +
      '编号建议保持唯一，新增后可在凭证、辅助核算中引用。',
    '辅助字典说明',
    { confirmButtonText: '知道了' },
  )
}

function handleRefresh() {
  keyword.value = ''
  selectedIds.value.clear()
  ElMessage.success('已刷新')
}
</script>

<template>
  <div class="aux-page">
    <!-- 左侧：辅助字典类别树 -->
    <aside class="aux-side">
      <div class="side-title">
        <el-icon><Collection /></el-icon>
        <span>辅助字典</span>
      </div>
      <ul class="tree">
        <li
          v-for="c in CATEGORY_DEFS"
          :key="c.key"
          :class="['tree-node', { active: activeKey === c.key }]"
          @click="activeKey = c.key"
        >
          <span class="tree-dot" />
          <el-icon class="tree-icon"><component :is="c.icon" /></el-icon>
          <span class="tree-label">{{ c.label }}</span>
          <span class="tree-count">{{ store[c.key].length }}</span>
        </li>
      </ul>
    </aside>

    <!-- 右侧：主区域 -->
    <section class="aux-main">
      <!-- 顶部工具栏 -->
      <div class="toolbar">
        <div class="toolbar-left">
          <el-input
            v-model="keyword"
            placeholder="请输入编号、名称或关键字"
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

          <el-table-column
            v-for="col in columns"
            :key="col.key"
            :prop="col.key"
            :label="col.label"
            :width="col.width"
            :min-width="col.key === 'name' ? 160 : 120"
            :show-overflow-tooltip="col.type === 'text'"
          >
            <template #default="{ row }">
              <span class="cell-text">{{ row[col.key] || '—' }}</span>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="120" fixed="right" align="center">
            <template #default="{ row }">
              <el-button text type="primary" size="small" @click.stop="openEdit(row)">编辑</el-button>
              <el-button text type="danger" size="small" @click.stop="deleteRows(row)">删除</el-button>
            </template>
          </el-table-column>

          <template #empty>
            <el-empty description="暂无数据，点击「新增」添加记录" :image-size="80" />
          </template>
        </el-table>
      </div>
    </section>

    <!-- 隐藏的文件输入 -->
    <input ref="fileInput" type="file" accept=".csv" style="display: none" @change="onFileChange" />

    <!-- 新增 / 编辑 弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="`${dialogMode === 'add' ? '新增' : '编辑'} · ${currentDef.label}`"
      width="520px"
      @closed="formRef?.clearValidate()"
    >
      <el-form ref="formRef" :model="formModel" :rules="rules" label-width="96px">
        <el-form-item label="编号" prop="code">
          <el-input v-model="formModel.code" placeholder="请输入编号" />
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="formModel.name" placeholder="请输入名称" />
        </el-form-item>
        <el-form-item v-for="f in currentDef.fields" :key="f.key" :label="f.label">
          <el-date-picker
            v-if="f.type === 'date'"
            v-model="formModel[f.key]"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择日期"
            style="width: 100%"
          />
          <el-input v-else v-model="formModel[f.key]" :placeholder="f.placeholder || `请输入${f.label}`" />
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
.aux-page {
  display: flex;
  height: 100%;
  background: #fff;
  overflow: hidden;
}

/* ====== 左侧类别树 ====== */
.aux-side {
  width: 200px;
  flex-shrink: 0;
  border-right: 1px solid var(--el-border-color-lighter);
  background: #fafbfc;
  padding: 12px 0;
  overflow-y: auto;
}
.side-title {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 18px 12px;
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}
.side-title .el-icon {
  color: var(--el-color-primary);
}
.tree {
  list-style: none;
  margin: 0;
  padding: 0;
}
.tree-node {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 18px;
  cursor: pointer;
  font-size: 14px;
  color: var(--el-text-color-regular);
  border-left: 3px solid transparent;
  transition: all 0.15s;
  position: relative;
}
.tree-node:hover {
  background: var(--el-fill-color-light);
}
.tree-node.active {
  background: #ecf5ff;
  color: var(--el-color-primary);
  font-weight: 600;
  border-left-color: var(--el-color-primary);
}
.tree-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--el-border-color);
  flex-shrink: 0;
  margin-left: 4px;
}
.tree-node.active .tree-dot {
  background: var(--el-color-primary);
}
.tree-icon {
  font-size: 15px;
  flex-shrink: 0;
}
.tree-label {
  flex: 1;
}
.tree-count {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  background: var(--el-fill-color);
  border-radius: 10px;
  padding: 0 8px;
  min-width: 20px;
  text-align: center;
}

/* ====== 右侧主区 ====== */
.aux-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  gap: 12px;
  flex-wrap: wrap;
}
.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
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
  padding: 0;
}
.cell-text {
  color: var(--el-text-color-primary);
}
</style>
