<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    /** Element Plus 图标组件名，如 'DocumentDelete' / 'Folder' / 'Tickets' */
    icon?: string
    /** 主标题 */
    title?: string
    /** 辅助说明 */
    description?: string
    /** 图标尺寸 */
    size?: number
  }>(),
  {
    icon: 'DocumentDelete',
    title: '暂无数据',
    description: '',
    size: 48,
  },
)

const iconName = computed(() => props.icon)
</script>

<template>
  <div class="empty-state">
    <el-icon :size="size" class="empty-state__icon">
      <component :is="iconName" />
    </el-icon>
    <p class="empty-state__title">{{ title }}</p>
    <p v-if="description" class="empty-state__desc">{{ description }}</p>
    <div v-if="$slots.action" class="empty-state__action">
      <slot name="action" />
    </div>
    <slot />
  </div>
</template>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-6) var(--space-4);
  text-align: center;
  color: var(--text-muted);
}
.empty-state__icon {
  color: var(--text-faint);
  margin-bottom: var(--space-3);
}
.empty-state__title {
  font-size: var(--fs-md);
  font-weight: 500;
  color: var(--text-base);
  margin: 0 0 var(--space-1);
}
.empty-state__desc {
  font-size: var(--fs-sm);
  color: var(--text-muted);
  margin: 0;
  max-width: 320px;
  line-height: var(--lh-base);
}
.empty-state__action {
  margin-top: var(--space-3);
}
</style>
