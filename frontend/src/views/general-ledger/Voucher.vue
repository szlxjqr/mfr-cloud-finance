<script setup lang="ts">
import { onMounted, reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createVoucher, type VoucherCreate, type VoucherEntryCreate } from '@/api/voucher'
import { listSubjects as fetchSubjects } from '@/api/ledger'
import type { AccountSubject } from '@/types/ledger'

const router = useRouter()

/* ==================== 数据 ==================== */
const subjects = ref<AccountSubject[]>([])
const subjectMap = computed(() => {
  const m: Record<string, string> = {}
  for (const s of subjects.value) m[s.code] = s.name
  return m
})

interface EntryRow {
  subject_code: string
  summary: string
  direction: '借' | '贷'
  amount: number | null
}
const form = reactive({
  voucher_date: new Date().toISOString().slice(0, 10),
  voucher_word: '记',
  attach_count: 0,
  maker: '',
  summary: '',
})
const entries = ref<EntryRow[]>([
  { subject_code: '', summary: '', direction: '借', amount: null },
  { subject_code: '', summary: '', direction: '贷', amount: null },
])

const saving = ref(false)
const balanceError = ref('')

/* ==================== 计算 ==================== */
const totalDebit = computed(() =>
  entries.value.reduce((s, e) => s + (e.direction === '借' ? Number(e.amount) || 0 : 0), 0),
)
const totalCredit = computed(() =>
  entries.value.reduce((s, e) => s + (e.direction === '贷' ? Number(e.amount) || 0 : 0), 0),
)
const isBalanced = computed(() => Math.abs(totalDebit.value - totalCredit.value) < 0.005)

/* ==================== 方法 ==================== */
function onSubjectChange(row: EntryRow) {
  // 选/填科目后自动带出科目名（提交时后端也会校正）
  const name = subjectMap.value[row.subject_code]
  if (name && !row.summary) row.summary = name
}

function addRow() {
  entries.value.push({ subject_code: '', summary: '', direction: '借', amount: null })
}
function removeRow(idx: number) {
  if (entries.value.length <= 2) {
    ElMessage.warning('凭证至少需 2 条分录')
    return
  }
  entries.value.splice(idx, 1)
}

function validate(): string | null {
  if (!form.voucher_date) return '请选择凭证日期'
  if (entries.value.length < 2) return '凭证至少需 2 条分录'
  for (const e of entries.value) {
    if (!e.subject_code) return '存在未填科目的分录'
    if (!e.amount || Number(e.amount) <= 0) return '分录金额必须为正数'
  }
  if (!isBalanced.value)
    return `借贷不平衡：借方 ${totalDebit.value.toFixed(2)} / 贷方 ${totalCredit.value.toFixed(2)}`
  return null
}

async function handleSave() {
  const err = validate()
  if (err) {
    balanceError.value = err
    ElMessage.error(err)
    return
  }
  balanceError.value = ''
  saving.value = true
  const payload: VoucherCreate = {
    voucher_date: form.voucher_date,
    voucher_word: form.voucher_word,
    attach_count: Number(form.attach_count) || 0,
    maker: form.maker || undefined,
    summary: form.summary || undefined,
    entries: entries.value.map((e) => ({
      subject_code: e.subject_code,
      summary: e.summary || undefined,
      direction: e.direction,
      amount: Number(e.amount),
    })) as VoucherEntryCreate[],
  }
  try {
    await createVoucher(payload)
    ElMessage.success('手工凭证已保存（待审核，未进账簿）')
    router.push('/general-ledger/voucher-list')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

function handleReset() {
  form.summary = ''
  form.attach_count = 0
  entries.value = [
    { subject_code: '', summary: '', direction: '借', amount: null },
    { subject_code: '', summary: '', direction: '贷', amount: null },
  ]
}

onMounted(async () => {
  try {
    const res = await fetchSubjects()
    subjects.value = res.data
  } catch {
    /* 科目加载失败不阻断录单，科目名后端会校正 */
  }
})
</script>

<template>
  <div class="voucher-entry">
    <el-card shadow="never" class="entry-card">
      <template #header>
        <div class="entry-header">
          <span class="entry-title">凭证录入</span>
          <el-tag type="warning" size="small" effect="plain">手工录入 · 独立来源</el-tag>
          <span class="entry-hint">保存后为「未审核」草稿，审核通过才进入账簿与报表</span>
        </div>
      </template>

      <!-- 凭证头 -->
      <el-form label-width="84px" class="entry-form">
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="凭证日期">
              <el-date-picker v-model="form.voucher_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="凭证字">
              <el-select v-model="form.voucher_word" style="width: 100%">
                <el-option label="记" value="记" />
                <el-option label="收" value="收" />
                <el-option label="付" value="付" />
                <el-option label="转" value="转" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="5">
            <el-form-item label="附单据">
              <el-input-number v-model="form.attach_count" :min="0" :controls="true" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="5">
            <el-form-item label="制单人">
              <el-input v-model="form.maker" placeholder="可选" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="凭证摘要">
          <el-input v-model="form.summary" placeholder="本张凭证的概括说明（可选）" />
        </el-form-item>
      </el-form>

      <!-- 分录表 -->
      <div class="entry-table-wrap">
        <el-table :data="entries" border stripe class="entry-table">
          <el-table-column type="index" label="#" width="48" align="center" />
          <el-table-column label="科目编码" min-width="200">
            <template #default="{ row }">
              <el-select
                v-model="row.subject_code"
                filterable
                allow-create
                default-first-option
                placeholder="选择 / 输入科目编码"
                style="width: 100%"
                @change="onSubjectChange(row)"
              >
                <el-option
                  v-for="s in subjects"
                  :key="s.code"
                  :label="`${s.code} ${s.name}`"
                  :value="s.code"
                />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="摘要" min-width="160">
            <template #default="{ row }">
              <el-input v-model="row.summary" placeholder="可为空（默认带科目名）" />
            </template>
          </el-table-column>
          <el-table-column label="方向" width="140" align="center">
            <template #default="{ row }">
              <el-radio-group v-model="row.direction">
                <el-radio value="借" border>借</el-radio>
                <el-radio value="贷" border>贷</el-radio>
              </el-radio-group>
            </template>
          </el-table-column>
          <el-table-column label="金额" width="180">
            <template #default="{ row }">
              <el-input-number
                v-model="row.amount"
                :min="0"
                :precision="2"
                :step="0.01"
                :controls="false"
                style="width: 100%"
              />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80" align="center" fixed="right">
            <template #default="{ $index }">
              <el-button text type="danger" size="small" @click="removeRow($index)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="entry-add">
          <el-button text type="primary" @click="addRow">+ 增行</el-button>
        </div>
      </div>

      <!-- 借贷平衡条 -->
      <div class="balance-bar" :class="{ ok: isBalanced, bad: !isBalanced }">
        <span>借方合计：<strong>¥{{ totalDebit.toFixed(2) }}</strong></span>
        <span>贷方合计：<strong>¥{{ totalCredit.toFixed(2) }}</strong></span>
        <span class="balance-mark">
          <el-tag v-if="isBalanced" type="success" size="small" effect="dark">借贷平衡</el-tag>
          <el-tag v-else type="danger" size="small" effect="dark">借贷不平衡</el-tag>
        </span>
      </div>

      <!-- 底部操作 -->
      <div class="entry-footer">
        <el-button @click="handleReset">重置</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存凭证</el-button>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.voucher-entry {
  padding: 16px;
}
.entry-card {
  max-width: 1080px;
  margin: 0 auto;
}
.entry-header {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.entry-title {
  font-size: 16px;
  font-weight: 600;
}
.entry-hint {
  font-size: 12px;
  color: var(--text-muted);
}
.entry-form {
  margin-bottom: 12px;
}
.entry-table-wrap {
  margin-bottom: 8px;
}
.entry-add {
  text-align: left;
  padding: 8px 0 0;
}
.balance-bar {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 14px;
  background: #fef0f0;
  color: var(--danger);
  margin-bottom: 16px;
}
.balance-bar.ok {
  background: #f0f9eb;
  color: var(--success);
}
.balance-bar .balance-mark {
  margin-left: auto;
}
.entry-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
