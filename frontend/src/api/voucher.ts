/** 记账凭证状态机 API 客户端：审核 / 记账。 */
import request from '@/utils/request'

/**
 * 审核凭证：未审核 → 已审核（已审核/已记账幂等返回当前态）。
 * 对应后端 POST /api/vouchers/{id}/audit
 */
export function auditVoucher(id: number) {
  return request.post(`/vouchers/${id}/audit`)
}

/**
 * 记账凭证：已审核 → 已记账（未审核不可直接记账，后端返 400）。
 * 对应后端 POST /api/vouchers/{id}/post
 */
export function postVoucher(id: number) {
  return request.post(`/vouchers/${id}/post`)
}
