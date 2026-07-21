import type { Invoice } from './invoice'

export type ReimburseStatus = '草稿' | '待审批' | '已通过' | '已驳回' | '已支付'

export interface ReimbursementBill {
  id: number
  bill_no?: string | null
  applicant: string
  department?: string | null
  amount?: number | null
  reason?: string | null
  status: ReimburseStatus
  submit_date?: string | null
  approve_date?: string | null
  approver?: string | null
  approve_remark?: string | null
  attachment_path?: string | null
  remark?: string | null
  invoices?: Invoice[]
}
