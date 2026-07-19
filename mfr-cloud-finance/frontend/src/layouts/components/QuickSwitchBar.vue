<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Close, CircleClose, RefreshRight } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useTabsStore } from '@/stores/tabs'

const route = useRoute()
const router = useRouter()
const tabsStore = useTabsStore()

onMounted(() => {
  tabsStore.init()
  tabsStore.openTab(route)
})

// 路由变化即把当前页加入快速切换面板，但不移动位置
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

function closeOthers(path: string) {
  tabsStore.closeOthers(path)
  router.push(path)
  ElMessage.success('已关闭其他标签')
}

function closeAll() {
  tabsStore.closeAll()
  router.push('/dashboard')
  ElMessage.success('已关闭全部标签')
}

function refresh(path: string) {
  hideMenu()
  if (path === route.path) {
    window.location.reload()
  } else {
    router.push(path).then(() => window.location.reload())
  }
}

/* ===== 右键菜单 ===== */
const menuVisible = ref(false)
const menuX = ref(0)
const menuY = ref(0)
const menuPath = ref('')

function showMenu(e: MouseEvent, path: string) {
  e.preventDefault()
  e.stopPropagation()
  menuPath.value = path
  menuX.value = e.clientX
  menuY.value = e.clientY
  menuVisible.value = true
}

function hideMenu() {
  menuVisible.value = false
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
        @contextmenu.prevent="showMenu($event, t.path)"
      >
        <span class="qs-dot" />
        <span class="qs-title">{{ t.title }}</span>
        <span class="qs-close" @click.stop="close(t.path)">
          <el-icon><Close /></el-icon>
        </span>
      </div>
    </div>

    <div class="qs-actions">
      <el-tooltip content="关闭其他标签" placement="bottom">
        <el-button text size="small" class="qs-action-btn" @click="closeOthers(route.path)">
          <el-icon><CircleClose /></el-icon>
        </el-button>
      </el-tooltip>
    </div>

    <!-- 右键菜单 -->
    <div
      v-show="menuVisible"
      v-click-outside="hideMenu"
      class="context-menu"
      :style="{ left: menuX + 'px', top: menuY + 'px' }"
    >
      <div class="menu-item" @click="refresh(menuPath)">
        <el-icon><RefreshRight /></el-icon> 刷新
      </div>
      <div class="menu-item" @click="close(menuPath); hideMenu()">
        <el-icon><Close /></el-icon> 关闭
      </div>
      <div class="menu-item" @click="closeOthers(menuPath); hideMenu()">
        <el-icon><CircleClose /></el-icon> 关闭其他
      </div>
      <div class="menu-item" @click="closeAll(); hideMenu()">
        <el-icon><CircleClose /></el-icon> 关闭全部
      </div>
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
  position: relative;
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

/* 右键菜单 */
.context-menu {
  position: fixed;
  z-index: 2000;
  min-width: 120px;
  padding: 4px 0;
  background: #fff;
  border-radius: 6px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.12);
  border: 1px solid var(--el-border-color-light);
}
.menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  font-size: 13px;
  color: var(--el-text-color-primary);
  cursor: pointer;
  transition: background 0.15s;
}
.menu-item:hover {
  background: var(--el-fill-color-light);
  color: var(--el-color-primary);
}
</style>
