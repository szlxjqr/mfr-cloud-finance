import request from '@/utils/request'
import type {
  BalanceSheetOut,
  IncomeStatementOut,
  CashFlowOut,
  QuarterOut,
} from '@/types/financial_statement'

// 资产负债表（期末余额，损益自动结转）
export function getBalanceSheet(period?: string) {
  return request.get<BalanceSheetOut>('/financial/balance-sheet', { params: { period } })
}

// 利润表（本期 + 本年累计 双列）
export function getIncomeStatement(period?: string) {
  return request.get<IncomeStatementOut>('/financial/income-statement', { params: { period } })
}

// 现金流量表（按对方科目分类）
export function getCashFlow(period?: string) {
  return request.get<CashFlowOut>('/financial/cash-flow', { params: { period } })
}

// 季报（季度内汇总 + 季末快照）
export function getQuarterly(year: number, quarter: number) {
  return request.get<QuarterOut>('/financial/quarterly', { params: { year, quarter } })
}
