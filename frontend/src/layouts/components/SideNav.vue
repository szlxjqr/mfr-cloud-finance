<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { menuItems } from '../menuConfig'

const appStore = useAppStore()
const route = useRoute()
const router = useRouter()

/** 每个一级菜单的展开状态 */
const expandedKeys = ref<Set<string>>(new Set())

/** 根据当前路由自动展开对应的一级菜单 */
function autoExpand() {
  const path = route.path
  for (const item of menuItems) {
    if (item.groups) {
      for (const g of item.groups) {
        if (g.children.some(c => path === c.path || path.startsWith(c.path + '/'))) {
          expandedKeys.value.add(item.module || item.title)
          return
        }
      }
    }
  }
}

// 路由变化时自动展开
watch(() => route.path, autoExpand, { immediate: true })

const asideWidth = computed(() => (appStore.sidebarCollapsed ? '64px' : '240px'))

function toggleExpand(item: typeof menuItems[number]) {
  const key = item.module || item.title
  if (expandedKeys.value.has(key)) {
    expandedKeys.value.delete(key)
  } else {
    expandedKeys.value.add(key)
  }
  // force reactivity
  expandedKeys.value = new Set(expandedKeys.value)
}

function isExpanded(item: typeof menuItems[number]): boolean {
  return expandedKeys.value.has(item.module || item.title)
}

/** 判断某个子菜单项是否是当前激活的路由 */
function isSubActive(subPath: string): boolean {
  return route.path === subPath || route.path.startsWith(subPath + '/')
}

/** 判断一级菜单是否有子项处于激活态 */
function hasActiveChild(item: typeof menuItems[number]): boolean {
  if (!item.groups) return false
  return item.groups.some(g => g.children.some(c => isSubActive(c.path)))
}

function navigateTo(path: string) {
  router.push(path)
}

function handleClick(item: typeof menuItems[number]) {
  // 如果有子菜单，切换展开；否则直接导航
  if (item.groups && item.groups.length > 0) {
    toggleExpand(item)
  } else if (item.path) {
    navigateTo(item.path)
  } else if (item.module) {
    // 没有子菜单但有 module，导航到模块首页
    router.push('/' + item.module)
  }
}
</script>

<template>
  <el-aside :width="asideWidth" class="side-aside">
    <!-- 品牌区 -->
    <div class="side-logo">
      <img src="/logo.png" alt="智慧经营" class="logo-img" />
      <span v-show="!appStore.sidebarCollapsed" class="logo-text">智慧经营</span>
    </div>

    <!-- 手风琴菜单 -->
    <el-scrollbar class="side-scroll">
      <div class="menu-list">
        <!-- 首页（特殊处理，无子菜单） -->
        <div
          v-for="item in menuItems"
          :key="item.module || item.path || item.title"
          class="menu-group"
        >
          <!-- 一级菜单项 -->
          <div
            :class="['menu-item', { expanded: isExpanded(item), 'has-active': hasActiveChild(item) }]"
            @click="handleClick(item)"
          >
            <div class="menu-item-left">
              <AppIcon v-if="item.icon" :size="18" class="menu-icon" :name="item.icon" />
              <span v-show="!appStore.sidebarCollapsed" class="menu-title">{{ item.title }}</span>
            </div>
            <!-- 展开/折叠箭头（仅在有子菜单且未折叠时显示） -->
            <svg
              v-if="item.groups?.length && !appStore.sidebarCollapsed"
              :class="['arrow', { rotated: isExpanded(item) }]"
              viewBox="0 0 24 24"
              width="16"
              height="16"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </div>

          <!-- 二级子菜单（展开时显示） -->
          <transition name="slide">
            <div v-if="isExpanded(item) && item.groups && !appStore.sidebarCollapsed" class="sub-menu">
              <template v-for="group in item.groups" :key="group.title">
                <div
                  v-for="sub in group.children"
                  :key="sub.path"
                  :class="['sub-item', { active: isSubActive(sub.path) }]"
                  @click.stop="navigateTo(sub.path)"
                >
                  {{ sub.title }}
                </div>
              </template>
            </div>
          </transition>
        </div>
      </div>
    </el-scrollbar>
  </el-aside>
</template>

<style scoped>
/* ============================================
   侧边栏 —— 深色手风琴风格（参考企业管理系统 UI）
   ============================================ */
.side-aside {
  display: flex;
  flex-direction: column;
  height: 100vh;
  /* 深色背景 */
  background: #0d1b2a;
  transition: width 0.25s ease;
  overflow: hidden;
  user-select: none;
}

/* ---- 品牌区 ---- */
.side-logo {
  height: 56px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 0 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.logo-img {
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  border-radius: 6px;
  object-fit: contain;
  background: rgba(255, 255, 255, 0.08);
  padding: 2px;
}
.logo-text {
  font-size: 16px;
  font-weight: 650;
  color: #e8edf5;
  letter-spacing: 0.5px;
  white-space: nowrap;
  overflow: hidden;
}

/* ---- 滚动区 ---- */
.side-scroll {
  flex: 1;
  min-height: 0;
}
.side-scroll :deep(.el-scrollbar__bar) {
  opacity: 0;
  transition: opacity 0.2s;
}
.side-scroll:hover :deep(.el-scrollbar__bar) {
  opacity: 1;
}

/* ---- 菜单容器 ---- */
.menu-list {
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

/* ---- 一级菜单项 ---- */
.menu-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 46px;
  padding: 0 14px;
  border-radius: 8px;
  cursor: pointer;
  color: #8b9cb8;
  transition: all 0.18s ease;
  user-select: none;
}
.menu-item:hover {
  color: #c4d3e8;
  background: rgba(255, 255, 255, 0.05);
}
.menu-item:hover .menu-icon {
  color: #c4d3e8;
}
.menu-item.expanded,
.menu-item.has-active {
  color: #e8edf5;
}
.menu-item.expanded .menu-icon,
.menu-item.has-active .menu-icon {
  color: #e8edf5;
}

.menu-item-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.menu-icon {
  color: #5a6b85;
  flex-shrink: 0;
  transition: color 0.18s ease;
}

.menu-title {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 右侧箭头 */
.arrow {
  color: #5a6b85;
  transition: transform 0.25s ease, color 0.18s ease;
  flex-shrink: 0;
}
.arrow.rotated {
  transform: rotate(180deg);
  color: #8b9cb8;
}
.menu-item:hover .arrow {
  color: #c4d3e8;
}

/* ---- 二级子菜单 ---- */
.sub-menu {
  padding: 4px 0 8px 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sub-item {
  height: 40px;
  display: flex;
  align-items: center;
  padding: 0 16px 0 44px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13.5px;
  font-weight: 400;
  color: #8b9cb8;
  transition: all 0.15s ease;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.sub-item:hover {
  color: #c4d3e8;
  background: rgba(255, 255, 255, 0.04);
}

/* 选中态：蓝色圆角背景 + 白字 */
.sub-item.active {
  background: #1667ff;
  color: #ffffff;
  font-weight: 500;
}
.sub-item.active:hover {
  background: #337dff;
  color: #ffffff;
}

/* ---- 展开动画 ---- */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}
.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}
.slide-enter-to,
.slide-leave-from {
  opacity: 1;
  max-height: 600px;
}

/* ---- 折叠态：仅图标 ---- */
:global(.sidebar-collapsed) .side-aside {
  width: 64px !important;
}
</style>
