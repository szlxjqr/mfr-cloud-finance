// 财务报表类型（与后端 schemas/financial_statement.py 对齐）

export interface BalanceSheetItem {
  code: string
  name: string
  amount: number
}

export interface BalanceSheetSection {
  name: string
  items: BalanceSheetItem[]
  total: number
}

export interface BalanceSheetOut {
  as_of: string
  sections: BalanceSheetSection[]
  total_assets: number
  total_liabilities: number
  total_equity: number
  balanced: boolean
  note: string
}

export interface IncomeLine {
  code: string
  name: string
  current: number
  cumulative: number
}

export interface IncomeStatementOut {
  period: string
  revenue: IncomeLine[]
  cost: IncomeLine[]
  expense: IncomeLine[]
  total_revenue_cur: number
  total_revenue_cum: number
  total_expense_cur: number
  total_expense_cum: number
  operating_profit_cur: number
  operating_profit_cum: number
  total_profit_cur: number
  total_profit_cum: number
  net_profit_cur: number
  net_profit_cum: number
}

export interface CashFlowLine {
  name: string
  amount: number
}

export interface CashFlowSection {
  name: string
  items: CashFlowLine[]
  total: number
}

export interface CashFlowOut {
  period: string
  operating: CashFlowSection
  investing: CashFlowSection
  financing: CashFlowSection
  net_operating: number
  net_investing: number
  net_financing: number
  net_increase: number
  note: string
}

export interface QuarterOut {
  year: number
  quarter: number
  as_of: string
  months: string[]
  balance_sheet: BalanceSheetOut
  income: IncomeStatementOut
  cash_flow: CashFlowOut
  note?: string | null
}
