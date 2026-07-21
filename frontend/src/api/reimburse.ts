import http from '@/utils/request'
import type { ReimbursementBill } from '@/types/reimburse'

export const reimburseApi = {
  list: (params?: { keyword?: string; status?: string; applicant?: string }) =>
    http.get<ReimbursementBill[]>('/reimbursements', { params }),
  get: (id: number) => http.get<ReimbursementBill>(`/reimbursements/${id}`),
  nextBillNo: () => http.get<{ bill_no: string }>('/reimbursements/next-bill-no'),
  create: (data: Partial<ReimbursementBill>) => http.post<ReimbursementBill>('/reimbursements', data),
  update: (id: number, data: Partial<ReimbursementBill>) =>
    http.put<ReimbursementBill>(`/reimbursements/${id}`, data),
  remove: (id: number) => http.delete(`/reimbursements/${id}`),
  submit: (id: number) => http.post<ReimbursementBill>(`/reimbursements/${id}/submit`),
  approve: (id: number, data: { approver: string; remark?: string }) =>
    http.post<ReimbursementBill>(`/reimbursements/${id}/approve`, data),
  reject: (id: number, data: { approver: string; remark?: string }) =>
    http.post<ReimbursementBill>(`/reimbursements/${id}/reject`, data),
  pay: (id: number) => http.post<ReimbursementBill>(`/reimbursements/${id}/pay`),
}
