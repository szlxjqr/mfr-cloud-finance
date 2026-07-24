<script setup lang="ts">
withDefaults(
  defineProps<{
    /** 已选中数量 */
    selectedCount?: number
    /** 布局：between=左右分布，left=左对齐 */
    align?: 'left' | 'between'
  }>(),
  { selectedCount: 0, align: 'between' },
)

const emit = defineEmits<{ (e: 'clear'): void }>()
</script>

<template>
  <transition name="batch-bar-fade">
    <div v-show="selectedCount > 0" class="batch-bar" :class="`batch-bar--${align}`">
      <span class="batch-bar__count">已选 <b>{{ selectedCount }}</b> 项</span>
      <div class="batch-bar__actions">
        <slot />
      </div>
      <button class="batch-bar__clear" type="button" @click="emit('clear')">
        取消选择
      </button>
    </div>
  </transition>
</template>

<style scoped>
.batch-bar {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-4);
  margin-bottom: var(--space-3);
  background: var(--el-color-primary-light-9);
  border: 1px solid var(--el-color-primary-light-7);
  border-radius: var(--r-md);
}
.batch-bar--between {
  justify-content: space-between;
}
.batch-bar--left {
  justify-content: flex-start;
}
.batch-bar__count {
  font-size: var(--fs-sm);
  color: var(--text-base);
  white-space: nowrap;
}
.batch-bar__count b {
  color: var(--el-color-primary);
  font-size: var(--fs-md);
  margin: 0 2px;
}
.batch-bar__actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex: 1;
  flex-wrap: wrap;
}
.batch-bar__clear {
  border: none;
  background: transparent;
  color: var(--text-muted);
  font-size: var(--fs-sm);
  cursor: pointer;
  padding: var(--space-1) var(--space-2);
  border-radius: var(--r-sm);
  transition: all var(--motion-base) var(--ease);
  white-space: nowrap;
}
.batch-bar__clear:hover {
  color: var(--el-color-danger);
  background: var(--el-color-danger-light-9);
}
.batch-bar-fade-enter-active,
.batch-bar-fade-leave-active {
  transition: opacity var(--motion-base) var(--ease), transform var(--motion-base) var(--ease);
}
.batch-bar-fade-enter-from,
.batch-bar-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
