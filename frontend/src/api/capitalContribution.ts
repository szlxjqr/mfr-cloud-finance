/** 股东入资 API 客户端 */
import http from '@/utils/request'
import type { CapitalContribution } from '@/types/finance'

export const capitalContributionApi = {
  list: (params?: { keyword?: string; status?: string; investor?: string }) =>
    http.get<CapitalContribution[]>('/capital-contributions', { params }),
  get: (id: number) => http.get<CapitalContribution>(`/capital-contributions/${id}`),
  nextBillNo: () => http.get<{ bill_no: string }>('/capital-contributions/next-bill-no'),
  create: (data: Partial<CapitalContribution>) =>
    http.post<CapitalContribution>('/capital-contributions', data),
  update: (id: number, data: Partial<CapitalContribution>) =>
    http.put<CapitalContribution>(`/capital-contributions/${id}`, data),
  remove: (id: number) => http.delete(`/capital-contributions/${id}`),
  confirm: (id: number) => http.post<CapitalContribution>(`/capital-contributions/${id}/confirm`),
}
