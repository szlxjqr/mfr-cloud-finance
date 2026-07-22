export type ReqStatus = '草稿' | '待审批' | '已通过' | '已驳回'

/** 采购申请明细：一条申请可包含多个物品 / 服务 */
export interface PurchaseItem {
  id?: number
  req_id?: number
  item_name: string
  spec?: string | null
  quantity: number
  unit_price?: number | null
  amount?: number | null
  supplier?: string | null
  remark?: string | null
}

export interface PurchaseReq {
  id: number
  req_no?: string | null
  applicant: string
  department?: string | null
  item_name: string
  spec?: string | null
  quantity: number
  expected_amount?: number | null
  supplier?: string | null
  expected_date?: string | null
  reason?: string | null
  status: ReqStatus
  submit_date?: string | null
  approver?: string | null
  approve_date?: string | null
  approve_remark?: string | null
  is_rd_project?: string | null
  rd_project_code?: string | null
  remark?: string | null
  items?: PurchaseItem[]
}
