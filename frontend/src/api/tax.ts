/** 税务取数 API 客户端：从凭证/工资/合同实时汇总增值税、个税、印花税。 */
import request from '@/utils/request'
import type { TaxSummaryDetail, IndividualTax, StampTax, TaxWorkbench } from '@/types/tax'

/** 发票税务汇总：本期 KPI + 进项税额明细 + 月度趋势。period 形如 2026-07。 */
export function getTaxSummary(period?: string) {
  return request.get<TaxSummaryDetail>('/tax/summary', {
    params: period ? { period } : {},
  })
}

/** 个税申报：按员工 × 期间聚合工资单的个人所得税。period 形如 2026-07。 */
export function getIndividualTax(period?: string) {
  return request.get<IndividualTax>('/tax/individual', {
    params: period ? { period } : {},
  })
}

/** 印花税：销售 + 采购合同按金额 0.03% 计征（劳动合同免税已排除）。year 形如 2026。 */
export function getStampTax(year?: string) {
  return request.get<StampTax>('/tax/stamp', {
    params: year ? { year } : {},
  })
}

/** 税务工作台：聚合增值税 + 个税 + 印花税 的概览。period 形如 2026-07。 */
export function getTaxWorkbench(period?: string) {
  return request.get<TaxWorkbench>('/tax/workbench', {
    params: period ? { period } : {},
  })
}
