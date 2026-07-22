export type ReqStatus = '草稿' | '待审批' | '已通过' | '已驳回'

export interface TravelReq {
  id: number
  req_no?: string | null
  applicant: string
  department?: string | null
  traveler?: string | null
  destination?: string | null
  travel_start?: string | null
  travel_end?: string | null
  expected_amount?: number | null
  reason?: string | null
  status: ReqStatus
  submit_date?: string | null
  approver?: string | null
  approve_date?: string | null
  approve_remark?: string | null
  remark?: string | null
}
