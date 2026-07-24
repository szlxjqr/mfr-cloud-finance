<script setup lang="ts">
import { computed } from 'vue'
import AppIcon from './AppIcon.vue'

type Accent = 'brand' | 'success' | 'warning' | 'danger' | 'info'

const props = withDefaults(
  defineProps<{
    /** 指标名 */
    label: string
    /** 指标值（已格式化好的字符串或数字） */
    value: string | number
    /** 同比/环比变化量；传 null 表示不展示 */
    delta?: number | null
    /** 变化量后缀，如 '%' / '万' */
    deltaLabel?: string
    /** 图标名（Element Plus 图标组件名） */
    icon?: string
    /** 强调色 */
    accent?: Accent
  }>(),
  { delta: null, deltaLabel: '', icon: '', accent: 'brand' },
)

const deltaDir = computed<'up' | 'down' | 'none'>(() =>
  props.delta == null ? 'none' : props.delta >= 0 ? 'up' : 'down',
)
const accentVar = computed(
  () =>
    ({
      brand: 'var(--brand)',
      success: 'var(--success)',
      warning: 'var(--warning)',
      danger: 'var(--danger)',
      info: 'var(--info)',
    })[props.accent],
)
</script>

<template>
  <div class="kpi-tile" :style="{ '--kpi-accent': accentVar }">
    <div class="kpi-tile__head">
      <span class="kpi-tile__label">{{ label }}</span>
      <span v-if="icon" class="kpi-tile__icon">
        <AppIcon :name="icon" :size="18" :color="accentVar" />
      </span>
    </div>
    <div class="kpi-tile__value">{{ value }}</div>
    <div v-if="delta !== null" class="kpi-tile__delta" :class="`is-${deltaDir}`">
      <el-icon :size="14">
        <component :is="deltaDir === 'up' ? 'CaretTop' : 'CaretBottom'" />
      </el-icon>
      <span>{{ Math.abs(delta) }}{{ deltaLabel }}</span>
    </div>
  </div>
</template>

<style scoped>
.kpi-tile {
  background: var(--bg-surface);
  border: 1px solid var(--border-soft);
  border-left: 3px solid var(--kpi-accent);
  border-radius: var(--r-md);
  box-shadow: var(--sh-card);
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  transition: box-shadow var(--motion-base) var(--ease);
}
.kpi-tile:hover {
  box-shadow: var(--sh-pop);
}
.kpi-tile__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.kpi-tile__label {
  font-size: var(--fs-sm);
  color: var(--text-muted);
}
.kpi-tile__icon {
  display: inline-flex;
}
.kpi-tile__value {
  font-size: var(--fs-xl);
  font-weight: 600;
  color: var(--text-strong);
  line-height: var(--lh-tight);
  font-variant-numeric: tabular-nums;
}
.kpi-tile__delta {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  font-size: var(--fs-xs);
  font-weight: 500;
}
.kpi-tile__delta.is-up {
  color: var(--success);
}
.kpi-tile__delta.is-down {
  color: var(--danger);
}
</style>
