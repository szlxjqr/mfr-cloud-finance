/** 财务模块类型：股东入资 / 收入 */

/** 股东入资单 */
export interface CapitalContribution {
  id: number
  bill_no?: string | null
  investor: string
  amount?: number | null
  capital_type?: string // 货币资金/实物
  receive_subject?: string // 收款科目编码（默认 1002 银行存款）
  contribution_date?: string | null // YYYY-MM-DD
  status: string // 草稿/已确认
  remark?: string | null
  voucher_no?: string | null
}

/** 收入单 */
export interface Revenue {
  id: number
  bill_no?: string | null
  customer: string
  total_amount?: number | null // 价税合计（含税）
  tax_rate?: number // 增值税税率
  settle_method?: string // 银行收讫/应收账款
  revenue_date?: string | null // YYYY-MM-DD
  status: string // 草稿/已确认
  remark?: string | null
  voucher_no?: string | null
}
