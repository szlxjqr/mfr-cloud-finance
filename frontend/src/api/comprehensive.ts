import http from '@/utils/request'
import type { ComprehensiveOverview } from '@/types/comprehensive'

/** 综合报表看板：跨模块一次性聚合（资金/经营/税务/业务/凭证） */
export function getComprehensiveOverview(period?: string) {
  return http.get<ComprehensiveOverview>('/comprehensive/overview', {
    params: period ? { period } : {},
  })
}
