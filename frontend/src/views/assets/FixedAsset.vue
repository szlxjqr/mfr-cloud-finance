<template>
  <div class="page">
    <!-- 资产总览卡片 -->
    <div class="summary-cards" v-loading="summaryLoading">
      <div class="scard">
        <div class="scard-label">资产原值合计</div>
        <div class="scard-value">{{ fmt(summary.total_original) }}</div>
      </div>
      <div class="scard">
        <div class="scard-label">累计折旧合计</div>
        <div class="scard-value warn">{{ fmt(summary.total_accum_dep) }}</div>
      </div>
      <div class="scard">
        <div class="scard-label">资产净值合计</div>
        <div class="scard-value success">{{ fmt(summary.total_net) }}</div>
      </div>
      <div class="scard">
        <div class="scard-label">在用 / 总数</div>
        <div class="scard-value">{{ summary.in_use_count }} / {{ summary.total_count }}</div>
      </div>
    </div>

    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索单号/名称/部门" clearable style="width: 220px" @keyup.enter="load" @clear="load" />
      <el-select v-model="statusFilter" placeholder="全部状态" clearable style="width: 120px" @change="load">
        <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
      </el-select>
      <el-select v-model="categoryFilter" placeholder="全部类别" clearable style="width: 130px" @change="load">
        <el-option v-for="c in ASSET_CATEGORIES" :key="c" :label="c" :value="c" />
      </el-select>
      <el-button type="primary" @click="openCreate">新建资产</el-button>
      <el-button type="success" @click="openDepreciate" :loading="depLoading">计提折旧</el-button>
    </div>

    <el-table :data="list" border stripe v-loading="loading">
      <el-table-column prop="asset_no" label="资产编号" width="140" />
      <el-table-column prop="name" label="资产名称" min-width="140" />
      <el-table-column prop="category" label="类别" width="110" />
      <el-table-column prop="department" label="使用部门" width="110" />
      <el-table-column prop="acquisition_date" label="购入日期" width="120" />
      <el-table-column label="原值" width="120" align="right">
        <template #default="{ row }">{{ fmt(row.original_value) }}</template>
      </el-table-column>
      <el-table-column label="累计折旧" width="120" align="right">
        <template #default="{ row }">{{ fmt(row.accum_dep) }}</template>
      </el-table-column>
      <el-table-column label="月折旧" width="110" align="right">
        <template #default="{ row }">
          <span style="color: var(--el-color-warning)">{{ fmt(row.monthly_dep) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="净值" width="120" align="right">
        <template #default="{ row }">
          <span style="font-weight: 600; color: var(--el-color-success)">{{ fmt(row.net_value) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="statusTag(row.status)" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="入账凭证" prop="record_voucher_no" width="160" />
      <el-table-column label="操作" width="300" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openView(row)">查看</el-button>
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button
            v-if="row.status === '未入账'"
            link
            type="success"
            @click="doRecord(row)"
          >入账</el-button>
          <el-button
            v-if="row.status === '已处置'"
            link
            type="info"
            @click="openDepRecords(row)"
          >折旧记录</el-button>
          <el-button
            v-if="row.status === '在用'"
            link
            type="danger"
            @click="doDispose(row)"
          >处置</el-button>
          <el-button link type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新建 / 编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑资产' : '新建资产'" width="780px" :close-on-click-modal="false">
      <el-form :model="form" label-width="110px">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="资产编号">
              <el-input :model-value="form.asset_no || previewNo || '保存后自动生成'" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="购入日期">
              <el-date-picker v-model="form.acquisition_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="14">
            <el-form-item label="资产名称" required>
              <el-input v-model="form.name" placeholder="必填，如 研发服务器" />
            </el-form-item>
          </el-col>
          <el-col :span="10">
            <el-form-item label="使用部门">
              <el-input v-model="form.department" placeholder="选填" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="资产类别">
              <el-select v-model="form.category" placeholder="选择类别" style="width: 100%">
                <el-option v-for="c in ASSET_CATEGORIES" :key="c" :label="c" :value="c" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="折旧计入科目">
              <el-select v-model="form.dep_subject_code" style="width: 100%">
                <el-option v-for="d in DEP_SUBJECTS" :key="d.code" :label="`${d.code} ${d.name}`" :value="d.code" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-divider content-position="left">折旧参数</el-divider>
        <el-row :gutter="12">
          <el-col :span="8"><el-form-item label="原值(¥)" required><el-input-number v-model="form.original_value" :min="0" :precision="2" :controls="false" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="残值率(%)"><el-input-number v-model="form.salvage_rate" :min="0" :max="100" :precision="2" :controls="false" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="使用年限(年)"><el-input-number v-model="form.useful_life" :min="0" :precision="1" :controls="false" style="width: 100%" /></el-form-item></el-col>
        </el-row>
        <el-alert
          type="info"
          :closable="false"
          show-icon
          style="margin-top: 4px"
          :title="`按月折旧 ¥${fmt(preview.monthly)} ｜ 当前净值 ¥${fmt(preview.net)}（按现有累计折旧 ${fmt(toNum(form.accum_dep))} 估算）`"
        />
        <el-form-item label="备注" style="margin-top: 12px">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <!-- 计提折旧弹窗（含预览） -->
    <el-dialog v-model="depDialogVisible" title="计提折旧（按月汇总一张凭证）" width="720px" :close-on-click-modal="false">
      <el-form label-width="110px" style="margin-bottom: 8px">
        <el-form-item label="计提期间" required>
          <el-date-picker v-model="depPeriod" type="month" value-format="YYYY-MM" placeholder="选择期间" style="width: 200px" @change="loadDepPreview" />
        </el-form-item>
      </el-form>
      <el-table :data="depPreview" border stripe max-height="320" v-loading="depPreviewLoading">
        <el-table-column prop="asset_no" label="资产编号" width="140" />
        <el-table-column prop="name" label="名称" min-width="120" />
        <el-table-column prop="original_value" label="原值" width="110" align="right">
          <template #default="{ row }">{{ fmt(row.original_value) }}</template>
        </el-table-column>
        <el-table-column prop="accum_dep" label="已提折旧" width="110" align="right">
          <template #default="{ row }">{{ fmt(row.accum_dep) }}</template>
        </el-table-column>
        <el-table-column prop="monthly_dep" label="本月折旧" width="120" align="right">
          <template #default="{ row }"><span style="color: var(--el-color-warning)">{{ fmt(row.monthly_dep) }}</span></template>
        </el-table-column>
        <el-table-column prop="net_value" label="计提后净值" width="120" align="right">
          <template #default="{ row }">{{ fmt(row.net_value) }}</template>
        </el-table-column>
      </el-table>
      <div style="margin-top: 10px; text-align: right; color: #909399">
        本期合计折旧：<strong style="color: var(--el-color-warning)">{{ fmt(depPreviewTotal) }}</strong>
      </div>
      <template #footer>
        <el-button @click="depDialogVisible = false">取消</el-button>
        <el-button type="success" @click="submitDepreciate" :disabled="!depPeriod || depPreview.length === 0" :loading="depLoading">确认计提并生成凭证</el-button>
      </template>
    </el-dialog>

    <!-- 折旧记录弹窗 -->
    <el-dialog v-model="depRecordsVisible" title="折旧记录" width="560px" :close-on-click-modal="false">
      <el-table :data="depRecords" border stripe v-loading="depRecordsLoading" empty-text="暂无折旧记录">
        <el-table-column prop="period" label="期间" width="120" />
        <el-table-column label="折旧额" width="140" align="right">
          <template #default="{ row }">{{ fmt(row.amount) }}</template>
        </el-table-column>
        <el-table-column prop="voucher_no" label="凭证号" />
      </el-table>
      <template #footer>
        <el-button @click="depRecordsVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 详情弹窗 -->
    <el-dialog v-model="viewVisible" title="资产详情" width="680px" :close-on-click-modal="false">
      <el-descriptions v-if="viewRow" :column="2" border>
        <el-descriptions-item label="资产编号">{{ viewRow.asset_no }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusTag(viewRow.status)" size="small">{{ viewRow.status }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="资产名称">{{ viewRow.name }}</el-descriptions-item>
        <el-descriptions-item label="类别">{{ viewRow.category || '-' }}</el-descriptions-item>
        <el-descriptions-item label="使用部门">{{ viewRow.department || '-' }}</el-descriptions-item>
        <el-descriptions-item label="购入日期">{{ viewRow.acquisition_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="原值">{{ fmt(viewRow.original_value) }}</el-descriptions-item>
        <el-descriptions-item label="残值率">{{ toNum(viewRow.salvage_rate) }}%</el-descriptions-item>
        <el-descriptions-item label="使用年限">{{ toNum(viewRow.useful_life) }} 年</el-descriptions-item>
        <el-descriptions-item label="折旧计入科目">{{ viewRow.dep_subject_code || '-' }}</el-descriptions-item>
        <el-descriptions-item label="累计折旧" :span="2">{{ fmt(viewRow.accum_dep) }}</el-descriptions-item>
        <el-descriptions-item label="月折旧额">{{ fmt(viewRow.monthly_dep) }}</el-descriptions-item>
        <el-descriptions-item label="净值">{{ fmt(viewRow.net_value) }}</el-descriptions-item>
        <el-descriptions-item label="入账凭证">{{ viewRow.record_voucher_no || '-' }}</el-descriptions-item>
        <el-descriptions-item label="处置凭证">{{ viewRow.dispose_voucher_no || '-' }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ viewRow.remark || '-' }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="viewVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { assetApi } from '@/api/fixedAsset'
import type { FixedAsset, AssetSummary, DepRecord, DepPreviewItem } from '@/types/fixedAsset'
import { ASSET_CATEGORIES, DEP_SUBJECTS } from '@/types/fixedAsset'

const statusOptions = ['未入账', '在用', '闲置', '已处置']

const keyword = ref('')
const statusFilter = ref<string | null>(null)
const categoryFilter = ref<string | null>(null)
const list = ref<FixedAsset[]>([])
const loading = ref(false)

const summary = ref<AssetSummary>({ total_original: 0, total_accum_dep: 0, total_net: 0, in_use_count: 0, total_count: 0 })
const summaryLoading = ref(false)

const dialogVisible = ref(false)
const editing = ref(false)
const editingId = ref<number | null>(null)
const previewNo = ref<string | null>(null)

const depDialogVisible = ref(false)
const depPeriod = ref<string>(curMonth())
const depPreview = ref<DepPreviewItem[]>([])
const depPreviewLoading = ref(false)
const depLoading = ref(false)
const depPreviewTotal = computed(() => depPreview.value.reduce((s, x) => s + toNum(x.monthly_dep), 0))

const depRecordsVisible = ref(false)
const depRecords = ref<DepRecord[]>([])
const depRecordsLoading = ref(false)

const viewVisible = ref(false)
const viewRow = ref<FixedAsset | null>(null)

function curMonth(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

function toNum(v: any): number {
  if (v === null || v === undefined || v === '') return 0
  const n = Number(v)
  return Number.isFinite(n) ? n : 0
}

function fmt(v: any): string {
  return '¥' + toNum(v).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function statusTag(status: string): '' | 'success' | 'warning' | 'danger' | 'info' | 'primary' {
  switch (status) {
    case '在用': return 'success'
    case '闲置': return 'warning'
    case '已处置': return 'info'
    default: return 'primary'
  }
}

// 客户端折旧预览（与服务端公式一致）
const preview = computed(() => {
  const original = toNum(form.original_value)
  const salvageRate = toNum(form.salvage_rate)
  const life = toNum(form.useful_life)
  const accum = editing.value ? toNum(form.accum_dep) : 0
  if (original <= 0 || life <= 0) return { monthly: 0, net: original - accum }
  const salvage = original * salvageRate / 100
  const depreciable = original - salvage
  const perMonth = depreciable / (life * 12)
  const remaining = depreciable - accum
  const monthly = Math.min(perMonth, Math.max(remaining, 0))
  return { monthly, net: original - accum - monthly }
})

function emptyForm() {
  return {
    asset_no: null as string | null,
    name: '',
    category: '办公设备' as string,
    department: '' as string | null,
    acquisition_date: '' as string | null,
    original_value: 0 as number | null,
    salvage_rate: 5 as number | null,
    useful_life: 5 as number | null,
    dep_subject_code: '5602' as string | null,
    accum_dep: 0 as number | null,
    remark: '' as string | null,
  }
}
const form = reactive(emptyForm())

async function loadSummary() {
  summaryLoading.value = true
  try {
    const res = await assetApi.summary()
    summary.value = res.data
  } catch (e) {
    console.warn('资产总览加载失败', e)
  } finally {
    summaryLoading.value = false
  }
}

async function load() {
  loading.value = true
  try {
    const params: { keyword?: string; status?: string; category?: string } = {}
    if (keyword.value) params.keyword = keyword.value
    if (statusFilter.value) params.status = statusFilter.value
    if (categoryFilter.value) params.category = categoryFilter.value
    const res = await assetApi.list(params)
    list.value = res.data
  } finally {
    loading.value = false
  }
  await loadSummary()
}

async function openCreate() {
  Object.assign(form, emptyForm())
  editing.value = false
  editingId.value = null
  previewNo.value = null
  dialogVisible.value = true
  try {
    const res = await assetApi.nextNo()
    previewNo.value = res.data.asset_no
  } catch (e) {
    console.warn('预占编号失败', e)
  }
}

function openEdit(row: FixedAsset) {
  Object.assign(form, emptyForm(), row, {
    original_value: toNum(row.original_value),
    salvage_rate: toNum(row.salvage_rate) || 5,
    useful_life: toNum(row.useful_life) || 5,
    accum_dep: toNum(row.accum_dep),
  })
  editing.value = true
  editingId.value = row.id
  previewNo.value = row.asset_no ?? null
  dialogVisible.value = true
}

async function save() {
  if (!form.name || !form.name.trim()) {
    ElMessage.warning('请填写资产名称')
    return
  }
  if (!toNum(form.original_value)) {
    ElMessage.warning('请填写原值')
    return
  }
  const payload: Record<string, unknown> = {
    name: form.name.trim(),
    category: form.category,
    department: form.department || null,
    acquisition_date: form.acquisition_date || null,
    original_value: toNum(form.original_value),
    salvage_rate: toNum(form.salvage_rate),
    useful_life: toNum(form.useful_life),
    dep_subject_code: form.dep_subject_code || '5602',
    remark: form.remark || null,
  }
  if (previewNo.value && !editing.value && !payload.asset_no) {
    payload.asset_no = previewNo.value
  }
  try {
    if (editing.value && editingId.value != null) {
      await assetApi.update(editingId.value, payload)
      ElMessage.success('已更新')
    } else {
      await assetApi.create(payload)
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    await load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  }
}

async function doRecord(row: FixedAsset) {
  await ElMessageBox.confirm(
    `确认将资产 ${row.asset_no}（${row.name}）入账？将自动生成购置凭证（借 固定资产 / 贷 银行存款）。`,
    '入账确认',
    { type: 'warning' },
  )
  try {
    const res = await assetApi.record(row.id)
    if (res.data.skipped) {
      ElMessage.info(res.data.voucher_no ? `已入账，凭证号：${res.data.voucher_no}` : '资产已入账')
    } else {
      ElMessage.success(`已入账，凭证号：${res.data.voucher_no}`)
    }
    await load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '入账失败')
  }
}

async function doDispose(row: FixedAsset) {
  await ElMessageBox.confirm(
    `确认处置资产 ${row.asset_no}（${row.name}）？将自动生成清理凭证（借 累计折旧 / 借 管理费用净值 / 贷 固定资产）。`,
    '处置确认',
    { type: 'warning' },
  )
  try {
    const res = await assetApi.dispose(row.id, { action_date: new Date().toISOString().slice(0, 10) })
    if (res.data.skipped) {
      ElMessage.info(res.data.voucher_no ? `已处置，凭证号：${res.data.voucher_no}` : '资产已处置')
    } else {
      ElMessage.success(`已处置，凭证号：${res.data.voucher_no}`)
    }
    await load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '处置失败')
  }
}

async function openDepreciate() {
  depPeriod.value = curMonth()
  depDialogVisible.value = true
  await loadDepPreview()
}

async function loadDepPreview() {
  if (!depPeriod.value) {
    depPreview.value = []
    return
  }
  depPreviewLoading.value = true
  try {
    const res = await assetApi.depreciatePreview(depPeriod.value)
    depPreview.value = res.data
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '预览失败')
  } finally {
    depPreviewLoading.value = false
  }
}

async function submitDepreciate() {
  if (!depPeriod.value) return
  depLoading.value = true
  try {
    const res = await assetApi.depreciate({ period: depPeriod.value })
    if (res.data.skipped) {
      ElMessage.info(res.data.message || '本期折旧凭证已存在（幂等跳过）')
    } else {
      ElMessage.success(`已计提 ${res.data.count} 项，凭证号：${res.data.voucher_no}，合计 ¥${toNum(res.data.total).toFixed(2)}`)
    }
    depDialogVisible.value = false
    await load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '计提失败')
  } finally {
    depLoading.value = false
  }
}

async function openDepRecords(row: FixedAsset) {
  depRecordsVisible.value = true
  depRecordsLoading.value = true
  try {
    const res = await assetApi.depRecords(row.id)
    depRecords.value = res.data
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载失败')
  } finally {
    depRecordsLoading.value = false
  }
}

function openView(row: FixedAsset) {
  viewRow.value = row
  viewVisible.value = true
}

async function remove(row: FixedAsset) {
  await ElMessageBox.confirm(`确认删除资产 ${row.asset_no ?? row.id}？`, '提示', { type: 'warning' })
  await assetApi.remove(row.id)
  ElMessage.success('已删除')
  await load()
}

onMounted(load)
</script>

<style scoped>
.page { padding: 16px; }
.summary-cards { display: flex; gap: 12px; margin-bottom: 14px; flex-wrap: wrap; }
.scard {
  flex: 1; min-width: 160px;
  background: var(--el-fill-color-light, #f5f7fa);
  border: 1px solid var(--el-border-color-lighter, #ebeef5);
  border-radius: 8px;
  padding: 14px 16px;
}
.scard-label { font-size: 13px; color: #909399; margin-bottom: 6px; }
.scard-value { font-size: 22px; font-weight: 700; color: var(--el-text-color-primary, #303133); }
.scard-value.warn { color: var(--el-color-warning); }
.scard-value.success { color: var(--el-color-success); }
.toolbar { display: flex; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; }
</style>
