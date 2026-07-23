export type PartyType = 'customer' | 'supplier'

export interface Party {
  id: number
  name: string
  tax_no?: string | null
  ptype: PartyType
  contact?: string | null
  phone?: string | null
  address?: string | null
  status: string
  remark?: string | null
}

/** 人事合同状态机：草稿 → 待审批 → 已生效 → 已到期/已终止 */
export type HRContractStatus = '草稿' | '待审批' | '已生效' | '已到期' | '已终止'

export interface HRContract {
  id: number
  // 员工联动
  employee_id?: number | null
  employee_no?: string | null
  employee_name: string
  id_number?: string | null
  department?: string | null
  position?: string | null
  phone?: string | null
  // 合同期限
  contract_type: string
  contract_term?: string | null
  sign_date?: string | null
  start_date?: string | null
  end_date?: string | null
  // 试用期
  probation_months?: number | null
  probation_start?: string | null
  probation_end?: string | null
  probation_salary?: number | null
  // 工作
  work_content?: string | null
  work_location?: string | null
  work_hours_type?: string | null
  // 报酬
  salary?: number | null
  pay_method?: string | null
  pay_day?: number | null
  // 保险福利
  social_insurance?: string | null
  benefits?: string | null
  // 甲方乙方
  party_a?: string | null
  party_b?: string | null
  // 状态/审批
  status: HRContractStatus
  approver?: string | null
  approve_date?: string | null
  approve_remark?: string | null
  // 模板
  template_id?: number | null
  attachment_path?: string | null
  remark?: string | null
}

export interface SalesContract {
  id: number
  contract_no?: string | null
  customer_id?: number | null
  sign_date?: string | null
  effective_date?: string | null
  expire_date?: string | null
  amount?: number | null
  tax_rate?: number | null
  tax_amount?: number | null
  status: string
  attachment_path?: string | null
  remark?: string | null
}

export interface PurchaseContract {
  id: number
  contract_no?: string | null
  supplier_id?: number | null
  sign_date?: string | null
  effective_date?: string | null
  expire_date?: string | null
  amount?: number | null
  tax_rate?: number | null
  tax_amount?: number | null
  status: string
  attachment_path?: string | null
  remark?: string | null
}

export interface ContractTemplate {
  id: number
  name: string
  ctype: string
  content?: string | null
  remark?: string | null
}

/** 合同打印接口的聚合返回：合同 + 公司信息 + 模板内容 */
export interface HRContractPrintData {
  contract: HRContract
  company: {
    company_name?: string | null
    legal_rep?: string | null
    address?: string | null
    phone?: string | null
    tax_no?: string | null
  } | null
  template: {
    name?: string | null
    content?: string | null
  } | null
}
