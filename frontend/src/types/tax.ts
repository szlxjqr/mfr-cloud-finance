/** 税务取数类型（snake_case 匹配后端 JSON） */

/** 税务汇总 KPI（期间感知） */
export interface TaxSummary {
  period: string | null
  input_tax: number // 进项税额
  output_tax: number // 销项税额
  vat_payable: number // 应交增值税（负值=留抵）
  carryforward: boolean // 是否留抵
}

/** 进项税额明细行（关联来源业务单） */
export interface TaxInputDetail {
  voucher_no: string
  date: string
  period: string
  summary: string | null
  amount: number
  source_type: string | null
  source_no: string | null
}

/** 月度趋势行 */
export interface TaxMonthlyRow {
  period: string
  input_tax: number
  output_tax: number
}

/** 发票税务汇总：KPI + 进项税额明细 + 月度趋势 */
export interface TaxSummaryDetail {
  summary: TaxSummary
  details: TaxInputDetail[]
  monthly: TaxMonthlyRow[]
}
