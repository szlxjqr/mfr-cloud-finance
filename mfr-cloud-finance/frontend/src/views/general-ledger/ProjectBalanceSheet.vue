<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

/* ==================== 类型定义 ==================== */

/** 辅助核算类别 */
interface AuxCategory {
  id: string
  name: string           // 类别名称：客户/供应商/部门/员工/专项/存货/其他
}

/** 余额行 */
interface ProjectBalanceRow {
  id: string
  projectCode: string    // 项目编号
  projectName: string    // 项目名称（辅助项名称）
  // 期初余额
  openDebit: number      // 期初借方
  openCredit: number     // 期初贷方
  // 本期发生额
  curDebit: number       // 本期借方
  curCredit: number      // 本期贷方
  // 本年累计发生额
  ytdDebit: number       // 本年累计借方
  ytdCredit: number      // 本年累计贷方
  // 期末余额
  closeDebit: number     // 期末借方
  closeCredit: number    // 期末贷方
}

/* ==================== 状态 ==================== */

const periodRange = ref(['2026-05', '2026-05'])
const showLevelOneOnly = ref(false)   // 只显示一级科目
const hideZeroBalance = ref(false)    // 隐藏余额为0
const hideYtdCumulative = ref(false)  // 隐藏本年累计

const displayMode = ref('')          // 显示方式
const auxItemFilter = ref('全部辅助项')
const accountFilter = ref('全部科目')

const searchKeyword = ref('')
const selectedCategory = ref<AuxCategory | null>(null)

/** 左侧辅助类别列表 */
const categoryList = ref<AuxCategory[]>([])
/** 右侧表格数据 */
const tableData = ref<ProjectBalanceRow[]>([])
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

const categoryData: Record<string, { projects:{code:string,name:string}[], accounts:string[] }> = {
  'c1': {
    projects:[
      {code:'KM001',name:'华宇科技'},{code:'KM002',name:'明达集团'},
      {code:'KM003',name:'星辰电子'},{code:'KM004',name:'博远贸易'}
    ],
    accounts:['应收账款','主营业务收入','银行存款']
  },
  'c2': {
    projects:[
      {code:'GY001',name:'鑫达原料公司'},{code:'GY002',name:'恒通物流'},
      {code:'GY003',name:'南方钢铁集团'},{code:'GY004',name:'东方化工'}
    ],
    accounts:['应付账款','预付账款','原材料','库存商品']
  },
  'c3': {
    projects:[
      {code:'DP001',name:'销售一部'},{code:'DP002',name:'销售二部'},
      {code:'DP003',name:'行政部'},{code:'DP004',name:'财务部'},
      {code:'DP005',name:'研发中心'}
    ],
    accounts:['管理费用','销售费用','应付职工薪酬']
  },
  'c4': {
    projects:[
      {code:'EP001',name:'张三'},{code:'EP002',name:'李四'},
      {code:'EP003',name:'王五'},{code:'EP004',name:'赵六'},
      {code:'EP005',name:'钱七'},{code:'EP006',name:'孙八'}
    ],
    accounts:['应付职工薪酬','管理费用','其他应收款']
  },
  'c5': {
    projects:[
      {code:'PJ001',name:'研发项目A'},{code:'PJ002',name:'营销项目B'},
      {code:'PJ003',name:'技改项目C'}
    ],
    accounts:['在建工程','研发费用','管理费用']
  },
  'c6': {
    projects:[
      {code:'IV001',name:'A系列产品'},{code:'IV002',name:'B系列产品'},
      {code:'IV003',name:'原材料-钢材'},{code:'IV004',name:'原材料-塑料'}
    ],
    accounts:['原材料','库存商品','存货跌价准备','主营业务成本']
  },
  'c7': {
    projects:[
      {code:'OT001',name:'税金-增值税'},{code:'OT002',name:'税金-所得税'},
      {code:'OT003',name:'往来-内部借款'}
    ],
    accounts:['应交税费','其他应付款','其他应收款']
  },
}

function generateData(cat:AuxCategory): ProjectBalanceRow[] {
  const rows:ProjectBalanceRow[]=[]
  const data=categoryData[cat.id]
  if(!data) return rows

  for(let i=0;i<data.projects.length;i++){
    const proj=data.projects[i]
    let bal=Math.floor(Math.random()*80000)+5000
    const isDebitBal=Math.random()>0.35

    const openD=isDebitBal?bal:0
    const openC=isDebitBal?0:bal

    const cDebit=Math.floor(Math.random()*30000)+1000
    const cCredit=Math.floor(Math.random()*25000)+500
    bal+=cDebit-cCredit

    const ytdD=cDebit+Math.floor(Math.random()*100000)
    const ytdC=cCredit+Math.floor(Math.random()*90000)

    const closeDebit=bal>=0?bal:0
    const closeCredit=bal<0?Math.abs(bal):0

    rows.push({
      id:`b${i}`, projectCode:proj.code, projectName:proj.name,
      openDebit:openD, openCredit:openC,
      curDebit:cDebit, curCredit:cCredit,
      ytdDebit:ytdD, ytdCredit:ytdC,
      closeDebit, closeCredit
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
    data=data.filter(r=>r.projectName===auxItemFilter.value)
  }
  if(hideZeroBalance.value){
    data=data.filter(r=>r.closeDebit!==0||r.closeCredit!==0)
  }
  return data
})

const idx=computed(()=>!selectedCategory.value?-1:filteredList.value.findIndex(x=>x.id===selectedCategory.value!.id))
const hasPrev=computed(()=>idx.value>0)
const hasNext=computed(()=>idx.value>=0&&filteredList.value.length-1)

const auxItemOptions=computed(()=>{
  if(!selectedCategory.value) return ['全部辅助项']
  const data=categoryData[selectedCategory.value.id]
  return data?['全部辅助项',...data.projects.map(p=>p.name)]:['全部辅助项']
})
const accountOptions=computed(()=>{
  if(!selectedCategory.value) return ['全部科目']
  const data=categoryData[selectedCategory.value.id]
  return data?['全部科目',...data.accounts]:['全部科目']
})

/* 合计行 */
const totals=computed(()=>{
  const data=displayData.value
  if(data.length===0) return null
  return data.reduce((acc,r)=>({
    openDebit:acc.openDebit+r.openDebit, openCredit:acc.openCredit+r.openCredit,
    curDebit:acc.curDebit+r.curDebit, curCredit:acc.curCredit+r.curCredit,
    ytdDebit:acc.ytdDebit+r.ytdDebit, ytdCredit:acc.ytdCredit+r.ytdCredit,
    closeDebit:acc.closeDebit+r.closeDebit, closeCredit:acc.closeCredit+r.closeCredit
  }),{openDebit:0,openCredit:0,curDebit:0,curCredit:0,ytdDebit:0,ytdCredit:0,closeDebit:0,closeCredit:0})
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
  <div class="project-balance-page">
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
        <el-checkbox v-model="showLevelOneOnly" size="small">只显示一级科目</el-checkbox>
        <el-checkbox v-model="hideZeroBalance" size="small">隐藏余额为0</el-checkbox>
        <el-checkbox v-model="hideYtdCumulative" size="small">隐藏本年累计</el-checkbox>
        <el-button size="small" style="margin-left:12px">打印</el-button>
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
            <el-button size="small" :disabled="!hasPrev" @click="prev" class="nav-btn">◀</el-button>
            <div class="sel-display" :class="{ active: !!selectedCategory }">
              <template v-if="selectedCategory">
                <span class="sel-text">{{ selectedCategory.name }}</span>
              </template>
              <span v-else class="sel-placeholder">请选择</span>
            </div>
            <el-button size="small" :disabled="!hasNext" @click="next" class="nav-btn">▶</el-button>
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
          <!-- 显示方式 -->
          <div class="mode-area">
            <span class="mode-label">显示方式：</span>
            <el-select v-model="displayMode" size="small" style="width:130px" placeholder="请选择" clearable>
              <el-option label="按项目汇总" value="project-summary" />
              <el-option label="按科目汇总" value="acct-summary" />
              <el-option label="按期间汇总" value="period-summary" />
            </el-select>
          </div>
        </div>

        <!-- 数据表格 -->
        <div class="table-area">
          <el-table v-if="displayData.length > 0" :data="displayData" v-loading="loading"
            border stripe size="small" show-summary :summary-method="()=>totals?[totals]:[]"
            :header-cell-style="{ background:'#f5f7fa', color:'#303133', fontWeight:600, fontSize:'13px' }"
            style="width:100%" max-height="calc(100vh - 260px)">
            <el-table-column prop="projectCode" label="项目编号" width="110" align="center" fixed />
            <el-table-column prop="projectName" label="项目名称" min-width="130" fixed />

            <!-- 期初余额 -->
            <el-table-column label="期初余额" align="center">
              <el-table-column prop="openDebit" label="借方" width="105" align="right">
                <template #default="{ row }"><span class="amt debit">{{ fmt(row.openDebit) }}</span></template>
              </el-table-column>
              <el-table-column prop="openCredit" label="贷方" width="105" align="right">
                <template #default="{ row }"><span class="amt credit">{{ fmt(row.openCredit) }}</span></template>
              </el-table-column>
            </el-table-column>

            <!-- 本期发生额 -->
            <el-table-column label="本期发生额" align="center">
              <el-table-column prop="curDebit" label="借方" width="105" align="right">
                <template #default="{ row }"><span class="amt debit">{{ fmt(row.curDebit) }}</span></template>
              </el-table-column>
              <el-table-column prop="curCredit" label="贷方" width="105" align="right">
                <template #default="{ row }"><span class="amt credit">{{ fmt(row.curCredit) }}</span></template>
              </el-table-column>
            </el-table-column>

            <!-- 本年累计发生额（可隐藏） -->
            <el-table-column v-if="!hideYtdCumulative" label="本年累计发生额" align="center">
              <el-table-column prop="ytdDebit" label="借方" width="110" align="right">
                <template #default="{ row }"><span class="amt debit">{{ fmt(row.ytdDebit) }}</span></template>
              </el-table-column>
              <el-table-column prop="ytdCredit" label="贷方" width="110" align="right">
                <template #default="{ row }"><span class="amt credit">{{ fmt(row.ytdCredit) }}</span></template>
              </el-table-column>
            </el-table-column>

            <!-- 期末余额 -->
            <el-table-column label="期末余额" align="center">
              <el-table-column prop="closeDebit" label="借方" width="105" align="right">
                <template #default="{ row }"><span class="amt bal">{{ fmt(row.closeDebit) }}</span></template>
              </el-table-column>
              <el-table-column prop="closeCredit" label="贷方" width="105" align="right">
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
.project-balance-page{ display:flex; flex-direction:column; height:100%; background:#f0f2f5; }

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
  display:flex; align-items:flex-start; justify-content:space-between;
  padding:10px 16px; border-bottom:1px solid #e4e7ed; gap:12px; flex-wrap:wrap;
}
.selector-bar{ display:flex; align-items:center; gap:4px; }
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
.mode-area{
  display:flex; align-items:center; gap:4px; margin-top:2px; flex-shrink:0;
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
:deep(.el-table__footer-wrapper){ font-weight:600; background:#fafafa; }
</style>
