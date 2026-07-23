import http from '@/utils/request'
import type { CompanySettings } from '@/types/company'

/** 公司设置：全局单例（id=1），首次访问自动种入默认值 */
export const companyApi = {
  get: () => http.get<CompanySettings>('/company-settings'),
  update: (data: Partial<CompanySettings>) => http.put<CompanySettings>('/company-settings', data),
}
