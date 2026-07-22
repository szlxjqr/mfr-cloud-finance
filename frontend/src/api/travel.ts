import http from '@/utils/request'
import type { TravelReq } from '@/types/travel'

export const travelApi = {
  list: (params?: { keyword?: string; status?: string; applicant?: string }) =>
    http.get<TravelReq[]>('/travels', { params }),
  get: (id: number) => http.get<TravelReq>(`/travels/${id}`),
  nextReqNo: () => http.get<{ req_no: string }>('/travels/next-req-no'),
  create: (data: Partial<TravelReq>) => http.post<TravelReq>('/travels', data),
  update: (id: number, data: Partial<TravelReq>) =>
    http.put<TravelReq>(`/travels/${id}`, data),
  remove: (id: number) => http.delete(`/travels/${id}`),
  submit: (id: number) => http.post<TravelReq>(`/travels/${id}/submit`),
  approve: (id: number, data: { approver: string; remark?: string }) =>
    http.post<TravelReq>(`/travels/${id}/approve`, data),
  reject: (id: number, data: { approver: string; remark?: string }) =>
    http.post<TravelReq>(`/travels/${id}/reject`, data),
}
