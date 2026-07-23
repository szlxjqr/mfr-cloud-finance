<template>
  <div class="page">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="客户" name="customer" />
      <el-tab-pane label="供应商" name="supplier" />
    </el-tabs>
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索名称" clearable style="width: 220px" @clear="load" />
      <el-button type="primary" @click="openCreate">新建</el-button>
    </div>
    <el-table :data="list" border stripe>
      <el-table-column type="index" label="#" width="50" />
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="tax_no" label="税号" />
      <el-table-column prop="contact" label="联系人" />
      <el-table-column prop="phone" label="电话" />
      <el-table-column prop="status" label="状态" />
      <el-table-column label="操作" width="220">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">详情</el-button>
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑' : '新建'" width="560px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="税号"><el-input v-model="form.tax_no" /></el-form-item>
        <el-form-item label="联系人"><el-input v-model="form.contact" /></el-form-item>
        <el-form-item label="电话"><el-input v-model="form.phone" /></el-form-item>
        <el-form-item label="地址"><el-input v-model="form.address" /></el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status">
            <el-option label="启用" value="enabled" />
            <el-option label="停用" value="disabled" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="form.remark" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <!-- 往来单位详情抽屉：客户→销售合同；供应商→采购合同+采购申请 -->
    <el-drawer v-model="drawerVisible" :title="`${currentParty?.name || ''} · 往来详情`" size="58%">
      <template v-if="currentParty">
        <el-descriptions :column="2" border size="small" class="mb">
          <el-descriptions-item label="类型">{{ currentParty.ptype === 'customer' ? '客户' : '供应商' }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ currentParty.status === 'enabled' ? '启用' : '停用' }}</el-descriptions-item>
          <el-descriptions-item label="税号">{{ currentParty.tax_no || '—' }}</el-descriptions-item>
          <el-descriptions-item label="联系人">{{ currentParty.contact || '—' }}</el-descriptions-item>
          <el-descriptions-item label="电话">{{ currentParty.phone || '—' }}</el-descriptions-item>
          <el-descriptions-item label="地址">{{ currentParty.address || '—' }}</el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ currentParty.remark || '—' }}</el-descriptions-item>
        </el-descriptions>

        <!-- 客户：销售合同 -->
        <template v-if="currentParty.ptype === 'customer'">
          <h4 class="sec-title">销售合同（{{ salesContracts.length }}）</h4>
          <el-table :data="salesContracts" border size="small">
            <el-table-column prop="contract_no" label="合同号" />
            <el-table-column label="金额">
              <template #default="{ row }">{{ fmt(row.amount) }}</template>
            </el-table-column>
            <el-table-column prop="status" label="状态" />
            <el-table-column label="签订日">
              <template #default="{ row }">{{ row.sign_date || '—' }}</template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!salesContracts.length" description="暂无销售合同" />
        </template>

        <!-- 供应商：采购合同 + 采购申请 -->
        <template v-else>
          <h4 class="sec-title">采购合同（{{ purchaseContracts.length }}）</h4>
          <el-table :data="purchaseContracts" border size="small">
            <el-table-column prop="contract_no" label="合同号" />
            <el-table-column label="金额">
              <template #default="{ row }">{{ fmt(row.amount) }}</template>
            </el-table-column>
            <el-table-column prop="status" label="状态" />
            <el-table-column label="签订日">
              <template #default="{ row }">{{ row.sign_date || '—' }}</template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!purchaseContracts.length" description="暂无采购合同" />

          <h4 class="sec-title">采购申请（{{ purchaseReqs.length }}）</h4>
          <el-alert type="info" :closable="false" show-icon class="mb"
            title="采购申请以自由文本记录供应商，按名称精确匹配；若申请中供应商名称与往来单位不一致则不关联显示。" />
          <el-table :data="purchaseReqs" border size="small">
            <el-table-column prop="req_no" label="申请单号" />
            <el-table-column prop="item_name" label="采购事项" />
            <el-table-column label="预计金额">
              <template #default="{ row }">{{ fmt(row.expected_amount) }}</template>
            </el-table-column>
            <el-table-column prop="status" label="状态" />
            <el-table-column label="申请日">
              <template #default="{ row }">{{ row.submit_date || '—' }}</template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!purchaseReqs.length" description="暂无关联采购申请" />
        </template>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { partyApi, salesApi, purchaseApi as purchaseContractApi } from '@/api/contract'
import { purchaseApi as purchaseReqApi } from '@/api/purchase'
import type { Party, SalesContract, PurchaseContract } from '@/types/contract'
import type { PurchaseReq } from '@/types/purchase'

const activeTab = ref<'customer' | 'supplier'>('customer')
const keyword = ref('')
const list = ref<Party[]>([])
const dialogVisible = ref(false)
const editing = ref(false)
const editingId = ref<number | null>(null)

const emptyForm = () => ({
  name: '',
  tax_no: '',
  contact: '',
  phone: '',
  address: '',
  status: 'enabled',
  remark: '',
})
const form = reactive(emptyForm())

async function load() {
  const res = await partyApi.list({ ptype: activeTab.value, keyword: keyword.value || undefined })
  list.value = res.data
}
function openCreate() {
  Object.assign(form, emptyForm())
  editing.value = false
  editingId.value = null
  dialogVisible.value = true
}
function openEdit(row: Party) {
  Object.assign(form, emptyForm(), row)
  editing.value = true
  editingId.value = row.id
  dialogVisible.value = true
}
async function save() {
  const payload = { ...form, ptype: activeTab.value }
  if (editing.value && editingId.value != null) {
    await partyApi.update(editingId.value, payload)
    ElMessage.success('已更新')
  } else {
    await partyApi.create(payload)
    ElMessage.success('已创建')
  }
  dialogVisible.value = false
  load()
}
async function remove(row: Party) {
  await ElMessageBox.confirm('确认删除？', '提示', { type: 'warning' })
  await partyApi.remove(row.id)
  ElMessage.success('已删除')
  load()
}

// ============ 往来单位详情抽屉 ============
const drawerVisible = ref(false)
const currentParty = ref<Party | null>(null)
const salesContracts = ref<SalesContract[]>([])
const purchaseContracts = ref<PurchaseContract[]>([])
const purchaseReqs = ref<PurchaseReq[]>([])

function fmt(v: number | null | undefined): string {
  return v != null ? '¥' + Number(v).toFixed(2) : '—'
}

async function openDetail(row: Party) {
  currentParty.value = row
  salesContracts.value = []
  purchaseContracts.value = []
  purchaseReqs.value = []
  drawerVisible.value = true
  try {
    if (row.ptype === 'customer') {
      const res = await salesApi.list({ customer_id: row.id })
      salesContracts.value = res.data
    } else {
      const [pc, pr] = await Promise.all([
        purchaseContractApi.list({ supplier_id: row.id }),
        purchaseReqApi.list({ supplier: row.name }),
      ])
      purchaseContracts.value = pc.data
      purchaseReqs.value = pr.data
    }
  } catch {
    ElMessage.error('加载往来详情失败')
  }
}

watch(activeTab, load)
load()
</script>

<style scoped>
.page {
  padding: 16px;
}
.toolbar {
  display: flex;
  gap: 12px;
  margin: 12px 0;
}
.sec-title {
  margin: 18px 0 8px;
  font-size: 14px;
  color: #303133;
}
.mb {
  margin-bottom: 12px;
}
</style>
