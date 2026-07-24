import http from '@/utils/request'
import type { PurchaseReq } from '@/types/purchase'

export const purchaseApi = {
  list: (params?: { keyword?: string; status?: string; applicant?: string; supplier?: string }) =>
    http.get<PurchaseReq[]>('/purchases', { params }),
  get: (id: number) => http.get<PurchaseReq>(`/purchases/${id}`),
  nextReqNo: () => http.get<{ req_no: string }>('/purchases/next-req-no'),
  create: (data: Partial<PurchaseReq>) => http.post<PurchaseReq>('/purchases', data),
  update: (id: number, data: Partial<PurchaseReq>) =>
    http.put<PurchaseReq>(`/purchases/${id}`, data),
  remove: (id: number) => http.delete(`/purchases/${id}`),
  submit: (id: number) => http.post<PurchaseReq>(`/purchases/${id}/submit`),
  approve: (id: number, data: { approver: string; remark?: string }) =>
    http.post<PurchaseReq>(`/purchases/${id}/approve`, data),
  reject: (id: number, data: { approver: string; remark?: string }) =>
    http.post<PurchaseReq>(`/purchases/${id}/reject`, data),
  pay: (id: number) => http.post<PurchaseReq>(`/purchases/${id}/pay`),
}
