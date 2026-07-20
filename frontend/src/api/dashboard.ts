import http from '@/utils/request'
import type {
  DashboardSummary,
  FundItem,
  RevenueDataPoint,
  TaxItem,
} from '@/types/dashboard'

/** 获取仪表盘汇总数据 */
export function getDashboardSummary() {
  return http.get<DashboardSummary>('/dashboard/summary')
}

/** 获取资金概览 */
export function getFundsOverview() {
  return http.get<FundItem[]>('/dashboard/funds')
}

/** 获取经营/收入趋势 */
export function getRevenueTrend() {
  return http.get<RevenueDataPoint[]>('/dashboard/revenue-trend')
}

/** 获取税费概览 */
export function getTaxOverview() {
  return http.get<TaxItem[]>('/dashboard/tax')
}

/** 获取指定月份的凭证总数 */
export function getVoucherCount(month?: string) {
  return http.get<number>('/dashboard/voucher-count', { params: { month } })
}
