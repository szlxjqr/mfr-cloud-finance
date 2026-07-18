/**
 * 仪表盘相关 TypeScript 接口定义
 */

/** 快捷功能项 */
export interface QuickAction {
  /** 图标组件名（Element Plus 图标，如 'Wallet'） */
  icon: string
  /** 显示文案 */
  label: string
  /** 跳转路由 */
  path: string
  /** 主题色（可选，用于图标/卡片着色） */
  color?: string
}

/** 资金指标项 */
export interface FundItem {
  /** 指标名称（如：现金及等价物、应收账款） */
  name: string
  /** 金额数值 */
  amount: number
  /** 展示颜色 */
  color: string
  /** 单位（如：元、万元） */
  unit: string
}

/** 税费项 */
export interface TaxItem {
  /** 税费名称（如：增值税、企业所得税） */
  name: string
  /** 数值（金额或比率，视具体业务而定） */
  value: number
  /** 展示颜色 */
  color: string
}

/** 经营数据点（用于收入趋势等图表） */
export interface RevenueDataPoint {
  /** 月份标识，如 '2026-01' 或 '一月' */
  month: string
  /** 数值 */
  value: number
}

/** 仪表盘汇总数据 */
export interface DashboardSummary {
  /** 当前公司名称 */
  companyName: string
  /** 统计周期（如 '2026年7月'） */
  period: string
  /** 快捷功能入口 */
  quickActions: QuickAction[]
  /** 资金概览指标 */
  funds: FundItem[]
  /** 税费概览 */
  taxItems: TaxItem[]
  /** 经营/收入趋势 */
  revenueTrend: RevenueDataPoint[]
  /** 数据更新时间（可选） */
  updatedAt?: string
}
