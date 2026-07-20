/**
 * 通用格式化工具函数
 */

/**
 * 格式化金额：千分位 + 两位小数 + 元单位
 * @param value 数值
 * @returns 例如：1,234,567.89元
 */
export function formatCurrency(value: number): string {
  const safe = Number.isFinite(value) ? value : 0
  const formatted = safe.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
  return `${formatted}元`
}

/**
 * 格式化数字：千分位（最多保留两位小数）
 * @param value 数值
 * @returns 例如：1,234,567.89
 */
export function formatNumber(value: number): string {
  const safe = Number.isFinite(value) ? value : 0
  return safe.toLocaleString('zh-CN', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  })
}
