<script setup lang="ts">
import { ref } from 'vue'
import { useAppStore } from '@/stores/app'
import { ElMessage } from 'element-plus'
import {
  Search,
  Bell,
  ArrowDown,
  User,
  Setting,
  Lock,
  SwitchButton,
} from '@element-plus/icons-vue'

const appStore = useAppStore()

interface Company {
  value: string
  label: string
}

/** 可切换的公司列表（演示数据） */
const companies = ref<Company[]>([
  { value: 'mfr-tech', label: 'MFR科技有限公司' },
  { value: 'mfr-trade', label: 'MFR贸易有限公司' },
  { value: 'mfr-group', label: 'MFR集团总部' },
])

const currentCompany = ref<string>('MFR科技有限公司')

/** 用户下拉菜单命令 */
type UserCommand = 'profile' | 'settings' | 'lock' | 'logout'

function handleUserCommand(command: UserCommand) {
  switch (command) {
    case 'profile':
      ElMessage.info('打开个人中心')
      break
    case 'settings':
      ElMessage.info('打开账号设置')
      break
    case 'lock':
      ElMessage.info('已锁定屏幕')
      break
    case 'logout':
      ElMessage.success('已退出登录')
      break
  }
}

</script>

<template>
  <el-header class="top-bar" height="56px">
    <!-- 左侧：Logo + 公司切换 + 折叠 + 搜索 -->
    <div class="top-left">
      <div class="brand">
        <span class="brand-logo">MFR</span>
        <span class="brand-name">智慧经营</span>
      </div>

      <el-dropdown
        class="company-switch"
        trigger="click"
        @command="(val: string) => (currentCompany = companies.find((c) => c.value === val)?.label || val)"
      >
        <span class="company-trigger">
          <span class="company-label">{{ currentCompany }}</span>
          <el-icon><ArrowDown /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item
              v-for="c in companies"
              :key="c.value"
              :command="c.value"
            >
              {{ c.label }}
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <el-tooltip content="折叠/展开菜单" placement="bottom">
        <el-icon class="icon-btn collapse-btn" @click="appStore.toggleSidebar()">
          <component :is="appStore.sidebarCollapsed ? 'Expand' : 'Fold'" />
        </el-icon>
      </el-tooltip>

      <el-tooltip content="全局搜索" placement="bottom">
        <el-icon class="icon-btn" @click="() => {}">
          <Search />
        </el-icon>
      </el-tooltip>
    </div>

    <!-- 右侧功能按钮组 -->
    <div class="top-right">
      <el-link type="primary" class="nav-link" :underline="false">在线咨询</el-link>
      <el-link type="primary" class="nav-link" :underline="false">帮助中心</el-link>

      <el-tooltip content="AI 助理" placement="bottom">
        <el-tag type="primary" effect="light" round class="ai-tag">AI助理</el-tag>
      </el-tooltip>

      <el-badge is-dot class="bell-icon hide-md">
        <el-icon class="icon-btn"><Bell /></el-icon>
      </el-badge>

      <!-- 用户头像 + 下拉菜单 -->
      <el-dropdown class="user-dropdown" trigger="click" @command="handleUserCommand">
        <span class="user-trigger">
          <el-avatar :size="32" class="user-avatar">M</el-avatar>
          <span class="user-name hide-md">管理员</span>
          <el-icon class="hide-md"><ArrowDown /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item :command="'profile'">
              <el-icon><User /></el-icon> 个人中心
            </el-dropdown-item>
            <el-dropdown-item :command="'settings'">
              <el-icon><Setting /></el-icon> 账号设置
            </el-dropdown-item>
            <el-dropdown-item :command="'lock'">
              <el-icon><Lock /></el-icon> 锁定屏幕
            </el-dropdown-item>
            <el-dropdown-item divided :command="'logout'">
              <el-icon><SwitchButton /></el-icon> 退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </el-header>
</template>

<style scoped>
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
  padding: 0 16px;
  background: #fff;
  border-bottom: 1px solid var(--el-border-color-light);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  position: relative;
  z-index: 10;
}

/* ===== 左侧 ===== */
.top-left {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.brand {
  display: flex;
  align-items: baseline;
  gap: 4px;
  user-select: none;
}
.brand-logo {
  font-size: 17px;
  font-weight: 800;
  color: #fff;
  letter-spacing: 0.5px;
  background: var(--brand-grad);
  border-radius: 8px;
  padding: 3px 10px;
  box-shadow: 0 2px 8px rgba(47, 107, 255, 0.28);
}
.brand-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.company-switch {
  margin-left: 4px;
}
.company-trigger {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 32px;
  padding: 0 10px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  cursor: pointer;
  color: var(--el-text-color-primary);
  font-size: 14px;
  transition: all 0.2s;
  max-width: 220px;
}
.company-trigger:hover {
  border-color: var(--el-color-primary);
  color: var(--el-color-primary);
}
.company-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.icon-btn {
  font-size: 18px;
  color: var(--el-text-color-regular);
  cursor: pointer;
  padding: 6px;
  border-radius: 8px;
  transition: all 0.2s;
}
.icon-btn:hover {
  color: var(--el-color-primary);
  background: var(--el-fill-color-light);
}
.collapse-btn {
  font-size: 20px;
}

/* ===== 右侧 ===== */
.top-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.erp-btn {
  background: linear-gradient(135deg, #ffa53d 0%, #ff7a18 100%);
  border: none;
  color: #fff;
  font-weight: 600;
  padding: 8px 16px;
  box-shadow: 0 2px 8px rgba(255, 122, 24, 0.35);
}
.erp-btn:hover {
  background: linear-gradient(135deg, #ff9430 0%, #ff6a00 100%);
  box-shadow: 0 4px 12px rgba(255, 122, 24, 0.45);
}

.nav-link {
  font-size: 14px;
  font-weight: 500;
}

.ai-tag {
  cursor: pointer;
  font-weight: 600;
  padding: 2px 10px;
}

.bell-icon {
  display: flex;
  align-items: center;
}

.user-dropdown {
  margin-left: 2px;
}
.user-trigger {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  outline: none;
}
.user-avatar {
  background: var(--brand-grad);
  color: #fff;
  font-weight: 700;
  box-shadow: 0 2px 6px rgba(47, 107, 255, 0.4);
}
.user-name {
  font-size: 14px;
  color: var(--el-text-color-primary);
}

/* ===== 响应式 ===== */
@media (max-width: 1100px) {
  .hide-md {
    display: none !important;
  }
  .nav-link {
    display: none;
  }
}
@media (max-width: 768px) {
  .top-bar {
    padding: 0 10px;
  }
  .brand-name {
    display: none;
  }
  .company-trigger {
    max-width: 130px;
  }
}
</style>
