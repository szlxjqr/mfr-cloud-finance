import http from '@/utils/request'
import type { Employee, LoginResp, CurrentUser } from '@/types/employee'

/** 登录 */
export function login(data: { username: string; password: string }) {
  return http.post<LoginResp>('/auth/login', data)
}

/** 当前登录用户 */
export function fetchCurrentUser() {
  return http.get<CurrentUser>('/auth/me')
}

/** 员工列表（支持关键字 / 状态筛选） */
export function listEmployees(params?: { keyword?: string; status?: string }) {
  return http.get<Employee[]>('/employees', { params })
}

/** 预览姓名对应的登录账号（新增时实时带出） */
export function previewUsername(name: string) {
  return http.get<{ username: string }>('/employees/username-preview', { params: { name } })
}

/** 新增员工（后端自动按姓名全拼创建账号） */
export function createEmployee(data: Partial<Employee>) {
  return http.post<Employee>('/employees', data)
}

/** 编辑员工档案 */
export function updateEmployee(employeeNo: string, data: Partial<Employee>) {
  return http.put<Employee>(`/employees/${employeeNo}`, data)
}

/** 删除员工（级联删除账号） */
export function deleteEmployee(employeeNo: string) {
  return http.delete(`/employees/${employeeNo}`)
}
