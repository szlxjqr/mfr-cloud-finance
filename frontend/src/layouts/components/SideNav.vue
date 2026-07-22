<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { menuItems } from '../menuConfig'

const appStore = useAppStore()
const route = useRoute()
const router = useRouter()

/** 根据当前路由计算所属模块 */
const activeModule = computed<string>(() => {
  const path = route.path
  const item = menuItems.find((m) => m.module && path.startsWith('/' + m.module))
  return item?.module || ''
})

const asideWidth = computed(() => (appStore.sidebarCollapsed ? '64px' : '200px'))

function handleClick(item: typeof menuItems[number]) {
  if (item.path) {
    router.push(item.path)
  } else if (item.module) {
    router.push('/' + item.module)
  }
}

function isActive(item: typeof menuItems[number]): boolean {
  if (item.module) return activeModule.value === item.module
  return item.path ? route.path === item.path : false
}
</script>

<template>
  <el-aside :width="asideWidth" class="side-aside">
    <!-- 品牌区 -->
    <div class="side-logo">
      <img src="/logo.png" alt="智慧经营" class="logo-img" />
      <span v-show="!appStore.sidebarCollapsed" class="logo-text">智慧经营</span>
    </div>

    <!-- 一级模块菜单 -->
    <el-scrollbar class="side-scroll">
      <ul class="module-menu">
        <li
          v-for="item in menuItems"
          :key="item.module || item.path"
          :class="['module-item', { active: isActive(item), collapsed: appStore.sidebarCollapsed }]"
          @click="handleClick(item)"
        >
          <el-icon v-if="item.icon" :size="20" class="module-icon">
            <component :is="item.icon" />
          </el-icon>
          <span v-if="!appStore.sidebarCollapsed" class="module-title">{{ item.title }}</span>
          <span v-if="!appStore.sidebarCollapsed && item.badge" class="module-badge">{{ item.badge }}</span>
        </li>
      </ul>
    </el-scrollbar>
  </el-aside>
</template>

<style scoped>
.side-aside {
  display: flex;
  flex-direction: column;
  height: 100vh;
  /* 深色科技渐变底 */
  background: linear-gradient(180deg, #0e1726 0%, #16233b 100%);
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  transition: width 0.2s ease;
  overflow: hidden;
  user-select: none;
}

/* 品牌区 */
.side-logo {
  height: 56px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 0 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.logo-img {
  width: 30px;
  height: 30px;
  flex-shrink: 0;
  border-radius: 8px;
  object-fit: contain;
  background: rgba(255, 255, 255, 0.08);
  padding: 3px;
}
.logo-text {
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.5px;
  white-space: nowrap;
  overflow: hidden;
}

/* 菜单滚动区 */
.side-scroll {
  flex: 1;
  min-height: 0;
}
.module-menu {
  list-style: none;
  margin: 0;
  padding: 14px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

/* 一级模块项 */
.module-item {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 46px;
  padding: 0 14px;
  border-radius: 10px;
  cursor: pointer;
  color: rgba(255, 255, 255, 0.68);
  transition: all 0.15s ease;
  position: relative;
}
.module-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}
.module-item:hover .module-icon {
  color: #fff;
}

.module-icon {
  color: rgba(255, 255, 255, 0.6);
  flex-shrink: 0;
  transition: color 0.15s ease;
}
.module-title {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
}
.module-badge {
  font-size: 11px;
  color: #fff;
  background: #ff9c4b;
  border-radius: 10px;
  padding: 2px 8px;
  line-height: 1;
  flex-shrink: 0;
}

/* 选中态：左侧品牌竖条 + 浅蓝底 + 光晕 */
.module-item.active {
  background: rgba(47, 107, 255, 0.18);
  color: #fff;
  font-weight: 600;
  box-shadow: inset 3px 0 0 0 var(--brand), 0 4px 14px rgba(47, 107, 255, 0.28);
}
.module-item.active .module-icon {
  color: #9db8ff;
}
.module-item.active .module-badge {
  background: #fff;
  color: var(--brand-strong);
}

/* 折叠态：仅图标 */
.module-item.collapsed {
  justify-content: center;
  padding: 0;
}
.module-item.collapsed .module-icon {
  margin: 0;
}
</style>
