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

/** 分录行 */
interface QtyFxDetailRow {
  id: string
  date: string
  voucherWord: string
  voucherNumber: number
  summary: string
  // 借方
  debitQty: number
  debitPrice: number
  debitAmount: number
  // 贷方
  creditQty: number
  creditPrice: number
  creditAmount: number
  // 余额
  direction: '借' | '贷'
  balanceQty: number
  balancePrice: number
  balanceAmount: number
}

/* ==================== 状态 ==================== */

const periodRange = ref(['2026-05', '2026-05'])
const showDetailName = ref(false)    // 显示明细科目名称
const showMethod = ref(false)        // 显示方式
const qtyAmtMode = ref('数量金额')   // 数量金额 / 仅数量 / 仅金额 / 原币本位

const searchKeyword = ref('')
const selectedNode = ref<AccountNode | null>(null)

/** 左侧科目树 */
const accountTree = ref<AccountNode[]>([])
/** 右侧表格数据 */
const tableData = ref<QtyFxDetailRow[]>([])
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
      { id:'a2-1', code:'20101', name:'工商银行', level:2, parentCode:'1002', hasChildren:false },
      { id:'a2-2', code:'20102', name:'建设银行', level:2, parentCode:'1002', hasChildren:false },
      { id:'a2-3', code:'20103', name:'招商银行', level:2, parentCode:'1002', hasChildren:false },
    ]
  },
  { id:'a3', code:'1122', name:'应收账款', level:1, parentCode:'', hasChildren:false },
  { id:'a4', code:'1403', name:'原材料', level:1, parentCode:'', hasChildren:true,
    children:[
      { id:'a4-1', code:'140301', name:'钢材', level:2, parentCode:'1403', hasChildren:false },
      { id:'a4-2', code:'140302', name:'塑料粒子', level:2, parentCode:'1403', hasChildren:false },
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

function generateData(_node:AccountNode): QtyFxDetailRow[] {
  const rows: QtyFxDetailRow[] = []
  let balQty = Math.floor(Math.random() * 5000) + 200
  const unitPrice = Math.floor(Math.random() * 300) + 5

  // 期初余额行
  rows.push({
    id:`r0`, date:'', voucherWord:'', voucherNumber:0,
    summary:'期初余额',
    debitQty:0, debitPrice:0, debitAmount:0,
    creditQty:0, creditPrice:0, creditAmount:0,
    direction:'借',
    balanceQty:balQty, balancePrice:unitPrice, balanceAmount:balQty*unitPrice
  })

  const count = Math.floor(Math.random() * 8) + 4
  const words=['记','收','付','转']
  const summaries=[
    '采购入库','销售出库','材料领用','产品完工',
    '调拨转入','调拨转出','盘盈','盘亏','报废处理',
    '外币兑换','汇率调整','结汇'
  ]

  for (let i=0; i<count; i++) {
    const day=Math.floor((i/count)*28)+1
    const date=`${periodRange.value[0]}-${String(day).padStart(2,'0')}`
    const word=words[Math.floor(Math.random()*words.length)]
    const vNum=Math.floor(Math.random()*80)+1
    const summary=summaries[Math.floor(Math.random()*summaries.length)]
    const isDebit=Math.random()>0.45
    const qty=Math.floor(Math.random()*500)+10

    if (isDebit) balQty+=qty; else balQty-=qty

    rows.push({
      id:`r${i+1}`, date, voucherWord:word, voucherNumber:vNum, summary,
      debitQty: isDebit ? qty : 0, debitPrice: isDebit ? unitPrice : 0,
      debitAmount: isDebit ? qty*unitPrice : 0,
      creditQty: isDebit ? 0 : qty, creditPrice: isDebit ? 0 : unitPrice,
      creditAmount: isDebit ? 0 : qty*unitPrice,
      direction: balQty>=0?'借':'贷',
      balanceQty:Math.abs(balQty), balancePrice:unitPrice, balanceAmount:Math.abs(balQty)*unitPrice
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

/* ==================== 方法 ==================== */
function loadTree(){ accountTree.value=mockAccounts }

function selectNode(node:AccountNode){
  selectedNode.value=node
  loading.value=true
  setTimeout(()=>{tableData.value=generateData(node);loading.value=false},150)
}
function prev(){if(hasPrev.value)selectNode(flatList.value[idx.value-1])}
function next(){if(hasNext.value)selectNode(flatList.value[idx.value+1])}

function fmt(v:number):string{if(!v)return '';return v.toLocaleString('zh-CN',{minimumFractionDigits:2,maximumFractionDigits:2})}
function refresh(){if(selectedNode.value)selectNode(selectedNode.value)}

onMounted(()=>loadTree())
</script>

<template>
  <div class="qty-fx-detail-page">
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
        <el-button size="small">导出 ▾</el-button>
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
            <div class="sel-display" :class="{ active: !!selectedNode }">
              <template v-if="selectedNode">
                <span class="sel-text">{{ selectedNode.code }} {{ selectedNode.name }}</span>
              </template>
              <span v-else class="sel-placeholder">请选择科目</span>
            </div>
            <el-button size="small" :disabled="!hasNext" @click="next" class="nav-btn">▶</el-button>
          </div>
          <!-- 表格上方选项行 -->
          <div class="table-options">
            <el-checkbox v-model="showDetailName" size="small">显示明细科目名称</el-checkbox>
            <el-checkbox v-model="showMethod" size="small" style="margin-left:12px">显示方式</el-checkbox>
            <el-select v-model="qtyAmtMode" size="small" style="width:110px;margin-left:12px">
              <el-option label="数量金额" value="数量金额" />
              <el-option label="仅数量" value="仅数量" />
              <el-option label="仅金额" value="仅金额" />
              <el-option label="原币本位" value="原币本位" />
            </el-select>
          </div>
        </div>

        <!-- 数据表格 -->
        <div class="table-area">
          <el-table v-if="selectedNode && tableData.length > 0" :data="tableData" v-loading="loading"
            border stripe size="small"
            :header-cell-style="{ background:'#f5f7fa', color:'#303133', fontWeight:600, fontSize:'13px' }"
            style="width:100%" max-height="calc(100vh - 260px)">
            <el-table-column prop="date" label="日期" width="95" align="center" sortable />
            <el-table-column label="凭证号" width="90" align="center">
              <template #default="{ row }">
                <span v-if="row.voucherWord">{{ row.voucherWord }}-{{ String(row.voucherNumber).padStart(3,'0') }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="summary" label="摘要" min-width="120" />

            <!-- 借方：数量/单价/金额 -->
            <el-table-column label="借方" align="center">
              <el-table-column v-if="qtyAmtMode==='数量金额'||qtyAmtMode==='仅数量'" prop="debitQty" label="数量" width="75" align="right">
                <template #default="{ row }"><span class="amt">{{ row.debitQty || '' }}</span></template>
              </el-table-column>
              <el-table-column v-if="qtyAmtMode==='数量金额'||qtyAmtMode==='原币本位'" prop="debitPrice" label="单价" width="85" align="right">
                <template #default="{ row }"><span class="amt">{{ fmt(row.debitPrice) }}</span></template>
              </el-table-column>
              <el-table-column v-if="qtyAmtMode==='数量金额'||qtyAmtMode==='仅金额'||qtyAmtMode==='原币本位'" prop="debitAmount" label="金额" width="105" align="right">
                <template #default="{ row }"><span class="amt debit">{{ fmt(row.debitAmount) }}</span></template>
              </el-table-column>
            </el-table-column>

            <!-- 贷方：数量/单价/金额 -->
            <el-table-column label="贷方" align="center">
              <el-table-column v-if="qtyAmtMode==='数量金额'||qtyAmtMode==='仅数量'" prop="creditQty" label="数量" width="75" align="right">
                <template #default="{ row }"><span class="amt">{{ row.creditQty || '' }}</span></template>
              </el-table-column>
              <el-table-column v-if="qtyAmtMode==='数量金额'||qtyAmtMode==='原币本位'" prop="creditPrice" label="单价" width="85" align="right">
                <template #default="{ row }"><span class="amt">{{ fmt(row.creditPrice) }}</span></template>
              </el-table-column>
              <el-table-column v-if="qtyAmtMode==='数量金额'||qtyAmtMode==='仅金额'||qtyAmtMode==='原币本位'" prop="creditAmount" label="金额" width="105" align="right">
                <template #default="{ row }"><span class="amt credit">{{ fmt(row.creditAmount) }}</span></template>
              </el-table-column>
            </el-table-column>

            <!-- 余额：方向/数量/单价/余额 -->
            <el-table-column label="余额" align="center">
              <el-table-column label="方向" width="60" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.direction==='借'?'':'success'" size="small" effect="plain">{{ row.direction }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column v-if="qtyAmtMode==='数量金额'||qtyAmtMode==='仅数量'" prop="balanceQty" label="数量" width="75" align="right">
                <template #default="{ row }"><span class="amt bal">{{ row.balanceQty || '' }}</span></template>
              </el-table-column>
              <el-table-column v-if="qtyAmtMode==='数量金额'||qtyAmtMode==='原币本位'" prop="balancePrice" label="单价" width="85" align="right">
                <template #default="{ row }"><span class="amt">{{ fmt(row.balancePrice) }}</span></template>
              </el-table-column>
              <el-table-column v-if="qtyAmtMode==='数量金额'||qtyAmtMode==='仅金额'||qtyAmtMode==='原币本位'" prop="balanceAmount" label="余额" width="105" align="right">
                <template #default="{ row }"><span class="amt bal">{{ fmt(row.balanceAmount) }}</span></template>
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
.qty-fx-detail-page{ display:flex; flex-direction:column; height:100%; background:#f0f2f5; }

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
.selector-bar{ display:flex; align-items:center; gap:8px; }
.nav-btn{ padding:4px 8px; font-size:12px; }
.sel-display{
  flex:1; padding:6px 20px; border-radius:4px;
  text-align:center; font-size:14px; font-weight:500; min-width:180px;
}
.sel-display.active{ background:#409eff; color:#fff; }
.sel-display:not(.active){ background:#f5f7fa; color:#909399; }
.table-options{
  display:flex; align-items:center; flex-wrap:wrap; gap:4px; margin-top:2px; flex-shrink:0;
}

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
</style>
