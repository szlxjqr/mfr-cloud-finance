/** 收入 API 客户端 */
import http from '@/utils/request'
import type { Revenue } from '@/types/finance'

export const revenueApi = {
  list: (params?: { keyword?: string; status?: string; customer?: string }) =>
    http.get<Revenue[]>('/revenues', { params }),
  get: (id: number) => http.get<Revenue>(`/revenues/${id}`),
  nextBillNo: () => http.get<{ bill_no: string }>('/revenues/next-bill-no'),
  create: (data: Partial<Revenue>) => http.post<Revenue>('/revenues', data),
  update: (id: number, data: Partial<Revenue>) => http.put<Revenue>(`/revenues/${id}`, data),
  remove: (id: number) => http.delete(`/revenues/${id}`),
  confirm: (id: number) => http.post<Revenue>(`/revenues/${id}/confirm`),
}
