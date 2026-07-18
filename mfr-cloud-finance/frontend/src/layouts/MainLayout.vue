<script setup lang="ts">
import TopBar from './components/TopBar.vue'
import SideNav from './components/SideNav.vue'
</script>

<template>
  <el-container class="main-layout">
    <!-- 左侧导航 -->
    <SideNav />

    <!-- 右侧：顶部栏 + 主内容区 -->
    <el-container class="main-right">
      <TopBar />

      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.main-layout {
  height: 100vh;
  width: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: row;
}

.main-right {
  display: flex;
  flex-direction: column;
  flex: 1;
  height: 100vh;
  min-width: 0;
}

.main-content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  background: var(--el-fill-color-light);
  padding: 16px;
}

/* 路由切换过渡 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 小屏：内容区内边距收紧 */
@media (max-width: 768px) {
  .main-content {
    padding: 10px;
  }
}
</style>
