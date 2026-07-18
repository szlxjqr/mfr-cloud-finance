import axios from 'axios'
import type {
  DashboardSummary,
  FundItem,
  RevenueDataPoint,
  TaxItem,
} from '@/types/dashboard'

/** 创建 axios 实例 */
const http = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器：自动携带鉴权 token
http.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// 响应拦截器：统一处理错误
http.interceptors.response.use(
  (response) => response,
  (error) => {
    // 此处可接入统一的错误提示（如 ElMessage）
    return Promise.reject(error)
  },
)

/** 获取仪表盘汇总数据 */
export function getDashboardSummary() {
  return http.get<DashboardSummary>('/dashboard/summary')
}

/** 获取资金概览 */
export function getFundsOverview() {
  return http.get<FundItem[]>('/dashboard/funds')
}

/** 获取经营/收入趋势 */
export function getRevenueTrend() {
  return http.get<RevenueDataPoint[]>('/dashboard/revenue-trend')
}

/** 获取税费概览 */
export function getTaxOverview() {
  return http.get<TaxItem[]>('/dashboard/tax')
}

/** 获取指定月份的凭证总数 */
export function getVoucherCount(month?: string) {
  return http.get<number>('/dashboard/voucher-count', { params: { month } })
}

export default http
