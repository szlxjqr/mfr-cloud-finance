<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

/* ==================== 类型定义 ==================== */

/** 科目节点 */
interface AccountNode {
  id: string
  code: string
  name: string
  level: number
  parentCode: string
  children?: AccountNode[]
  hasChildren: boolean
}

/** 余额行 */
interface QtyFxBalanceRow {
  id: string
  accountCode: string    // 科目编号
  accountName: string    // 科目名称
  unit: string           // 计量单位
  // 期初余额
  openQty: number        // 期初数量
  openPrice: number      // 期初单价
  openDebit: number      // 期初借方
  openCredit: number     // 期初贷方
  // 本期发生额
  curDebitQty: number    // 本期借方数量
  curDebitAmt: number    // 本期借方金额
  curCreditQty: number   // 本期贷方数量
  curCreditAmt: number   // 本期贷方金额
  // 期末余额
  closeQty: number       // 期末数量
  closePrice: number     // 期末单价
  closeDebit: number     // 期末借方
  closeCredit: number    // 期末贷方
}

/* ==================== 状态 ==================== */

const periodRange = ref(['2026-05', '2026-05'])
const qtyAmtMode = ref('数量金额')    // 数量金额 / 仅数量 / 仅金额 / 原币本位
const hideZeroBalance = ref(false)    // 隐藏余额为0

const searchKeyword = ref('')
const selectedNode = ref<AccountNode | null>(null)

/** 左侧科目树 */
const accountTree = ref<AccountNode[]>([])
/** 右侧表格数据 */
const tableData = ref<QtyFxBalanceRow[]>([])
const loading = ref(false)

/* ==================== Mock 数据 ==================== */
const mockAccounts: AccountNode[] = [
  { id:'a1', code:'1001', name:'库存现金', level:1, parentCode:'', hasChildren:true,
    children:[
      { id:'a1-1', code:'100101', name:'人民币', level:2, parentCode:'1001', hasChildren:false },
      { id:'a1-2', code:'100102', name:'美元', level:2, parentCode:'1001', hasChildren:false },
    ]
  },
  { id:'a2', code:'1002', name:'银行存款', level:1, parentCode:'', hasChildren:true,
    children:[
      { id:'a2-1', code:'100201', name:'工商银行', level:2, parentCode:'1002', hasChildren:false },
      { id:'a2-2', code:'100202', name:'建设银行', level:2, parentCode:'1002', hasChildren:false },
      { id:'a2-3', code:'100203', name:'招商银行', level:2, parentCode:'1002', hasChildren:false },
    ]
  },
  { id:'a3', code:'1122', name:'应收账款', level:1, parentCode:'', hasChildren:false },
  { id:'a4', code:'1403', name:'原材料', level:1, parentCode:'', hasChildren:true,
    children:[
      { id:'a4-1', code:'140301', name:'钢材', level:2, parentCode:'1403', hasChildren:false },
      { id:'a4-2', code:'140302', name:'塑料粒子', level:2, parentCode:'1403', hasChildren:false },
      { id:'a4-3', code:'140303', name:'电子元件', level:2, parentCode:'1403', hasChildren:false },
    ]
  },
  { id:'a5', code:'1405', name:'库存商品', level:1, parentCode:'', hasChildren:true,
    children:[
      { id:'a5-1', code:'140501', name:'A系列产品', level:2, parentCode:'1405', hasChildren:false },
      { id:'a5-2', code:'140502', name:'B系列产品', level:2, parentCode:'1405', hasChildren:false },
    ]
  },
  { id:'a6', code:'1501', name:'长期债券投资', level:1, parentCode:'', hasChildren:true,
    children:[
      { id:'a6-1', code:'150101', name:'国债', level:2, parentCode:'1501', hasChildren:false },
      { id:'a6-2', code:'150102', name:'企业债券', level:2, parentCode:'1501', hasChildren:false },
    ]
  },
  { id:'a7', code:'2202', name:'应付账款', level:1, parentCode:'', hasChildren:false },
  { id:'a8', code:'2203', name:'预收账款', level:1, parentCode:'', hasChildren:false },
]

const units = ['件','套','台','吨','批','次','项']

function generateData(): QtyFxBalanceRow[] {
  const rows: QtyFxBalanceRow[] = []
  const nodes = selectedNode.value?.children ? selectedNode.value.children : (selectedNode.value ? [selectedNode.value] : [])
  
  if (nodes.length === 0) return rows

  for (let i=0; i<nodes.length; i++) {
    const node = nodes[i]
    const unitPrice = Math.floor(Math.random() * 500) + 10
    const openQty = Math.floor(Math.random() * 3000) + 20
    const openPrice = unitPrice
    const openDebitAmt = openQty * unitPrice
    const openCreditAmt = Math.floor(Math.random() * 8000)

    const curDebitQty = Math.floor(Math.random() * 400)
    const curDebitAmt = curDebitQty * unitPrice
    const curCreditQty = Math.floor(Math.random() * 300)
    const curCreditAmt = curCreditQty * unitPrice

    let closeQty = openQty + curDebitQty - curCreditQty
    const closePrice = unitPrice
    const closeDebitAmt = closeQty > 0 ? Math.abs(closeQty * closePrice) : 0
    const closeCreditAmt = closeQty < 0 ? Math.abs(closeQty * closePrice) : 0
    if (closeQty < 0) closeQty = Math.abs(closeQty)

    rows.push({
      id:`b${i}`, accountCode:node.code, accountName:node.name,
      unit:units[i % units.length],
      openQty, openPrice, openDebit:openDebitAmt, openCredit:openCreditAmt,
      curDebitQty, curDebitAmt, curCreditQty, curCreditAmt,
      closeQty, closePrice, closeDebit:closeDebitAmt, closeCredit:closeCreditAmt
    })
  }
  return rows
}

/* ==================== 计算属性 ==================== */
const filteredTree = computed(() => {
  if (!searchKeyword.value.trim()) return accountTree.value
  const kw=searchKeyword.value.trim().toLowerCase()
  
  function filter(nodes:AccountNode[]):AccountNode[] {
    return nodes.reduce((acc,n)=>{
      const match=n.code.includes(kw)||n.name.toLowerCase().includes(kw)
      const sub=n.children?filter(n.children):[]
      if(match||sub.length>0){
        acc.push({...n, children:sub.length>0?sub:n.children})
      }
      return acc
    },[] as AccountNode[])
  }
  return filter(accountTree.value)
})

/** 隐藏余额为0的行 */
const displayData = computed(() => {
  if (!hideZeroBalance.value) return tableData.value
  return tableData.value.filter(r =>
    r.closeQty !== 0 || r.closeDebit !== 0 || r.closeCredit !== 0
  )
})

/** 展开所有节点为扁平列表（用于索引定位） */
const flatList=computed(()=>{
  function flatten(nodes:AccountNode[]):AccountNode[]{
    return nodes.reduce((acc,n)=>{
      acc.push(n)
      if(n.children&&n.children.length)acc.push(...flatten(n.children))
      return acc
    },[] as AccountNode[])
  }
  return flatten(filteredTree.value)
})

const idx=computed(()=>!selectedNode.value?-1:flatList.value.findIndex(x=>x.id===selectedNode.value!.id))
const hasPrev=computed(()=>idx.value>0)
const hasNext=computed(()=>idx.value>=0&&idx.value<flatList.value.length-1)

/* 合计行 */
const totals = computed(() => {
  const data = displayData.value
  if (data.length === 0) return null
  return data.reduce((acc, r)=>({
    openQty:acc.openQty+r.openQty, openPrice:acc.openPrice+r.openPrice,
    openDebit:acc.openDebit+r.openDebit, openCredit:acc.openCredit+r.openCredit,
    curDebitQty:acc.curDebitQty+r.curDebitQty, curDebitAmt:acc.curDebitAmt+r.curDebitAmt,
    curCreditQty:acc.curCreditQty+r.curCreditQty, curCreditAmt:acc.curCreditAmt+r.curCreditAmt,
    closeQty:acc.closeQty+r.closeQty, closePrice:acc.closePrice+r.closePrice,
    closeDebit:acc.closeDebit+r.closeDebit, closeCredit:acc.closeCredit+r.closeCredit
  }),{openQty:0,openPrice:0,openDebit:0,openCredit:0,curDebitQty:0,curDebitAmt:0,curCreditQty:0,curCreditAmt:0,closeQty:0,closePrice:0,closeDebit:0,closeCredit:0})
})

/* ==================== 方法 ==================== */
function loadTree(){ accountTree.value=mockAccounts }

function selectNode(node:AccountNode){
  selectedNode.value=node
  loading.value=true
  setTimeout(()=>{tableData.value=generateData();loading.value=false},150)
}
function prev(){if(hasPrev.value)selectNode(flatList.value[idx.value-1])}
function next(){if(hasNext.value)selectNode(flatList.value[idx.value+1])}

function fmt(v:number):string{if(!v)return '';return v.toLocaleString('zh-CN',{minimumFractionDigits:2,maximumFractionDigits:2})}
function refresh(){if(selectedNode.value)selectNode(selectedNode.value)}

onMounted(()=>loadTree())
</script>

<template>
  <div class="qty-fx-balance-page">
    <!-- ===== 顶部工具栏 ===== -->
    <div class="top-toolbar">
      <div class="toolbar-left">
        <span class="label">期间</span>
        <el-date-picker v-model="periodRange" type="monthrange"
          range-separator="-" start-placeholder="" end-placeholder=""
          format="YYYY年MM期" value-format="YYYY-MM"
          size="small" style="width:220px" @change="refresh" />
        <el-button size="small" type="primary" plain style="margin-left:8px">筛选 ▾</el-button>
        <el-button size="small" circle @click="refresh"><span style="font-size:13px">🔄</span></el-button>
      </div>
      <div class="toolbar-right">
        <el-button size="small">打印</el-button>
        <el-button size="small">导出</el-button>
      </div>
    </div>

    <!-- ===== 主体区域 ===== -->
    <div class="main-content">
      <!-- 左侧科目树面板 -->
      <div class="left-panel">
        <div class="panel-search">
          <el-input v-model="searchKeyword" size="small" placeholder="请输入要搜索的科目" clearable>
            <template #prefix><span style="color:#c0c4cc;font-size:13px">🔍</span></template>
          </el-input>
        </div>
        <div class="panel-list">
          <div v-if="filteredTree.length === 0" class="no-data">暂无数据</div>
          <template v-for="node in filteredTree" :key="node.id">
            <div
              class="tree-node"
              :class="{ active: selectedNode?.id === node.id }"
              :style="{ paddingLeft: (node.level - 1) * 16 + 12 + 'px' }"
              @click="selectNode(node)"
            >
              <span class="node-code">{{ node.code }}</span>
              <span class="node-name">{{ node.name }}</span>
            </div>
            <template v-if="node.children && node.children.length">
              <div
                v-for="child in node.children"
                :key="child.id"
                class="tree-node child"
                :class="{ active: selectedNode?.id === child.id }"
                :style="{ paddingLeft: child.level * 16 + 12 + 'px' }"
                @click="selectNode(child)"
              >
                <span class="node-code">{{ child.code }}</span>
                <span class="node-name">{{ child.name }}</span>
              </div>
            </template>
          </template>
        </div>
      </div>

      <!-- 拖拽条 -->
      <div class="resizer"><div class="resizer-handle">◀▶</div></div>

      <!-- 右侧 -->
      <div class="right-panel">
        <!-- 选择器 -->
        <div class="selector-row">
          <div class="selector-bar">
            <el-button size="small" :disabled="!hasPrev" @click="prev" class="nav-btn">◀</el-button>
            <el-button size="small" :disabled="!hasPrev" @click="prev" class="nav-btn">◀</el-button>
            <div class="sel-display" :class="{ active: !!selectedNode }">
              <template v-if="selectedNode">
                <span class="sel-text">{{ selectedNode.code }} {{ selectedNode.name }}</span>
              </template>
              <span v-else class="sel-placeholder">请选择科目</span>
            </div>
            <el-button size="small" :disabled="!hasNext" @click="next" class="nav-btn">▶</el-button>
            <el-button size="small" :disabled="!hasNext" @click="next" class="nav-btn">▶</el-button>
          </div>
          <!-- 表格上方选项行 -->
          <div class="table-options">
            <span class="opt-label">显示方式</span>
            <el-select v-model="qtyAmtMode" size="small" style="width:110px;margin-left:6px">
              <el-option label="数量金额" value="数量金额" />
              <el-option label="仅数量" value="仅数量" />
              <el-option label="仅金额" value="仅金额" />
              <el-option label="原币本位" value="原币本位" />
            </el-select>
            <el-checkbox v-model="hideZeroBalance" size="small" style="margin-left:16px">隐藏余额为0</el-checkbox>
          </div>
        </div>

        <!-- 数据表格 -->
        <div class="table-area">
          <el-table v-if="displayData.length > 0" :data="displayData" v-loading="loading"
            border stripe size="small" show-summary :summary-method="()=>totals?[totals]:[]"
            :header-cell-style="{ background:'#f5f7fa', color:'#303133', fontWeight:600, fontSize:'13px' }"
            style="width:100%" max-height="calc(100vh - 260px)">
            <el-table-column prop="accountCode" label="科目编号" width="110" align="center" fixed />
            <el-table-column prop="accountName" label="科目名称" min-width="130" fixed />

            <!-- 计量单位 -->
            <el-table-column v-if="qtyAmtMode==='数量金额'||qtyAmtMode==='仅数量'" prop="unit" label="计量单位" width="80" align="center" />

            <!-- 期初余额：数量/单价/借方/贷方 -->
            <el-table-column label="期初余额" align="center">
              <el-table-column v-if="qtyAmtMode==='数量金额'||qtyAmtMode==='仅数量'" prop="openQty" label="数量" width="75" align="right">
                <template #default="{ row }"><span class="amt">{{ row.openQty || '' }}</span></template>
              </el-table-column>
              <el-table-column v-if="qtyAmtMode==='数量金额'||qtyAmtMode==='原币本位'" prop="openPrice" label="单价" width="85" align="right">
                <template #default="{ row }"><span class="amt">{{ fmt(row.openPrice) }}</span></template>
              </el-table-column>
              <el-table-column v-if="qtyAmtMode==='数量金额'||qtyAmtMode==='仅金额'||qtyAmtMode==='原币本位'" prop="openDebit" label="借方" width="105" align="right">
                <template #default="{ row }"><span class="amt debit">{{ fmt(row.openDebit) }}</span></template>
              </el-table-column>
              <el-table-column v-if="qtyAmtMode==='数量金额'||qtyAmtMode==='仅金额'||qtyAmtMode==='原币本位'" prop="openCredit" label="贷方" width="105" align="right">
                <template #default="{ row }"><span class="amt credit">{{ fmt(row.openCredit) }}</span></template>
              </el-table-column>
            </el-table-column>

            <!-- 本期发生额：借方数量/借方金额/贷方数量/贷方金额 -->
            <el-table-column label="本期发生额" align="center">
              <el-table-column v-if="qtyAmtMode==='数量金额'||qtyAmtMode==='仅数量'" prop="curDebitQty" label="借方数量" width="90" align="right">
                <template #default="{ row }"><span class="amt">{{ row.curDebitQty || '' }}</span></template>
              </el-table-column>
              <el-table-column v-if="qtyAmtMode==='数量金额'||qtyAmtMode==='仅金额'||qtyAmtMode==='原币本位'" prop="curDebitAmt" label="借方金额" width="105" align="right">
                <template #default="{ row }"><span class="amt debit">{{ fmt(row.curDebitAmt) }}</span></template>
              </el-table-column>
              <el-table-column v-if="qtyAmtMode==='数量金额'||qtyAmtMode==='仅数量'" prop="curCreditQty" label="贷方数量" width="90" align="right">
                <template #default="{ row }"><span class="amt">{{ row.curCreditQty || '' }}</span></template>
              </el-table-column>
              <el-table-column v-if="qtyAmtMode==='数量金额'||qtyAmtMode==='仅金额'||qtyAmtMode==='原币本位'" prop="curCreditAmt" label="贷方金额" width="105" align="right">
                <template #default="{ row }"><span class="amt credit">{{ fmt(row.curCreditAmt) }}</span></template>
              </el-table-column>
            </el-table-column>

            <!-- 期末余额：数量/单价/借方/贷方 -->
            <el-table-column label="期末余额" align="center">
              <el-table-column v-if="qtyAmtMode==='数量金额'||qtyAmtMode==='仅数量'" prop="closeQty" label="数量" width="75" align="right">
                <template #default="{ row }"><span class="amt bal">{{ row.closeQty || '' }}</span></template>
              </el-table-column>
              <el-table-column v-if="qtyAmtMode==='数量金额'||qtyAmtMode==='原币本位'" prop="closePrice" label="单价" width="85" align="right">
                <template #default="{ row }"><span class="amt">{{ fmt(row.closePrice) }}</span></template>
              </el-table-column>
              <el-table-column v-if="qtyAmtMode==='数量金额'||qtyAmtMode==='仅金额'||qtyAmtMode==='原币本位'" prop="closeDebit" label="借方" width="105" align="right">
                <template #default="{ row }"><span class="amt bal">{{ fmt(row.closeDebit) }}</span></template>
              </el-table-column>
              <el-table-column v-if="qtyAmtMode==='数量金额'||qtyAmtMode==='仅金额'||qtyAmtMode==='原币本位'" prop="closeCredit" label="贷方" width="105" align="right">
                <template #default="{ row }"><span class="amt">{{ fmt(row.closeCredit) }}</span></template>
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
.qty-fx-balance-page{ display:flex; flex-direction:column; height:100%; background:#f0f2f5; }

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
.panel-list{ flex:1; overflow-y:auto; }
.no-data{
  text-align:center; color:#c0c4cc; font-size:14px; padding:60px 16px;
}
.tree-node{
  padding:7px 12px; cursor:pointer; display:flex; align-items:center; gap:8px;
  transition:background .15s; font-size:13px; white-space:nowrap;
}
.tree-node:hover{ background:#f5f7fa; }
.tree-node.active{ background:#ecf5ff; color:#409eff; }
.tree-node.child{ font-size:12.5px; }
.node-code{ color:#909399; font-size:12px; min-width:55px; flex-shrink:0; }
.node-name{ flex:1; color:#303133; }
.tree-node.active .node-name{ color:#409eff; font-weight:500; }
.tree-node.active .node-code{ color:#409eff; }

.resizer{ width:6px; background:#e4e7ed; cursor:col-resize; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.resizer-handle{ font-size:10px; color:#c0c4cc; writing-mode:vertical-rl; letter-spacing:2px; }

.right-panel{ flex:1; display:flex; flex-direction:column; overflow:hidden; background:#fff; }
.selector-row{
  display:flex; align-items:flex-start; justify-content:space-between;
  padding:10px 16px; border-bottom:1px solid #e4e7ed; gap:12px; flex-wrap:wrap;
}
.selector-bar{ display:flex; align-items:center; gap:4px; }
.nav-btn{ padding:4px 8px; font-size:12px; }
.sel-display{
  flex:1; padding:6px 20px; border-radius:4px;
  text-align:center; font-size:14px; font-weight:500; min-width:180px;
}
.sel-display.active{ background:#409eff; color:#fff; }
.sel-display:not(.active){ background:#f5f7fa; color:#909399; }
.table-options{
  display:flex; align-items:center; gap:4px; margin-top:2px; flex-shrink:0;
}
.opt-label{ font-size:13px; color:#606266; white-space:nowrap; }

.table-area{ flex:1; overflow:auto; }
.empty-state{ display:flex; align-items:center; justify-content:center; height:100%; }

.amt{ font-family:'SF Mono','Menlo','Consolas',monospace; font-size:13px; color:#606266; }
.amt.debit{ color:#303133; font-weight:500; }
.amt.credit{ color:#67c23a; }
.amt.bal{ color:#409eff; font-weight:600; }

:deep(.el-table){ font-size:13px; }
:deep(.el-table th){ padding:8px 0; }
:deep(.el-table td){ padding:5px 0; }
:deep(.el-empty__description){ font-size:14px; color:#909399; }
:deep(.el-table__footer-wrapper){ font-weight:600; background:#fafafa; }
</style>
