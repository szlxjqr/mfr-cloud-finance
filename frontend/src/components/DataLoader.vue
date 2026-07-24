<script setup lang="ts">
import { computed } from 'vue'
import EmptyState from './EmptyState.vue'

const props = withDefaults(
  defineProps<{
    /** 加载中 */
    loading?: boolean
    /** 错误信息（非空即进入错误态） */
    error?: string | null
    /** 数据为空（非加载、非错误时生效） */
    isEmpty?: boolean
    /** 空态标题 */
    emptyTitle?: string
    /** 空态说明 */
    emptyDescription?: string
    /** 空态图标名 */
    emptyIcon?: string
    /** 加载文案 */
    loadingText?: string
  }>(),
  {
    loading: false,
    error: null,
    isEmpty: false,
    emptyTitle: '暂无数据',
    emptyDescription: '',
    emptyIcon: 'DocumentDelete',
    loadingText: '加载中…',
  },
)

const showEmpty = computed(() => !props.loading && !props.error && props.isEmpty)
const showError = computed(() => !props.loading && !!props.error)
</script>

<template>
  <div class="data-loader">
    <!-- 加载态 -->
    <div v-if="loading" class="data-loader__state">
      <el-icon class="is-loading" :size="28"><Loading /></el-icon>
      <span class="data-loader__text">{{ loadingText }}</span>
    </div>

    <!-- 错误态 -->
    <div v-else-if="showError" class="data-loader__state">
      <el-icon :size="40" class="data-loader__error-icon"><WarningFilled /></el-icon>
      <p class="data-loader__text">{{ error }}</p>
      <div v-if="$slots.error" class="data-loader__error-action">
        <slot name="error" />
      </div>
    </div>

    <!-- 空态 -->
    <EmptyState
      v-else-if="showEmpty"
      :icon="emptyIcon"
      :title="emptyTitle"
      :description="emptyDescription"
    >
      <template v-if="$slots.empty" #action><slot name="empty" /></template>
    </EmptyState>

    <!-- 正常内容 -->
    <slot v-else />
  </div>
</template>

<style scoped>
.data-loader__state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-6) var(--space-4);
  color: var(--text-muted);
  min-height: 160px;
}
.data-loader__text {
  font-size: var(--fs-sm);
  margin: 0;
}
.data-loader__error-icon {
  color: var(--el-color-danger);
}
.data-loader__error-action {
  margin-top: var(--space-2);
}
</style>
