<script setup lang="ts">
/**
 * 共享 KPI 卡片（全站统一，替代原先 5 套内联/变体实现）
 * - 顶部 5px 彩色条 + 大数字，颜色来自 design-tokens（--kpi-* / --warning 等）
 * - 支持 prefix/suffix（行内）、unit（小字单位，如 元/人/份）
 * - isZero 自动置灰（避免空数据抢镜）；tint 叠加同色淡底强化主视觉
 */
const props = withDefaults(
  defineProps<{
    label: string
    number: string | number
    prefix?: string
    suffix?: string
    unit?: string
    color: string
    isZero?: boolean
    tint?: boolean
  }>(),
  { prefix: '', suffix: '', unit: '', isZero: false, tint: false },
)
</script>

<template>
  <div
    class="kpi-card"
    :class="{ 'is-zero': isZero, 'is-tint': tint }"
    :style="{ '--accent': color }"
  >
    <div class="kpi-card__accent"></div>
    <div class="kpi-card__body">
      <div class="kpi-card__label">{{ label }}</div>
      <div class="kpi-card__value">
        <span v-if="prefix" class="kpi-card__prefix">{{ prefix }}</span>
        <span class="kpi-card__number">{{ number }}</span>
        <span v-if="suffix" class="kpi-card__suffix">{{ suffix }}</span>
      </div>
      <div v-if="unit" class="kpi-card__unit">{{ unit }}</div>
    </div>
  </div>
</template>

<style scoped>
.kpi-card {
  position: relative;
  background: var(--bg-surface);
  border: 1px solid var(--border-soft);
  border-radius: var(--r-lg);
  box-shadow: var(--sh-card);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: transform var(--motion-base) var(--ease),
    box-shadow var(--motion-base) var(--ease);
}
.kpi-card:hover {
  box-shadow: var(--sh-pop);
  transform: translateY(-2px);
}
/* hero 卡：同色淡底叠加，强化主视觉但不喧宾夺主 */
.kpi-card.is-tint::after {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--accent);
  opacity: 0.05;
  pointer-events: none;
}
.kpi-card__accent {
  height: 5px;
  width: 100%;
  flex-shrink: 0;
  background: var(--accent);
}
.kpi-card__body {
  position: relative;
  z-index: 1;
  padding: 22px 24px 26px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 10px;
}
.kpi-card__label {
  font-size: var(--fs-sm);
  color: var(--text-muted);
  line-height: var(--lh-tight);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.kpi-card__value {
  display: flex;
  align-items: baseline;
  gap: 4px;
  color: var(--accent);
  line-height: 1;
}
.kpi-card__number {
  font-size: 30px; /* 驾驶舱指标统一字号 */
  font-weight: 700;
  letter-spacing: -0.8px;
  font-variant-numeric: tabular-nums;
}
.kpi-card__prefix,
.kpi-card__suffix {
  font-size: var(--fs-lg);
  font-weight: 600;
  opacity: 0.85;
}
.kpi-card__unit {
  font-size: var(--fs-xs);
  color: var(--text-muted);
  opacity: 0.85;
}
.kpi-card.is-zero .kpi-card__value {
  color: var(--text-muted) !important;
}
.kpi-card.is-zero .kpi-card__prefix,
.kpi-card.is-zero .kpi-card__suffix {
  opacity: 1;
}
</style>
