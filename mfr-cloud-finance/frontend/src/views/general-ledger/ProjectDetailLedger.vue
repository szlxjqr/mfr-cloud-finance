<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

/* ==================== 类型定义 ==================== */

/** 辅助核算类别 */
interface AuxCategory {
  id: string
  name: string           // 类别名称：客户/供应商/部门/员工/专项/存货/其他
}

/** 分录行 */
interface ProjectDetailRow {
  id: string
  date: string
  accountName: string    // 科目名称
  auxItem: string        // 辅助项名称
  voucherWord: string
  voucherNumber: number
  summary: string
  debitAmount: number    // 借方金额
  creditAmount: number   // 贷方金额
  direction: '借' | '贷'
  balanceAmount: number  // 余额
}

/* ==================== 状态 ==================== */

const periodRange = ref(['2026-05', '2026-05'])
const displayMode = ref('')          // 显示方式
const auxItemFilter = ref('全部辅助项')  // 辅助项筛选
const accountFilter = ref('全部科目')    // 科目筛选

const searchKeyword = ref('')
const selectedCategory = ref<AuxCategory | null>(null)

/** 左侧辅助类别列表 */
const categoryList = ref<AuxCategory[]>([])
/** 右侧表格数据 */
const tableData = ref<ProjectDetailRow[]>([])
const loading = ref(false)

/* ==================== Mock 数据 ==================== */
const mockCategories: AuxCategory[] = [
  { id:'c1', name:'客户' },
  { id:'c2', name:'供应商' },
  { id:'c3', name:'部门' },
  { id:'c4', name:'员工' },
  { id:'c5', name:'专项' },
  { id:'c6', name:'存货' },
  { id:'c7', name:'其他' },
]

/** 每个类别下的辅助项和科目 */
const categoryData: Record<string, { items:string[], accounts:string[] }> = {
  'c1': {
    items:['华宇科技','明达集团','星辰电子','博远贸易'],
    accounts:['应收账款','主营业务收入','银行存款']
  },
  'c2': {
    items:['鑫达原料公司','恒通物流','南方钢铁集团','东方化工'],
    accounts:['应付账款','预付账款','原材料','库存商品']
  },
  'c3': {
    items:['销售一部','销售二部','行政部','财务部','研发中心'],
    accounts:['管理费用','销售费用','应付职工薪酬']
  },
  'c4': {
    items:['张三','李四','王五','赵六','钱七','孙八'],
    accounts:['应付职工薪酬','管理费用','其他应收款']
  },
  'c5': {
    items:['研发项目A','营销项目B','技改项目C'],
    accounts:'在建工程 研发费用 管理费用'.split(' ')
  },
  'c6': {
    items:['A系列产品','B系列产品','原材料-钢材','原材料-塑料'],
    accounts:'原材料 库存商品 存货跌价准备 主营业务成本'.split(' ')
  },
  'c7': {
    items:['税金-增值税','税金-所得税','往来-内部借款'],
    accounts:'应交税费 其他应付款 其他应收款'.split(' ')
  },
}

function generateData(cat:AuxCategory): ProjectDetailRow[] {
  const rows: ProjectDetailRow[] = []
  const data=categoryData[cat.id]
  if(!data) return rows

  let bal = Math.floor(Math.random() * 50000) + 1000
  const isDebitBal = Math.random() > 0.35

  // 期初余额行
  rows.push({
    id:`r0`, date:'', accountName:'', auxItem:'',
    voucherWord:'', voucherNumber:0,
    summary:'期初余额',
    debitAmount:0, creditAmount:0,
    direction:isDebitBal?'借':'贷',
    balanceAmount:bal
  })

  const count=Math.floor(Math.random()*10)+5
  const words=['记','收','付','转']
  const summaries=[
    '销售商品','采购入库','费用报销','工资发放',
    '收款结算','付款结算','费用分摊','项目拨款',
    '材料领用','产品完工','资产折旧','税费计提'
  ]

  for(let i=0;i<count;i++){
    const day=Math.floor((i/count)*28)+1
    const date=`${periodRange.value[0]}-${String(day).padStart(2,'0')}`
    const word=words[Math.floor(Math.random()*words.length)]
    const vNum=Math.floor(Math.random()*80)+1
    const summary=summaries[Math.floor(Math.random()*summaries.length)]

    const item=data.items[Math.floor(Math.random()*data.items.length)]
    const acct=data.accounts[Math.floor(Math.random()*data.accounts.length)]
    const isDebit=Math.random()>0.45
    const amt=Math.floor(Math.random()*20000)+100

    if(isDebit) bal+=amt; else bal-=amt

    rows.push({
      id:`r${i+1}`, date,
      accountName:acct, auxItem:item,
      voucherWord:word, voucherNumber:vNum, summary,
      debitAmount:isDebit?amt:0,
      creditAmount:isDebit?0:amt,
      direction:bal>=0?'借':'贷',
      balanceAmount:Math.abs(bal)
    })
  }
  return rows
}

/* ==================== 计算属性 ==================== */
const filteredList=computed(()=>{
  if(!searchKeyword.value.trim()) return categoryList.value
  const kw=searchKeyword.value.trim().toLowerCase()
  return categoryList.value.filter(c=>c.name.toLowerCase().includes(kw))
})

/** 按辅助项/科目过滤后的数据 */
const displayData=computed(()=>{
  let data=tableData.value
  if(auxItemFilter.value!=='全部辅助项'){
    data=data.filter(r=>r.auxItem===auxItemFilter.value)
  }
  if(accountFilter.value!=='全部科目'){
    data=data.filter(r=>r.accountName===accountFilter.value)
  }
  return data
})

const idx=computed(()=>!selectedCategory.value?-1:filteredList.value.findIndex(x=>x.id===selectedCategory.value!.id))
const hasPrev=computed(()=>idx.value>0)
const hasNext=computed(()=>idx.value>=0&&filteredList.value.length-1)

/** 当前类别的辅助项选项 */
const auxItemOptions=computed(()=>{
  if(!selectedCategory.value) return ['全部辅助项']
  const data=categoryData[selectedCategory.value.id]
  return data?['全部辅助项',...data.items]:['全部辅助项']
})

/** 当前类别的科目选项 */
const accountOptions=computed(()=>{
  if(!selectedCategory.value) return ['全部科目']
  const data=categoryData[selectedCategory.value.id]
  return data?['全部科目',...data.accounts]:['全部科目']
})

/* ==================== 方法 ==================== */
function loadList(){ categoryList.value=mockCategories }

function selectCat(cat:AuxCategory){
  selectedCategory.value=cat
  loading.value=true
  setTimeout(()=>{tableData.value=generateData(cat);loading.value=false},150)
}
function prev(){if(hasPrev.value)selectCat(filteredList.value[idx.value-1])}
function next(){if(hasNext.value)selectCat(filteredList.value[idx.value+1])}

function fmt(v:number):string{if(!v)return '';return v.toLocaleString('zh-CN',{minimumFractionDigits:2,maximumFractionDigits:2})}
function refresh(){if(selectedCategory.value)selectCat(selectedCategory.value)}

onMounted(()=>loadList())
</script>

<template>
  <div class="project-detail-page">
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
      <!-- 左侧辅助类别面板 -->
      <div class="left-panel">
        <div class="panel-search">
          <el-input v-model="searchKeyword" size="small" placeholder="请输入要搜索的辅助类别" clearable>
            <template #prefix><span style="color:#c0c4cc;font-size:13px">🔍</span></template>
          </el-input>
        </div>
        <div class="panel-list">
          <div v-if="filteredList.length === 0" class="no-data">暂无数据</div>
          <div
            v-for="cat in filteredList" :key="cat.id"
            class="cat-item"
            :class="{ active: selectedCategory?.id === cat.id }"
            @click="selectCat(cat)"
          >
            {{ cat.name }}
          </div>
        </div>
      </div>

      <!-- 拖拽条 -->
      <div class="resizer"><div class="resizer-handle">◀▶</div></div>

      <!-- 右侧 -->
      <div class="right-panel">
        <!-- 选择器 + 筛选行 -->
        <div class="selector-row">
          <div class="selector-bar">
            <el-button size="small" :disabled="!hasPrev" @click="prev" class="nav-btn">◀</el-button>
            <div class="sel-display" :class="{ active: !!selectedCategory }">
              <template v-if="selectedCategory">
                <span class="sel-text">{{ selectedCategory.name }}</span>
              </template>
              <span v-else class="sel-placeholder">请选择</span>
            </div>
            <el-button size="small" :disabled="!hasNext" @click="next" class="nav-btn">▶</el-button>
          </div>
          <!-- 辅助项 + 科目筛选 -->
          <div class="filter-bar">
            <span class="filter-label">辅助项：</span>
            <el-select v-model="auxItemFilter" size="small" style="width:160px">
              <el-option v-for="opt in auxItemOptions" :key="opt" :label="opt" :value="opt" />
            </el-select>
            <span class="filter-label" style="margin-left:16px">科目：</span>
            <el-select v-model="accountFilter" size="small" style="width:140px">
              <el-option v-for="opt in accountOptions" :key="opt" :label="opt" :value="opt" />
            </el-select>
          </div>
        </div>

        <!-- 显示方式行 -->
        <div class="mode-row">
          <span class="mode-label">显示方式：</span>
          <el-select v-model="displayMode" size="small" style="width:170px" placeholder="请选择显示方式" clearable>
            <el-option label="按凭证顺序" value="voucher-order" />
            <el-option label="按辅助项汇总" value="aux-summary" />
            <el-option label="按科目汇总" value="acct-summary" />
            <el-option label="按期间汇总" value="period-summary" />
          </el-select>
        </div>

        <!-- 数据表格 -->
        <div class="table-area">
          <el-table v-if="displayData.length > 0" :data="displayData" v-loading="loading"
            border stripe size="small"
            :header-cell-style="{ background:'#f5f7fa', color:'#303133', fontWeight:600, fontSize:'13px' }"
            style="width:100%" max-height="calc(100vh - 290px)">
            <el-table-column prop="date" label="日期" width="95" align="center" sortable />
            <el-table-column prop="accountName" label="科目名称" min-width="120" />
            <el-table-column prop="auxItem" label="辅助项" min-width="110" />
            <el-table-column label="凭证号" width="90" align="center">
              <template #default="{ row }">
                <span v-if="row.voucherWord">{{ row.voucherWord }}-{{ String(row.voucherNumber).padStart(3,'0') }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="summary" label="摘要" min-width="110" />
            <el-table-column prop="debitAmount" label="借方" width="115" align="right">
              <template #default="{ row }"><span class="amt debit">{{ fmt(row.debitAmount) }}</span></template>
            </el-table-column>
            <el-table-column prop="creditAmount" label="贷方" width="115" align="right">
              <template #default="{ row }"><span class="amt credit">{{ fmt(row.creditAmount) }}</span></template>
            </el-table-column>
            <el-table-column label="方向" width="60" align="center">
              <template #default="{ row }">
                <el-tag :type="row.direction==='借'?'':'success'" size="small" effect="plain">{{ row.direction }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="balanceAmount" label="余额" width="130" align="right">
              <template #default="{ row }"><span class="amt bal">{{ fmt(row.balanceAmount) }}</span></template>
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
.project-detail-page{ display:flex; flex-direction:column; height:100%; background:#f0f2f5; }

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
.cat-item{
  padding:10px 16px; cursor:pointer; font-size:14px; color:#303133;
  transition:background .15s; border-radius:4px; margin:2px 8px;
}
.cat-item:hover{ background:#f5f7fa; }
.cat-item.active{
  background:#409eff; color:#fff; font-weight:500;
}

.resizer{ width:6px; background:#e4e7ed; cursor:col-resize; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.resizer-handle{ font-size:10px; color:#c0c4cc; writing-mode:vertical-rl; letter-spacing:2px; }

.right-panel{ flex:1; display:flex; flex-direction:column; overflow:hidden; background:#fff; }
.selector-row{
  display:flex; align-items:center; justify-content:space-between;
  padding:10px 16px; border-bottom:1px solid #e4e7ed; gap:12px; flex-wrap:wrap;
}
.selector-bar{ display:flex; align-items:center; gap:8px; }
.nav-btn{ padding:4px 8px; font-size:12px; }
.sel-display{
  padding:6px 28px; border-radius:4px;
  text-align:center; font-size:14px; font-weight:500; min-width:100px;
}
.sel-display.active{ background:#409eff; color:#fff; }
.sel-display:not(.active){ background:#f5f7fa; color:#909399; }
.filter-bar{
  display:flex; align-items:center; gap:4px; flex-wrap:wrap; flex-shrink:0;
}
.filter-label{ font-size:13px; color:#606266; white-space:nowrap; }

.mode-row{
  display:flex; align-items:center; padding:6px 16px;
  border-bottom:1px solid #ebeef5; gap:8px;
}
.mode-label{ font-size:13px; color:#606266; white-space:nowrap; }

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
