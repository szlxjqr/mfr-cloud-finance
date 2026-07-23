import http from '@/utils/request'
import type { SalaryBill, SalarySetting, SalaryAllocation } from '@/types/salary'

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
  // 工资设置（社保/公积金/个税口径）
  getSetting: () => http.get<SalarySetting>('/salary-settings'),
  saveSetting: (data: Partial<SalarySetting>) => http.put<SalarySetting>('/salary-settings', data),
  // 按设置自动计算代扣（不落库，供回填）
  calcDeductions: (data: {
    base_salary?: number
    performance?: number
    overtime?: number
    bonus?: number
  }) => http.post<{
    gross_pay: number
    social_personal: number
    fund_personal: number
    tax_personal: number
    deduct_total: number
    net_pay: number
  }>('/salary-settings/calc-deductions', data),
  // 部门工资汇总表
  deptSummary: (params?: { period?: string; status?: string }) =>
    http.get<Record<string, unknown>[]>('/salaries/dept-summary', { params }),
  // 个税报表
  taxReport: (params?: { period?: string; employee_name?: string }) =>
    http.get<Record<string, unknown>[]>('/salaries/tax-report', { params }),
  // 工资分摊（按部门归集 + 占比）
  allocation: (params?: { period?: string; status?: string }) =>
    http.get<SalaryAllocation>('/salaries/allocation', { params }),
}
