<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

/* ==================== 类型定义 ==================== */

/** 科目树节点 */
interface AccountNode {
  id: string
  code: string
  name: string
  level: number
  parentCode: string
  children: AccountNode[]
  hasChildren: boolean
}

/** 总账分录行 */
interface GeneralLedgerEntry {
  id: string
  period: string
  summary: string
  openingDebit: number
  openingCredit: number
  periodDebit: number
  periodCredit: number
  endingDebit: number
  endingCredit: number
  direction: '借' | '贷'
  balance: number
}

/* ==================== 状态 ==================== */

/** 会计期间 */
const period = ref('2026-05')

/** 科目搜索关键词 */
const searchKeyword = ref('')

/** 只显示一级科目 */
const showLevel1Only = ref(false)

/** 不显示无发生额且余额为0 */
const hideZeroBalance = ref(true)

/** 当前选中的科目 */
const selectedAccount = ref<AccountNode | null>(null)

/** 科目树数据 */
const accountTree = ref<AccountNode[]>([])

/** 右侧表格数据 */
const tableData = ref<GeneralLedgerEntry[]>([])

/** 加载状态 */
const loading = ref(false)

/* ==================== 科目树数据 ==================== */

const mockAccountTree: AccountNode[] = [
  { id: 'a1', code: '1001', name: '库存现金', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a2', code: '1002', name: '银行存款', level: 1, parentCode: '', hasChildren: true, children: [
    { id: 'a2-1', code: '1002-01', name: '基本户(工行)', level: 2, parentCode: '1002', hasChildren: false, children: [] },
    { id: 'a2-2', code: '1002-02', name: '一般户(建行)', level: 2, parentCode: '1002', hasChildren: false, children: [] }
  ]},
  { id: 'a3', code: '1012', name: '其他货币资金', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a4', code: '1101', name: '短期投资', level: 1, parentCode: '', hasChildren: true, children: [
    { id: 'a4-1', code: '1101-01', name: '股票', level: 2, parentCode: '1101', hasChildren: false, children: [] },
    { id: 'a4-2', code: '1101-02', name: '债券', level: 2, parentCode: '1101', hasChildren: false, children: [] }
  ]},
  { id: 'a5', code: '1121', name: '应收票据', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a6', code: '1122', name: '应收账款', level: 1, parentCode: '', hasChildren: true, children: [
    { id: 'a6-1', code: '1122-01', name: '华宇科技', level: 2, parentCode: '1122', hasChildren: false, children: [] },
    { id: 'a6-2', code: '1122-02', name: '明达集团', level: 2, parentCode: '1122', hasChildren: false, children: [] }
  ]},
  { id: 'a7', code: '1123', name: '预付账款', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a8', code: '1131', name: '应收股利', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a9', code: '1132', name: '应收利息', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a10', code: '1221', name: '其他应收款', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a11', code: '1401', name: '材料采购', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a12', code: '1402', name: '在途物资', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a13', code: '1403', name: '原材料', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a14', code: '1404', name: '材料成本差异', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a15', code: '1405', name: '库存商品', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a16', code: '1407', name: '商品进销差价', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a17', code: '1408', name: '委托加工物资', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a18', code: '1411', name: '周转材料', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a19', code: '1421', name: '消耗性生物资产', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a20', code: '1501', name: '长期债券投资', level: 1, parentCode: '', hasChildren: true, children: [
    { id: 'a20-1', code: '1501-01', name: '国债投资', level: 2, parentCode: '1501', hasChildren: false, children: [] },
    { id: 'a20-2', code: '1501-02', name: '企业债券', level: 2, parentCode: '1501', hasChildren: false, children: [] }
  ]},
  { id: 'a21', code: '1511', name: '长期股权投资', level: 1, parentCode: '', hasChildren: true, children: [
    { id: 'a21-1', code: '1511-01', name: '成本法核算', level: 2, parentCode: '1511', hasChildren: false, children: [] },
    { id: 'a21-2', code: '1511-02', name: '权益法核算', level: 2, parentCode: '1511', hasChildren: false, children: [] }
  ]},
  { id: 'a22', code: '1601', name: '固定资产', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a23', code: '1602', name: '累计折旧', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a24', code: '1604', name: '在建工程', level: 1, parentCode: '', hasChildren: true, children: [
    { id: 'a24-1', code: '1604-01', name: '建筑工程', level: 2, parentCode: '1604', hasChildren: false, children: [] },
    { id: 'a24-2', code: '1604-02', name: '安装工程', level: 2, parentCode: '1604', hasChildren: false, children: [] },
    { id: 'a24-3', code: '1604-03', name: '技术改造工程', level: 2, parentCode: '1604', hasChildren: false, children: [] }
  ]},
  { id: 'a25', code: '1605', name: '工程物资', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a26', code: '1606', name: '固定资产清理', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a27', code: '1621', name: '生产性生物资产', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a28', code: '1622', name: '生产性生物资产累计折旧', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a29', code: '1701', name: '无形资产', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a30', code: '1702', name: '累计摊销', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a31', code: '1801', name: '长期待摊费用', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a32', code: '1901', name: '待处理财产损溢', level: 1, parentCode: '', hasChildren: false, children: [] },
  // 负债类
  { id: 'a33', code: '2001', name: '短期借款', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a34', code: '2201', name: '应付票据', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a35', code: '2202', name: '应付账款', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a36', code: '2203', name: '预收账款', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a37', code: '2211', name: '应付职工薪酬', level: 1, parentCode: '', hasChildren: true, children: [
    { id: 'a37-1', code: '2211-01', name: '工资奖金津贴和补贴', level: 2, parentCode: '2211', hasChildren: false, children: [] },
    { id: 'a37-2', code: '2211-02', name: '职工福利费', level: 2, parentCode: '2211', hasChildren: false, children: [] },
    { id: 'a37-3', code: '2211-03', name: '社会保险费', level: 2, parentCode: '2211', hasChildren: false, children: [] },
    { id: 'a37-4', code: '2211-04', name: '住房公积金', level: 2, parentCode: '2211', hasChildren: false, children: [] },
    { id: 'a37-5', code: '2211-05', name: '工会经费和职工教育经费', level: 2, parentCode: '2211', hasChildren: false, children: [] }
  ]},
  { id: 'a38', code: '2221', name: '应交税费', level: 1, parentCode: '', hasChildren: true, children: [
    { id: 'a38-1', code: '2221-01', name: '增值税', level: 2, parentCode: '2221', hasChildren: false, children: [] },
    { id: 'a38-2', code: '2221-02', name: '消费税', level: 2, parentCode: '2221', hasChildren: false, children: [] },
    { id: 'a38-3', code: '2221-03', name: '企业所得税', level: 2, parentCode: '2221', hasChildren: false, children: [] },
    { id: 'a38-4', code: '2221-04', name: '个人所得税', level: 2, parentCode: '2221', hasChildren: false, children: [] },
    { id: 'a38-5', code: '2221-05', name: '城市维护建设税', level: 2, parentCode: '2221', hasChildren: false, children: [] },
    { id: 'a38-6', code: '2221-06', name: '教育费附加', level: 2, parentCode: '2221', hasChildren: false, children: [] },
    { id: 'a38-7', code: '2221-07', name: '印花税', level: 2, parentCode: '2221', hasChildren: false, children: [] },
    { id: 'a38-8', code: '2221-08', name: '房产税', level: 2, parentCode: '2221', hasChildren: false, children: [] }
  ]},
  { id: 'a39', code: '2231', name: '应付利息', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a40', code: '2232', name: '应付利润', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a41', code: '2241', name: '其他应付款', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a42', code: '2401', name: '递延收益', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a43', code: '2501', name: '长期借款', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a44', code: '2701', name: '长期应付款', level: 1, parentCode: '', hasChildren: false, children: [] },
  // 权益类
  { id: 'a45', code: '3001', name: '实收资本', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a46', code: '3002', name: '资本公积', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a47', code: '3101', name: '盈余公积', level: 1, parentCode: '', hasChildren: true, children: [
    { id: 'a47-1', code: '3101-01', name: '法定盈余公积', level: 2, parentCode: '3101', hasChildren: false, children: [] },
    { id: 'a47-2', code: '3101-02', name: '任意盈余公积', level: 2, parentCode: '3101', hasChildren: false, children: [] },
    { id: 'a47-3', code: '3101-03', name: '法定公益金', level: 2, parentCode: '3101', hasChildren: false, children: [] }
  ]},
  { id: 'a48', code: '3103', name: '本年利润', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a49', code: '3104', name: '利润分配', level: 1, parentCode: '', hasChildren: true, children: [
    { id: 'a49-1', code: '3104-01', name: '提取法定盈余公积', level: 2, parentCode: '3104', hasChildren: false, children: [] },
    { id: 'a49-2', code: '3104-02', name: '提取任意盈余公积', level: 2, parentCode: '3104', hasChildren: false, children: [] },
    { id: 'a49-3', code: '3104-03', name: '应付利润', level: 2, parentCode: '3104', hasChildren: false, children: [] },
    { id: 'a49-4', code: '3104-04', name: '未分配利润', level: 2, parentCode: '3104', hasChildren: false, children: [] }
  ]},
  // 成本类
  { id: 'a50', code: '4001', name: '生产成本', level: 1, parentCode: '', hasChildren: true, children: [
    { id: 'a50-1', code: '4001-01', name: '基本生产成本', level: 2, parentCode: '4001', hasChildren: false, children: [] },
    { id: 'a50-2', code: '4001-02', name: '辅助生产成本', level: 2, parentCode: '4001', hasChildren: false, children: [] }
  ]},
  { id: 'a51', code: '4101', name: '制造费用', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a52', code: '4301', name: '研发支出', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a53', code: '4401', name: '工程施工', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a54', code: '4403', name: '机械作业', level: 1, parentCode: '', hasChildren: false, children: [] },
  // 损益类 — 收入
  { id: 'a55', code: '5001', name: '主营业务收入', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a56', code: '5051', name: '其他业务收入', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a57', code: '5111', name: '投资收益', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a58', code: '5301', name: '营业外收入', level: 1, parentCode: '', hasChildren: true, children: [
    { id: 'a58-1', code: '5301-01', name: '非流动资产处置利得', level: 2, parentCode: '5301', hasChildren: false, children: [] },
    { id: 'a58-2', code: '5301-02', name: '政府补助', level: 2, parentCode: '5301', hasChildren: false, children: [] },
    { id: 'a58-3', code: '5301-03', name: '盘盈利得', level: 2, parentCode: '5301', hasChildren: false, children: [] },
    { id: 'a58-4', code: '5301-04', name: '捐赠利得', level: 2, parentCode: '5301', hasChildren: false, children: [] },
    { id: 'a58-5', code: '5301-05', name: '罚没收入', level: 2, parentCode: '5301', hasChildren: false, children: [] }
  ]},
  // 损益类 — 成本费用
  { id: 'a59', code: '5401', name: '主营业务成本', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a60', code: '5402', name: '其他业务成本', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a61', code: '5403', name: '营业税金及附加', level: 1, parentCode: '', hasChildren: false, children: [] },
  { id: 'a62', code: '5601', name: '销售费用', level: 1, parentCode: '', hasChildren: true, children: [
    { id: 'a62-1', code: '5601-01', name: '销售人员工资', level: 2, parentCode: '5601', hasChildren: false, children: [] },
    { id: 'a62-2', code: '5601-02', name: '广告宣传费', level: 2, parentCode: '5601', hasChildren: false, children: [] },
    { id: 'a62-3', code: '5601-03', name: '运输费', level: 2, parentCode: '5601', hasChildren: false, children: [] },
    { id: 'a62-4', code: '5601-04', name: '包装费', level: 2, parentCode: '5601', hasChildren: false, children: [] },
    { id: 'a62-5', code: '5601-05', name: '业务招待费', level: 2, parentCode: '5601', hasChildren: false, children: [] }
  ]},
  { id: 'a63', code: '5602', name: '管理费用', level: 1, parentCode: '', hasChildren: true, children: [
    { id: 'a63-1', code: '5602-01', name: '管理人员工资', level: 2, parentCode: '5602', hasChildren: false, children: [] },
    { id: 'a63-2', code: '5602-02', name: '办公费', level: 2, parentCode: '5602', hasChildren: false, children: [] },
    { id: 'a63-3', code: '5602-03', name: '差旅费', level: 2, parentCode: '5602', hasChildren: false, children: [] },
    { id: 'a63-4', code: '5602-04', name: '折旧费', level: 2, parentCode: '5602', hasChildren: false, children: [] },
    { id: 'a63-5', code: '5602-05', name: '水电费', level: 2, parentCode: '5602', hasChildren: false, children: [] },
    { id: 'a63-6', code: '5602-06', name: '业务招待费', level: 2, parentCode: '5602', hasChildren: false, children: [] },
    { id: 'a63-7', code: '5602-07', name: '租赁费', level: 2, parentCode: '5602', hasChildren: false, children: [] },
    { id: 'a63-8', code: '5602-08', name: '其他管理费用', level: 2, parentCode: '5602', hasChildren: false, children: [] }
  ]},
  { id: 'a64', code: '5603', name: '财务费用', level: 1, parentCode: '', hasChildren: true, children: [
    { id: 'a64-1', code: '5603-01', name: '利息支出', level: 2, parentCode: '5603', hasChildren: false, children: [] },
    { id: 'a64-2', code: '5603-02', name: '利息收入', level: 2, parentCode: '5603', hasChildren: false, children: [] },
    { id: 'a64-3', code: '5603-03', name: '汇兑损益', level: 2, parentCode: '5603', hasChildren: false, children: [] },
    { id: 'a64-4', code: '5603-04', name: '手续费及佣金', level: 2, parentCode: '5603', hasChildren: false, children: [] }
  ]},
  { id: 'a65', code: '5711', name: '营业外支出', level: 1, parentCode: '', hasChildren: true, children: [
    { id: 'a65-1', code: '5711-01', name: '非流动资产处置损失', level: 2, parentCode: '5711', hasChildren: false, children: [] },
    { id: 'a65-2', code: '5711-02', name: '盘亏损失', level: 2, parentCode: '5711', hasChildren: false, children: [] },
    { id: 'a65-3', code: '5711-03', name: '捐赠支出', level: 2, parentCode: '5711', hasChildren: false, children: [] },
    { id: 'a65-4', code: '5711-04', name: '罚款支出', level: 2, parentCode: '5711', hasChildren: false, children: [] },
    { id: 'a65-5', code: '5711-05', name: '非常损失', level: 2, parentCode: '5711', hasChildren: false, children: [] }
  ]},
  { id: 'a66', code: '5801', name: '所得税费用', level: 1, parentCode: '', hasChildren: false, children: [] }
]

/* ==================== 计算属性 ==================== */

/** 筛选后的科目列表 */
const filteredAccounts = computed(() => {
  let data = accountTree.value

  // 只显示一级科目
  if (showLevel1Only.value) {
    data = data.filter(a => a.level === 1)
  }

  // 关键词搜索
  if (searchKeyword.value.trim()) {
    const kw = searchKeyword.value.trim().toLowerCase()
    data = data.filter(a =>
      a.code.toLowerCase().includes(kw) ||
      a.name.toLowerCase().includes(kw)
    )
  }

  return data
})

/** 扁平化的科目列表（用于上一个/下一个导航） */
const flatAccountList = computed(() => {
  const result: AccountNode[] = []
  const flatten = (nodes: AccountNode[]) => {
    nodes.forEach(n => {
      if (!showLevel1Only.value || n.level === 1) {
        result.push(n)
      }
      if (n.hasChildren && n.children.length > 0) {
        flatten(n.children)
      }
    })
  }
  flatten(accountTree.value)
  return result
})

/** 当前选中科目的索引 */
const currentIndex = computed(() => {
  if (!selectedAccount.value) return -1
  return flatAccountList.value.findIndex(a => a.id === selectedAccount.value!.id)
})

/** 是否有上一个科目 */
const hasPrev = computed(() => currentIndex.value > 0)

/** 是否有下一个科目 */
const hasNext = computed(() => currentIndex.value >= 0 && currentIndex.value < flatAccountList.value.length - 1)

/* ==================== 方法 ==================== */

/** 加载科目树 */
function loadAccountTree() {
  accountTree.value = mockAccountTree
}

/** 生成选中科目的总账数据 */
function generateLedgerData(account: AccountNode): GeneralLedgerEntry[] {
  const entries: GeneralLedgerEntry[] = []

  // 期初余额行
  const openingBalance = Math.floor(Math.random() * 500000) + 10000
  const isDebit = !account.code.startsWith('2') && !account.code.startsWith('3') && !account.code.startsWith('4')

  entries.push({
    id: 'e0',
    period: period.value,
    summary: '期初余额',
    openingDebit: isDebit ? openingBalance : 0,
    openingCredit: isDebit ? 0 : openingBalance,
    periodDebit: 0,
    periodCredit: 0,
    endingDebit: isDebit ? openingBalance : 0,
    endingCredit: isDebit ? 0 : openingBalance,
    direction: isDebit ? '借' : '贷',
    balance: openingBalance
  })

  // 本期发生额行
  const count = Math.floor(Math.random() * 6) + 3
  let balance = openingBalance
  let totalDebit = 0
  let totalCredit = 0

  const summaries = [
    '采购原材料', '支付货款', '收到销售款', '支付工资',
    '报销差旅费', '缴纳税费', '计提折旧', '销售商品确认收入',
    '支付水电费', '结转销售成本', '银行利息收入', '归还借款',
    '购买办公用品', '支付租金', '收到投资款', '结转本月损益'
  ]

  for (let i = 0; i < count; i++) {
    const isDebitEntry = Math.random() > 0.45
    const amount = Math.floor(Math.random() * 200000) + 2000

    if (isDebitEntry) {
      totalDebit += amount
      balance = isDebit ? balance + amount : balance - amount
    } else {
      totalCredit += amount
      balance = isDebit ? balance - amount : balance + amount
    }

    entries.push({
      id: `e${i + 1}`,
      period: period.value,
      summary: summaries[Math.floor(Math.random() * summaries.length)],
      openingDebit: 0,
      openingCredit: 0,
      periodDebit: isDebitEntry ? amount : 0,
      periodCredit: isDebitEntry ? 0 : amount,
      endingDebit: 0,
      endingCredit: 0,
      direction: balance >= 0 ? (isDebit ? '借' : '贷') : (isDebit ? '贷' : '借'),
      balance: Math.abs(balance)
    })
  }

  // 本期合计行
  entries.push({
    id: 'e-sum',
    period: period.value,
    summary: '本期合计',
    openingDebit: 0,
    openingCredit: 0,
    periodDebit: totalDebit,
    periodCredit: totalCredit,
    endingDebit: 0,
    endingCredit: 0,
    direction: balance >= 0 ? (isDebit ? '借' : '贷') : (isDebit ? '贷' : '借'),
    balance: Math.abs(balance)
  })

  // 本年累计行
  const cumDebit = totalDebit + Math.floor(Math.random() * 500000)
  const cumCredit = totalCredit + Math.floor(Math.random() * 500000)
  entries.push({
    id: 'e-cum',
    period: period.value,
    summary: '本年累计',
    openingDebit: 0,
    openingCredit: 0,
    periodDebit: cumDebit,
    periodCredit: cumCredit,
    endingDebit: 0,
    endingCredit: 0,
    direction: balance >= 0 ? (isDebit ? '借' : '贷') : (isDebit ? '贷' : '借'),
    balance: Math.abs(balance)
  })

  return entries
}

/** 选择科目 */
function selectAccount(account: AccountNode) {
  selectedAccount.value = account
  loading.value = true
  setTimeout(() => {
    tableData.value = generateLedgerData(account)
    loading.value = false
  }, 200)
}

/** 上一个科目 */
function prevAccount() {
  if (hasPrev.value) {
    selectAccount(flatAccountList.value[currentIndex.value - 1])
  }
}

/** 下一个科目 */
function nextAccount() {
  if (hasNext.value) {
    selectAccount(flatAccountList.value[currentIndex.value + 1])
  }
}

/** 格式化金额 */
function formatAmount(val: number): string {
  if (val === 0) return ''
  return val.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

/** 刷新 */
function refresh() {
  if (selectedAccount.value) {
    selectAccount(selectedAccount.value)
  }
}

/** 打印 */
function printLedger() {
  window.print()
}

/** 导出 */
function exportLedger() {
  // 占位
}

onMounted(() => {
  loadAccountTree()
})
</script>

<template>
  <div class="general-ledger-page">
    <!-- ===== 顶部工具栏 ===== -->
    <div class="top-toolbar">
      <div class="toolbar-left">
        <span class="toolbar-label">期间</span>
        <el-date-picker
          v-model="period"
          type="month"
          format="YYYY年MM期"
          value-format="YYYY-MM"
          size="small"
          style="width: 160px"
          @change="refresh"
        />
        <el-button size="small" type="primary" plain style="margin-left: 8px">
          筛选 ▾
        </el-button>
        <el-button size="small" circle @click="refresh">
          <span style="font-size: 13px">🔄</span>
        </el-button>
      </div>
      <div class="toolbar-right">
        <el-checkbox v-model="showLevel1Only" size="small">
          只显示一级科目
        </el-checkbox>
        <el-checkbox v-model="hideZeroBalance" size="small" style="margin-left: 12px">
          无发生额且余额为0不显示
        </el-checkbox>
        <el-button size="small" style="margin-left: 12px" @click="printLedger">
          打印
        </el-button>
        <el-button size="small" @click="exportLedger">
          导出
        </el-button>
      </div>
    </div>

    <!-- ===== 主体区域：左侧科目树 + 右侧表格 ===== -->
    <div class="main-content">
      <!-- 左侧科目树面板 -->
      <div class="left-panel">
        <div class="panel-search">
          <el-input
            v-model="searchKeyword"
            size="small"
            placeholder="请输入要搜索的科目"
            clearable
          >
            <template #prefix>
              <span style="color: #c0c4cc; font-size: 13px">🔍</span>
            </template>
          </el-input>
        </div>
        <div class="panel-tree">
          <div
            v-for="account in filteredAccounts"
            :key="account.id"
            class="account-item"
            :class="{
              active: selectedAccount?.id === account.id,
              'has-children': account.hasChildren
            }"
            @click="selectAccount(account)"
          >
            <span class="account-code">{{ account.code }}</span>
            <span class="account-name">{{ account.name }}</span>
            <span v-if="account.hasChildren" class="expand-icon">▶</span>
          </div>
        </div>
      </div>

      <!-- 中间拖拽条 -->
      <div class="resizer">
        <div class="resizer-handle">◀▶</div>
      </div>

      <!-- 右侧表格区域 -->
      <div class="right-panel">
        <!-- 科目选择器 -->
        <div class="account-selector">
          <el-button
            size="small"
            :disabled="!hasPrev"
            @click="prevAccount"
            class="nav-btn"
          >
            ◀
          </el-button>
          <div class="selector-display">
            <span v-if="selectedAccount" class="selector-text">
              {{ selectedAccount.code }} {{ selectedAccount.name }}
            </span>
            <span v-else class="selector-placeholder">请选择科目</span>
          </div>
          <el-button
            size="small"
            :disabled="!hasNext"
            @click="nextAccount"
            class="nav-btn"
          >
            ▶
          </el-button>
        </div>

        <!-- 数据表格 -->
        <div class="table-area">
          <el-table
            v-if="selectedAccount"
            :data="tableData"
            v-loading="loading"
            border
            stripe
            size="small"
            :header-cell-style="{ background: '#f5f7fa', color: '#303133', fontWeight: 600, fontSize: '13px' }"
            style="width: 100%"
            max-height="calc(100vh - 240px)"
          >
            <el-table-column prop="period" label="期间" width="100" align="center" />
            <el-table-column prop="summary" label="摘要" min-width="180" />
            <el-table-column label="借方" width="140" align="right">
              <template #default="{ row }">
                <span class="amount">{{ formatAmount(row.openingDebit || row.periodDebit) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="贷方" width="140" align="right">
              <template #default="{ row }">
                <span class="amount">{{ formatAmount(row.openingCredit || row.periodCredit) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="方向" width="60" align="center">
              <template #default="{ row }">
                <el-tag
                  :type="row.direction === '借' ? '' : 'success'"
                  size="small"
                  effect="plain"
                >
                  {{ row.direction }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="余额" width="140" align="right">
              <template #default="{ row }">
                <span class="amount balance">{{ formatAmount(row.balance) }}</span>
              </template>
            </el-table-column>
          </el-table>

          <!-- 空状态 -->
          <div v-else class="empty-state">
            <el-empty description="暂无数据" :image-size="200">
              <template #image>
                <div style="font-size: 80px; opacity: 0.3">📊</div>
              </template>
            </el-empty>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.general-ledger-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f0f2f5;
}

/* ===== 顶部工具栏 ===== */
.top-toolbar {
  background: #fff;
  padding: 8px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e4e7ed;
  flex-shrink: 0;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar-label {
  font-size: 13px;
  color: #606266;
  white-space: nowrap;
}

/* ===== 主体区域 ===== */
.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* ===== 左侧科目树面板 ===== */
.left-panel {
  width: 220px;
  background: #fff;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.panel-search {
  padding: 12px;
  border-bottom: 1px solid #e4e7ed;
}

.panel-tree {
  flex: 1;
  overflow-y: auto;
  padding: 4px 0;
}

.account-item {
  padding: 8px 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: background 0.15s;
  font-size: 13px;
}

.account-item:hover {
  background: #f5f7fa;
}

.account-item.active {
  background: #ecf5ff;
  color: #409eff;
}

.account-item.active .account-code {
  color: #409eff;
}

.account-code {
  color: #909399;
  font-size: 12px;
  min-width: 50px;
}

.account-name {
  flex: 1;
  color: #303133;
}

.account-item.active .account-name {
  color: #409eff;
  font-weight: 500;
}

.expand-icon {
  font-size: 10px;
  color: #909399;
}

/* ===== 中间拖拽条 ===== */
.resizer {
  width: 6px;
  background: #e4e7ed;
  cursor: col-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.resizer-handle {
  font-size: 10px;
  color: #c0c4cc;
  writing-mode: vertical-rl;
  letter-spacing: 2px;
}

/* ===== 右侧表格区域 ===== */
.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #fff;
}

/* 科目选择器 */
.account-selector {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  border-bottom: 1px solid #e4e7ed;
  gap: 8px;
}

.nav-btn {
  padding: 4px 8px;
  font-size: 12px;
}

.selector-display {
  flex: 1;
  background: #409eff;
  color: #fff;
  padding: 6px 16px;
  border-radius: 4px;
  text-align: center;
  font-size: 14px;
  font-weight: 500;
}

.selector-placeholder {
  opacity: 0.7;
}

/* 表格区域 */
.table-area {
  flex: 1;
  overflow: hidden;
  padding: 0;
}

/* 空状态 */
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

/* 金额样式 */
.amount {
  font-family: 'SF Mono', 'Menlo', 'Consolas', monospace;
  font-size: 13px;
  color: #606266;
}

.amount.balance {
  color: #409eff;
  font-weight: 600;
}

/* Element Plus 微调 */
:deep(.el-table) {
  font-size: 13px;
}

:deep(.el-table th) {
  padding: 8px 0;
}

:deep(.el-table td) {
  padding: 6px 0;
}

:deep(.el-table .cell) {
  padding: 0 8px;
}

:deep(.el-empty__description) {
  font-size: 14px;
  color: #909399;
}
</style>
