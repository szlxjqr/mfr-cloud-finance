<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listSubjects, createSubject, resetSubjects } from '@/api/ledger'
import type { AccountSubject } from '@/types/ledger'

const loading = ref(false)
const subjects = ref<AccountSubject[]>([])
const searchKey = ref('')
const dialogVisible = ref(false)
const form = ref<Partial<AccountSubject>>({
  code: '', name: '', category: '资产', direction: '借', level: 1, is_leaf: true, status: '启用',
})

const categoryLabel: Record<string, string> = {
  资产: '资产', 负债: '负债', 权益: '权益', 成本: '成本', 损益: '损益',
}

/* ====== 科目树（供新增弹窗的「上级科目」选择器） ====== */
interface TreeNode {
  value: string
  label: string
  children?: TreeNode[]
}
const subjectTree = computed<TreeNode[]>(() => {
  const map = new Map<string, TreeNode>()
  for (const s of subjects.value) {
    map.set(s.code, { value: s.code, label: `${s.code} ${s.name}` })
  }
  const roots: TreeNode[] = []
  for (const s of subjects.value) {
    const node = map.get(s.code)!
    if (s.parent_code && map.has(s.parent_code)) {
      const p = map.get(s.parent_code)!
      ;(p.children ||= []).push(node)
    } else {
      roots.push(node)
    }
  }
  return roots
})

/** 选中上级科目后，自动带出 类别 / 方向 / 层级 */
function onPickParent(code: string | null) {
  if (!code) {
    form.value.level = 1
    return
  }
  const p = subjects.value.find(s => s.code === code)
  if (p) {
    form.value.category = p.category
    form.value.direction = p.direction
    form.value.level = p.level + 1
  }
}

/** 依据所选上级，给出推荐的新科目编码前缀 */
const suggestedPrefix = computed(() => {
  const pc = form.value.parent_code
  if (!pc) return ''
  const siblings = subjects.value.filter(s => s.parent_code === pc)
  return siblings.length ? `${pc}.${String(siblings.length + 1).padStart(2, '0')}` : `${pc}.01`
})

const filtered = computed(() => {
  const kw = searchKey.value.trim().toLowerCase()
  if (!kw) return subjects.value
  return subjects.value.filter(
    s => s.code.toLowerCase().includes(kw) || s.name.toLowerCase().includes(kw),
  )
})

async function loadData() {
  loading.value = true
  try {
    subjects.value = (await listSubjects()).data
  } catch (e) {
    ElMessage.error('加载科目失败')
  } finally {
    loading.value = false
  }
}

async function handleReset() {
  try {
    await ElMessageBox.confirm(
      '将清空现有凭证与科目，重置为系统标准会计科目表。确定继续？',
      '重置科目',
      { confirmButtonText: '确定重置', cancelButtonText: '取消', type: 'warning' },
    )
    await resetSubjects()
    ElMessage.success('已重置为标准科目')
    await loadData()
  } catch (e) {
    // 取消
  }
}

function openAdd() {
  form.value = {
    code: '', name: '', category: '资产', direction: '借', level: 1, is_leaf: true, status: '启用',
  }
  dialogVisible.value = true
}

async function submitAdd() {
  if (!form.value.code || !form.value.name) {
    ElMessage.warning('科目编码与名称必填')
    return
  }
  try {
    await createSubject(form.value)
    ElMessage.success('科目已新增')
    dialogVisible.value = false
    await loadData()
  } catch (e) {
    ElMessage.error('新增失败（编码可能重复）')
  }
}

onMounted(loadData)
</script>

<template>
  <div class="account-page">
    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-input v-model="searchKey" placeholder="请输入科目编号或名称" clearable class="search-input">
          <template #suffix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-button text circle title="刷新" @click="loadData"><el-icon><Refresh /></el-icon></el-button>
      </div>
      <div class="toolbar-right">
        <el-button type="primary" @click="openAdd">新增科目</el-button>
        <el-button @click="handleReset">重置为标准科目</el-button>
      </div>
    </div>

    <!-- 表格 -->
    <div class="table-wrap">
      <el-table :data="filtered" v-loading="loading" border stripe size="small"
        :header-cell-style="{ background: '#f5f7fa', color: '#303133', fontWeight: 600 }"
        style="width: 100%" max-height="calc(100vh - 180px)">
        <el-table-column prop="code" label="科目编码" width="140" align="center" fixed />
        <el-table-column prop="name" label="科目名称" min-width="180" fixed />
        <el-table-column label="类别" width="90" align="center">
          <template #default="{ row }">
            <span class="cat-tag">{{ categoryLabel[row.category] || row.category }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="level" label="层级" width="72" align="center" />
        <el-table-column prop="parent_code" label="上级编码" width="120" align="center">
          <template #default="{ row }">{{ row.parent_code || '—' }}</template>
        </el-table-column>
        <el-table-column label="方向" width="80" align="center">
          <template #default="{ row }">
            <span :class="['dir-tag', row.direction]">{{ row.direction }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.status === '启用'" size="small" type="success" effect="light">{{ row.status }}</el-tag>
            <el-tag v-else size="small" type="info" effect="light">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 新增弹窗 -->
    <el-dialog v-model="dialogVisible" title="新增科目" width="460px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="科目编码" required>
          <el-input v-model="form.code" placeholder="如 112201" />
        </el-form-item>
        <el-form-item label="科目名称" required>
          <el-input v-model="form.name" placeholder="如 应收账款—客户A" />
        </el-form-item>
        <el-form-item label="类别">
          <el-select v-model="form.category" style="width: 100%" :disabled="!!form.parent_code">
            <el-option v-for="(v, k) in categoryLabel" :key="k" :label="v" :value="k" />
          </el-select>
        </el-form-item>
        <el-form-item label="方向">
          <el-radio-group v-model="form.direction" :disabled="!!form.parent_code">
            <el-radio value="借">借</el-radio>
            <el-radio value="贷">贷</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="层级">
          <el-input-number v-model="form.level" :min="1" :max="3" :disabled="!!form.parent_code" />
        </el-form-item>
        <el-form-item label="上级科目">
          <el-tree-select
            v-model="form.parent_code"
            :data="subjectTree"
            node-key="value"
            :props="{ label: 'label' }"
            placeholder="可选，留空为一级科目"
            clearable
            check-strictly
            style="width: 100%"
            @change="onPickParent"
          />
          <div v-if="suggestedPrefix" class="prefix-tip">
            推荐新编码前缀：<code>{{ suggestedPrefix }}</code>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAdd">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.account-page { display: flex; flex-direction: column; height: 100%; background: #fff; overflow: hidden; }
.toolbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 20px; border-bottom: 1px solid var(--el-border-color-lighter);
  gap: 12px; flex-wrap: wrap; flex-shrink: 0;
}
.toolbar-left { display: flex; align-items: center; gap: 8px; }
.search-input { width: 260px; }
.table-wrap { flex: 1; min-height: 0; overflow: auto; padding: 0 12px 12px; }
.cat-tag {
  display: inline-block; padding: 1px 10px; border-radius: 10px;
  font-size: 12px; background: #f4f4f5; color: #606266;
}
.dir-tag {
  display: inline-block; padding: 1px 10px; border-radius: 10px;
  font-size: 12px; font-weight: 500;
}
.dir-tag.借 { color: #409eff; background: rgba(64, 158, 255, .1); }
.dir-tag.贷 { color: #e6a23c; background: rgba(230, 162, 60, .12); }
.prefix-tip {
  margin-top: 6px;
  font-size: 12px;
  color: #909399;
  line-height: 1.6;
}
.prefix-tip code {
  background: #f5f7fa;
  padding: 1px 6px;
  border-radius: 3px;
  font-family: Consolas, monospace;
  color: #409eff;
}
</style>
