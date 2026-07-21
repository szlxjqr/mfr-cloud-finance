export interface InvoiceDetail {
  id: number
  invoice_id: number
  biz_type?: string | null
  item?: string | null
  qty: number
  amount: number
  tax_rate: number
  tax: number
  total: number
}

export interface Invoice {
  id: number
  invoice_type: string
  code?: string | null
  no: string
  invoice_date?: string | null
  buyer_name?: string | null
  buyer_tax_no?: string | null
  seller_name: string
  seller_tax_no?: string | null
  seller_address_phone?: string | null
  seller_bank_account?: string | null
  account?: string | null
  certify: string
  remark?: string | null
  reimbursement_bill_id?: number | null
  attachment_path?: string | null
  route_info?: string | null
  traveler?: string | null
  created_at: string
  details: InvoiceDetail[]
}

export interface InvoiceCreatePayload {
  invoice_type: string
  code?: string | null
  no: string
  invoice_date?: string | null
  buyer_name?: string | null
  buyer_tax_no?: string | null
  seller_name: string
  seller_tax_no?: string | null
  seller_address_phone?: string | null
  seller_bank_account?: string | null
  account?: string | null
  certify: string
  remark?: string | null
  reimbursement_bill_id?: number | null
  attachment_path?: string | null
  route_info?: string | null
  traveler?: string | null
  details: {
    biz_type?: string | null
    item?: string | null
    qty: number
    amount: number
    tax_rate: number
    tax: number
    total: number
  }[]
}
