import http from '@/utils/request'
import type { SalaryBill } from '@/types/salary'

export const salaryApi = {
  list: (params?: { keyword?: string; status?: string; employee_name?: string; period?: string }) =>
    http.get<SalaryBill[]>('/salaries', { params }),
  get: (id: number) => http.get<SalaryBill>(`/salaries/${id}`),
  nextSalaryNo: () => http.get<{ salary_no: string }>('/salaries/next-salary-no'),
  create: (data: Partial<SalaryBill>) => http.post<SalaryBill>('/salaries', data),
  update: (id: number, data: Partial<SalaryBill>) =>
    http.put<SalaryBill>(`/salaries/${id}`, data),
  remove: (id: number) => http.delete(`/salaries/${id}`),
  submit: (id: number) => http.post<SalaryBill>(`/salaries/${id}/submit`),
  approve: (id: number, data: { approver: string; remark?: string }) =>
    http.post<SalaryBill>(`/salaries/${id}/approve`, data),
  reject: (id: number, data: { approver: string; remark?: string }) =>
    http.post<SalaryBill>(`/salaries/${id}/reject`, data),
  pay: (id: number, data?: { approver?: string; remark?: string }) =>
    http.post<SalaryBill>(`/salaries/${id}/pay`, data || {}),
}
