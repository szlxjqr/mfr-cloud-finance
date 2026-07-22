/** 税务取数 API 客户端：从凭证实时汇总进项/销项/应交增值税。 */
import request from '@/utils/request'
import type { TaxSummaryDetail } from '@/types/tax'

/** 发票税务汇总：本期 KPI + 进项税额明细 + 月度趋势。period 形如 2026-07。 */
export function getTaxSummary(period?: string) {
  return request.get<TaxSummaryDetail>('/tax/summary', {
    params: period ? { period } : {},
  })
}
