/** 会计核算相关类型（对应后端 /api/subjects、/api/vouchers） */

/** 会计科目 */
export interface AccountSubject {
  id: number
  code: string
  name: string
  category: string // 资产/负债/权益/成本/损益
  direction: string // 借/贷
  level: number
  parent_code?: string | null
  is_leaf: boolean
  status: string
}

/** 凭证分录行 */
export interface VoucherEntry {
  seq: number
  subject_code: string
  subject_name: string
  summary?: string | null
  direction: string // 借/贷
  amount: number
}

/** 记账凭证（读） */
export interface Voucher {
  id: number
  voucher_no: string
  date: string
  period: string
  voucher_word: string // 记/收/付/转
  seq: number
  attach_count: number
  maker?: string | null
  status: string // 未审核/已审核/已记账
  source_type?: string | null
  source_no?: string | null
  summary?: string | null
  entries: VoucherEntry[]
}

/** 科目余额 */
export interface SubjectBalance {
  code: string
  name: string
  category: string
  direction: string
  period_debit: number
  period_credit: number
  cum_debit: number
  cum_credit: number
  ending_debit: number
  ending_credit: number
}

/** 一键补生成结果 */
export interface VoucherGenerateResult {
  generated: number
  skipped: number
  detail: string[]
}

/** 总账行（按期间汇总） */
export interface GeneralLedgerRow {
  period: string
  opening_debit: number
  opening_credit: number
  period_debit: number
  period_credit: number
  ending_debit: number
  ending_credit: number
  direction: string
  balance: number
}

/** 总账（某科目） */
export interface GeneralLedgerOut {
  subject_code: string
  subject_name: string
  direction: string
  rows: GeneralLedgerRow[]
}

/** 明细账分录行 */
export interface SubsidiaryLine {
  date: string
  voucher_no: string
  summary?: string | null
  debit: number
  credit: number
  direction: string
  balance: number
}

/** 明细账（某科目） */
export interface SubsidiaryLedgerOut {
  subject_code: string
  subject_name: string
  direction: string
  opening_debit: number
  opening_credit: number
  lines: SubsidiaryLine[]
  total_debit: number
  total_credit: number
  ending_debit: number
  ending_credit: number
}

/** 科目汇总表行（期间感知） */
export interface LedgerSummaryRow {
  code: string
  name: string
  category: string
  direction: string
  level: number
  parent_code?: string | null
  is_leaf: boolean
  opening_debit: number
  opening_credit: number
  period_debit: number
  period_credit: number
  cum_debit: number
  cum_credit: number
  ending_debit: number
  ending_credit: number
}

/** 序时账行 */
export interface JournalLine {
  date: string
  voucher_no: string
  period: string
  summary?: string | null
  subject_code: string
  subject_name: string
  direction: string
  amount: number
}

/** 序时账 */
export interface JournalOut {
  lines: JournalLine[]
}
