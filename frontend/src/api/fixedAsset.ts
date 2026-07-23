import http from '@/utils/request'
import type { FixedAsset, AssetSummary, DepRecord, DepPreviewItem } from '@/types/fixedAsset'

export const assetApi = {
  // 资产总览（总原值/累计折旧/净值/在用数）
  summary: () => http.get<AssetSummary>('/fixed-assets/summary'),
  // 折旧预览（某期间各在用资产应计提额，不落库）
  depreciatePreview: (period: string) =>
    http.get<DepPreviewItem[]>('/fixed-assets/depreciate-preview', { params: { period } }),
  // 列表
  list: (params?: { keyword?: string; status?: string; category?: string; department?: string }) =>
    http.get<FixedAsset[]>('/fixed-assets', { params }),
  get: (id: number) => http.get<FixedAsset>(`/fixed-assets/${id}`),
  nextNo: () => http.get<{ asset_no: string }>('/fixed-assets/next-no'),
  create: (data: Partial<FixedAsset>) => http.post<FixedAsset>('/fixed-assets', data),
  update: (id: number, data: Partial<FixedAsset>) =>
    http.put<FixedAsset>(`/fixed-assets/${id}`, data),
  remove: (id: number) => http.delete(`/fixed-assets/${id}`),
  // 折旧记录
  depRecords: (id: number) => http.get<DepRecord[]>(`/fixed-assets/${id}/dep-records`),
  // 入账：生成购置凭证，状态→在用
  record: (id: number, data?: { maker?: string; action_date?: string }) =>
    http.post<{ asset: FixedAsset; voucher_no: string | null; skipped: boolean }>(
      `/fixed-assets/${id}/record`,
      data || {},
    ),
  // 计提折旧：按期间汇总生成一张凭证
  depreciate: (data: { period: string; maker?: string }) =>
    http.post<{ voucher_no: string | null; count: number; total: number; skipped: boolean; message?: string }>(
      '/fixed-assets/depreciate',
      data,
    ),
  // 处置：生成清理凭证，状态→已处置
  dispose: (id: number, data?: { maker?: string; action_date?: string }) =>
    http.post<{ asset: FixedAsset; voucher_no: string | null; skipped: boolean }>(
      `/fixed-assets/${id}/dispose`,
      data || {},
    ),
}
