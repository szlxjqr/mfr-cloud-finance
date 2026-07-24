<script setup lang="ts">
withDefaults(
  defineProps<{
    /** Element Plus 图标组件名，如 'Money' / 'Document' / 'Tickets' */
    name: string
    /** 尺寸 */
    size?: number | string
    /** 颜色，默认 inherit（跟随文字） */
    color?: string
  }>(),
  { size: 18, color: 'inherit' },
)
</script>

<template>
  <el-icon :size="size" :color="color" class="app-icon">
    <component :is="name" />
  </el-icon>
</template>

<style scoped>
.app-icon {
  vertical-align: middle;
}
</style>
