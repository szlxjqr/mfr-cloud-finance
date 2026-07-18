<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

/* ==================== 类型定义 ==================== */

interface AccountNode {
  id: string; code: string; name: string; level: number
  parentCode: string; children: AccountNode[]; hasChildren: boolean
}

interface ColumnarEntry {
  id: string
  date: string
  voucherWord: string
  voucherNumber: number
  summary: string
  debitAmount: number
  creditAmount: number
  direction: '借' | '贷'
  balance: number
}

/* ==================== 状态 ==================== */

const period = ref('2026-05')
const searchKeyword = ref('')
const currency = ref('综合本位币')

const selectedAccount = ref<AccountNode | null>(null)
const accountTree = ref<AccountNode[]>([])
const tableData = ref<ColumnarEntry[]>([])
const loading = ref(false)

/* ==================== 科目树（支持多栏的科目） ==================== */
const mockAccounts: AccountNode[] = [
  { id:'c1', code:'1101', name:'短期投资', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'c2', code:'1501', name:'长期债券投资', level:1, parentCode:'', hasChildren:true, children:[
    { id:'c2-1', code:'1501-01', name:'国债投资', level:2, parentCode:'1501', hasChildren:false, children:[] },
    { id:'c2-2', code:'1501-02', name:'企业债券', level:2, parentCode:'1501', hasChildren:false, children:[] }
  ]},
  { id:'c3', code:'1511', name:'长期股权投资', level:1, parentCode:'', hasChildren:true, children:[] },
  { id:'c4', code:'1604', name:'在建工程', level:1, parentCode:'', hasChildren:true, children:[] },
  { id:'c5', code:'2211', name:'应付职工薪酬', level:1, parentCode:'', hasChildren:true, children:[] },
  { id:'c6', code:'2221', name:'应交税费', level:1, parentCode:'', hasChildren:true, children:[] },
  { id:'c7', code:'3101', name:'盈余公积', level:1, parentCode:'', hasChildren:true, children:[] },
  { id:'c8', code:'3104', name:'利润分配', level:1, parentCode:'', hasChildren:true, children:[] },
  { id:'c9', code:'4001', name:'生产成本', level:1, parentCode:'', hasChildren:true, children:[] },
  { id:'c10', code:'5301', name:'营业外收入', level:1, parentCode:'', hasChildren:true, children:[] },
  { id:'c11', code:'5601', name:'销售费用', level:1, parentCode:'', hasChildren:true, children:[] },
  { id:'c12', code:'5602', name:'管理费用', level:1, parentCode:'', hasChildren:true, children:[] },
  { id:'c13', code:'5603', name:'财务费用', level:1, parentCode:'', hasChildren:true, children:[] },
  { id:'c14', code:'5711', name:'营业外支出', level:1, parentCode:'', hasChildren:true, children:[] }
]

const currencyOptions = ['综合本位币','USD 美元','EUR 欧元','JPY 日元','HKD 港币']

/* ==================== 计算属性 ==================== */
const filteredAccounts = computed(() => {
  let data = accountTree.value
  if (searchKeyword.value.trim()) {
    const kw = searchKeyword.value.trim().toLowerCase()
    data = data.filter(a => a.code.includes(kw) || a.name.toLowerCase().includes(kw))
  }
  return data
})

const flatList = computed(() => {
  const r: AccountNode[] = []
  const flatten = (nodes: AccountNode[]) => nodes.forEach(n => { r.push(n); if (n.hasChildren && n.children.length) flatten(n.children) })
  flatten(accountTree.value)
  return r
})
const idx = computed(() => !selectedAccount.value ? -1 : flatList.value.findIndex(a => a.id === selectedAccount.value!.id))
const hasPrev = computed(() => idx.value > 0)
const hasNext = computed(() => idx.value >= 0 && idx.value < flatList.value.length - 1)

/* ==================== 方法 ==================== */
function loadTree() { accountTree.value = mockAccounts }

function generateData(acc: AccountNode): ColumnarEntry[] {
  const isDebit = acc.code.startsWith('1') ||
    ['4001','5401','5402','5403'].some(p => acc.code.startsWith(p)) ||
    ['5601','5602','5603','5711','5801'].some(p => acc.code.startsWith(p))

  let balance = Math.floor(Math.random() * 500000) + 10000
  if (!isDebit) balance = -balance

  // 期初余额
  const entries: ColumnarEntry[] = [{
    id:`e0`, date:'', voucherWord:'', voucherNumber:0,
    summary:'期初余额', debitAmount:0, creditAmount:0,
    direction: balance >= 0 ? '借' : '贷', balance: Math.abs(balance)
  }]

  // 分录行
  const count = Math.floor(Math.random() * 8) + 3
  const words = ['记','收','付','转']
  const summaries = [
    '购入债券/股票','收到利息/股利','计提减值准备','出售投资',
    '支付工程款','结转完工成本','材料领用','人工费分摊',
    '广告投放支出','差旅报销','办公费用','银行手续费'
  ]

  for (let i = 0; i < count; i++) {
    const day = Math.floor((i / count) * 28) + 1
    const date = `${period.value}-${String(day).padStart(2,'0')}`
    const word = words[Math.floor(Math.random() * words.length)]
    const vNum = Math.floor(Math.random() * 50) + 1
    const summary = summaries[Math.floor(Math.random() * summaries.length)]
    const isD = Math.random() > 0.45
    const amount = Math.floor(Math.random() * 100000) + 2000

    balance += isD ? amount : -amount

    entries.push({
      id:`e${i+1}`, date, voucherWord:word, voucherNumber:vNum,
      summary,
      debitAmount: isD ? amount : 0,
      creditAmount: isD ? 0 : amount,
      direction: balance >= 0 ? '借' : '贷',
      balance: Math.abs(balance)
    })
  }
  return entries
}

function selectAccount(a: AccountNode) {
  selectedAccount.value = a
  loading.value = true
  setTimeout(() => { tableData.value = generateData(a); loading.value = false }, 150)
}
function prev() { if (hasPrev.value) selectAccount(flatList.value[idx.value - 1]) }
function next() { if (hasNext.value) selectAccount(flatList.value[idx.value + 1]) }
function clearSelection() { selectedAccount.value = null; tableData.value = [] }
function fmt(v: number): string { if (!v) return ''; return v.toLocaleString('zh-CN',{minimumFractionDigits:2,maximumFractionDigits:2}) }

onMounted(() => loadTree())
</script>

<template>
  <div class="columnar-page">
    <!-- ===== 顶部工具栏 ===== -->
    <div class="top-toolbar">
      <div class="toolbar-left">
        <span class="label">期间</span>
        <el-date-picker v-model="period" type="month" format="YYYY年MM期" value-format="YYYY-MM"
          size="small" style="width:160px" />
        <el-button size="small" type="primary" plain style="margin-left:8px">筛选 ▾</el-button>
        <el-button size="small" circle><span style="font-size:13px">🔄</span></el-button>
      </div>
      <div class="toolbar-right">
        <el-button size="small">打印</el-button>
        <el-button size="small">导出</el-button>
        <el-button size="small">导出历史</el-button>
      </div>
    </div>

    <!-- ===== 主体区域 ===== -->
    <div class="main-content">
      <!-- 左侧科目树 -->
      <div class="left-panel">
        <div class="panel-search">
          <el-input v-model="searchKeyword" size="small" placeholder="请输入要搜索的科目" clearable>
            <template #prefix><span style="color:#c0c4cc;font-size:13px">🔍</span></template>
          </el-input>
        </div>
        <div class="panel-tree">
          <div v-for="a in filteredAccounts" :key="a.id"
            class="account-item" :class="{ active: selectedAccount?.id===a.id, 'has-children':a.hasChildren }"
            @click="selectAccount(a)">
            <span class="acc-code">{{ a.code }}</span>
            <span class="acc-name">{{ a.name }}</span>
            <span v-if="a.hasChildren" class="exp-icon">▶</span>
          </div>
        </div>
      </div>

      <!-- 拖拽条 -->
      <div class="resizer"><div class="resizer-handle">◀▶</div></div>

      <!-- 右侧 -->
      <div class="right-panel">
        <!-- 科目选择器 + 币别 -->
        <div class="selector-row">
          <div class="account-selector">
            <el-button size="small" :disabled="!hasPrev" @click="prev" class="nav-btn">◀</el-button>
            <div class="sel-display" :class="{ active: !!selectedAccount }">
              <template v-if="selectedAccount">
                <span class="sel-text">{{ selectedAccount.code }} {{ selectedAccount.name }}</span>
                <span class="close-btn" @click.stop="clearSelection">✕</span>
              </template>
              <span v-else class="sel-placeholder">请选择科目</span>
            </div>
            <el-button size="small" :disabled="!hasNext" @click="next" class="nav-btn">▶</el-button>
          </div>
          <div class="currency-select">
            币别：
            <el-select v-model="currency" size="small" style="width:130px">
              <el-option v-for="c in currencyOptions" :key="c" :label="c" :value="c" />
            </el-select>
          </div>
        </div>

        <!-- 数据表格 -->
        <div class="table-area">
          <el-table v-if="selectedAccount && tableData.length > 0" :data="tableData" v-loading="loading"
            border stripe size="small"
            :header-cell-style="{ background:'#f5f7fa', color:'#303133', fontWeight:600, fontSize:'13px' }"
            style="width:100%" max-height="calc(100vh - 240px)">
            <el-table-column prop="date" label="日期" width="110" align="center" sortable />
            <el-table-column label="凭证号" width="110" align="center">
              <template #default="{ row }">
                <span v-if="row.voucherWord">{{ row.voucherWord }}-{{ String(row.voucherNumber).padStart(3,'0') }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="summary" label="摘要" min-width="180" />
            <el-table-column label="借方" width="130" align="right">
              <template #default="{ row }"><span class="amt debit">{{ fmt(row.debitAmount) }}</span></template>
            </el-table-column>
            <el-table-column label="贷方" width="130" align="right">
              <template #default="{ row }"><span class="amt credit">{{ fmt(row.creditAmount) }}</span></template>
            </el-table-column>
            <el-table-column label="方向" width="60" align="center">
              <template #default="{ row }">
                <el-tag :type="row.direction==='借'?'':'success'" size="small" effect="plain">{{ row.direction }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="余额" width="130" align="right">
              <template #default="{ row }"><span class="amt bal">{{ fmt(row.balance) }}</span></template>
            </el-table-column>
          </el-table>

          <div v-else class="empty-state">
            <el-empty description="暂无数据" :image-size="200">
              <template #image><div style="font-size:80px;opacity:0.3">📊</div></template>
            </el-empty>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.columnar-page{ display:flex; flex-direction:column; height:100%; background:#f0f2f5; }

.top-toolbar{
  background:#fff; padding:8px 16px; display:flex; align-items:center;
  justify-content:space-between; border-bottom:1px solid #e4e7ed; flex-shrink:0;
}
.toolbar-left,.toolbar-right{ display:flex; align-items:center; gap:8px; }
.label{ font-size:13px; color:#606266; white-space:nowrap; }

.main-content{ display:flex; flex:1; overflow:hidden; }

.left-panel{
  width:220px; background:#fff; border-right:1px solid #e4e7ed;
  display:flex; flex-direction:column; flex-shrink:0;
}
.panel-search{ padding:12px; border-bottom:1px solid #e4e7ed; }
.panel-tree{ flex:1; overflow-y:auto; padding:4px 0; }
.account-item{
  padding:8px 12px; cursor:pointer; display:flex; align-items:center; gap:6px;
  transition:background .15s; font-size:13px;
}
.account-item:hover{ background:#f5f7fa; }
.account-item.active{ background:#ecf5ff; color:#409eff; }
.acc-code{ color:#909399; font-size:12px; min-width:50px; }
.acc-name{ flex:1; color:#303133; }
.account-item.active .acc-name{ color:#409eff; font-weight:500; }
.account-item.active .acc-code{ color:#409eff; }
.exp-icon{ font-size:10px; color:#909399; }

.resizer{ width:6px; background:#e4e7ed; cursor:col-resize; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.resizer-handle{ font-size:10px; color:#c0c4cc; writing-mode:vertical-rl; letter-spacing:2px; }

.right-panel{ flex:1; display:flex; flex-direction:column; overflow:hidden; background:#fff; }
.selector-row{
  display:flex; align-items:center; justify-content:space-between;
  padding:10px 16px; border-bottom:1px solid #e4e7ed; gap:12px; flex-wrap:wrap;
}
.account-selector{ display:flex; align-items:center; gap:8px; }
.nav-btn{ padding:4px 8px; font-size:12px; }
.sel-display{
  flex:1; padding:6px 16px 6px 36px; border-radius:4px;
  text-align:center; font-size:14px; font-weight:500;
  position:relative; min-width:180px;
  transition:background .15s;
}
.sel-display.active{ background:#409eff; color:#fff; }
.sel-display:not(.active){ background:#f5f7fa; color:#909399; }
.sel-text{ }
.sel-placeholder{ opacity:.7; }
.close-btn{
  position:absolute; left:10px; top:50%; transform:translateY(-50%);
  font-size:14px; cursor:pointer; color:inherit; opacity:.6;
  line-height:1;
}
.close-btn:hover{ opacity:1; }
.currency-select{ display:flex; align-items:center; gap:6px; font-size:13px; color:#606266; white-space:nowrap; flex-shrink:0; }

.table-area{ flex:1; overflow:hidden; }
.empty-state{ display:flex; align-items:center; justify-content:center; height:100%; }

.amt{ font-family:'SF Mono','Menlo','Consolas',monospace; font-size:13px; color:#606266; }
.amt.debit{ color:#303133; font-weight:500; }
.amt.credit{ color:#67c23a; }
.amt.bal{ color:#409eff; font-weight:600; }

:deep(.el-table){ font-size:13px; }
:deep(.el-table th){ padding:8px 0; }
:deep(.el-table td){ padding:6px 0; }
:deep(.el-empty__description){ font-size:14px; color:#909399; }
</style>
