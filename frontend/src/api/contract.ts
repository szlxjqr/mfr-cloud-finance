import http from '@/utils/request'
import type {
  ContractTemplate,
  HRContract,
  HRContractPrintData,
  Party,
  PurchaseContract,
  SalesContract,
} from '@/types/contract'

export const partyApi = {
  list: (params?: { ptype?: string; keyword?: string }) =>
    http.get<Party[]>('/contracts/parties', { params }),
  create: (data: Partial<Party>) => http.post<Party>('/contracts/parties', data),
  update: (id: number, data: Partial<Party>) => http.put<Party>(`/contracts/parties/${id}`, data),
  remove: (id: number) => http.delete(`/contracts/parties/${id}`),
}

export const hrApi = {
  list: (params?: { keyword?: string; status?: string; employee_id?: number }) =>
    http.get<HRContract[]>('/contracts/hr-contracts', { params }),
  create: (data: Partial<HRContract>) => http.post<HRContract>('/contracts/hr-contracts', data),
  update: (id: number, data: Partial<HRContract>) =>
    http.put<HRContract>(`/contracts/hr-contracts/${id}`, data),
  remove: (id: number) => http.delete(`/contracts/hr-contracts/${id}`),
  /** 提交：一键从草稿 → 待审批 → 已生效（一人公司自动审批） */
  submit: (id: number) => http.post<HRContract>(`/contracts/hr-contracts/${id}/submit`),
  /** 审批：待审批 → 已生效 */
  approve: (id: number, data: { approver: string; remark?: string }) =>
    http.post<HRContract>(`/contracts/hr-contracts/${id}/approve`, data),
  /** 终止：已生效/已到期 → 已终止 */
  terminate: (id: number, data?: { remark?: string }) =>
    http.post<HRContract>(`/contracts/hr-contracts/${id}/terminate`, data || {}),
  /** 打印：聚合合同 + 公司设置 + 模板内容，前端用于渲染 A4 打印页 */
  print: (id: number) => http.get<HRContractPrintData>(`/contracts/hr-contracts/${id}/print`),
}

export const salesApi = {
  list: (params?: { keyword?: string; status?: string; customer_id?: number }) =>
    http.get<SalesContract[]>('/contracts/sales-contracts', { params }),
  create: (data: Partial<SalesContract>) => http.post<SalesContract>('/contracts/sales-contracts', data),
  update: (id: number, data: Partial<SalesContract>) =>
    http.put<SalesContract>(`/contracts/sales-contracts/${id}`, data),
  remove: (id: number) => http.delete(`/contracts/sales-contracts/${id}`),
}

export const purchaseApi = {
  list: (params?: { keyword?: string; status?: string; supplier_id?: number }) =>
    http.get<PurchaseContract[]>('/contracts/purchase-contracts', { params }),
  create: (data: Partial<PurchaseContract>) => http.post<PurchaseContract>('/contracts/purchase-contracts', data),
  update: (id: number, data: Partial<PurchaseContract>) =>
    http.put<PurchaseContract>(`/contracts/purchase-contracts/${id}`, data),
  remove: (id: number) => http.delete(`/contracts/purchase-contracts/${id}`),
}

export const templateApi = {
  list: (params?: { ctype?: string; keyword?: string }) =>
    http.get<ContractTemplate[]>('/contracts/templates', { params }),
  create: (data: Partial<ContractTemplate>) => http.post<ContractTemplate>('/contracts/templates', data),
  update: (id: number, data: Partial<ContractTemplate>) =>
    http.put<ContractTemplate>(`/contracts/templates/${id}`, data),
  remove: (id: number) => http.delete(`/contracts/templates/${id}`),
}
