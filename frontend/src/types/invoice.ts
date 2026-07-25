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
  invoice_code?: string | null
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
  purchase_requisition_item_id?: number | null
  attachment_path?: string | null
  route_info?: string | null
  traveler?: string | null
  created_at: string
  details: InvoiceDetail[]
}

// 发票箱（收口/暂存）记录
export interface InvoiceInbox {
  id: number
  filename: string
  storage_path: string
  source: string // upload | box
  duplicated?: boolean // P1 去重：本次上传与箱中已有同票重复时置 true
  extracted_json?: string | null
  status: string // pending | recognized | linked | error
  linked_doc_type?: string | null // reimburse | purchase
  linked_doc_id?: number | null
  verify_result?: string | null // none | real | fake | abnormal
  verify_note?: string | null
  created_at: string
  recognized_at?: string | null
  linked_at?: string | null
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
  purchase_requisition_item_id?: number | null
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
