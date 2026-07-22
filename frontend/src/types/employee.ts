/** 员工档案 + 登录返回结构 */
export interface Employee {
  id: number
  employee_no: string
  name: string
  department?: string | null
  position?: string | null
  phone?: string | null
  email?: string | null
  status: string
  hire_date?: string | null
  created_at?: string | null
  username?: string | null
}

export interface LoginResp {
  token: string
  username: string
  role: string
  employee_no: string
  name?: string | null
}

export interface CurrentUser {
  username: string
  role: string
  employee_no: string
  name?: string | null
}
