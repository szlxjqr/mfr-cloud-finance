<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

/* ==================== 类型定义 ==================== */

/** 辅助核算项目 */
interface AuxItem {
  id: string
  code: string       // 辅助核算编码
  name: string       // 辅助核算名称（如客户/供应商/部门/人员）
}

/** 分录行 */
interface AuxDetailRow {
  id: string
  auxCode: string    // 辅助核算编码
  auxName: string    // 辅助核算名称
  date: string       // 日期
  voucherWord: string
  voucherNumber: number
  summary: string
  debitQty: number   // 借方数量
  debitPrice: number // 借方单价
  debitAmount: number// 借方金额
  creditQty: number  // 贷方数量
  creditPrice: number// 贷方单价
  creditAmount: number // 贷方金额
  direction: '借' | '贷'
  balanceQty: number  // 余额数量
  balancePrice: number // 余额单价
  balanceAmount: number // 余额金额
}

/* ==================== 状态 ==================== */

const period = ref('2026-05')
const showSealed = ref(false)     // 显示封存科目
const currency = ref('本币')      // 本币 / 外币

const searchKeyword = ref('')
const selectedAuxItem = ref<AuxItem | null>(null)

/** 左侧辅助核算列表 */
const auxList = ref<AuxItem[]>([])
/** 右侧表格数据 */
const tableData = ref<AuxDetailRow[]>([])
const loading = ref(false)

/* ==================== Mock 数据 ==================== */
const mockAuxItems: AuxItem[] = [
  { id:'x1', code:'C001', name:'华宇科技' },
  { id:'x2', code:'C002', name:'明达集团' },
  { id:'x3', code:'S001', name:'鑫达原料公司' },
  { id:'x4', code:'S002', name:'恒通物流' },
  { id:'x5', code:'D001', name:'销售一部' },
  { id:'x6', code:'D002', name:'销售二部' },
  { id:'x7', code:'D003', name:'行政部' },
  { id:'x8', code:'D004', name:'财务部' },
  { id:'x9', code:'P001', name:'张三' },
  { id:'x10', code:'P002', name:'李四' },
  { id:'x11', code:'P003', name:'王五' },
  { id:'x12', code:'P004', name:'赵六' }
]

function generateData(item: AuxItem): AuxDetailRow[] {
  const rows: AuxDetailRow[] = []
  let balQty = Math.floor(Math.random() * 1000) + 50
  const unitPrice = Math.floor(Math.random() * 500) + 10

  // 期初余额行
  rows.push({
    id:`r0`, auxCode:item.code, auxName:item.name,
    date:'', voucherWord:'', voucherNumber:0,
    summary:'期初余额',
    debitQty:0, debitPrice:0, debitAmount:0,
    creditQty:0, creditPrice:0, creditAmount:0,
    direction:'借',
    balanceQty:balQty, balancePrice:unitPrice, balanceAmount:balQty*unitPrice
  })

  const count = Math.floor(Math.random() * 6) + 3
  const words=['记','收','付','转']
  const summaries=[
    '采购入库','销售出库','材料领用','产品完工',
    '调拨转入','调拨转出','盘盈','盘亏','报废处理'
  ]

  for (let i=0; i<count; i++) {
    const day=Math.floor((i/count)*28)+1
    const date=`${period.value}-${String(day).padStart(2,'0')}`
    const word=words[Math.floor(Math.random()*words.length)]
    const vNum=Math.floor(Math.random()*40)+1
    const summary=summaries[Math.floor(Math.random()*summaries.length)]
    const isDebit=Math.random()>0.45
    const qty=Math.floor(Math.random()*200)+5

    if (isDebit) balQty+=qty; else balQty-=qty

    rows.push({
      id:`r${i+1}`, auxCode:item.code, auxName:item.name,
      date, voucherWord:word, voucherNumber:vNum, summary,
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
const filteredAuxList = computed(() => {
  if (!searchKeyword.value.trim()) return auxList.value
  const kw=searchKeyword.value.trim().toLowerCase()
  return auxList.value.filter(x=>x.code.includes(kw)||x.name.toLowerCase().includes(kw))
})

const idx=computed(()=>!selectedAuxItem.value?-1:auxList.value.findIndex(x=>x.id===selectedAuxItem.value!.id))
const hasPrev=computed(()=>idx.value>0)
const hasNext=computed(()=>idx.value>=0&&idx.value<auxList.value.length-1)

/* ==================== 方法 ==================== */
function loadAuxList(){ auxList.value=mockAuxItems }

function selectItem(item:AuxItem){
  selectedAuxItem.value=item
  loading.value=true
  setTimeout(()=>{tableData.value=generateData(item);loading.value=false},150)
}
function prev(){if(hasPrev.value)selectItem(auxList.value[idx.value-1])}
function next(){if(hasNext.value)selectItem(auxList.value[idx.value+1])}
function clearSelection(){selectedAuxItem.value=null;tableData.value=[]}

function fmt(v:number):string{if(!v)return '';return v.toLocaleString('zh-CN',{minimumFractionDigits:2,maximumFractionDigits:2})}
function refresh(){if(selectedAuxItem.value)selectItem(selectedAuxItem.value)}

onMounted(()=>loadAuxList())
</script>

<template>
  <div class="aux-detail-page">
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
        <el-checkbox v-model="showSealed" size="small">显示封存科目</el-checkbox>
        <el-button size="small" style="margin-left:12px">打印</el-button>
        <el-button size="small">导出</el-button>
      </div>
    </div>

    <!-- ===== 主体区域 ===== -->
    <div class="main-content">
      <!-- 左侧辅助核算面板 -->
      <div class="left-panel">
        <div class="panel-search">
          <el-input v-model="searchKeyword" size="small" placeholder="请输入要搜索的科目" clearable>
            <template #prefix><span style="color:#c0c4cc;font-size:13px">🔍</span></template>
          </el-input>
        </div>
        <div class="panel-list">
          <div v-if="filteredAuxList.length === 0" class="no-data">暂无数据</div>
          <div
            v-for="item in filteredAuxList" :key="item.id"
            class="aux-item"
            :class="{ active: selectedAuxItem?.id === item.id }"
            @click="selectItem(item)"
          >
            <span class="aux-code">{{ item.code }}</span>
            <span class="aux-name">{{ item.name }}</span>
          </div>
        </div>
      </div>

      <!-- 拖拽条 -->
      <div class="resizer"><div class="resizer-handle">◀▶</div></div>

      <!-- 右侧 -->
      <div class="right-panel">
        <!-- 选择器 + 币别 -->
        <div class="selector-row">
          <div class="selector-bar">
            <el-button size="small" :disabled="!hasPrev" @click="prev" class="nav-btn">◀</el-button>
            <div class="sel-display" :class="{ active: !!selectedAuxItem }">
              <template v-if="selectedAuxItem">
                <span class="sel-text">{{ selectedAuxItem.code }} {{ selectedAuxItem.name }}</span>
                <span class="close-btn" @click.stop="clearSelection">✕</span>
              </template>
              <span v-else class="sel-placeholder">请选择科目</span>
            </div>
            <el-button size="small" :disabled="!hasNext" @click="next" class="nav-btn">▶</el-button>
          </div>
          <div class="currency-select">
            <el-select v-model="currency" size="small" style="width:110px">
              <el-option label="本币" value="本币" />
              <el-option label="USD" value="USD" />
              <el-option label="EUR" value="EUR" />
            </el-select>
          </div>
        </div>

        <!-- 数据表格 -->
        <div class="table-area">
          <el-table v-if="selectedAuxItem && tableData.length > 0" :data="tableData" v-loading="loading"
            border stripe size="small"
            :header-cell-style="{ background:'#f5f7fa', color:'#303133', fontWeight:600, fontSize:'13px' }"
            style="width:100%" max-height="calc(100vh - 240px)">
            <el-table-column prop="auxCode" label="辅助核算编码" width="120" align="center" fixed />
            <el-table-column prop="auxName" label="辅助核算名称" min-width="140" fixed />

            <el-table-column prop="date" label="日期" width="100" align="center" sortable />
            <el-table-column label="凭证号" width="95" align="center">
              <template #default="{ row }">
                <span v-if="row.voucherWord">{{ row.voucherWord }}-{{ String(row.voucherNumber).padStart(3,'0') }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="summary" label="摘要" min-width="130" />

            <!-- 借方：数量/单价/金额 -->
            <el-table-column label="借方" align="center">
              <el-table-column prop="debitQty" label="数量" width="75" align="right">
                <template #default="{ row }"><span class="amt">{{ row.debitQty || '' }}</span></template>
              </el-table-column>
              <el-table-column prop="debitPrice" label="单价" width="85" align="right">
                <template #default="{ row }"><span class="amt">{{ fmt(row.debitPrice) }}</span></template>
              </el-table-column>
              <el-table-column prop="debitAmount" label="金额" width="110" align="right">
                <template #default="{ row }"><span class="amt debit">{{ fmt(row.debitAmount) }}</span></template>
              </el-table-column>
            </el-table-column>

            <!-- 贷方：数量/单价/金额 -->
            <el-table-column label="贷方" align="center">
              <el-table-column prop="creditQty" label="数量" width="75" align="right">
                <template #default="{ row }"><span class="amt">{{ row.creditQty || '' }}</span></template>
              </el-table-column>
              <el-table-column prop="creditPrice" label="单价" width="85" align="right">
                <template #default="{ row }"><span class="amt">{{ fmt(row.creditPrice) }}</span></template>
              </el-table-column>
              <el-table-column prop="creditAmount" label="金额" width="110" align="right">
                <template #default="{ row }"><span class="amt credit">{{ fmt(row.creditAmount) }}</span></template>
              </el-table-column>
            </el-table-column>

            <!-- 方向 -->
            <el-table-column label="方向" width="60" align="center">
              <template #default="{ row }">
                <el-tag :type="row.direction==='借'?'':'success'" size="small" effect="plain">{{ row.direction }}</el-tag>
              </template>
            </el-table-column>

            <!-- 科目余额：数量/单价/金额 -->
            <el-table-column label="科目余额" align="center">
              <el-table-column prop="balanceQty" label="数量" width="75" align="right">
                <template #default="{ row }"><span class="amt bal">{{ row.balanceQty || '' }}</span></template>
              </el-table-column>
              <el-table-column prop="balancePrice" label="单价" width="85" align="right">
                <template #default="{ row }"><span class="amt">{{ fmt(row.balancePrice) }}</span></template>
              </el-table-column>
              <el-table-column prop="balanceAmount" label="金额" width="110" align="right">
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
.aux-detail-page{ display:flex; flex-direction:column; height:100%; background:#f0f2f5; }

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
.aux-item{
  padding:8px 12px; cursor:pointer; display:flex; align-items:center; gap:8px;
  transition:background .15s; font-size:13px;
}
.aux-item:hover{ background:#f5f7fa; }
.aux-item.active{ background:#ecf5ff; color:#409eff; }
.aux-code{ color:#909399; font-size:12px; min-width:55px; }
.aux-name{ flex:1; color:#303133; }
.aux-item.active .aux-name{ color:#409eff; font-weight:500; }
.aux-item.active .aux-code{ color:#409eff; }

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
  flex:1; padding:6px 16px 6px 36px; border-radius:4px;
  text-align:center; font-size:14px; font-weight:500; position:relative; min-width:180px;
}
.sel-display.active{ background:#409eff; color:#fff; }
.sel-display:not(.active){ background:#f5f7fa; color:#909399; }
.close-btn{
  position:absolute; left:10px; top:50%; transform:translateY(-50%);
  font-size:14px; cursor:pointer; opacity:.6; line-height:1;
}
.close-btn:hover{ opacity:1; }
.currency-select{ display:flex; align-items:center; gap:6px; font-size:13px; color:#606266; white-space:nowrap; flex-shrink:0; }

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
