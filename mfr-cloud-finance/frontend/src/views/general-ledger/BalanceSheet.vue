<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

/* ==================== 类型定义 ==================== */

interface AccountNode {
  id: string; code: string; name: string; level: number
  parentCode: string; children: AccountNode[]; hasChildren: boolean
}

interface BalanceRow {
  id: string
  accountCode: string
  accountName: string
  openingDebit: number; openingCredit: number
  periodDebit: number; periodCredit: number
  cumDebit: number; cumCredit: number
  endingDebit: number; endingCredit: number
}

/* ==================== 状态 ==================== */

const period = ref('2026-05')
const searchKeyword = ref('')
const showLevel1Only = ref(false)
const hideZeroBalance = ref(true)
const showNoOpening = ref(false)       // 显示无发生无期初科目
const showAuxAccounting = ref(false)   // 显示辅助核算
const showSealed = ref(false)          // 显示封存科目
const hideCumulative = ref(false)      // 隐藏本年累计

const selectedAccount = ref<AccountNode | null>(null)
const accountTree = ref<AccountNode[]>([])
const tableData = ref<BalanceRow[]>([])
const loading = ref(false)

/* ==================== 科目树（复用） ==================== */
const mockAccounts: AccountNode[] = [
  { id:'b1', code:'1001', name:'库存现金', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b2', code:'1002', name:'银行存款', level:1, parentCode:'', hasChildren:true, children:[
    { id:'b2-1', code:'1002-01', name:'基本户(工行)', level:2, parentCode:'1002', hasChildren:false, children:[] },
    { id:'b2-2', code:'1002-02', name:'一般户(建行)', level:2, parentCode:'1002', hasChildren:false, children:[] }
  ]},
  { id:'b3', code:'1012', name:'其他货币资金', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b4', code:'1101', name:'短期投资', level:1, parentCode:'', hasChildren:true, children:[] },
  { id:'b5', code:'1121', name:'应收票据', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b6', code:'1122', name:'应收账款', level:1, parentCode:'', hasChildren:true, children:[
    { id:'b6-1', code:'1122-01', name:'华宇科技', level:2, parentCode:'1122', hasChildren:false, children:[] },
    { id:'b6-2', code:'1122-02', name:'明达集团', level:2, parentCode:'1122', hasChildren:false, children:[] }
  ]},
  { id:'b7', code:'1123', name:'预付账款', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b8', code:'1131', name:'应收股利', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b9', code:'1132', name:'应收利息', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b10', code:'1221', name:'其他应收款', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b11', code:'1401', name:'材料采购', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b12', code:'1402', name:'在途物资', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b13', code:'1403', name:'原材料', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b14', code:'1404', name:'材料成本差异', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b15', code:'1405', name:'库存商品', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b16', code:'1407', name:'商品进销差价', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b17', code:'1408', name:'委托加工物资', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b18', code:'1411', name:'周转材料', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b19', code:'1421', name:'消耗性生物资产', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b20', code:'1501', name:'长期债券投资', level:1, parentCode:'', hasChildren:true, children:[] },
  { id:'b21', code:'1511', name:'长期股权投资', level:1, parentCode:'', hasChildren:true, children:[] },
  { id:'b22', code:'1601', name:'固定资产', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b23', code:'1602', name:'累计折旧', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b24', code:'1604', name:'在建工程', level:1, parentCode:'', hasChildren:true, children:[] },
  { id:'b25', code:'1605', name:'工程物资', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b26', code:'1701', name:'无形资产', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b27', code:'1801', name:'长期待摊费用', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b28', code:'1901', name:'待处理财产损溢', level:1, parentCode:'', hasChildren:false, children:[] },
  // 负债类
  { id:'b29', code:'2001', name:'短期借款', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b30', code:'2201', name:'应付票据', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b31', code:'2202', name:'应付账款', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b32', code:'2203', name:'预收账款', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b33', code:'2211', name:'应付职工薪酬', level:1, parentCode:'', hasChildren:true, children:[] },
  { id:'b34', code:'2221', name:'应交税费', level:1, parentCode:'', hasChildren:true, children:[] },
  { id:'b35', code:'2231', name:'应付利息', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b36', code:'2232', name:'应付利润', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b37', code:'2241', name:'其他应付款', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b38', code:'2401', name:'递延收益', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b39', code:'2501', name:'长期借款', level:1, parentCode:'', hasChildren:false, children:[] },
  // 权益类
  { id:'b40', code:'3001', name:'实收资本', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b41', code:'3002', name:'资本公积', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b42', code:'3101', name:'盈余公积', level:1, parentCode:'', hasChildren:true, children:[] },
  { id:'b43', code:'3103', name:'本年利润', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b44', code:'3104', name:'利润分配', level:1, parentCode:'', hasChildren:true, children:[] },
  // 成本类
  { id:'b45', code:'4001', name:'生产成本', level:1, parentCode:'', hasChildren:true, children:[] },
  { id:'b46', code:'4101', name:'制造费用', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b47', code:'4301', name:'研发支出', level:1, parentCode:'', hasChildren:false, children:[] },
  // 损益类 — 收入
  { id:'b48', code:'5001', name:'主营业务收入', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b49', code:'5051', name:'其他业务收入', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b50', code:'5111', name:'投资收益', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b51', code:'5301', name:'营业外收入', level:1, parentCode:'', hasChildren:true, children:[] },
  // 损益类 — 成本费用
  { id:'b52', code:'5401', name:'主营业务成本', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b53', code:'5402', name:'其他业务成本', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b54', code:'5403', name:'营业税金及附加', level:1, parentCode:'', hasChildren:false, children:[] },
  { id:'b55', code:'5601', name:'销售费用', level:1, parentCode:'', hasChildren:true, children:[] },
  { id:'b56', code:'5602', name:'管理费用', level:1, parentCode:'', hasChildren:true, children:[] },
  { id:'b57', code:'5603', name:'财务费用', level:1, parentCode:'', hasChildren:true, children:[] },
  { id:'b58', code:'5711', name:'营业外支出', level:1, parentCode:'', hasChildren:true, children:[] },
  { id:'b59', code:'5801', name:'所得税费用', level:1, parentCode:'', hasChildren:false, children:[] }
]

/* ==================== 计算属性 ==================== */
const filteredAccounts = computed(() => {
  let data = accountTree.value
  if (showLevel1Only.value) data = data.filter(a => a.level === 1)
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

function generateData(acc: AccountNode): BalanceRow[] {
  const isDebit = acc.code.startsWith('1') || acc.code.startsWith('5') && (
    ['5401','5402','5403','560','5711','5801'].some(p => acc.code.startsWith(p))
  )
  const od = Math.floor(Math.random()*500000)+5000
  const pd = Math.floor(Math.random()*200000)+1000
  const cd = Math.floor(Math.random()*800000)+5000
  const ed = od + pd - (isDebit ? pd*0.6 : pd*1.4)
  const ec = isDebit ? 0 : Math.abs(ed)
  const ebd = isDebit ? Math.abs(ed) : 0

  return [{
    id: `br-${acc.id}`, accountCode: acc.code, accountName: acc.name,
    openingDebit: isDebit ? od : 0, openingCredit: isDebit ? 0 : od,
    periodDebit: isDebit ? Math.round(pd*0.55) : Math.round(pd*0.35),
    periodCredit: isDebit ? Math.round(pd*0.35) : Math.round(pd*0.65),
    cumDebit: isDebit ? Math.round(cd*0.55) : Math.round(cd*0.35),
    cumCredit: isDebit ? Math.round(cd*0.35) : Math.round(cd*0.65),
    endingDebit: ebd, endingCredit: ec
  }]
}

function selectAccount(a: AccountNode) {
  selectedAccount.value = a
  loading.value = true
  setTimeout(() => { tableData.value = generateData(a); loading.value = false }, 150)
}
function prev() { if (hasPrev.value) selectAccount(flatList.value[idx.value - 1]) }
function next() { if (hasNext.value) selectAccount(flatList.value[idx.value + 1]) }
function fmt(v: number): string { if (!v) return ''; return v.toLocaleString('zh-CN',{minimumFractionDigits:2,maximumFractionDigits:2}) }
function refresh() { if (selectedAccount.value) selectAccount(selectedAccount.value) }

onMounted(() => loadTree())
</script>

<template>
  <div class="balance-sheet-page">
    <!-- ===== 顶部工具栏 ===== -->
    <div class="top-toolbar">
      <div class="toolbar-left">
        <span class="label">期间</span>
        <el-date-picker v-model="period" type="month" format="YYYY年MM期" value-format="YYYY-MM"
          size="small" style="width:160px" @change="refresh" />
        <el-button size="small" type="primary" plain style="margin-left:8px">筛选 ▾</el-button>
        <el-button size="small" circle @click="refresh"><span style="font-size:13px">🔄</span></el-button>
      </div>
      <div class="toolbar-right">
        <el-checkbox v-model="showLevel1Only" size="small">只显示一级科目</el-checkbox>
        <el-checkbox v-model="hideZeroBalance" size="small">隐藏余额为0</el-checkbox>
        <el-checkbox v-model="showNoOpening" size="small">显示无发生无期初科目</el-checkbox>
        <el-checkbox v-model="showAuxAccounting" size="small">显示辅助核算</el-checkbox>
        <el-checkbox v-model="showSealed" size="small">显示封存科目</el-checkbox>
        <el-button size="small" style="margin-left:12px">打印</el-button>
        <el-button size="small">导出</el-button>
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
        <!-- 科目选择器 + 隐藏累计开关 -->
        <div class="selector-row">
          <div class="account-selector">
            <el-button size="small" :disabled="!hasPrev" @click="prev" class="nav-btn">◀</el-button>
            <div class="sel-display">
              <span v-if="selectedAccount" class="sel-text">{{ selectedAccount.code }} {{ selectedAccount.name }}</span>
              <span v-else class="sel-placeholder">请选择科目</span>
            </div>
            <el-button size="small" :disabled="!hasNext" @click="next" class="nav-btn">▶</el-button>
          </div>
          <div class="cum-toggle">
            <span>隐藏本年累计</span>
            <el-switch v-model="hideCumulative" size="small" />
          </div>
        </div>

        <!-- 数据表格 -->
        <div class="table-area">
          <el-table v-if="selectedAccount" :data="tableData" v-loading="loading" border stripe size="small"
            :header-cell-style="{ background:'#f5f7fa', color:'#303133', fontWeight:600, fontSize:'13px' }"
            style="width:100%" max-height="calc(100vh - 260px)">
            <el-table-column prop="accountCode" label="科目编码" width="120" align="center" fixed />
            <el-table-column prop="accountName" label="科目名称" min-width="160" fixed />

            <!-- 期初余额 -->
            <el-table-column label="期初余额" align="center">
              <el-table-column label="借方" width="110" align="right">
                <template #default="{ row }"><span class="amt">{{ fmt(row.openingDebit) }}</span></template>
              </el-table-column>
              <el-table-column label="贷方" width="110" align="right">
                <template #default="{ row }"><span class="amt">{{ fmt(row.openingCredit) }}</span></template>
              </el-table-column>
            </el-table-column>

            <!-- 本期发生额 -->
            <el-table-column label="本期发生额" align="center">
              <el-table-column label="借方" width="110" align="right">
                <template #default="{ row }"><span class="amt hl">{{ fmt(row.periodDebit) }}</span></template>
              </el-table-column>
              <el-table-column label="贷方" width="110" align="right">
                <template #default="{ row }"><span class="amt hl">{{ fmt(row.periodCredit) }}</span></template>
              </el-table-column>
            </el-table-column>

            <!-- 本年累计（可隐藏） -->
            <el-table-column v-if="!hideCumulative" label="本年累计发生额" align="center">
              <el-table-column label="借方" width="110" align="right">
                <template #default="{ row }"><span class="amt">{{ fmt(row.cumDebit) }}</span></template>
              </el-table-column>
              <el-table-column label="贷方" width="110" align="right">
                <template #default="{ row }"><span class="amt">{{ fmt(row.cumCredit) }}</span></template>
              </el-table-column>
            </el-table-column>

            <!-- 期末余额 -->
            <el-table-column label="期末余额" align="center">
              <el-table-column label="借方" width="110" align="right">
                <template #default="{ row }"><span class="amt end">{{ fmt(row.endingDebit) }}</span></template>
              </el-table-column>
              <el-table-column label="贷方" width="110" align="right">
                <template #default="{ row }"><span class="amt end">{{ fmt(row.endingCredit) }}</span></template>
              </el-table-column>
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
.balance-sheet-page{ display:flex; flex-direction:column; height:100%; background:#f0f2f5; }

.top-toolbar {
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
.selector-row{ display:flex; align-items:center; justify-content:space-between; padding:10px 16px; border-bottom:1px solid #e4e7ed; gap:8px; }
.account-selector{ display:flex; align-items:center; gap:8px; }
.nav-btn{ padding:4px 8px; font-size:12px; }
.sel-display{
  flex:1; background:#409eff; color:#fff; padding:6px 16px; border-radius:4px;
  text-align:center; font-size:14px; font-weight:500;
}
.sel-placeholder{ opacity:.7; }
.cum-toggle{ display:flex; align-items:center; gap:6px; font-size:13px; color:#606266; white-space:nowrap; flex-shrink:0; }

.table-area{ flex:1; overflow:hidden; }
.empty-state{ display:flex; align-items:center; justify-content:center; height:100%; }

.amt{ font-family:'SF Mono','Menlo','Consolas',monospace; font-size:13px; color:#909399; }
.amt.hl{ color:#303133; font-weight:500; }
.amt.end{ color:#409eff; font-weight:600; }

:deep(.el-table){ font-size:13px; }
:deep(.el-table th){ padding:8px 0; }
:deep(.el-table td){ padding:6px 0; }
:deep(.el-empty__description){ font-size:14px; color:#909399; }
</style>
