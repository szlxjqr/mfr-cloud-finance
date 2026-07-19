/** 子菜单项 */
export interface SubMenuItem {
  title: string
  path: string
}

/** 菜单分组（用于总账等有子菜单的情况） */
export interface MenuGroup {
  title: string
  icon: string
  color: string
  children: SubMenuItem[]
}

/** 菜单项（支持普通项和分组展开） */
export interface MenuItem {
  title: string
  path?: string
  icon?: string
  badge?: string
  module?: string
  groups?: MenuGroup[]
}

/** 左侧主导航菜单配置 —— 单一真相源 */
export const menuItems: MenuItem[] = [
  { title: '首页', path: '/dashboard', icon: 'HomeFilled', module: 'dashboard' },
  {
    title: '总账',
    icon: 'Document',
    module: 'general-ledger',
    groups: [
      {
        title: '凭证管理',
        icon: 'Document',
        color: '#409EFF',
        children: [
          { title: '凭证', path: '/general-ledger/voucher' },
          { title: '查看凭证', path: '/general-ledger/voucher-list' },
          { title: '原始凭证', path: '/general-ledger/original-voucher' },
        ],
      },
      {
        title: '账簿',
        icon: 'Coin',
        color: '#E6A23C',
        children: [
          { title: '总账', path: '/general-ledger/general' },
          { title: '明细账', path: '/general-ledger/detail' },
          { title: '余额表', path: '/general-ledger/balance' },
          { title: '序时账', path: '/general-ledger/chronological' },
          { title: '多栏账', path: '/general-ledger/columnar' },
          { title: '科目汇总表', path: '/general-ledger/account-summary' },
        ],
      },
      {
        title: '辅助账簿',
        icon: 'Grid',
        color: '#909399',
        children: [
          { title: '科目辅助明细账', path: '/general-ledger/aux-detail' },
          { title: '科目辅助余额表', path: '/general-ledger/aux-balance' },
          { title: '数量外币明细账', path: '/general-ledger/qty-fx-detail' },
          { title: '数量外币余额表', path: '/general-ledger/qty-fx-balance' },
          { title: '核算项目明细账', path: '/general-ledger/project-detail' },
          { title: '核算项目余额表', path: '/general-ledger/project-balance' },
        ],
      },
    ],
  },
  {
    title: '报表',
    icon: 'DataAnalysis',
    module: 'reports',
    groups: [
      {
        title: '财务报表',
        icon: 'DataAnalysis',
        color: '#67C23A',
        children: [
          { title: '资产负债表', path: '/reports/balance-sheet' },
          { title: '利润表', path: '/reports/income-statement' },
          { title: '利润表季报', path: '/reports/income-statement-quarterly' },
          { title: '现金流量表', path: '/reports/cash-flow' },
          { title: '现金流量表季报', path: '/reports/cash-flow-quarterly' },
        ],
      },
    ],
  },
  {
    title: '出纳',
    icon: 'Money',
    module: 'cashier',
    groups: [
      {
        title: '资金管理',
        icon: 'Money',
        color: '#9B59B6',
        children: [
          { title: '日记账', path: '/cashier/diary' },
          { title: '业务类型', path: '/cashier/biz-type' },
          { title: '核对总账', path: '/cashier/check-general' },
        ],
      },
    ],
  },
  {
    title: '资产',
    icon: 'OfficeBuilding',
    module: 'assets',
    groups: [
      {
        title: '固定资产',
        icon: 'OfficeBuilding',
        color: '#13C2C2',
        children: [
          { title: '固定资产管理', path: '/assets/fixed-asset' },
        ],
      },
    ],
  },
  {
    title: '工资',
    icon: 'User',
    module: 'payroll',
    groups: [
      {
        title: '工资',
        icon: 'UserFilled',
        color: '#67C23A',
        children: [
          { title: '员工基本信息', path: '/payroll/employee-info' },
          { title: '工资列表', path: '/payroll/salary-list' },
          { title: '部门工资汇总表', path: '/payroll/dept-summary' },
          { title: '个税报表', path: '/payroll/tax-report' },
        ],
      },
      {
        title: '工资设置',
        icon: 'Setting',
        color: '#409EFF',
        children: [
          { title: '社保及公积金设置', path: '/payroll/social-fund-setting' },
          { title: '工资计算设置', path: '/payroll/calc-setting' },
          { title: '工资分摊', path: '/payroll/allocation' },
        ],
      },
    ],
  },
  {
    title: '发票',
    icon: 'Ticket',
    module: 'invoice',
    groups: [
      {
        title: '发票',
        icon: 'Ticket',
        color: '#409EFF',
        children: [
          { title: '进项发票', path: '/invoice/input' },
          { title: '销项发票', path: '/invoice/output' },
          { title: '费用发票', path: '/invoice/expense' },
        ],
      },
      {
        title: '发票设置',
        icon: 'Wallet',
        color: '#E6A23C',
        children: [
          { title: '发票抬头', path: '/invoice/title' },
          { title: '发票设置', path: '/invoice/setting' },
        ],
      },
    ],
  },
  {
    title: '结账',
    icon: 'CircleCheck',
    module: 'closing',
    groups: [
      {
        title: '结账',
        icon: 'CircleCheck',
        color: '#E6A23C',
        children: [
          { title: '期末结转', path: '/closing/carry-forward' },
          { title: '结账', path: '/closing/close' },
        ],
      },
    ],
  },
  {
    title: '设置',
    icon: 'Setting',
    module: 'settings',
    groups: [
      {
        title: '基础数据',
        icon: 'DataLine',
        color: '#409EFF',
        children: [
          { title: '科目', path: '/settings/account' },
          { title: '期初', path: '/settings/opening' },
          { title: '辅助字典', path: '/settings/aux-dict' },
          { title: '币别', path: '/settings/currency' },
          { title: '凭证摘要', path: '/settings/summary' },
          { title: '凭证字', path: '/settings/voucher-word' },
        ],
      },
      {
        title: '基础设置',
        icon: 'Setting',
        color: '#E6A23C',
        children: [
          { title: '凭证模板', path: '/settings/voucher-template' },
          { title: '凭证配置', path: '/settings/voucher-config' },
          { title: '日记账模板', path: '/settings/diary-template' },
          { title: '归档管理', path: '/settings/archive' },
          { title: '系统设置', path: '/settings/system' },
          { title: '审计接口文件导出', path: '/settings/audit-export' },
        ],
      },
    ],
  },
  { title: '新手指引', path: '/guide', icon: 'Notebook', module: 'guide' },
]
