// 综合报表看板数据类型（与后端 /api/comprehensive/overview 对齐）

export interface FundItem {
  code: string
  name: string
  amount: number
}

export interface RevenuePoint {
  period: string
  revenue: number
}

export type StatusMap = Record<string, number>

export interface BusinessSummary {
  reimburse: StatusMap
  purchase: StatusMap
  travel: StatusMap
  pending_total: number
}

export interface VoucherSummary {
  total: number
  period: string | null
  period_count: number
}

export interface TaxSummary {
  period: string | null
  input_tax: number
  output_tax: number
  vat_payable: number
  carryforward: boolean
}

export interface ComprehensiveOverview {
  period: string | null
  funds: FundItem[]
  revenue_trend: RevenuePoint[]
  tax: TaxSummary
  business: BusinessSummary
  voucher: VoucherSummary
}
