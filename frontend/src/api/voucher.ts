/** 记账凭证 API 客户端：状态机（审核/记账/反审核/反记账）+ 手工录入。 */
import request from '@/utils/request'

/** 手工凭证分录（写入用） */
export interface VoucherEntryCreate {
  subject_code: string
  summary?: string
  direction: '借' | '贷'
  amount: number
}

/** 手工录入凭证（写入用） */
export interface VoucherCreate {
  voucher_date: string            // YYYY-MM-DD
  voucher_word?: string        // 记/收/付/转
  attach_count?: number
  maker?: string
  summary?: string
  entries: VoucherEntryCreate[]
}

/**
 * 手工录入凭证：独立 source_type='手工'，借贷平衡 + 至少 2 条分录。
 * 对应后端 POST /api/vouchers
 */
export function createVoucher(payload: VoucherCreate) {
  return request.post('/vouchers', payload)
}

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

/**
 * 反记账：已记账 → 已审核（释放记账锁定，仍在账簿中）。
 * 对应后端 POST /api/vouchers/{id}/unpost
 */
export function unpostVoucher(id: number) {
  return request.post(`/vouchers/${id}/unpost`)
}

/**
 * 反审核：已审核 → 未审核（拉出账簿）；已记账须先反记账。
 * 对应后端 POST /api/vouchers/{id}/unaudit
 */
export function unauditVoucher(id: number) {
  return request.post(`/vouchers/${id}/unaudit`)
}
