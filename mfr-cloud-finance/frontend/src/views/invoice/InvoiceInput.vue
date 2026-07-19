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
  Upload,
} from '@element-plus/icons-vue'

/** 发票明细行 */
interface InvoiceDetail {
  id: string
  bizType: string
  item: string
  qty: number
  amount: number
  taxRate: number
  tax: number
  total: number
}

/** 发票主记录 */
interface InvoiceRecord {
  id: string
  invoiceId: string
  type: string
  code: string
  no: string
  date: string
  sellerName: string
  sellerTaxNo: string
  sellerAddressPhone: string
  sellerBankAccount: string
  account: string
  certify: 'current' | 'none'
  remark: string
  bizType: string
  item: string
  qty: number
  amount: number
  taxRate: number
  tax: number
  total: number
}

let _seq = 0
function genId(): string {
  _seq += 1
  return `inv_${Date.now().toString(36)}_${_seq}`
}

const invoiceTypes = [
  '增值税专用发票',
  '增值税普通发票',
  '电子专用发票',
  '电子普通发票',
  '机动车销售统一发票',
]

const taxRateOptions = ['0', '1', '3', '6', '9', '13']
const accountOptions = ['库存商品', '管理费用', '销售费用', '固定资产', '原材料', '工程施工']
const bizTypeOptions = ['采购商品', '接受服务', '采购固定资产', '费用报销', '其他']

/** 示例数据 */
const rows = reactive<InvoiceRecord[]>([
  {
    id: genId(),
    invoiceId: 'inv_sample_1',
    type: '增值税专用发票',
    code: '044002100111',
    no: '12345678',
    date: '2026-05-01',
    sellerName: '某办公用品有限公司',
    sellerTaxNo: '91440100MA5xxxxxx',
    sellerAddressPhone: '广州市天河区xxx 020-12345678',
    sellerBankAccount: '中国工商银行广州分行 6222xxxxxxxx',
    account: '库存商品',
    certify: 'none',
    remark: '',
    bizType: '采购商品',
    item: '办公用品',
    qty: 10,
    amount: 1000,
    taxRate: 13,
    tax: 130,
    total: 1130,
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
      r.sellerName.toLowerCase().includes(kw) ||
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

const formModel = reactive<{
  invoiceId: string
  type: string
  code: string
  no: string
  account: string
  date: string
  sellerName: string
  sellerTaxNo: string
  sellerAddressPhone: string
  sellerBankAccount: string
  certify: 'current' | 'none'
  remark: string
  details: InvoiceDetail[]
}>({
  invoiceId: '',
  type: '增值税专用发票',
  code: '',
  no: '',
  account: '',
  date: '2026-05-01',
  sellerName: '',
  sellerTaxNo: '',
  sellerAddressPhone: '',
  sellerBankAccount: '',
  certify: 'none',
  remark: '',
  details: [],
})

const rules: FormRules = {
  code: [{ required: true, message: '请输入发票代码', trigger: 'blur' }],
  no: [{ required: true, message: '请输入发票号码', trigger: 'blur' }],
  account: [{ required: true, message: '请选择结算科目', trigger: 'change' }],
  date: [{ required: true, message: '请选择开票日期', trigger: 'change' }],
  sellerName: [{ required: true, message: '请输入销方名称', trigger: 'blur' }],
}

function emptyDetail(): InvoiceDetail {
  return {
    id: genId(),
    bizType: '',
    item: '',
    qty: 1,
    amount: 0,
    taxRate: 13,
    tax: 0,
    total: 0,
  }
}

function resetForm() {
  Object.assign(formModel, {
    invoiceId: '',
    type: '增值税专用发票',
    code: '',
    no: '',
    account: '',
    date: '2026-05-01',
    sellerName: '',
    sellerTaxNo: '',
    sellerAddressPhone: '',
    sellerBankAccount: '',
    certify: 'none',
    remark: '',
    details: [emptyDetail()],
  })
}

function calcDetail(row: InvoiceDetail) {
  row.tax = Number((row.amount * (row.taxRate / 100)).toFixed(2))
  row.total = Number((row.amount + row.tax).toFixed(2))
}

const detailTotal = computed(() => {
  return formModel.details.reduce(
    (sum, d) => ({
      amount: sum.amount + d.amount,
      tax: sum.tax + d.tax,
      total: sum.total + d.total,
    }),
    { amount: 0, tax: 0, total: 0 },
  )
})

function addDetail() {
  formModel.details.push(emptyDetail())
}

function removeDetail(idx: number) {
  if (formModel.details.length <= 1) {
    ElMessage.warning('至少保留一条明细')
    return
  }
  formModel.details.splice(idx, 1)
}

function openAdd() {
  dialogMode.value = 'add'
  resetForm()
  dialogVisible.value = true
  formRef.value?.clearValidate()
}

function openEdit(row: InvoiceRecord) {
  dialogMode.value = 'edit'
  // 收集同一张发票的所有明细行
  const siblings = rows.filter((r) => r.invoiceId === row.invoiceId)
  const details: InvoiceDetail[] = siblings.map((r) => ({
    id: r.id,
    bizType: r.bizType,
    item: r.item,
    qty: r.qty,
    amount: r.amount,
    taxRate: r.taxRate,
    tax: r.tax,
    total: r.total,
  }))
  Object.assign(formModel, {
    invoiceId: row.invoiceId,
    type: row.type,
    code: row.code,
    no: row.no,
    account: row.account,
    date: row.date,
    sellerName: row.sellerName,
    sellerTaxNo: row.sellerTaxNo,
    sellerAddressPhone: row.sellerAddressPhone,
    sellerBankAccount: row.sellerBankAccount,
    certify: row.certify,
    remark: row.remark,
    details: details.length ? details : [emptyDetail()],
  })
  dialogVisible.value = true
  formRef.value?.clearValidate()
}

function submitForm() {
  formRef.value?.validate((valid) => {
    if (!valid) return
    if (formModel.details.length === 0) {
      ElMessage.warning('请至少录入一条明细')
      return
    }
    // 校验明细
    for (const d of formModel.details) {
      if (!d.bizType || !d.item) {
        ElMessage.warning('请完善业务类型和开票项目')
        return
      }
      calcDetail(d)
    }

    const invoiceId = dialogMode.value === 'add' ? genId() : formModel.invoiceId

    // 删除旧发票的明细行（编辑时）
    if (dialogMode.value === 'edit') {
      for (let i = rows.length - 1; i >= 0; i--) {
        if (rows[i].invoiceId === invoiceId) rows.splice(i, 1)
      }
    }

    // 添加新行
    formModel.details.forEach((d) => {
      rows.push({
        id: d.id === formModel.details[0].id && dialogMode.value === 'add' ? genId() : d.id,
        invoiceId,
        type: formModel.type,
        code: formModel.code,
        no: formModel.no,
        date: formModel.date,
        sellerName: formModel.sellerName,
        sellerTaxNo: formModel.sellerTaxNo,
        sellerAddressPhone: formModel.sellerAddressPhone,
        sellerBankAccount: formModel.sellerBankAccount,
        account: formModel.account,
        certify: formModel.certify,
        remark: formModel.remark,
        bizType: d.bizType,
        item: d.item,
        qty: d.qty,
        amount: d.amount,
        taxRate: d.taxRate,
        tax: d.tax,
        total: d.total,
      })
    })

    ElMessage.success(dialogMode.value === 'add' ? '已新增' : '已保存')
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
      '• 发票代码 / 发票号码：纸质发票左上角和右上角信息\n' +
      '• 结算科目：该发票对应入账的会计科目\n' +
      '• 销方单位：销售方名称、税号、地址电话、开户行及账号\n' +
      '• 是否认证：专票是否在本期进行进项认证\n' +
      '• 明细：业务类型、开票项目、数量、金额、税率、税额、价税合计\n\n' +
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

        <el-table-column prop="code" label="发票代码" width="130" show-overflow-tooltip />
        <el-table-column prop="no" label="发票号码" width="110" show-overflow-tooltip />
        <el-table-column prop="bizType" label="业务类型" min-width="110" show-overflow-tooltip />
        <el-table-column prop="item" label="开票项目" min-width="150" show-overflow-tooltip />
        <el-table-column prop="account" label="结算科目" min-width="120" show-overflow-tooltip />
        <el-table-column prop="qty" label="数量" width="80" align="right" />
        <el-table-column prop="amount" label="金额" width="120" align="right">
          <template #default="{ row }">{{ row.amount.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="taxRate" label="税率(%)" width="80" align="right" />
        <el-table-column prop="tax" label="税额" width="110" align="right">
          <template #default="{ row }">{{ row.tax.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="total" label="价税合计" width="120" align="right">
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
      width="960px"
      :close-on-click-modal="false"
      @closed="formRef?.clearValidate()"
    >
      <el-form ref="formRef" :model="formModel" :rules="rules" label-width="0" class="invoice-form">
        <!-- 发票类型 -->
        <div class="invoice-type-bar">
          <el-select v-model="formModel.type" class="invoice-type-select" popper-class="invoice-type-popper">
            <el-option v-for="t in invoiceTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </div>

        <!-- 发票头信息 -->
        <div class="invoice-header">
          <div class="form-row">
            <el-form-item prop="code" class="required">
              <template #label><span class="form-label">发票代码</span></template>
              <el-input v-model="formModel.code" placeholder="10或12位发票代码" />
            </el-form-item>
            <el-form-item prop="no" class="required">
              <template #label><span class="form-label">发票号码</span></template>
              <el-input v-model="formModel.no" placeholder="8位或20位发票号码" />
            </el-form-item>
            <el-form-item prop="account" class="required">
              <template #label><span class="form-label">结算科目</span></template>
              <el-select v-model="formModel.account" placeholder="请选择" style="width: 100%">
                <el-option v-for="a in accountOptions" :key="a" :label="a" :value="a" />
              </el-select>
            </el-form-item>
            <el-form-item prop="date" class="required">
              <template #label><span class="form-label">开票日期</span></template>
              <el-date-picker v-model="formModel.date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </div>
        </div>

        <!-- 销方单位 + 认证/备注 -->
        <div class="seller-section">
          <div class="seller-left">
            <div class="seller-title">销方单位</div>
            <el-form-item prop="sellerName" class="required">
              <template #label><span class="form-label">名 称</span></template>
              <el-input v-model="formModel.sellerName" placeholder="请输入名称" />
            </el-form-item>
            <el-form-item>
              <template #label><span class="form-label">纳税人识别号</span></template>
              <el-input v-model="formModel.sellerTaxNo" />
            </el-form-item>
            <el-form-item>
              <template #label><span class="form-label">地址、电话</span></template>
              <el-input v-model="formModel.sellerAddressPhone" />
            </el-form-item>
            <el-form-item>
              <template #label><span class="form-label">开户行及账号</span></template>
              <el-input v-model="formModel.sellerBankAccount" />
            </el-form-item>
          </div>
          <div class="seller-right">
            <el-form-item>
              <template #label><span class="form-label">是否认证</span></template>
              <el-radio-group v-model="formModel.certify">
                <el-radio label="current">本期认证</el-radio>
                <el-radio label="none">暂不认证</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item>
              <template #label><span class="form-label">备 注</span></template>
              <el-input v-model="formModel.remark" type="textarea" :rows="4" />
            </el-form-item>
          </div>
        </div>

        <!-- 明细表格 -->
        <div class="detail-section">
          <table class="detail-table">
            <thead>
              <tr>
                <th class="required" style="width: 140px">业务类型</th>
                <th class="required" style="min-width: 180px">开票项目</th>
                <th style="width: 80px">数量</th>
                <th class="required" style="width: 130px">金额</th>
                <th class="required" style="width: 110px">税率(%)</th>
                <th class="required" style="width: 110px">税额</th>
                <th class="required" style="width: 120px">价税合计</th>
                <th style="width: 60px">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, idx) in formModel.details" :key="row.id">
                <td>
                  <el-select v-model="row.bizType" placeholder="请选择" size="small">
                    <el-option v-for="b in bizTypeOptions" :key="b" :label="b" :value="b" />
                  </el-select>
                </td>
                <td>
                  <el-input v-model="row.item" placeholder="请输入" size="small" />
                </td>
                <td>
                  <el-input-number v-model="row.qty" :min="1" :controls="false" size="small" style="width: 100%" />
                </td>
                <td>
                  <el-input-number
                    v-model="row.amount"
                    :min="0"
                    :precision="2"
                    :controls="false"
                    size="small"
                    style="width: 100%"
                    @change="calcDetail(row)"
                  />
                </td>
                <td>
                  <el-select v-model="row.taxRate" size="small" style="width: 100%" @change="calcDetail(row)">
                    <el-option v-for="r in taxRateOptions" :key="r" :label="r" :value="Number(r)" />
                  </el-select>
                </td>
                <td>
                  <el-input-number v-model="row.tax" :precision="2" :controls="false" size="small" style="width: 100%" disabled />
                </td>
                <td>
                  <el-input-number v-model="row.total" :precision="2" :controls="false" size="small" style="width: 100%" disabled />
                </td>
                <td>
                  <el-button text type="danger" size="small" @click="removeDetail(idx)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </td>
              </tr>
            </tbody>
            <tfoot>
              <tr>
                <td colspan="2" class="total-label">合计</td>
                <td></td>
                <td class="total-num">{{ detailTotal.amount.toFixed(2) }}</td>
                <td></td>
                <td class="total-num">{{ detailTotal.tax.toFixed(2) }}</td>
                <td class="total-num">{{ detailTotal.total.toFixed(2) }}</td>
                <td></td>
              </tr>
            </tfoot>
          </table>
          <el-button text type="primary" class="add-detail-btn" @click="addDetail">
            <el-icon><Plus /></el-icon>添加明细行
          </el-button>
        </div>

        <!-- 上传附件 -->
        <div class="upload-section">
          <el-upload action="#" :auto-upload="false" :show-file-list="false">
            <el-button text>
              <el-icon><Upload /></el-icon>上传附件
            </el-button>
          </el-upload>
        </div>
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

/* ====== 发票录入弹窗样式 ====== */
.invoice-form :deep(.el-form-item) {
  margin-bottom: 12px;
}
.invoice-form :deep(.el-form-item__label) {
  padding: 0 8px 0 0;
  line-height: 32px;
}
.invoice-form :deep(.el-input__inner) {
  border-radius: 0;
  border-top: none;
  border-left: none;
  border-right: none;
  border-bottom: 1px solid #d8b692;
  background: transparent;
}
.invoice-form :deep(.el-input__inner:focus) {
  border-bottom-color: #a0522d;
}
.invoice-form :deep(.el-input__wrapper) {
  box-shadow: none !important;
}
.invoice-form :deep(.el-textarea__inner) {
  border-radius: 0;
  border: 1px solid #d8b692;
  background: transparent;
}
.invoice-form :deep(.el-textarea__inner:focus) {
  border-color: #a0522d;
}
.invoice-form :deep(.el-radio__input.is-checked .el-radio__inner) {
  background-color: #409eff;
  border-color: #409eff;
}
.invoice-form :deep(.el-radio__input.is-checked + .el-radio__label) {
  color: #409eff;
}

.invoice-type-bar {
  text-align: center;
  padding: 8px 0 16px;
  border-bottom: 2px solid #a0522d;
  margin-bottom: 16px;
}
.invoice-type-select :deep(.el-input__inner) {
  font-size: 18px;
  font-weight: 600;
  color: #a0522d;
  text-align: center;
  border: none;
  width: 240px;
}

.form-label {
  color: #a0522d;
  font-size: 14px;
  white-space: nowrap;
}
.required .form-label::before {
  content: '*';
  color: #f56c6c;
  margin-right: 4px;
}

.form-row {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}
.form-row .el-form-item {
  flex: 1;
  min-width: 200px;
}

/* 销方单位区域 */
.seller-section {
  display: flex;
  gap: 16px;
  border: 1px solid #d8b692;
  padding: 16px;
  margin: 16px 0;
  position: relative;
}
.seller-left,
.seller-right {
  flex: 1;
  min-width: 280px;
}
.seller-title {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  writing-mode: vertical-lr;
  letter-spacing: 4px;
  padding: 8px 4px;
  color: #a0522d;
  font-size: 14px;
  font-weight: 600;
  border-right: 1px solid #d8b692;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.seller-left {
  padding-left: 32px;
}

/* 明细表格 */
.detail-section {
  border: 1px solid #d8b692;
  padding: 12px;
  margin-bottom: 16px;
}
.detail-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}
.detail-table th,
.detail-table td {
  border: 1px solid #d8b692;
  padding: 6px;
  text-align: center;
  font-size: 13px;
}
.detail-table th {
  color: #a0522d;
  background: #fdf8f3;
  font-weight: 600;
}
.detail-table tfoot td {
  background: #fff8e6;
  color: #a0522d;
  font-weight: 600;
}
.total-label {
  text-align: center !important;
}
.total-num {
  text-align: right !important;
  padding-right: 12px !important;
}
.add-detail-btn {
  margin-top: 8px;
}

/* 上传附件 */
.upload-section {
  padding: 8px 0;
}

/* 响应式 */
@media (max-width: 768px) {
  .seller-section {
    flex-direction: column;
  }
  .seller-title {
    position: static;
    writing-mode: horizontal-tb;
    border-right: none;
    border-bottom: 1px solid #d8b692;
    width: 100%;
    height: auto;
    transform: none;
  }
  .seller-left {
    padding-left: 0;
  }
}
</style>
