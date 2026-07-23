<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { menuItems } from '../menuConfig'

const route = useRoute()
const router = useRouter()

const currentModule = computed<string>(() => {
  if (route.meta?.module) return route.meta.module as string
  // 兜底：根据 path 前缀推导，如 /general-ledger/voucher → general-ledger
  const path = route.path
  const item = menuItems.find((m) => m.module && path.startsWith('/' + m.module))
  return item?.module || ''
})

const moduleData = computed(() => menuItems.find((m) => m.module === currentModule.value))
const groups = computed(() => moduleData.value?.groups ?? [])

function navigate(path: string) {
  router.push(path)
}
</script>

<template>
  <div class="menu-panel">
    <div class="panel-header">
      <h2 class="panel-title">{{ moduleData?.title || '模块导航' }}</h2>
      <span class="panel-sub">请选择功能进入</span>
    </div>

    <div class="groups-grid">
      <div
        v-for="group in groups"
        :key="group.title"
        class="group-card"
      >
        <div class="group-header">
          <span
            class="group-icon"
            :style="{ background: group.color + '15', color: group.color }"
          >
            <el-icon :size="20"><component :is="group.icon" /></el-icon>
          </span>
          <span class="group-title">{{ group.title }}</span>
        </div>
        <div class="group-items">
          <div
            v-for="child in group.children"
            :key="child.path"
            class="group-item"
            @click="navigate(child.path)"
          >
            {{ child.title }}
          </div>
        </div>
      </div>
    </div>

    <el-empty v-if="groups.length === 0" description="该模块暂无子菜单" :image-size="120" />
  </div>
</template>

<style scoped>
.menu-panel {
  height: 100%;
  padding: 28px 32px;
  box-sizing: border-box;
  overflow-y: auto;
  background: var(--bg-app);
}

.panel-header {
  margin-bottom: 28px;
}
.panel-title {
  font-size: 22px;
  font-weight: 600;
  color: var(--text-strong);
  margin: 0 0 4px;
}
.panel-sub {
  font-size: 14px;
  color: var(--text-muted);
}

.groups-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  align-items: flex-start;
}

.group-card {
  flex: 1 1 280px;
  min-width: 220px;
  max-width: 400px;
  background: var(--bg-surface);
  border: 1px solid var(--border-soft);
  border-radius: 8px;
  padding: 20px;
  box-shadow: var(--shadow-card);
  transition: box-shadow 0.2s ease;
}
.group-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.group-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-soft);
}
.group-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.group-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-strong);
}

.group-items {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.group-item {
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 14px;
  color: var(--text-base);
  cursor: pointer;
  transition: all 0.12s ease;
}
.group-item:hover {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  font-weight: 500;
}
</style>
