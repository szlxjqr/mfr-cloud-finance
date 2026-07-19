<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  Plus,
  Delete,
  Refresh,
  Setting,
  QuestionFilled,
  Filter,
  MagicStick,
  DocumentChecked,
  ArrowDown,
  EditPen,
} from '@element-plus/icons-vue'

/** 进项发票行 */
interface InvoiceRecord {
  id: string
  bizType: string       // 业务类型
  item: string        // 开票项目
  account: string     // 结算科目
  qty: number         // 数量
  price: number       // 单价
  amount: number      // 金额
  taxRate: number     // 税率(%)
  tax: number         // 税额
  total: number       // 价税合计
}

let _seq = 0
function genId(): string {
  _seq += 1
  return `inv_${Date.now().toString(36)}_${_seq}`
}

/** 示例数据 */
const rows = reactive<InvoiceRecord[]>([
  {
    id: genId(),
    bizType: '采购商品',
    item: '办公用品',
    account: '库存商品',
    qty: 10,
    price: 100,
    amount: 1000,
    taxRate: 13,
    tax: 130,
    total: 1130,
  },
  {
    id: genId(),
    bizType: '接受服务',
    item: '咨询服务费',
    account: '管理费用',
    qty: 1,
    price: 5000,
    amount: 5000,
    taxRate: 6,
    tax: 300,
    total: 5300,
  },
])

/** 期间 */
const period = ref<string>('2026-05')

/** 搜索 / 筛选关键字 */
const keyword = ref('')
const filteredRows = computed<InvoiceRecord[]>(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return rows
  return rows.filter(
    (r) =>
      r.bizType.toLowerCase().includes(kw) ||
      r.item.toLowerCase().includes(kw) ||
      r.account.toLowerCase().includes(kw),
  )
})

/** 选中行 */
const selectedIds = ref<Set<string>>(new Set())
function isSelected(id: string): boolean {
  return selectedIds.value.has(id)
}
function toggleSelect(row: InvoiceRecord, e: Event) {
  e.stopPropagation()
  if (selectedIds.value.has(row.id)) selectedIds.value.delete(row.id)
  else selectedIds.value.add(row.id)
}
function onRowClick(row: InvoiceRecord) {
  if (selectedIds.value.has(row.id)) selectedIds.value.delete(row.id)
  else selectedIds.value.add(row.id)
}

/* ============ 新增 / 编辑 弹窗 ============ */
const dialogVisible = ref(false)
const dialogMode = ref<'add' | 'edit'>('add')
const formRef = ref<FormInstance>()
const formModel = reactive<InvoiceRecord>({
  id: '',
  bizType: '',
  item: '',
  account: '',
  qty: 1,
  price: 0,
  amount: 0,
  taxRate: 13,
  tax: 0,
  total: 0,
})

const rules: FormRules = {
  bizType: [{ required: true, message: '请输入业务类型', trigger: 'blur' }],
  item: [{ required: true, message: '请输入开票项目', trigger: 'blur' }],
  account: [{ required: true, message: '请输入结算科目', trigger: 'blur' }],
}

function resetForm() {
  Object.assign(formModel, {
    id: '',
    bizType: '',
    item: '',
    account: '',
    qty: 1,
    price: 0,
    amount: 0,
    taxRate: 13,
    tax: 0,
    total: 0,
  })
}

function calcAmount() {
  formModel.amount = Number((formModel.qty * formModel.price).toFixed(2))
  calcTax()
}
function calcTax() {
  formModel.tax = Number((formModel.amount * (formModel.taxRate / 100)).toFixed(2))
  formModel.total = Number((formModel.amount + formModel.tax).toFixed(2))
}

function openAdd() {
  dialogMode.value = 'add'
  resetForm()
  dialogVisible.value = true
  formRef.value?.clearValidate()
}

function openEdit(row: InvoiceRecord) {
  dialogMode.value = 'edit'
  Object.assign(formModel, JSON.parse(JSON.stringify(row)))
  dialogVisible.value = true
  formRef.value?.clearValidate()
}

function submitForm() {
  formRef.value?.validate((valid) => {
    if (!valid) return
    calcAmount()
    const rec = JSON.parse(JSON.stringify(formModel)) as InvoiceRecord
    if (dialogMode.value === 'add') {
      rec.id = genId()
      rows.push(rec)
      ElMessage.success('已新增')
    } else {
      const idx = rows.findIndex((r) => r.id === rec.id)
      if (idx >= 0) rows[idx] = rec
      ElMessage.success('已保存')
    }
    dialogVisible.value = false
  })
}

/* ============ 删除 ============ */
function deleteRows(row?: InvoiceRecord) {
  const ids = row ? new Set([row.id]) : selectedIds.value
  if (ids.size === 0) {
    ElMessage.warning('请先勾选要删除的发票')
    return
  }
  ElMessageBox.confirm(`确定要删除选中的 ${ids.size} 条发票吗？`, '删除确认', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(() => {
      for (let i = rows.length - 1; i >= 0; i--) {
        if (ids.has(rows[i].id)) rows.splice(i, 1)
      }
      selectedIds.value.clear()
      ElMessage.success(`已删除 ${ids.size} 条发票`)
    })
    .catch(() => {})
}

/* ============ 工具栏操作 ============ */
function aiRecognize() {
  ElMessage.info('AI 发票识别功能开发中')
}
function aiMatch() {
  ElMessage.info('AI 科目匹配功能开发中')
}
function smartFetch(cmd: string) {
  ElMessage.info(`智能取票：${cmd}`)
}
function generateVoucher() {
  if (selectedIds.value.size === 0) {
    ElMessage.warning('请先勾选要生成凭证的发票')
    return
  }
  ElMessage.success(`已为 ${selectedIds.value.size} 条发票生成凭证`)
}
function adjustAccount() {
  if (selectedIds.value.size === 0) {
    ElMessage.warning('请先勾选要调整科目的发票')
    return
  }
  ElMessage.info('调整科目功能开发中')
}
function handleRefresh() {
  keyword.value = ''
  selectedIds.value.clear()
  ElMessage.success('已刷新')
}
function showHelp() {
  ElMessageBox.alert(
    '进项发票用于管理企业收到的增值税专用发票/普通发票：\n\n' +
      '• 业务类型：如采购商品、接受服务、固定资产等\n' +
      '• 开票项目：发票上的货物或应税劳务名称\n' +
      '• 结算科目：对应入账的会计科目\n' +
      '• 金额、税率、税额、价税合计：由数量×单价自动计算\n\n' +
      '勾选发票后可进行批量删除、调整科目或生成凭证。',
    '进项发票说明',
    { confirmButtonText: '知道了' },
  )
}
</script>

<template>
  <div class="invoice-input-page">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <span class="toolbar-label">期间</span>
        <el-date-picker
          v-model="period"
          type="month"
          format="YYYY年MM期"
          value-format="YYYY-MM"
          class="period-picker"
        />
        <el-dropdown trigger="click" @command="(c: string) => ElMessage.info(`筛选：${c}`)">
          <el-button>
            <el-icon><Filter /></el-icon>筛选<el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="全部">全部</el-dropdown-item>
              <el-dropdown-item command="已认证">已认证</el-dropdown-item>
              <el-dropdown-item command="未认证">未认证</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button text circle @click="handleRefresh">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
      <div class="toolbar-right">
        <el-button text circle @click="showHelp">
          <el-icon><QuestionFilled /></el-icon>帮助
        </el-button>
        <el-button class="ai-btn" @click="aiRecognize">
          <el-icon><MagicStick /></el-icon>AI 发票识别
        </el-button>
        <el-button class="ai-btn purple" @click="aiMatch">
          <el-icon><MagicStick /></el-icon>AI 科目匹配
        </el-button>
        <el-dropdown trigger="click" @command="smartFetch">
          <el-button type="primary">
            智能取票<el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="邮箱">邮箱取票</el-dropdown-item>
              <el-dropdown-item command="税盘">税盘取票</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button type="primary" @click="openAdd">
          <el-icon><Plus /></el-icon>新增
        </el-button>
        <el-dropdown trigger="click" @command="generateVoucher">
          <el-button>
            生成凭证(本月)<el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="本月">生成凭证（本月）</el-dropdown-item>
              <el-dropdown-item command="全部">生成凭证（全部）</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button @click="deleteRows()">
          <el-icon><Delete /></el-icon>全部删除
        </el-button>
        <el-button text circle>
          <el-icon><Setting /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 批量操作栏 -->
    <div class="batch-bar">
      <span class="selected-tip">已选中 <strong>{{ selectedIds.size }}</strong> 条</span>
      <el-button text @click="adjustAccount">
        <el-icon><EditPen /></el-icon>调整科目
      </el-button>
      <el-dropdown trigger="click" @command="generateVoucher">
        <el-button text>
          <el-icon><DocumentChecked /></el-icon>生成凭证<el-icon class="el-icon--right"><ArrowDown /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="本月">生成凭证（本月）</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
      <el-button text type="danger" @click="deleteRows()">
        <el-icon><Delete /></el-icon>删除
      </el-button>
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

        <el-table-column prop="bizType" label="业务类型" min-width="120" show-overflow-tooltip />
        <el-table-column prop="item" label="开票项目" min-width="160" show-overflow-tooltip />
        <el-table-column prop="account" label="结算科目" min-width="140" show-overflow-tooltip />
        <el-table-column prop="qty" label="数量" width="90" align="right" />
        <el-table-column prop="price" label="单价" width="110" align="right">
          <template #default="{ row }">{{ row.price.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="amount" label="金额" width="120" align="right">
          <template #default="{ row }">{{ row.amount.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="taxRate" label="税率(%)" width="90" align="right" />
        <el-table-column prop="tax" label="税额" width="120" align="right">
          <template #default="{ row }">{{ row.tax.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="total" label="价税合计" width="130" align="right">
          <template #default="{ row }">{{ row.total.toFixed(2) }}</template>
        </el-table-column>

        <el-table-column label="操作" width="120" fixed="right" align="center">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click.stop="openEdit(row)">编辑</el-button>
            <el-button text type="danger" size="small" @click.stop="deleteRows(row)">删除</el-button>
          </template>
        </el-table-column>

        <template #empty>
          <el-empty description="暂无进项发票，点击「新增」添加" :image-size="80" />
        </template>
      </el-table>
    </div>

    <!-- 新增 / 编辑 弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="`${dialogMode === 'add' ? '新增' : '编辑'}进项发票`"
      width="560px"
      @closed="formRef?.clearValidate()"
    >
      <el-form ref="formRef" :model="formModel" :rules="rules" label-width="96px">
        <el-form-item label="业务类型" prop="bizType">
          <el-input v-model="formModel.bizType" placeholder="如采购商品" />
        </el-form-item>
        <el-form-item label="开票项目" prop="item">
          <el-input v-model="formModel.item" placeholder="请输入开票项目" />
        </el-form-item>
        <el-form-item label="结算科目" prop="account">
          <el-input v-model="formModel.account" placeholder="如库存商品" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="数量">
              <el-input-number v-model="formModel.qty" :min="1" :controls="false" style="width: 100%" @change="calcAmount" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="单价">
              <el-input-number v-model="formModel.price" :min="0" :precision="2" :controls="false" style="width: 100%" @change="calcAmount" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="金额">
              <el-input-number v-model="formModel.amount" :min="0" :precision="2" :controls="false" style="width: 100%" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="税率(%)">
              <el-input-number v-model="formModel.taxRate" :min="0" :max="100" :precision="2" :controls="false" style="width: 100%" @change="calcTax" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="税额">
              <el-input-number v-model="formModel.tax" :min="0" :precision="2" :controls="false" style="width: 100%" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="价税合计">
              <el-input-number v-model="formModel.total" :min="0" :precision="2" :controls="false" style="width: 100%" disabled />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.invoice-input-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 12px 16px 0;
  box-sizing: border-box;
  background: #fff;
  overflow: hidden;
}

/* 顶部工具栏 */
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 0 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  gap: 12px;
  flex-wrap: wrap;
}
.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.toolbar-label {
  font-size: 14px;
  color: var(--el-text-color-regular);
}
.period-picker {
  width: 150px;
}

/* AI 按钮 */
.ai-btn {
  background: linear-gradient(90deg, #7c3aed 0%, #a855f7 100%);
  color: #fff;
  border: none;
}
.ai-btn:hover {
  background: linear-gradient(90deg, #6d28d9 0%, #9333ea 100%);
  color: #fff;
}
.ai-btn.purple {
  background: linear-gradient(90deg, #ec4899 0%, #f472b6 100%);
}
.ai-btn.purple:hover {
  background: linear-gradient(90deg, #db2777 0%, #ec4899 100%);
}

/* 批量操作栏 */
.batch-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 10px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
  margin-bottom: 8px;
}
.selected-tip {
  font-size: 14px;
  color: var(--el-text-color-regular);
}
.selected-tip strong {
  color: var(--el-color-primary);
}

/* 表格 */
.table-wrap {
  flex: 1;
  min-height: 0;
}
</style>
