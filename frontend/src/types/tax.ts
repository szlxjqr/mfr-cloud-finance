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

/** 个税申报明细行（按员工 × 期间聚合） */
export interface IndividualTaxRow {
  employee_name: string
  employee_no: string | null
  department: string | null
  period: string
  gross_pay: number // 应发合计
  social_personal: number // 社保(个人)
  fund_personal: number // 公积金(个人)
  tax_personal: number // 个人所得税
}

/** 个税申报：按员工 × 期间聚合的工资个税 */
export interface IndividualTax {
  period: string | null
  rows: IndividualTaxRow[]
  total_tax: number // 应申报个税合计
  total_gross: number // 应发合计
  headcount: number // 申报人数
}

/** 印花税明细行（买卖合同） */
export interface StampTaxRow {
  contract_no: string | null
  party: string | null
  type: string // 销售合同 / 采购合同
  sign_date: string
  amount: number // 合同金额
  rate: number // 印花税率
  tax: number // 应纳税额
}

/** 印花税：销售 + 采购合同按 0.03% 计征 */
export interface StampTax {
  year: string | null
  rows: StampTaxRow[]
  total_amount: number
  total_tax: number
  contract_count: number
}

/** 税务工作台概览 */
export interface TaxWorkbench {
  period: string | null
  vat: {
    input_tax: number
    output_tax: number
    vat_payable: number
    carryforward: boolean
  }
  individual: {
    total_tax: number
    total_gross: number
    headcount: number
  }
  stamp: {
    total_tax: number
    total_amount: number
    contract_count: number
  }
}
