export type ReqStatus = '草稿' | '待审批' | '已通过' | '已驳回'

export interface TravelItem {
  id: number
  req_id: number
  item_name: string
  amount?: number | null
  sort_order: number
  remark?: string | null
}

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
  is_rd_project?: string | null  // 是否归属研发项目：是/否
  rd_project_code?: string | null  // 研发项目编码
  remark?: string | null
  items?: TravelItem[]
}
