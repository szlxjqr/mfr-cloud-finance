export type SalaryStatus = '草稿' | '待审批' | '已通过' | '已驳回' | '已发放'

export interface SalaryBill {
  id: number
  salary_no?: string | null
  employee_name: string
  employee_no?: string | null
  department?: string | null
  period: string // YYYY-MM
  base_salary?: number | null
  performance?: number | null
  overtime?: number | null
  bonus?: number | null
  gross_pay?: number | null // 应发 = 基本+绩效+加班+奖金
  social_personal?: number | null
  fund_personal?: number | null
  tax_personal?: number | null
  deduct_total?: number | null // 代扣 = 社保+公积金+个税
  net_pay?: number | null // 实发 = 应发-代扣
  status: SalaryStatus
  submit_date?: string | null
  approve_date?: string | null
  pay_date?: string | null
  approver?: string | null
  payee?: string | null
  approve_remark?: string | null
  pay_remark?: string | null
  remark?: string | null
}

export interface SalarySetting {
  social_personal_rate: number // 社保个人比例 %
  fund_personal_rate: number // 公积金个人比例 %
  tax_threshold: number // 个税起征点
  tax_method: '月度税率表' | '固定比例'
  tax_flat_rate: number // 固定比例模式税率 %
}
