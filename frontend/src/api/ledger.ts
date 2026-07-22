/** 会计核算 API 客户端：科目 / 凭证 / 余额汇总 / 账簿查询。 */
import request from '@/utils/request'
import type {
  AccountSubject,
  Voucher,
  SubjectBalance,
  VoucherGenerateResult,
  GeneralLedgerOut,
  SubsidiaryLedgerOut,
  LedgerSummaryRow,
  JournalOut,
} from '@/types/ledger'

/** 科目列表 */
export function listSubjects() {
  return request.get<AccountSubject[]>('/subjects')
}

/** 新增科目 */
export function createSubject(payload: Partial<AccountSubject>) {
  return request.post<AccountSubject>('/subjects', payload)
}

/** 科目余额表 */
export function getSubjectBalance(period?: string) {
  return request.get<SubjectBalance[]>('/subjects/balance', {
    params: period ? { period } : {},
  })
}

/** 重置为标准科目（开发/演示用，会清空凭证） */
export function resetSubjects() {
  return request.post<{ ok: boolean; message: string }>('/subjects/reset')
}

/** 凭证列表 */
export function listVouchers() {
  return request.get<Voucher[]>('/vouchers')
}

/** 凭证详情 */
export function getVoucher(id: number) {
  return request.get<Voucher>(`/vouchers/${id}`)
}

/** 一键从「已通过」业务单补生成凭证 */
export function syncVouchers() {
  return request.post<VoucherGenerateResult>('/vouchers/sync')
}

/** 总账（某科目，按期间汇总） */
export function getGeneralLedger(subjectCode: string, period?: string) {
  return request.get<GeneralLedgerOut>('/ledger/general', {
    params: { subject_code: subjectCode, ...(period ? { period } : {}) },
  })
}

/** 明细账（某科目，逐笔分录） */
export function getSubsidiaryLedger(subjectCode: string, period?: string) {
  return request.get<SubsidiaryLedgerOut>('/ledger/subsidiary', {
    params: { subject_code: subjectCode, ...(period ? { period } : {}) },
  })
}

/** 科目汇总表（期间感知，含树信息） */
export function getLedgerSummary(period?: string) {
  return request.get<LedgerSummaryRow[]>('/ledger/summary', {
    params: period ? { period } : {},
  })
}

/** 序时账（全部凭证分录流水） */
export function getJournal(period?: string) {
  return request.get<JournalOut>('/ledger/journal', {
    params: period ? { period } : {},
  })
}
