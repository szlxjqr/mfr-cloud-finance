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

export interface HRContract {
  id: number
  employee_name: string
  id_number?: string | null
  contract_type: string
  party_a?: string | null
  party_b?: string | null
  start_date?: string | null
  end_date?: string | null
  status: string
  salary?: number | null
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
