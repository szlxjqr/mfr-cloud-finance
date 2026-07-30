<template>
  <div class="page">
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索单号/申请人/事由" clearable style="width: 240px" @keyup.enter="load" @clear="load" />
      <el-select v-model="statusFilter" placeholder="全部状态" clearable style="width: 140px" @change="load">
        <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
      </el-select>
      <el-button type="primary" @click="openCreate">新建报销单</el-button>
    </div>

    <DataLoader :loading="loading" :is-empty="!list.length">
      <el-table :data="list" border stripe>
      <el-table-column prop="bill_no" label="单号" width="160" />
      <el-table-column prop="applicant" label="申请人" width="100" />
      <el-table-column prop="department" label="部门" width="110" />
      <el-table-column label="类型" width="110">
        <template #default="{ row }">
          <el-tag :type="(row.bill_type || '采购报销') === '差旅报销' ? 'warning' : 'info'" size="small">
            {{ row.bill_type || '采购报销' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="发票" width="150" align="center">
        <template #default="{ row }">
          <span v-if="summaryMap[row.id]?.invoice_count">
            {{ summaryMap[row.id].invoice_count }} 张 /
            ¥{{ Number(summaryMap[row.id].total || 0).toFixed(2) }}
          </span>
          <span v-else class="text-muted">未挂票</span>
        </template>
      </el-table-column>
      <el-table-column prop="amount" label="预算金额" width="120" align="right">
        <template #default="{ row }">{{ row.amount != null ? '¥' + Number(row.amount).toFixed(2) : '-' }}</template>
      </el-table-column>
      <el-table-column label="报销金额" width="120" align="right">
        <template #default="{ row }">{{ reimburseDisplay(row) }}</template>
      </el-table-column>
      <el-table-column prop="reason" label="事由" show-overflow-tooltip />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <StatusTag :status="row.status" />
        </template>
      </el-table-column>
      <el-table-column prop="submit_date" label="提交日期" width="110" />
      <el-table-column prop="approve_date" label="审批日期" width="110" />
      <el-table-column label="操作" width="300" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status === '草稿' || row.status === '已驳回'" link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button
            v-for="act in transformActions(row)"
            :key="act.action"
            link
            :type="act.type"
            @click="runAction(act.action, row)"
          >{{ act.label }}</el-button>
          <el-button v-if="row.status === '草稿' || row.status === '已驳回'" link type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
      </el-table>
      </DataLoader>

    <!-- 报销单新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑报销单' : '新建报销单'" width="1040px" :close-on-click-modal="false">
      <el-form :model="form" label-width="100px">
        <el-form-item label="报销单编号">
          <el-input :model-value="form.bill_no || previewBillNo || '保存后自动生成'" disabled />
        </el-form-item>
        <el-form-item label="报销类型" required>
          <el-radio-group v-model="form.bill_type">
            <el-radio label="采购报销">采购报销</el-radio>
            <el-radio label="差旅报销">差旅报销</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="申请人">
          <el-input v-model="form.applicant" placeholder="必填" />
        </el-form-item>
        <el-form-item label="部门">
          <el-input v-model="form.department" />
        </el-form-item>

        <!-- 差旅报销专属字段 -->
        <template v-if="form.bill_type === '差旅报销'">
          <el-form-item label="出差人">
            <el-input v-model="form.traveler" placeholder="出差人员姓名" />
          </el-form-item>
          <el-form-item label="出差地点">
            <el-input v-model="form.travel_destination" placeholder="如：赣州、南昌" />
          </el-form-item>
          <el-form-item label="出差起止">
            <el-date-picker
              v-model="travelRange"
              type="daterange"
              range-separator="至"
              start-placeholder="出发日期"
              end-placeholder="返回日期"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </template>

        <el-form-item label="预算金额">
          <el-input v-model.number="form.amount" type="number" placeholder="0.00（采购报销取采购申请预算）" />
        </el-form-item>
        <el-form-item v-if="editing && editingId" label="发票合计">
          <el-input :model-value="editingInvoiceTotal.toFixed(2)" disabled />
          <span class="tax-hint">已挂发票含税合计（自动汇总）</span>
        </el-form-item>
        <el-form-item v-if="editing && editingId" label="报销金额">
          <el-input-number
            v-model="form.reimburse_amount"
            :min="0"
            :precision="2"
            :controls="false"
            :placeholder="editingInvoiceTotal.toFixed(2) + '（默认=发票合计）'"
            style="width: 200px"
          />
          <span class="tax-hint">默认=发票合计；可调低，须 &gt;0 且 ≤ 发票合计</span>
        </el-form-item>
        <el-form-item label="事由">
          <el-input v-model="form.reason" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>

      <!-- 采购/差旅费用细项（编辑模式：列出所有细项，每行"挂发票"按钮直达） -->
      <div v-if="editing && editingId && editPurchaseItems.length" class="purchase-items">
        <div class="linked-header">
          <span class="linked-title">{{ editItemKind === 'travel' ? '差旅费用细项' : '采购申请细项' }}（来源{{ editItemKind === 'travel' ? '差旅' : '采购' }}单：<strong>{{ editItemKind === 'travel' ? (editingRow?.travel_requisition_id ? '#' + editingRow.travel_requisition_id : '-') : (editingRow?.purchase_requisition_id ? '#' + editingRow.purchase_requisition_id : '-') }}</strong>）</span>
          <div class="header-actions">
            <el-button type="primary" size="small" @click="openUploadToPool">
              <AppIcon name="Upload" />上传发票
            </el-button>
            <span class="text-muted">点细项行末尾的「挂发票」从发票池选择发票入账</span>
          </div>
        </div>
        <el-table :data="editPurchaseItems" border stripe size="small">
          <el-table-column label="序号" width="55" align="center">
            <template #default="{ $index }">{{ $index + 1 }}</template>
          </el-table-column>
          <el-table-column :label="editItemKind === 'travel' ? '费用名称' : '物品/服务'" prop="item_name" min-width="140" show-overflow-tooltip />
          <el-table-column v-if="editItemKind !== 'travel'" label="规格" prop="spec" width="110" show-overflow-tooltip />
          <el-table-column v-if="editItemKind !== 'travel'" label="数量" prop="quantity" width="60" align="center" />
          <el-table-column label="预算金额" width="100" align="right">
            <template #default="{ row }">¥{{ formatMoney(row.amount) }}</template>
          </el-table-column>
          <el-table-column v-if="editItemKind !== 'travel'" label="供应商" prop="supplier" min-width="100" show-overflow-tooltip />
          <el-table-column label="已挂" width="80" align="center">
            <template #default="{ row }">
              <span :class="{ 'has-invoices': (editItemInvoiceCount.get(row.id) || 0) > 0 }">
                {{ editItemInvoiceCount.get(row.id) || 0 }} 张
              </span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" align="center" fixed="right">
            <template #default="{ row }">
              <el-button link type="success" size="small" @click="openAttachFromEdit(row.id)">挂发票</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 已关联发票（编辑模式或保存后可见） -->
      <div v-if="editing && editingId" class="linked-invoices">
        <div class="linked-header">
          <span class="linked-title">已关联发票</span>
          <!-- 无采购细项时（差旅报销 / 手工采购报销）补统一挂发票入口，照抄采购细项行按钮的同一 AttachInvoiceDialog -->
          <div v-if="!editPurchaseItems.length" class="header-actions">
            <el-button type="primary" size="small" @click="openAttachFromEdit(null)">挂发票</el-button>
          </div>
        </div>
        <el-table :key="linkedTableKey" :data="linkedInvoices" border stripe size="small" empty-text="暂无发票，点击上方按钮添加">
          <el-table-column prop="invoice_date" label="开票日期" width="95" />
          <el-table-column prop="invoice_type" label="类型" width="90" />
          <el-table-column prop="invoice_code" label="发票编码" width="150" show-overflow-tooltip />
          <el-table-column prop="no" label="发票号码" width="110" />
          <el-table-column prop="seller_name" label="销方名称" min-width="120" show-overflow-tooltip />
          <el-table-column label="对应细项" width="120" show-overflow-tooltip>
            <template #default="{ row }">
              {{ itemLabel(row) }}
            </template>
          </el-table-column>
          <el-table-column label="不含税金额" width="95" align="right">
            <template #default="{ row }">
              ¥{{ invoiceSubtotal(row).toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column label="税率" width="70" align="center">
            <template #default="{ row }">
              {{ invoiceTaxRateLabel(row) }}
            </template>
          </el-table-column>
          <el-table-column label="税金" width="90" align="right">
            <template #default="{ row }">
              ¥{{ invoiceTax(row).toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column label="含税价金额" width="95" align="right">
            <template #default="{ row }">
              ¥{{ invoiceTotal(row).toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="70" align="center">
            <template #default="{ row }">
              <el-button link type="danger" size="small" @click="unlinkInvoice(row)">移除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <!-- 挂发票弹窗（编辑弹窗里点采购细项行的"挂发票"触发） -->
    <AttachInvoiceDialog
      v-model="attachVisible"
      :bill="attachBill"
      :initial-item-id="attachInitialItemId"
      @attached="onAttachDone"
    />

    <!-- 上传发票到池（点击「增加发票」触发，统一入口，先入发票池再挂接） -->
    <UploadToInboxDialog v-model="uploadVisible" @saved="onUploadSaved" />

    <!-- 挂发票入口已迁至「我的报销」页（MyReimburse.vue）——此处不重复 -->

    <!-- 增加发票弹窗（支持上传识别 + 人工核实） -->
    <el-dialog v-model="invoiceDialogVisible" title="增加发票" width="780px" :close-on-click-modal="false">
      <!-- 上传识别区 -->
      <div class="recognize-section">
        <div class="recognize-title">
          <AppIcon name="Picture"/>
          <span>上传发票自动识别</span>
        </div>
        <el-upload
          drag
          action="#"
          :auto-upload="false"
          accept=".jpg,.jpeg,.png,.pdf,.ofd"
          :show-file-list="false"
          :disabled="recognizing"
          :on-change="onRecognizeFileChange"
          class="recognize-uploader"
        >
          <AppIcon class="recognize-upload-icon" name="Picture" />
          <div class="recognize-upload-text">
            <p>点击或拖拽上传发票图片 / PDF / OFD</p>
            <p class="recognize-upload-tip">支持 JPG、PNG、PDF、OFD 格式，上传后自动识别并填入下方表单</p>
          </div>
        </el-upload>

        <div v-if="recognizeFile" class="recognize-file">
          <div class="recognize-file-info">
            <AppIcon name="Document"/>
            <span class="recognize-file-name">{{ recognizeFile.name }}</span>
            <el-button text type="danger" size="small" :disabled="recognizing" @click="removeRecognizeFile">
              <AppIcon name="Close"/>
            </el-button>
          </div>
          <div v-if="recognizePreviewUrl && recognizeFile.type.startsWith('image')" class="recognize-image-preview">
            <img :src="recognizePreviewUrl" alt="发票预览" />
          </div>
        </div>

        <div v-if="recognizing" class="recognize-loading">
          <AppIcon class="recognize-spin" name="Refresh" />
          <span>正在识别发票内容，请稍候…</span>
        </div>

        <el-alert
          v-if="recognizeError"
          :title="recognizeError"
          type="warning"
          :closable="false"
          show-icon
          class="recognize-error"
        />
      </div>

      <el-divider content-position="left">识别结果核实</el-divider>

      <el-form ref="invoiceFormRef" :model="invoiceForm" :rules="invoiceRules" label-width="100px">
        <div class="invoice-form-row">
          <el-form-item label="发票类型" prop="invoice_type" style="flex: 1">
            <el-select v-model="invoiceForm.invoice_type" style="width: 100%">
              <el-option v-for="t in invoiceTypes" :key="t" :label="t" :value="t" />
            </el-select>
          </el-form-item>
          <el-form-item label="开票日期" prop="invoice_date" style="flex: 1">
            <el-date-picker v-model="invoiceForm.invoice_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
          </el-form-item>
        </div>
        <div class="invoice-form-row">
          <el-form-item label="发票代码" prop="code" style="flex: 1">
            <el-input v-model="invoiceForm.code" placeholder="数电票可空" />
          </el-form-item>
          <el-form-item label="发票号码" prop="no" style="flex: 1">
            <el-input v-model="invoiceForm.no" placeholder="必填" />
          </el-form-item>
        </div>
        <el-form-item label="购买方">
          <el-input v-model="invoiceForm.buyer_name" placeholder="购买方名称" />
        </el-form-item>
        <el-form-item label="销方名称" prop="seller_name">
          <el-input v-model="invoiceForm.seller_name" placeholder="必填" />
        </el-form-item>
        <div class="invoice-form-row">
          <el-form-item label="结算科目" prop="account" style="flex: 1">
            <el-select v-model="invoiceForm.account" placeholder="请选择" style="width: 100%">
              <el-option v-for="a in accountOptions" :key="a" :label="a" :value="a" />
            </el-select>
          </el-form-item>
          <el-form-item label="是否认证" style="flex: 1">
            <el-radio-group v-model="invoiceForm.certify">
              <el-radio label="current">本期认证</el-radio>
              <el-radio label="none">暂不认证</el-radio>
            </el-radio-group>
          </el-form-item>
        </div>
        <el-form-item label="备注">
          <el-input v-model="invoiceForm.remark" type="textarea" :rows="2" />
        </el-form-item>

        <!-- 明细 -->
        <div class="detail-section">
          <table class="detail-table">
            <thead>
              <tr>
                <th style="width: 120px">业务类型</th>
                <th style="min-width: 160px">开票项目</th>
                <th style="width: 70px">数量</th>
                <th style="width: 110px">金额</th>
                <th style="width: 90px">税率%</th>
                <th style="width: 100px">税额</th>
                <th style="width: 110px">价税合计</th>
                <th style="width: 50px">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(d, idx) in invoiceForm.details" :key="idx">
                <td>
                  <el-select v-model="d.biz_type" size="small" style="width: 100%">
                    <el-option v-for="b in bizTypeOptions" :key="b" :label="b" :value="b" />
                  </el-select>
                </td>
                <td>
                  <el-input v-model="d.item" size="small" placeholder="开票项目" />
                </td>
                <td>
                  <el-input-number v-model="d.qty" :min="1" :controls="false" size="small" style="width: 100%" />
                </td>
                <td>
                  <el-input-number v-model="d.amount" :min="0" :precision="2" :controls="false" size="small" style="width: 100%" @change="calcDetail(d)" />
                </td>
                <td>
                  <el-select v-model="d.tax_rate" size="small" style="width: 100%" @change="calcDetail(d)">
                    <el-option v-for="r in taxRateOptions" :key="r" :label="r" :value="Number(r)" />
                  </el-select>
                </td>
                <td>
                  <el-input-number v-model="d.tax" :precision="2" :controls="false" size="small" style="width: 100%" disabled />
                </td>
                <td>
                  <el-input-number v-model="d.total" :precision="2" :controls="false" size="small" style="width: 100%" disabled />
                </td>
                <td>
                  <el-button text type="danger" size="small" @click="removeDetail(idx)">
                    <AppIcon name="Delete"/>
                  </el-button>
                </td>
              </tr>
            </tbody>
          </table>
          <el-button text type="primary" size="small" @click="addDetail">
            <AppIcon name="Plus"/>添加明细行
          </el-button>
        </div>
      </el-form>

      <template #footer>
        <el-button @click="invoiceDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitInvoice">保存并关联</el-button>
      </template>
    </el-dialog>

    <!-- 审批弹窗 -->
    <el-dialog
      v-model="approveDialogVisible"
      :title="approveAction === 'approve' ? '审批通过' : '驳回报销单'"
      width="420px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="approveFormRef"
        :model="approveForm"
        :rules="approveRules"
        label-width="90px"
      >
        <el-form-item label="报销单号">
          <el-input :model-value="approveRow?.bill_no ?? approveRow?.id" disabled />
        </el-form-item>
        <el-form-item label="审批人" prop="approver">
          <el-input v-model="approveForm.approver" placeholder="请输入审批人姓名" />
        </el-form-item>
        <el-form-item label="审批意见">
          <el-input
            v-model="approveForm.remark"
            type="textarea"
            :rows="3"
            placeholder="选填"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="approveDialogVisible = false">取消</el-button>
        <el-button :type="approveAction === 'approve' ? 'success' : 'danger'" @click="submitApprove">
          {{ approveAction === 'approve' ? '确认通过' : '确认驳回' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 报销单浏览弹窗（先展示再打印） -->
    <el-dialog
      v-model="detailVisible"
      title="报销单浏览"
      width="900px"
      :close-on-click-modal="false"
      class="detail-dialog"
    >
      <div v-if="detailLoading" class="detail-loading">正在加载报销单…</div>
      <ReimbursePrint
        v-else-if="detailRow"
        :bill="detailRow"
        :summary="detailSummary"
        :purchase="detailPurchase"
        :invoices="detailInvoices"
      />
      <template #footer>
        <div class="detail-footer">
          <el-button @click="detailVisible = false">关闭</el-button>
          <el-button type="primary" @click="printReimbursement">打印报销单</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { reimburseApi } from '@/api/reimburse'
import { invoiceApi } from '@/api/invoice'
import type { ReimbursementBill } from '@/types/reimburse'
import type { Invoice, InvoiceCreatePayload } from '@/types/invoice'
import { parseInvoiceFile, type ParsedInvoice } from '@/utils/invoiceParser'
import { purchaseApi } from '@/api/purchase'
import { travelApi } from '@/api/travel'
import type { PurchaseItem, PurchaseReq } from '@/types/purchase'
import type { TravelItem } from '@/types/travel'
import AttachInvoiceDialog from '@/components/AttachInvoiceDialog.vue'
import UploadToInboxDialog from '@/components/UploadToInboxDialog.vue'
import ReimbursePrint from './ReimbursePrint.vue'

const statusOptions = ['草稿', '待审批', '已通过', '已归档', '已驳回', '已支付']

const invoiceTypes = [
  '增值税专用发票',
  '增值税普通发票',
  '电子专用发票',
  '电子普通发票',
  '机动车销售统一发票',
  '火车票',
  '机票',
  '航空运输电子客票行程单',
  '铁路电子客票',
]
const taxRateOptions = ['0', '1', '3', '6', '9', '13']
const accountOptions = ['库存商品', '管理费用', '销售费用', '固定资产', '原材料', '工程施工', '管理费用-差旅费']
const bizTypeOptions = ['采购商品', '接受服务', '采购固定资产', '费用报销', '其他']

const keyword = ref('')
const statusFilter = ref<string | null>(null)
const list = ref<ReimbursementBill[]>([])
const loading = ref(false)

// 路由驱动 bill_type 过滤：采购报销/差旅报销 各自只显示对应类型；报销单(/reimburse/bill)显示全部。
const route = useRoute()
const routeBillType = computed<string | undefined>(() => {
  switch (route.name) {
    case 'PurchaseReimburse': return '采购报销'
    case 'TravelReimburse': return '差旅报销'
    default: return undefined
  }
})
const dialogVisible = ref(false)
const editing = ref(false)
const editingId = ref<number | null>(null)
const editingRow = ref<ReimbursementBill | null>(null)
const previewBillNo = ref<string | null>(null)
const linkedInvoices = ref<Invoice[]>([])
const linkedTableKey = ref(0)

// 编辑中报销单的「发票合计」= 已挂发票含税合计（实时算，不存）
const editingInvoiceTotal = computed(() => {
  return linkedInvoices.value.reduce((s, inv) => s + invoiceTotal(inv), 0)
})
// 采购/差旅细项 id → 名称映射（openEdit 拉取来源单的 items 时填充，供"已关联发票"表"对应细项"列展示）
const itemNameMap = ref<Record<number, string>>({})
// 编辑模式下当前报销单对应的细项（采购或差旅，结构兼容：都有 id/item_name/amount）
const editPurchaseItems = ref<(PurchaseItem | TravelItem)[]>([])
const editItemInvoiceCount = ref<Map<number, number>>(new Map())
// 区分细项来源：采购报销 → 'purchase'，差旅报销 → 'travel'
const editItemKind = ref<'purchase' | 'travel' | null>(null)

// 已关联发票表"对应细项"列：兼容采购细项和差旅细项
function itemLabel(row: Invoice): string {
  if (row.purchase_requisition_item_id) {
    return itemNameMap.value[row.purchase_requisition_item_id] || '#' + row.purchase_requisition_item_id
  }
  if (row.travel_requisition_item_id) {
    return itemNameMap.value[row.travel_requisition_item_id] || '#' + row.travel_requisition_item_id
  }
  return '—'
}

// 挂发票弹窗（编辑弹窗里点细项行的"挂发票"按钮触发）
const attachVisible = ref(false)
const attachBill = ref<ReimbursementBill | null>(null)
const attachInitialItemId = ref<number | null>(null)

// 上传发票到池（统一组件）
const uploadVisible = ref(false)

// 报销单浏览/预览弹窗（先展示再打印，参照采购「浏览」模式）
const detailVisible = ref(false)
const detailLoading = ref(false)
const detailRow = ref<ReimbursementBill | null>(null)
const detailPurchase = ref<PurchaseReq | null>(null)
const detailInvoices = ref<Invoice[]>([])
const detailSummary = ref<InvoiceSummary>({ amount: 0, tax: 0, total: 0, invoice_count: 0 })

function openUploadToPool() {
  uploadVisible.value = true
}

function onUploadSaved() {
  ElMessage.success('发票已暂存到发票池，可在挂发票中选择并入单')
}

// 审批弹窗
const approveDialogVisible = ref(false)
const approveAction = ref<'approve' | 'reject' | null>(null)
const approveRow = ref<ReimbursementBill | null>(null)
const approveForm = ref({ approver: '', remark: '' })
const approveFormRef = ref<any>(null)
const approveRules = {
  approver: [{ required: true, message: '请输入审批人', trigger: 'blur' }],
}

const emptyForm = () => ({
  bill_no: null as string | null,
  applicant: '',
  department: '',
  amount: null as number | null,
  reimburse_amount: null as number | null,
  reason: '',
  remark: '',
  bill_type: '采购报销' as string,
  traveler: '' as string,
  travel_destination: '' as string,
  travel_start: null as string | null,
  travel_end: null as string | null,
})
const form = reactive(emptyForm())

// 出差起止日期区间：与 form.travel_start / travel_end 双向联动
const travelRange = computed<string[]>({
  get: () => [form.travel_start || '', form.travel_end || ''],
  set: (v) => {
    form.travel_start = v?.[0] || null
    form.travel_end = v?.[1] || null
  },
})

// 每个报销单的发票汇总（金额/张数）
interface InvoiceSummary {
  amount: number
  tax: number
  total: number
  invoice_count: number
}
const summaryMap = ref<Record<number, InvoiceSummary>>({})

interface RowAction {
  action: 'submit' | 'approve' | 'reject' | 'submit_finance' | 'revert' | 'pay' | 'view'
  label: string
  type: 'warning' | 'success' | 'danger' | 'primary' | 'info'
}

function transformActions(row: ReimbursementBill): RowAction[] {
  switch (row.status) {
    case '草稿':
    case '已驳回':
      return [{ action: 'submit', label: '提交', type: 'warning' }]
    case '待审批':
      return [
        { action: 'approve', label: '通过', type: 'success' },
        { action: 'reject', label: '驳回', type: 'danger' },
      ]
    case '已通过':
      return [
        { action: 'submit_finance', label: '提交财务', type: 'primary' },
        { action: 'revert', label: '退回', type: 'info' },
      ]
    case '已归档':
      return [
        { action: 'pay', label: '支付', type: 'success' },
        { action: 'view', label: '浏览', type: 'info' },
      ]
    case '已支付':
      return [{ action: 'view', label: '浏览', type: 'info' }]
    default:
      return []
  }
}

async function load() {
  loading.value = true
  try {
    const params: { keyword?: string; status?: string; bill_type?: string } = {}
    if (keyword.value) params.keyword = keyword.value
    if (statusFilter.value) params.status = statusFilter.value
    if (routeBillType.value) params.bill_type = routeBillType.value
    const res = await reimburseApi.list(params)
    list.value = res.data
    await loadInvoiceSummaries(res.data)
  } finally {
    loading.value = false
  }
}

async function loadInvoiceSummaries(bills: ReimbursementBill[]) {
  const map: Record<number, InvoiceSummary> = {}
  await Promise.all(
    bills.map(async (bill) => {
      try {
        const res = await invoiceApi.summaryByBill(bill.id)
        map[bill.id] = res.data
      } catch (e) {
        map[bill.id] = { amount: 0, tax: 0, total: 0, invoice_count: 0 }
      }
    })
  )
  summaryMap.value = map
}

async function loadLinkedInvoices() {
  if (!editingId.value) {
    linkedInvoices.value = []
    return
  }
  try {
    const res = await invoiceApi.list({ reimbursement_bill_id: editingId.value })
    linkedInvoices.value = res.data
    linkedTableKey.value += 1
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载已关联发票失败')
  }
}

function toNum(v: any): number {
  if (v === null || v === undefined || v === '') return 0
  const n = Number(v)
  return Number.isFinite(n) ? n : 0
}

function formatMoney(v: any): string {
  const n = toNum(v)
  return n.toFixed(2)
}

// 报销金额显示：优先取 reimburse_amount；为空则回落到发票合计（默认=发票合计）
function reimburseDisplay(row: ReimbursementBill): string {
  const ra = row.reimburse_amount != null ? Number(row.reimburse_amount) : null
  const invoiceTotal = Number(summaryMap.value[row.id]?.total || 0)
  const v = ra != null ? ra : invoiceTotal
  return v ? '¥' + v.toFixed(2) : '-'
}

function invoiceSubtotal(inv: Invoice): number {
  return (inv.details || []).reduce((sum, d) => sum + toNum(d.amount), 0)
}

function invoiceTax(inv: Invoice): number {
  return (inv.details || []).reduce((sum, d) => sum + toNum(d.tax), 0)
}

function invoiceTotal(inv: Invoice): number {
  return (inv.details || []).reduce((sum, d) => sum + toNum(d.total), 0)
}

function invoiceTaxRateLabel(inv: Invoice): string {
  const details = inv.details || []
  if (details.length === 0) return '-'
  const rates = Array.from(new Set(details.map((d) => d.tax_rate).filter((r) => r !== null && r !== undefined)))
  if (rates.length === 0) return '-'
  if (rates.length === 1) {
    const r = Number(rates[0])
    return `${r}%`
  }
  return '多税率'
}

async function openCreate() {
  Object.assign(form, emptyForm())
  if (routeBillType.value) form.bill_type = routeBillType.value
  editing.value = false
  editingId.value = null
  previewBillNo.value = null
  linkedInvoices.value = []
  linkedTableKey.value += 1
  dialogVisible.value = true
  try {
    const res = await reimburseApi.nextBillNo()
    previewBillNo.value = res.data.bill_no
  } catch (e: any) {
    // 预占单号失败仍可继续，保存时后端会生成
    console.warn('预占单号失败', e)
  }
}

async function openEdit(row: ReimbursementBill) {
  Object.assign(form, emptyForm(), row)
  editing.value = true
  editingId.value = row.id
  previewBillNo.value = row.bill_no ?? null
  editingRow.value = row
  dialogVisible.value = true
  await loadLinkedInvoices()
  // 报销金额默认=发票合计（reimburse_amount 为空时回落）
  if (form.reimburse_amount == null) {
    form.reimburse_amount = editingInvoiceTotal.value || null
  }
  // 采购/差旅报销且有来源单 → 加载细项 + 已挂统计（供编辑弹窗的细项区）
  editPurchaseItems.value = []
  editItemInvoiceCount.value = new Map()
  editItemKind.value = null
  if (row.purchase_requisition_id) {
    editItemKind.value = 'purchase'
    try {
      const res = await purchaseApi.get(row.purchase_requisition_id)
      const items = (res.data.items || []) as PurchaseItem[]
      editPurchaseItems.value = items
      const map: Record<number, string> = {}
      items.forEach((it: PurchaseItem) => { if (it.id) map[it.id] = it.item_name })
      itemNameMap.value = map
      const linkedRes = await invoiceApi.list({ reimbursement_bill_id: row.id })
      const counts = new Map<number, number>()
      ;(linkedRes.data || []).forEach((inv: Invoice) => {
        if (inv.purchase_requisition_item_id) {
          counts.set(inv.purchase_requisition_item_id, (counts.get(inv.purchase_requisition_item_id) || 0) + 1)
        }
      })
      editItemInvoiceCount.value = counts
    } catch {
      // 非关键异常
    }
  } else if (row.travel_requisition_id) {
    // 差旅报销：加载差旅费用细项（镜像采购报销流程）
    editItemKind.value = 'travel'
    try {
      const res = await travelApi.get(row.travel_requisition_id)
      const items = (res.data.items || []) as TravelItem[]
      editPurchaseItems.value = items
      const map: Record<number, string> = {}
      items.forEach((it: TravelItem) => { if (it.id) map[it.id] = it.item_name })
      itemNameMap.value = map
      const linkedRes = await invoiceApi.list({ reimbursement_bill_id: row.id })
      const counts = new Map<number, number>()
      ;(linkedRes.data || []).forEach((inv: Invoice) => {
        if (inv.travel_requisition_item_id) {
          counts.set(inv.travel_requisition_item_id, (counts.get(inv.travel_requisition_item_id) || 0) + 1)
        }
      })
      editItemInvoiceCount.value = counts
    } catch {
      // 非关键异常
    }
  }
}

// 从编辑弹窗里"采购申请细项"表的某行点"挂发票"按钮触发
function openAttachFromEdit(itemId: number | null) {
  if (!editingId.value) return
  // 构造 attachBill：用当前表单的最新数据（编辑后未保存的字段也带上）
  attachBill.value = {
    ...(form as any),
    id: editingId.value,
    bill_no: previewBillNo.value,
  } as ReimbursementBill
  attachInitialItemId.value = itemId
  attachVisible.value = true
}

async function onAttachDone() {
  // 关联成功后：刷新已挂发票表 + 各细项已挂计数 + 列表的发票数（summaryMap）
  await loadLinkedInvoices()
  if (editingId.value) {
    // 刷新当前编辑单据的 summaryMap（挂发票弹窗关闭后老板要看到正确的「N 张」）
    try {
      const res = await invoiceApi.summaryByBill(editingId.value)
      summaryMap.value[editingId.value] = res.data
    } catch {
      // 非关键
    }
  }
  if (!editingId.value) return
  try {
    const linkedRes = await invoiceApi.list({ reimbursement_bill_id: editingId.value })
    const counts = new Map<number, number>()
    ;(linkedRes.data || []).forEach((inv: Invoice) => {
      if (inv.purchase_requisition_item_id) {
        counts.set(inv.purchase_requisition_item_id, (counts.get(inv.purchase_requisition_item_id) || 0) + 1)
      }
      if (inv.travel_requisition_item_id) {
        counts.set(inv.travel_requisition_item_id, (counts.get(inv.travel_requisition_item_id) || 0) + 1)
      }
    })
    editItemInvoiceCount.value = counts
  } catch {
    // 非关键
  }
}

async function save() {
  const payload: Record<string, unknown> = { ...form }
  if (payload.amount === '' || payload.amount === null) payload.amount = null
  // 报销金额校验：有发票时须 >0 且 ≤ 发票合计
  if (editing.value && editingId.value != null) {
    const invTotal = editingInvoiceTotal.value
    const ra = form.reimburse_amount != null ? Number(form.reimburse_amount) : null
    if (invTotal > 0) {
      if (ra == null || ra <= 0) {
        ElMessage.warning('报销金额须大于 0')
        return
      }
      if (ra > invTotal + 0.01) {
        ElMessage.warning(`报销金额不能超过发票合计 ¥${invTotal.toFixed(2)}`)
        return
      }
    }
    if (payload.reimburse_amount === '' || payload.reimburse_amount === null) payload.reimburse_amount = null
    await reimburseApi.update(editingId.value, payload)
    ElMessage.success('已更新')
    dialogVisible.value = false
    load()
  } else {
    // 新建：若有预占单号则传入，保持前后一致
    if (previewBillNo.value && !payload.bill_no) {
      payload.bill_no = previewBillNo.value
    }
    const res = await reimburseApi.create(payload)
    ElMessage.success('已创建')
    // 保存后进入编辑态，方便继续增加发票
    editing.value = true
    editingId.value = res.data.id
    form.bill_no = res.data.bill_no ?? null
    previewBillNo.value = res.data.bill_no ?? null
    await loadLinkedInvoices()
    await load()
  }
}

// 金额大写（人民币）
function moneyToChinese(n: number): string {
  if (!isFinite(n)) return '-'
  if (n < 0) return '负' + moneyToChinese(-n)
  if (n === 0) return '零元整'
  const intPart = Math.floor(n)
  const cents = Math.round((n - intPart) * 100)
  const digit = ['零', '壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖']
  const unit = ['', '拾', '佰', '仟']
  const secUnit = ['', '万', '亿', '兆']
  let intStr = ''
  if (intPart > 0) {
    const s = String(intPart)
    const secs: string[] = []
    for (let i = s.length; i > 0; i -= 4) {
      secs.unshift(s.slice(Math.max(0, i - 4), i))
    }
    let needZero = false
    secs.forEach((sec, idx) => {
      const secPos = secs.length - 1 - idx
      let secStr = ''
      let zeroInSec = false
      for (let i = 0; i < sec.length; i++) {
        const d = sec.charCodeAt(i) - 48
        const unitPos = sec.length - 1 - i
        if (d === 0) {
          zeroInSec = true
        } else {
          if (zeroInSec || (needZero && secStr.length > 0)) secStr += digit[0]
          secStr += digit[d] + unit[unitPos]
          zeroInSec = false
        }
      }
      if (secStr.length > 0) {
        intStr += secStr + secUnit[secPos]
        needZero = zeroInSec
      } else if (needZero) {
        needZero = false
      }
    })
    intStr += '元'
  } else {
    intStr = '零元'
  }
  const jiao = Math.floor(cents / 10)
  const fen = cents % 10
  let decStr = ''
  if (jiao === 0 && fen === 0) {
    if (intPart > 0) decStr = '整'
  } else {
    if (jiao > 0) decStr += digit[jiao] + '角'
    else if (intPart > 0) decStr += digit[0]
    if (fen > 0) decStr += digit[fen] + '分'
  }
  return intStr + decStr
}

async function openDetail(row: ReimbursementBill) {
  detailVisible.value = true
  detailLoading.value = true
  detailRow.value = row
  detailSummary.value = summaryMap.value[row.id] || { amount: 0, tax: 0, total: 0, invoice_count: 0 }
  detailPurchase.value = null
  detailInvoices.value = []
  try {
    const res = await reimburseApi.get(row.id)
    const fullBill = res.data
    detailRow.value = fullBill
    detailInvoices.value = fullBill.invoices || []
    if (fullBill.purchase_requisition_id) {
      try {
        const pRes = await purchaseApi.get(fullBill.purchase_requisition_id)
        detailPurchase.value = pRes.data
      } catch (e) {
        console.warn('加载来源采购单失败', e)
      }
    }
  } catch (e: any) {
    ElMessage.warning(e?.response?.data?.detail || '详情加载失败，已展示列表数据')
  } finally {
    detailLoading.value = false
  }
}

function printReimbursement() {
  const p = detailRow.value
  if (!p) return
  const billType = p.bill_type || '采购报销'
  const summary = detailSummary.value || { total: 0, amount: 0, tax: 0, invoice_count: 0 }
  const budgetAmount = Number(p.amount != null ? p.amount : 0)        // 预算金额
  const invoiceTotal = Number(summary.total || 0)                      // 发票合计（含税）
  // 报销金额：优先 reimburse_amount，为空回落到发票合计（默认=发票合计）
  const reimburse = p.reimburse_amount != null ? Number(p.reimburse_amount) : invoiceTotal
  const cnAmount = moneyToChinese(reimburse)

  const travelRows = billType === '差旅报销'
    ? `<tr>
      <td class="label">出差人</td><td>${p.traveler || '-'}</td>
      <td class="label">出差地点</td><td colspan="3">${p.travel_destination || '-'}</td>
    </tr>
    <tr>
      <td class="label">出差起止</td><td colspan="5">${p.travel_start || '-'} 至 ${p.travel_end || '-'}</td>
    </tr>`
    : ''
  const purchaseRow = p.purchase_requisition_id
    ? `<tr><td class="label">来源采购单</td><td colspan="5">采购单 #${p.purchase_requisition_id}</td></tr>`
    : ''

  // 采购细项：按来源采购单的 items 逐行展示，并匹配已挂发票
  const purchaseItems = detailPurchase.value?.items || []
  const invoices = detailInvoices.value || []
  const purchaseDetailRows = purchaseItems.length
    ? purchaseItems.map((it, idx) => {
        const matched = invoices.filter((inv) => inv.purchase_requisition_item_id === it.id)
        const total = matched.reduce(
          (s, inv) => s + (inv.details || []).reduce((ds, d) => ds + (Number(d.total) || 0), 0),
          0,
        )
        return `
      <tr>
        <td style="text-align:center;width:40px">${idx + 1}</td>
        <td class="left">${it.item_name || '-'}</td>
        <td style="width:130px">${matched.map((inv) => inv.no).join(', ') || '-'}</td>
        <td style="width:140px">${matched.map((inv) => inv.seller_name).join(', ') || '-'}</td>
        <td style="width:100px;text-align:center">${matched.map((inv) => inv.invoice_date).filter(Boolean).join(', ') || '-'}</td>
        <td style="width:110px" class="num">¥${total.toFixed(2)}</td>
        <td class="left">${it.remark || '-'}</td>
      </tr>`
      }).join('')
    : `<tr><td colspan="7" style="text-align:center;color:#999;padding:20px">暂无采购细项</td></tr>`
  const purchaseDetailSection = purchaseItems.length
    ? `<div class="section-title">二、采购细项</div>
  <table class="detail-table">
    <thead><tr>
      <th style="width:40px">编号</th><th>采购内容</th>
      <th style="width:130px">发票号</th><th style="width:140px">销售方</th>
      <th style="width:100px">开票日期</th><th style="width:110px">发票金额<br><span style="font-size:9pt;font-weight:normal;color:#555">（价税合计）</span></th>
      <th>备注</th>
    </tr></thead>
    <tbody>${purchaseDetailRows}</tbody>
  </table>`
    : ''

  const html = `<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>报销申请单</title>
<style>
@page { size: A4; margin: 8mm 12mm; }
body { font-family: 'PingFang SC','Microsoft YaHei',sans-serif; padding:0; margin:0; }
.bill-form { width:210mm; min-height:297mm; margin:0 auto; padding:6mm 12mm; box-sizing:border-box; background:#fff; color:#000; font-size:10pt; }
.form-title { position:relative; text-align:center; border-bottom:2px solid #000; padding-bottom:8px; margin-bottom:12px; }
.company { font-size:15pt; font-weight:bold; letter-spacing:2px; }
.doc-type { font-size:17pt; font-weight:bold; margin-top:3px; }
.unit { position:absolute; right:0; top:0; font-size:9pt; color:#333; }
.section-title { font-weight:bold; margin:12px 0 5px; font-size:10pt; }
table { width:100%; border-collapse:collapse; table-layout:fixed; }
.info-table td, .sign-table td, .detail-table th, .detail-table td { border:1px solid #333; padding:3px 5px; word-break:break-all; vertical-align:middle; }
.detail-table th { background:#f2f2f2; font-weight:600; text-align:center; font-size:10pt; }
.detail-table td { font-size:11pt; }
.detail-table td.left { text-align:left; }
.label { background:#f2f2f2; font-weight:600; text-align:center; width:78px; font-size:10pt; }
.base-table td { font-size:11pt; }
.num { text-align:right; font-family:'Courier New',monospace; font-size:14pt; font-weight:bold; color:#000; }
.num-strong { text-align:right; font-weight:bold; font-family:'Courier New',monospace; font-size:16pt; color:#000; }
.cn-amount { font-size:14pt; font-weight:bold; color:#000; }
.bill-no { word-break:break-all; text-align:center; font-family:'Courier New',monospace; font-size:12pt; font-weight:bold; letter-spacing:0.5px; color:#000; }
.date-cell { white-space:nowrap; text-align:center; font-size:11pt; }
.sign-table td { text-align:center; height:28px; }
.sign-row td { height:56px; }
.form-footer { margin-top:12px; font-size:9pt; color:#333; }
</style></head>
<body>
<div class="bill-form">
  <div class="form-title">
    <div class="company">深圳市流形机器人科技有限公司</div>
    <div class="doc-type">报销申请单</div>
    <div class="unit">单位：元</div>
  </div>
  <div class="section-title">一、基本信息</div>
  <table class="info-table base-table">
    <tr>
      <td class="label">报销单号</td><td class="bill-no">${p.bill_no || '-'}</td>
      <td class="label">报销类型</td><td>${billType}</td>
      <td class="label">申请日期</td><td class="date-cell">${p.submit_date || '-'}</td>
    </tr>
    <tr>
      <td class="label">申请人</td><td>${p.applicant || '-'}</td>
      <td class="label">部门</td><td colspan="3">${p.department || '-'}</td>
    </tr>
    ${travelRows}
    ${purchaseRow}
    <tr><td class="label">事由</td><td colspan="5">${p.reason || '-'}</td></tr>
    <tr><td class="label">备注</td><td colspan="5">${p.remark || '-'}</td></tr>
  </table>
  ${purchaseDetailSection}
  <div class="section-title">三、金额汇总</div>
  <table class="info-table base-table">
    <tr>
      <td class="label">发票张数</td><td>${summary.invoice_count} 张</td>
      <td class="label">不含税金额</td><td class="num">¥${Number(summary.amount || 0).toFixed(2)}</td>
      <td class="label">税额</td><td class="num">¥${Number(summary.tax || 0).toFixed(2)}</td>
    </tr>
    <tr>
      <td class="label">预算金额</td><td class="num" colspan="2">¥${budgetAmount.toFixed(2)}</td>
      <td class="label">发票合计</td><td class="num" colspan="2">¥${invoiceTotal.toFixed(2)}</td>
    </tr>
    <tr>
      <td class="label">报销金额</td><td class="num num-strong" colspan="2">¥${reimburse.toFixed(2)}</td>
      <td class="label">金额大写</td><td class="cn-amount" colspan="2">${cnAmount}</td>
    </tr>
  </table>
  <div class="section-title">四、审批与支付</div>
  <table class="info-table base-table">
    <tr>
      <td class="label">状态</td><td>${p.status || '-'}</td>
      <td class="label">审批人</td><td>${p.approver || '-'}</td>
      <td class="label">审批日期</td><td class="date-cell">${p.approve_date || '-'}</td>
    </tr>
    <tr>
      <td class="label">审批意见</td><td colspan="5">${p.approve_remark || '-'}</td>
    </tr>
    <tr>
      <td class="label">付款日期</td><td colspan="5">${p.pay_date || '-'}</td>
    </tr>
  </table>
  <div class="section-title">五、签字栏</div>
  <table class="sign-table">
    <tr>
      <td class="label">申请人</td>
      <td class="label">部门负责人</td>
      <td class="label">财务负责人</td>
      <td class="label">总经理</td>
    </tr>
    <tr class="sign-row">
      <td>${p.applicant || ''}</td>
      <td></td>
      <td></td>
      <td></td>
    </tr>
  </table>
  <div class="form-footer">备注：本单经审批通过并付款后入账；金额以实际发票为准，差异应在审批意见中说明。</div>
</div>
</body></html>`

  // 使用隐藏 iframe 打印，不被浏览器弹窗拦截
  const iframe = document.createElement('iframe')
  iframe.style.cssText = 'position:fixed;top:-9999px;left:-9999px;width:0;height:0;border:none;'
  document.body.appendChild(iframe)
  const doc = iframe.contentWindow!.document
  doc.open()
  doc.write(html)
  doc.close()
  // 等 iframe 加载完成后触发打印
  iframe.contentWindow!.focus()
  iframe.contentWindow!.print()
  // 打印完后清理 iframe
  setTimeout(() => { if (iframe.parentNode) iframe.parentNode.removeChild(iframe) }, 2000)
}

async function runAction(action: RowAction['action'], row: ReimbursementBill) {
  if (action === 'view') {
    openDetail(row)
    return
  }
  if (action === 'approve' || action === 'reject') {
    approveAction.value = action
    approveRow.value = row
    approveForm.value = { approver: '', remark: '' }
    approveDialogVisible.value = true
    return
  }

  if (action === 'submit_finance') {
    await ElMessageBox.confirm(
      `确认将报销单 ${row.bill_no ?? row.id} 提交财务？提交后不可退回，将自动生成记账凭证形成待支付挂账。`,
      '提交财务确认',
      { type: 'warning', confirmButtonText: '确认提交', cancelButtonText: '取消' },
    )
  } else if (action === 'revert') {
    await ElMessageBox.confirm(
      `确认退回报销单 ${row.bill_no ?? row.id} 至草稿状态？退回后可修改重新提交。`,
      '退回确认',
      { type: 'warning', confirmButtonText: '确认退回', cancelButtonText: '取消' },
    )
  } else if (action === 'pay') {
    await ElMessageBox.confirm(
      `确认支付报销单 ${row.bill_no ?? row.id}？系统将自动生成付款凭证（借：其他应付款，贷：银行存款）。`,
      '支付确认',
      { type: 'warning', confirmButtonText: '确认支付', cancelButtonText: '取消' },
    )
  }

  const map: Record<string, (id: number) => Promise<any>> = {
    submit: reimburseApi.submit,
    submit_finance: reimburseApi.submitFinance,
    revert: reimburseApi.revert,
    pay: reimburseApi.pay,
  }
  await map[action](row.id)
  ElMessage.success('操作成功')
  load()
}

async function submitApprove() {
  if (!approveFormRef.value) return
  await approveFormRef.value.validate()
  if (!approveRow.value || !approveAction.value) return

  const row = approveRow.value
  const data = {
    approver: approveForm.value.approver,
    remark: approveForm.value.remark,
  }
  if (approveAction.value === 'approve') {
    await reimburseApi.approve(row.id, data)
    ElMessage.success('审批通过')
  } else {
    await reimburseApi.reject(row.id, data)
    ElMessage.success('已驳回')
  }
  approveDialogVisible.value = false
  load()
}

async function remove(row: ReimbursementBill) {
  await ElMessageBox.confirm(`确认删除报销单 ${row.bill_no ?? row.id}？`, '提示', { type: 'warning' })
  await reimburseApi.remove(row.id)
  ElMessage.success('已删除')
  load()
}

/* ============ 挂发票入口已迁至 MyReimburse.vue（AttachInvoiceDialog 复用组件） ============ */

/* ============ 增加发票（上传识别） ============ */
const invoiceDialogVisible = ref(false)
const invoiceFormRef = ref<any>(null)

const recognizeFile = ref<File | null>(null)
const recognizePreviewUrl = ref('')
const recognizing = ref(false)
const recognizeError = ref('')

function resetRecognizeState() {
  recognizeFile.value = null
  recognizePreviewUrl.value = ''
  recognizing.value = false
  recognizeError.value = ''
}

function onRecognizeFileChange(uploadFile: any) {
  const raw = uploadFile?.raw || uploadFile
  if (!raw) return
  recognizeFile.value = raw
  recognizePreviewUrl.value = raw.type?.startsWith('image/') ? URL.createObjectURL(raw) : ''
  recognizeError.value = ''
  startRecognize()
}

function removeRecognizeFile() {
  resetRecognizeState()
}

async function startRecognize() {
  if (!recognizeFile.value) return
  recognizing.value = true
  recognizeError.value = ''
  try {
    const parsed = await parseInvoiceFile(recognizeFile.value)
    applyRecognized(parsed)
    ElMessage.success('发票识别完成，请核对下方信息')
  } catch (err: any) {
    console.error('发票识别失败', err)
    recognizeError.value = '发票识别失败：' + (err?.message || '请检查文件格式或改为手工录入')
  } finally {
    recognizing.value = false
  }
}

function applyRecognized(p: ParsedInvoice) {
  // 1. 发票类型推断
  let invoiceType = p.type || '增值税普通发票'
  if (/专票/.test(invoiceType)) invoiceType = '增值税专用发票'
  else if (/普通发票|电子发票/.test(invoiceType) && !/专用/.test(invoiceType)) invoiceType = '增值税普通发票'
  else if (/火车|铁路/.test(invoiceType)) invoiceType = '火车票'
  else if (/机票|航空/.test(invoiceType)) invoiceType = '机票'

  // 2. 根据类型给默认科目和税率
  const isTravel = /火车|铁路|机票|航空/.test(invoiceType)
  const isService = /服务|代理/.test(invoiceType)
  const defaultAccount = isTravel ? '管理费用-差旅费' : isService ? '管理费用' : '管理费用'
  const defaultTaxRate = isTravel ? 9 : isService ? 6 : 13

  // 3. 明细映射
  let details: InvoiceCreatePayload['details'] = []
  if (p.items && p.items.length > 0) {
    details = p.items.map((it) => {
      const amount = Number(it.amount) || 0
      const taxRate = it.taxRate && it.taxRate > 0 ? it.taxRate : defaultTaxRate
      const tax = Number(it.tax) || Number((amount * (taxRate / 100)).toFixed(2))
      return {
        biz_type: isTravel ? '费用报销' : '采购商品',
        item: it.name || (isTravel ? '差旅费' : '见发票明细'),
        qty: Number(it.qty) || 1,
        amount,
        tax_rate: taxRate,
        tax,
        total: Number((amount + tax).toFixed(2)),
      }
    })
  } else {
    const amount = Number(p.amount) || 0
    const tax = Number(p.tax) || 0
    const total = Number(p.total) || Number((amount + tax).toFixed(2))
    details = [
      {
        biz_type: isTravel ? '费用报销' : '采购商品',
        item: p.item || (isTravel ? '差旅费' : '见发票明细'),
        qty: 1,
        amount,
        tax_rate: p.taxRate && p.taxRate > 0 ? p.taxRate : defaultTaxRate,
        tax,
        total,
      },
    ]
  }

  // 4. 填充表单（保留原值兜底，便于用户只修改错误字段）
  Object.assign(invoiceForm, {
    invoice_type: invoiceType,
    code: p.code || null,
    no: p.no || invoiceForm.no,
    invoice_date: p.date || invoiceForm.invoice_date,
    buyer_name: p.buyerName || invoiceForm.buyer_name,
    buyer_tax_no: p.buyerTaxNo || invoiceForm.buyer_tax_no,
    seller_name: p.sellerName || invoiceForm.seller_name,
    seller_tax_no: p.sellerTaxNo || invoiceForm.seller_tax_no,
    account: defaultAccount,
    details,
  })
}

function emptyInvoiceForm(): InvoiceCreatePayload {
  return {
    invoice_type: '增值税专用发票',
    code: null,
    no: '',
    invoice_date: null,
    buyer_name: null,
    buyer_tax_no: null,
    seller_name: '',
    seller_tax_no: null,
    seller_address_phone: null,
    seller_bank_account: null,
    account: null,
    certify: 'none',
    remark: null,
    reimbursement_bill_id: editingId.value,
    attachment_path: null,
    route_info: null,
    traveler: null,
    details: [{ biz_type: '费用报销', item: '', qty: 1, amount: 0, tax_rate: 13, tax: 0, total: 0 }],
  }
}
const invoiceForm = reactive<InvoiceCreatePayload>(emptyInvoiceForm())

const invoiceRules = {
  invoice_type: [{ required: true, message: '请选择发票类型', trigger: 'change' }],
  no: [{ required: true, message: '请输入发票号码', trigger: 'blur' }],
  seller_name: [{ required: true, message: '请输入销方名称', trigger: 'blur' }],
  account: [{ required: true, message: '请选择结算科目', trigger: 'change' }],
}

function calcDetail(d: any) {
  d.tax = Number((d.amount * (d.tax_rate / 100)).toFixed(2))
  d.total = Number((d.amount + d.tax).toFixed(2))
}

function addDetail() {
  invoiceForm.details.push({ biz_type: '费用报销', item: '', qty: 1, amount: 0, tax_rate: 13, tax: 0, total: 0 })
}

function removeDetail(idx: number) {
  if (invoiceForm.details.length <= 1) {
    ElMessage.warning('至少保留一条明细')
    return
  }
  invoiceForm.details.splice(idx, 1)
}

async function submitInvoice() {
  invoiceFormRef.value?.validate(async (valid: boolean) => {
    if (!valid) return
    if (!editingId.value) {
      ElMessage.warning('报销单未保存')
      return
    }
    for (const d of invoiceForm.details) {
      calcDetail(d)
      if (!d.item) {
        ElMessage.warning('请完善开票项目')
        return
      }
    }
    const payload: InvoiceCreatePayload = { ...invoiceForm, reimbursement_bill_id: editingId.value }
    try {
      await invoiceApi.create(payload)
      ElMessage.success('发票已保存并关联')
      invoiceDialogVisible.value = false
      await loadLinkedInvoices()
      // 自动按关联发票汇总更新报销单金额
      await syncBillAmount()
      await load()
    } catch (e: any) {
      if (e?.response?.status === 409) {
        ElMessage.warning(e?.response?.data?.detail || '该发票已存在，不能重复录入')
      } else {
        ElMessage.error(e?.response?.data?.detail || '保存发票失败')
      }
    }
  })
}

async function syncBillAmount() {
  if (!editingId.value) return
  try {
    const sumRes = await invoiceApi.summaryByBill(editingId.value)
    const summary = sumRes.data
    const invoiceTotal = Number(summary.total || 0)
    if (invoiceTotal > 0) {
      // 报销金额默认=发票合计；用户已调低且未超额则保留，否则回落的发票合计
      const cur = form.reimburse_amount != null ? Number(form.reimburse_amount) : null
      const newVal = (cur == null || cur > invoiceTotal || cur <= 0) ? invoiceTotal : cur
      await reimburseApi.update(editingId.value, { reimburse_amount: newVal })
      form.reimburse_amount = newVal
    }
  } catch (e) {
    // 汇总更新失败不影响主流程
    console.warn('汇总更新报销单金额失败', e)
  }
}

async function unlinkInvoice(inv: Invoice) {
  try {
    await invoiceApi.unlink(inv.id)
    ElMessage.success('已移除关联')
    await loadLinkedInvoices()
    await syncBillAmount()
    await load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '移除关联失败')
  }
}

onMounted(load)
</script>

<style scoped>
.page {
  padding: 16px;
}
.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}
.text-muted {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
.tax-hint {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  margin-left: 4px;
}

/* 采购申请细项 + 已关联发票 */
.purchase-items {
  margin-top: 16px;
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}
.linked-invoices {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px dashed var(--el-border-color);
}
.linked-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.has-invoices {
  color: var(--success);
  font-weight: 600;
}
.linked-title {
  font-weight: 600;
  color: var(--el-text-color-regular);
}

/* 增加发票弹窗 */
.invoice-form-row {
  display: flex;
  gap: 16px;
}
.invoice-form-row .el-form-item {
  flex: 1;
  min-width: 0;
}
.detail-section {
  margin-top: 12px;
}
.detail-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  margin-bottom: 8px;
}
.detail-table th,
.detail-table td {
  border: 1px solid var(--el-border-color-lighter);
  padding: 6px;
  text-align: center;
  font-size: 13px;
}
.detail-table th {
  background: #f5f7fa;
  font-weight: 600;
}

/* 上传识别区 */
.recognize-section {
  margin-bottom: 8px;
}
.recognize-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: var(--el-color-primary);
  margin-bottom: 12px;
}
.recognize-uploader :deep(.el-upload-dragger) {
  width: 100%;
  padding: 32px 20px;
  border: 2px dashed var(--el-color-primary-light-5);
  border-radius: 8px;
  background: var(--el-color-primary-light-9);
}
.recognize-uploader :deep(.el-upload-dragger:hover) {
  border-color: var(--el-color-primary);
}
.recognize-uploader :deep(.el-upload.is-disabled .el-upload-dragger) {
  opacity: 0.7;
  cursor: not-allowed;
}
.recognize-upload-icon {
  font-size: 40px;
  color: var(--el-color-primary);
  margin-bottom: 8px;
}
.recognize-upload-text p {
  margin: 0;
  color: var(--el-text-color-primary);
  font-size: 15px;
  font-weight: 500;
}
.recognize-upload-tip {
  font-size: 12px !important;
  color: var(--el-text-color-secondary) !important;
  margin-top: 6px !important;
}
.recognize-file {
  margin-top: 12px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  padding: 10px 12px;
  background: #fff;
}
.recognize-file-info {
  display: flex;
  align-items: center;
  gap: 8px;
}
.recognize-file-name {
  flex: 1;
  font-size: 14px;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.recognize-image-preview {
  display: flex;
  justify-content: center;
  max-height: 200px;
  overflow: hidden;
  margin-top: 8px;
}
.recognize-image-preview img {
  max-width: 100%;
  max-height: 200px;
  border-radius: 4px;
  border: 1px solid var(--el-border-color-lighter);
}
.recognize-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-top: 12px;
  padding: 16px;
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  border-radius: 6px;
}
.recognize-spin {
  font-size: 22px;
  animation: recognize-spin 1s linear infinite;
}
@keyframes recognize-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.recognize-error {
  margin-top: 12px;
}

/* 报销单浏览弹窗 */
.detail-dialog :deep(.el-dialog__body) {
  max-height: 70vh;
  overflow-y: auto;
  padding-top: 10px;
}
.detail-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
