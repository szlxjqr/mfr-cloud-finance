import http from '@/utils/request'
import type { Invoice, InvoiceCreatePayload } from '@/types/invoice'

export const invoiceApi = {
  list: (params?: {
    keyword?: string
    reimbursement_bill_id?: number
    unlinked?: boolean
    start_date?: string
    end_date?: string
  }) => http.get<Invoice[]>('/invoices', { params }),

  create: (data: InvoiceCreatePayload) => http.post<Invoice>('/invoices', data),

  update: (id: number, data: Partial<InvoiceCreatePayload>) =>
    http.put<Invoice>(`/invoices/${id}`, data),

  remove: (id: number) => http.delete(`/invoices/${id}`),

  link: (invoiceId: number, billId: number) =>
    http.post<Invoice>(`/invoices/${invoiceId}/link/${billId}`),

  unlink: (invoiceId: number) => http.post<Invoice>(`/invoices/${invoiceId}/unlink`),

  batchLink: (invoiceIds: number[], billId: number) =>
    http.post('/invoices/batch-link', { invoice_ids: invoiceIds, bill_id: billId }),

  uploadAttachment: (invoiceId: number, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return http.post<Invoice>(`/invoices/${invoiceId}/attachment`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  voucherDraft: (invoiceIds: number[]) =>
    http.post<{
      entries: { account: string; summary: string; debit: number; credit: number }[]
      invoice_count: number
    }>('/invoices/voucher-draft', invoiceIds),

  summaryByBill: (billId: number) =>
    http.get<{
      amount: number
      tax: number
      total: number
      invoice_count: number
    }>(`/invoices/by-bill/${billId}/summary`),
}
