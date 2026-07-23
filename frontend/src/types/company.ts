/** 公司设置（全局单例 id=1） */
export interface CompanySettings {
  id: number
  company_name?: string | null
  legal_rep?: string | null
  address?: string | null
  phone?: string | null
  tax_no?: string | null
  bank_name?: string | null
  bank_account?: string | null
  contact?: string | null
  email?: string | null
  remark?: string | null
}
