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
      <img src="/logo.png" alt="云财务" class="logo-img" />
      <span v-show="!appStore.sidebarCollapsed" class="logo-text">云财务</span>
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
  background: #fff;
  border-right: 1px solid var(--el-border-color-light);
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
  border-bottom: 1px solid var(--el-border-color-light);
}
.logo-img {
  width: 30px;
  height: 30px;
  flex-shrink: 0;
  border-radius: 8px;
  object-fit: contain;
}
.logo-text {
  font-size: 16px;
  font-weight: 700;
  color: var(--el-text-color-primary);
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
  padding: 12px 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
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
  color: var(--el-text-color-regular);
  transition: all 0.15s ease;
  position: relative;
}
.module-item:hover {
  background: var(--el-fill-color-light);
  color: var(--el-color-primary);
}
.module-item:hover .module-icon {
  color: var(--el-color-primary);
}

.module-icon {
  color: var(--el-text-color-secondary);
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

/* 选中态：蓝色圆角高亮 */
.module-item.active {
  background: var(--el-color-primary);
  color: #fff;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}
.module-item.active .module-icon {
  color: #fff;
}
.module-item.active .module-badge {
  background: #fff;
  color: var(--el-color-primary);
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
