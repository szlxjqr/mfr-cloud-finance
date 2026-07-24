<script setup lang="ts">
import { computed } from 'vue'

type StatusKey =
  | 'draft'
  | 'pending'
  | 'approved'
  | 'paid'
  | 'rejected'
  | 'processing'
  | 'success'
  | 'failed'

const props = withDefaults(
  defineProps<{
    /** 状态键，命中内置映射；也可传任意字符串（走兜底） */
    status: StatusKey | string
    /** 自定义文案，优先级高于内置 */
    label?: string
  }>(),
  { label: '' },
)

const MAP: Record<string, { text: string; color: string; bg: string }> = {
  draft: { text: '草稿', color: 'var(--status-draft)', bg: 'var(--el-color-info-light-9)' },
  pending: { text: '待处理', color: 'var(--status-pending)', bg: 'var(--el-color-warning-light-9)' },
  approved: { text: '已通过', color: 'var(--status-approved)', bg: 'var(--el-color-success-light-9)' },
  paid: { text: '已支付', color: 'var(--status-paid)', bg: 'var(--el-color-primary-light-9)' },
  rejected: { text: '已驳回', color: 'var(--status-rejected)', bg: 'var(--el-color-danger-light-9)' },
  processing: { text: '处理中', color: 'var(--status-processing)', bg: 'var(--el-color-primary-light-9)' },
  success: { text: '成功', color: 'var(--success)', bg: 'var(--el-color-success-light-9)' },
  failed: { text: '失败', color: 'var(--danger)', bg: 'var(--el-color-danger-light-9)' },
}

const meta = computed(
  () => MAP[props.status] ?? { text: props.label || props.status, color: 'var(--text-muted)', bg: 'var(--bg-subtle)' },
)
const text = computed(() => props.label || meta.value.text)
</script>

<template>
  <span class="status-tag" :style="{ color: meta.color, background: meta.bg }">
    <i class="status-tag__dot" :style="{ background: meta.color }" />
    {{ text }}
  </span>
</template>

<style scoped>
.status-tag {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 2px 10px;
  border-radius: var(--r-pill);
  font-size: var(--fs-xs);
  font-weight: 500;
  line-height: 1.6;
  white-space: nowrap;
}
.status-tag__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex: none;
}
</style>
