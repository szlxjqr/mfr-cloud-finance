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
  padding: 24px;
  box-sizing: border-box;
  overflow-y: auto;
  background: #f5f7fa;
}

.panel-header {
  margin-bottom: 24px;
}
.panel-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin: 0 0 6px;
}
.panel-sub {
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.groups-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  align-items: flex-start;
}

.group-card {
  flex: 1 1 300px;
  min-width: 240px;
  max-width: 420px;
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}
.group-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.group-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}
.group-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.group-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--el-text-color-primary);
}

.group-items {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.group-item {
  padding: 10px 12px;
  border-radius: 8px;
  font-size: 14px;
  color: var(--el-text-color-regular);
  cursor: pointer;
  transition: all 0.15s ease;
}
.group-item:hover {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  font-weight: 600;
}
</style>
