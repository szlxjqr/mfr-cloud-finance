<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Close, CircleClose } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useTabsStore } from '@/stores/tabs'

const route = useRoute()
const router = useRouter()
const tabsStore = useTabsStore()

onMounted(() => {
  tabsStore.init()
  tabsStore.openTab(route)
})

// 路由变化即把当前页加入快速切换面板
watch(
  () => route.path,
  () => tabsStore.openTab(route),
)

function go(path: string) {
  if (path !== route.path) router.push(path)
}

function close(path: string) {
  const target = tabsStore.closeTab(path)
  if (target) router.push(target)
}

function closeOthers() {
  tabsStore.closeOthers(route.path)
  ElMessage.success('已关闭其他标签')
}
</script>

<template>
  <div class="quick-switch">
    <div class="qs-scroll">
      <div
        v-for="t in tabsStore.openedTabs"
        :key="t.path"
        class="qs-tab"
        :class="{ active: t.path === route.path }"
        :title="t.group ? `${t.title}（${t.group}）` : t.title"
        @click="go(t.path)"
      >
        <span class="qs-dot" />
        <span class="qs-title">{{ t.title }}</span>
        <span
          v-if="!t.fixed"
          class="qs-close"
          @click.stop="close(t.path)"
        >
          <el-icon><Close /></el-icon>
        </span>
      </div>
    </div>

    <div class="qs-actions">
      <el-tooltip content="关闭其他标签" placement="bottom">
        <el-button text size="small" class="qs-action-btn" @click="closeOthers">
          <el-icon><CircleClose /></el-icon>
        </el-button>
      </el-tooltip>
    </div>
  </div>
</template>

<style scoped>
.quick-switch {
  display: flex;
  align-items: center;
  height: 40px;
  flex-shrink: 0;
  background: #fff;
  border-bottom: 1px solid var(--el-border-color-light);
  padding: 0 10px;
  gap: 8px;
}

.qs-scroll {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  height: 100%;
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: thin;
}
.qs-scroll::-webkit-scrollbar {
  height: 4px;
}
.qs-scroll::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 2px;
}

/* 单个标签（程序坞药丸风格） */
.qs-tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 28px;
  padding: 0 10px;
  border-radius: 14px;
  background: #f4f4f5;
  color: #606266;
  font-size: 13px;
  white-space: nowrap;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.18s ease;
  user-select: none;
  flex-shrink: 0;
}
.qs-tab:hover {
  background: #e9e9eb;
  color: #303133;
}
.qs-tab.active {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  border-color: var(--el-color-primary-light-5);
  font-weight: 600;
}

.qs-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.55;
  flex-shrink: 0;
}
.qs-tab.active .qs-dot {
  opacity: 1;
}

.qs-title {
  line-height: 1;
}

.qs-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  font-size: 12px;
  color: #909399;
  transition: all 0.15s;
}
.qs-close:hover {
  background: var(--el-color-danger);
  color: #fff;
}

.qs-actions {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  border-left: 1px solid var(--el-border-color-lighter);
  padding-left: 8px;
}
.qs-action-btn {
  color: #909399;
}
.qs-action-btn:hover {
  color: var(--el-color-primary);
}
</style>
