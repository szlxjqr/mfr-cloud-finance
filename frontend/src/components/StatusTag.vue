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
  /* 英文键（发票箱等既有） */
  draft: { text: '草稿', color: 'var(--status-draft)', bg: 'var(--el-color-info-light-9)' },
  pending: { text: '待识别', color: 'var(--el-color-info)', bg: 'var(--el-color-info-light-9)' },
  recognized: { text: '已识别', color: 'var(--el-color-primary)', bg: 'var(--el-color-primary-light-9)' },
  linked: { text: '已挂接', color: 'var(--el-color-success)', bg: 'var(--el-color-success-light-9)' },
  error: { text: '异常', color: 'var(--el-color-danger)', bg: 'var(--el-color-danger-light-9)' },
  approved: { text: '已通过', color: 'var(--status-approved)', bg: 'var(--el-color-success-light-9)' },
  paid: { text: '已支付', color: 'var(--status-paid)', bg: 'var(--el-color-primary-light-9)' },
  rejected: { text: '已驳回', color: 'var(--status-rejected)', bg: 'var(--el-color-danger-light-9)' },
  processing: { text: '处理中', color: 'var(--status-processing)', bg: 'var(--el-color-primary-light-9)' },
  success: { text: '成功', color: 'var(--success)', bg: 'var(--el-color-success-light-9)' },
  failed: { text: '失败', color: 'var(--danger)', bg: 'var(--el-color-danger-light-9)' },
  /* 中文键（业务单/合同/员工/资产/税务/凭证，全站状态词统一） */
  '草稿': { text: '草稿', color: 'var(--status-draft)', bg: 'var(--el-color-info-light-9)' },
  '待审批': { text: '待审批', color: 'var(--el-color-warning)', bg: 'var(--el-color-warning-light-9)' },
  '已通过': { text: '已通过', color: 'var(--status-approved)', bg: 'var(--el-color-success-light-9)' },
  '已驳回': { text: '已驳回', color: 'var(--status-rejected)', bg: 'var(--el-color-danger-light-9)' },
  '已支付': { text: '已支付', color: 'var(--status-paid)', bg: 'var(--el-color-primary-light-9)' },
  '已生效': { text: '已生效', color: 'var(--status-approved)', bg: 'var(--el-color-success-light-9)' },
  '在职': { text: '在职', color: 'var(--el-color-success)', bg: 'var(--el-color-success-light-9)' },
  '离职': { text: '离职', color: 'var(--el-color-info)', bg: 'var(--el-color-info-light-9)' },
  '禁用': { text: '禁用', color: 'var(--el-color-danger)', bg: 'var(--el-color-danger-light-9)' },
  '启用': { text: '启用', color: 'var(--el-color-success)', bg: 'var(--el-color-success-light-9)' },
  '使用中': { text: '使用中', color: 'var(--el-color-success)', bg: 'var(--el-color-success-light-9)' },
  '闲置': { text: '闲置', color: 'var(--el-color-warning)', bg: 'var(--el-color-warning-light-9)' },
  '已处置': { text: '已处置', color: 'var(--el-color-info)', bg: 'var(--el-color-info-light-9)' },
  '待申报': { text: '待申报', color: 'var(--el-color-warning)', bg: 'var(--el-color-warning-light-9)' },
  '已申报': { text: '已申报', color: 'var(--el-color-success)', bg: 'var(--el-color-success-light-9)' },
  '待提交': { text: '待提交', color: 'var(--el-color-info)', bg: 'var(--el-color-info-light-9)' },
  '已记账': { text: '已记账', color: 'var(--el-color-primary)', bg: 'var(--el-color-primary-light-9)' },
  '已审核': { text: '已审核', color: 'var(--el-color-success)', bg: 'var(--el-color-success-light-9)' },
  '待结算': { text: '待结算', color: 'var(--el-color-warning)', bg: 'var(--el-color-warning-light-9)' },
  '已结算': { text: '已结算', color: 'var(--el-color-primary)', bg: 'var(--el-color-primary-light-9)' },
  '已作废': { text: '已作废', color: 'var(--el-color-danger)', bg: 'var(--el-color-danger-light-9)' },
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
