export type AssetStatus = '未入账' | '在用' | '闲置' | '已处置'

export interface FixedAsset {
  id: number
  asset_no?: string | null
  name: string
  category?: string | null
  department?: string | null
  acquisition_date?: string | null
  original_value?: number | null
  salvage_rate?: number | null
  useful_life?: number | null
  dep_subject_code?: string | null
  accum_dep?: number | null
  status: AssetStatus
  record_date?: string | null
  record_voucher_no?: string | null
  dispose_date?: string | null
  dispose_voucher_no?: string | null
  monthly_dep?: number | null // 派生：当月折旧额
  net_value?: number | null // 派生：净值 = 原值 − 累计折旧
  remark?: string | null
}

export interface DepRecord {
  id: number
  asset_id: number
  period: string
  amount?: number | null
  voucher_no?: string | null
}

export interface AssetSummary {
  total_original: number
  total_accum_dep: number
  total_net: number
  in_use_count: number
  total_count: number
}

export interface DepPreviewItem {
  id: number
  asset_no?: string | null
  name?: string | null
  category?: string | null
  department?: string | null
  original_value: number
  accum_dep: number
  monthly_dep: number
  net_value: number
  dep_subject_code: string
}

export const ASSET_CATEGORIES = ['房屋建筑物', '机器设备', '办公设备', '运输工具', '电子设备', '其他']
export const DEP_SUBJECTS = [
  { code: '5602', name: '管理费用' },
  { code: '4301', name: '研发支出' },
]
