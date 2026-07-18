<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { ElMessage } from 'element-plus'

const appStore = useAppStore()
const route = useRoute()

/** 子菜单项 */
interface SubMenuItem {
  title: string
  path: string
}

/** 菜单分组（用于总账等有子菜单的情况） */
interface MenuGroup {
  title: string
  icon: string
  color: string
  children: SubMenuItem[]
}

/** 菜单项（支持普通项和分组展开） */
interface MenuItem {
  title: string
  path?: string
  icon?: string
  badge?: string
  highlight?: boolean
  groups?: MenuGroup[] // 有子分组时使用
}

/** 左侧导航菜单定义 — 含总账三级结构 */
const menuItems: MenuItem[] = [
  { title: '首页', path: '/dashboard', icon: 'HomeFilled' },
  {
    title: '总账',
    icon: 'Document',
    groups: [
      {
        title: '凭证管理',
        icon: 'Document',
        color: '#409EFF',
        children: [
          { title: '凭证', path: '/general-ledger/voucher' },
          { title: '查看凭证', path: '/general-ledger/voucher-list' },
          { title: '原始凭证', path: '/general-ledger/original-voucher' },
        ],
      },
      {
        title: '账簿',
        icon: 'Coin',
        color: '#E6A23C',
        children: [
          { title: '总账', path: '/general-ledger/general' },
          { title: '明细账', path: '/general-ledger/detail' },
          { title: '余额表', path: '/general-ledger/balance' },
          { title: '序时账', path: '/general-ledger/chronological' },
          { title: '多栏账', path: '/general-ledger/columnar' },
          { title: '科目汇总表', path: '/general-ledger/account-summary' },
        ],
      },
      {
        title: '辅助账簿',
        icon: 'Grid',
        color: '#909399',
        children: [
          { title: '科目辅助明细账', path: '/general-ledger/aux-detail' },
          { title: '科目辅助余额表', path: '/general-ledger/aux-balance' },
          { title: '数量外币明细账', path: '/general-ledger/qty-fx-detail' },
          { title: '数量外币余额表', path: '/general-ledger/qty-fx-balance' },
          { title: '核算项目明细账', path: '/general-ledger/project-detail' },
          { title: '核算项目余额表', path: '/general-ledger/project-balance' },
        ],
      },
    ],
  },
  {
    title: '报表',
    icon: 'DataAnalysis',
    groups: [
      {
        title: '财务报表',
        icon: 'DataAnalysis',
        color: '#67C23A',
        children: [
          { title: '资产负债表', path: '/reports/balance-sheet' },
          { title: '利润表', path: '/reports/income-statement' },
          { title: '利润表季报', path: '/reports/income-statement-quarterly' },
          { title: '现金流量表', path: '/reports/cash-flow' },
          { title: '现金流量表季报', path: '/reports/cash-flow-quarterly' },
        ],
      },
    ],
  },
  {
    title: '出纳',
    icon: 'Money',
    groups: [
      {
        title: '资金管理',
        icon: 'Money',
        color: '#9B59B6',
        children: [
          { title: '日记账', path: '/cashier/diary' },
          { title: '业务类型', path: '/cashier/biz-type' },
          { title: '核对总账', path: '/cashier/check-general' },
        ],
      },
    ],
  },
  {
    title: '资产',
    icon: 'OfficeBuilding',
    groups: [
      {
        title: '固定资产',
        icon: 'OfficeBuilding',
        color: '#13C2C2',
        children: [
          { title: '固定资产管理', path: '/assets/fixed-asset' },
        ],
      },
    ],
  },
  {
    title: '工资',
    icon: 'User',
    groups: [
      {
        title: '工资',
        icon: 'UserFilled',
        color: '#67C23A',
        children: [
          { title: '员工基本信息', path: '/payroll/employee-info' },
          { title: '工资列表', path: '/payroll/salary-list' },
          { title: '部门工资汇总表', path: '/payroll/dept-summary' },
          { title: '个税报表', path: '/payroll/tax-report' },
        ],
      },
      {
        title: '工资设置',
        icon: 'Setting',
        color: '#409EFF',
        children: [
          { title: '社保及公积金设置', path: '/payroll/social-fund-setting' },
          { title: '工资计算设置', path: '/payroll/calc-setting' },
          { title: '工资分摊', path: '/payroll/allocation' },
        ],
      },
    ],
  },
  { title: '发票', path: '/invoice', icon: 'Ticket', badge: '账免' },
  { title: '结账', path: '/closing', icon: 'CircleCheck' },
  { title: '设置', path: '/settings', icon: 'Setting' },
  { title: '新手指引', path: '/guide', icon: 'Notebook' },
  { title: '业财一体', path: '/integration', icon: 'Connection', highlight: true },
]

/** 当前激活菜单项 */
const activeMenu = computed(() => route.path)

/** 总账/报表/出纳/资产/工资子菜单是否默认展开 */
const defaultOpenedMenus = ref(['general-ledger', 'reports', 'cashier', 'assets', 'payroll'])

const asideWidth = computed(() => (appStore.sidebarCollapsed ? '64px' : '200px'))

function handleFooter(command: 'service' | 'material') {
  if (command === 'service') ElMessage.info('正在为您接入在线客服…')
  else ElMessage.info('已为您准备学习资料包')
}
</script>

<template>
  <el-aside :width="asideWidth" class="side-aside">
    <!-- 品牌区 -->
    <div class="side-logo">
      <span class="logo-mark">M</span>
      <span v-show="!appStore.sidebarCollapsed" class="logo-text">MFR云财务</span>
    </div>

    <!-- 菜单 -->
    <el-scrollbar class="side-scroll">
      <el-menu
        class="side-menu"
        :default-active="activeMenu"
        :default-openeds="defaultOpenedMenus"
        :collapse="appStore.sidebarCollapsed"
        :collapse-transition="false"
        router
      >
        <!-- 首页：普通菜单项 -->
        <el-menu-item index="/dashboard">
          <el-icon><component is="HomeFilled" /></el-icon>
          <span class="menu-title">首页</span>
        </el-menu-item>

        <!-- 总账：带子分组的 el-sub-menu -->
        <el-sub-menu index="general-ledger">
          <template #title>
            <el-icon><component is="Document" /></el-icon>
            <span class="menu-title">总账</span>
          </template>

          <!-- 分组1: 凭证管理 -->
          <div v-for="(group, gi) in menuItems[1].groups" :key="gi" class="menu-group">
            <div class="group-header" :style="{ color: group.color }">
              <span class="group-icon-wrap" :style="{ background: group.color + '15' }">
                <el-icon :size="14"><component :is="group.icon" /></el-icon>
              </span>
              {{ group.title }}
            </div>
            <el-menu-item
              v-for="child in group.children"
              :key="child.path"
              :index="child.path"
            >
              {{ child.title }}
            </el-menu-item>
          </div>
        </el-sub-menu>

        <!-- 报表：带子分组的 el-sub-menu -->
        <el-sub-menu index="reports">
          <template #title>
            <el-icon><component is="DataAnalysis" /></el-icon>
            <span class="menu-title">报表</span>
          </template>

          <!-- 分组: 财务报表 -->
          <div v-for="(group, gi) in menuItems[2].groups" :key="gi" class="menu-group">
            <div class="group-header" :style="{ color: group.color }">
              <span class="group-icon-wrap" :style="{ background: group.color + '15' }">
                <el-icon :size="14"><component :is="group.icon" /></el-icon>
              </span>
              {{ group.title }}
            </div>
            <el-menu-item
              v-for="child in group.children"
              :key="child.path"
              :index="child.path"
            >
              {{ child.title }}
            </el-menu-item>
          </div>
        </el-sub-menu>

        <!-- 出纳：带子分组的 el-sub-menu -->
        <el-sub-menu index="cashier">
          <template #title>
            <el-icon><component is="Money" /></el-icon>
            <span class="menu-title">出纳</span>
          </template>

          <!-- 分组: 资金管理 -->
          <div v-for="(group, gi) in menuItems[3].groups" :key="gi" class="menu-group">
            <div class="group-header" :style="{ color: group.color }">
              <span class="group-icon-wrap" :style="{ background: group.color + '15' }">
                <el-icon :size="14"><component :is="group.icon" /></el-icon>
              </span>
              {{ group.title }}
            </div>
            <el-menu-item
              v-for="child in group.children"
              :key="child.path"
              :index="child.path"
            >
              {{ child.title }}
            </el-menu-item>
          </div>
        </el-sub-menu>

        <!-- 资产：带子分组的 el-sub-menu -->
        <el-sub-menu index="assets">
          <template #title>
            <el-icon><component is="OfficeBuilding" /></el-icon>
            <span class="menu-title">资产</span>
          </template>

          <!-- 分组: 固定资产 -->
          <div v-for="(group, gi) in menuItems[4].groups" :key="gi" class="menu-group">
            <div class="group-header" :style="{ color: group.color }">
              <span class="group-icon-wrap" :style="{ background: group.color + '15' }">
                <el-icon :size="14"><component :is="group.icon" /></el-icon>
              </span>
              {{ group.title }}
            </div>
            <el-menu-item
              v-for="child in group.children"
              :key="child.path"
              :index="child.path"
            >
              {{ child.title }}
            </el-menu-item>
          </div>
        </el-sub-menu>

        <!-- 工资：带子分组的 el-sub-menu（双分组） -->
        <el-sub-menu index="payroll">
          <template #title>
            <el-icon><component is="User" /></el-icon>
            <span class="menu-title">工资</span>
          </template>

          <!-- 分组: 工资 + 工资设置（两列布局） -->
          <div class="payroll-grid">
            <div v-for="(group, gi) in menuItems[5].groups" :key="gi" class="payroll-col">
              <div class="group-header" :style="{ color: group.color }">
                <span class="group-icon-wrap" :style="{ background: group.color + '15' }">
                  <el-icon :size="14"><component :is="group.icon" /></el-icon>
                </span>
                {{ group.title }}
              </div>
              <el-menu-item
                v-for="child in group.children"
                :key="child.path"
                :index="child.path"
              >
                {{ child.title }}
              </el-menu-item>
            </div>
          </div>
        </el-sub-menu>

        <!-- 其余：普通菜单项 -->
        <el-menu-item
          v-for="item in menuItems.slice(6)"
          :key="item.path"
          :index="item.path!"
          :class="{ 'menu-highlight': item.highlight }"
        >
          <el-icon><component :is="item.icon!" /></el-icon>
          <span class="menu-title">{{ item.title }}</span>
          <el-tag
            v-if="item.badge"
            size="small"
            type="warning"
            effect="dark"
            round
            class="menu-badge"
          >
            {{ item.badge }}
          </el-tag>
        </el-menu-item>
      </el-menu>
    </el-scrollbar>

    <!-- 底部功能区 -->
    <div class="side-footer">
      <el-button
        v-show="!appStore.sidebarCollapsed"
        class="footer-btn"
        text
        @click="handleFooter('service')"
      >
        联系客服
      </el-button>
      <el-button
        v-show="!appStore.sidebarCollapsed"
        class="footer-btn"
        text
        @click="handleFooter('material')"
      >
        领取资料
      </el-button>
      <div v-show="!appStore.sidebarCollapsed" class="powered">
        *Powered by MFR云
      </div>
      <el-tooltip
        v-if="appStore.sidebarCollapsed"
        content="联系客服"
        placement="right"
      >
        <el-icon class="collapsed-icon" @click="handleFooter('service')">
          <component is="Service" />
        </el-icon>
      </el-tooltip>
    </div>
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
}

/* 品牌区 */
.side-logo {
  height: 56px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 16px;
  border-bottom: 1px solid var(--el-border-color-light);
}
.logo-mark {
  width: 30px;
  height: 30px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: linear-gradient(135deg, #409eff, #2d7ff9);
  color: #fff;
  font-weight: 800;
  font-size: 18px;
  box-shadow: 0 2px 6px rgba(64, 158, 255, 0.4);
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
.side-menu {
  border-right: none;
  padding: 8px 0;
}

/* 一级菜单项 */
.side-menu :deep(.el-menu-item) {
  height: 46px;
  line-height: 46px;
  margin: 4px 10px;
  border-radius: 8px;
  position: relative;
  color: var(--el-text-color-regular);
}
.side-menu :deep(.el-menu-item .el-icon) {
  color: var(--el-text-color-secondary);
  font-size: 18px;
}
.side-menu :deep(.el-menu-item:hover) {
  background: var(--el-fill-color-light);
  color: var(--el-color-primary);
}
.side-menu :deep(.el-menu-item:hover .el-icon) {
  color: var(--el-color-primary);
}

/* 当前选中项：蓝色高亮 */
.side-menu :deep(.el-menu-item.is-active) {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  font-weight: 600;
}
.side-menu :deep(.el-menu-item.is-active .el-icon) {
  color: var(--el-color-primary);
}
.side-menu :deep(.el-menu-item.is-active)::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  border-radius: 2px;
  background: var(--el-color-primary);
}

/* ====== 子菜单 / sub-menu 样式 ====== */

/* 总账一级标题 */
.side-menu :deep(.el-sub-menu__title) {
  height: 46px;
  line-height: 46px;
  margin: 4px 10px;
  border-radius: 8px;
  position: relative;
  color: var(--el-text-color-regular);
  font-weight: 500;
}
.side-menu :deep(.el-sub-menu__title:hover) {
  background: var(--el-fill-color-light);
  color: var(--el-color-primary);
}
.side-menu :deep(.el-sub-menu.is-active > .el-sub-menu__title) {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  font-weight: 600;
}
.side-menu :deep(.el-sub-menu.is-active > .el-sub-menu__title::before) {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  border-radius: 2px;
  background: var(--el-color-primary);
}
.side-menu :deep(.el-sub-menu__title .el-icon) {
  color: var(--el-text-color-secondary);
  font-size: 18px;
}
.side-menu :deep(.el-sub-menu__title:hover .el-icon) {
  color: var(--el-color-primary);
}
.side-menu :deep(.el-sub-menu.is-active > .el-sub-menu__title .el-icon) {
  color: var(--el-color-primary);
}

/* 子菜单容器 */
.side-menu :deep(.el-menu--inline) {
  padding: 0 !important;
}

/* 二级子项（凭证、总账等） */
.side-menu :deep(.el-menu--inline .el-menu-item) {
  height: 40px;
  line-height: 40px;
  margin: 2px 8px 2px 8px;
  border-radius: 6px;
  font-size: 14px;
  padding-left: 44px !important;
  min-width: auto;
}
.side-menu :deep(.el-menu--inline .el-menu-item.is-active) {
  background: #ecf5ff;
  color: #409eff;
}
.side-menu :deep(.el-menu--inline .el-menu-item.is-active)::before {
  display: none;
}

/* ====== 分组标题样式 ====== */
.menu-group {
  padding: 6px 12px 4px 24px;
}

/* 工资菜单：双列网格布局 */
.payroll-grid {
  display: flex;
  gap: 0;
  padding: 0 8px;
}
.payroll-col {
  flex: 1;
  min-width: 0;
}
.payroll-col .group-header {
  padding-left: 12px;
}
.payroll-col :deep(.el-menu-item) {
  padding-left: 32px !important;
}
.group-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 700;
  padding: 10px 0 4px 0;
  letter-spacing: 0.5px;
  cursor: default;
  user-select: none;
}
.group-icon-wrap {
  width: 22px;
  height: 22px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 5px;
  flex-shrink: 0;
}

/* 菜单标题与徽标 */
.menu-title {
  flex: 1;
  margin-left: 6px;
}
.menu-badge {
  margin-left: auto;
  height: 18px;
  line-height: 16px;
  padding: 0 6px;
  font-weight: 600;
  transform: scale(0.9);
}

/* 业财一体：橙色高亮 */
.side-menu :deep(.menu-highlight) {
  background: linear-gradient(135deg, #ffa53d 0%, #ff6a00 100%) !important;
  color: #fff !important;
  font-weight: 700;
}
.side-menu :deep(.menu-highlight .el-icon) {
  color: #fff !important;
}
.side-menu :deep(.menu-highlight:hover) {
  background: linear-gradient(135deg, #ff9430 0%, #ff5a00 100%) !important;
  color: #fff !important;
}
.side-menu :deep(.menu-highlight.is-active)::before {
  display: none;
}

/* 底部 */
.side-footer {
  flex-shrink: 0;
  padding: 10px 12px;
  border-top: 1px solid var(--el-border-color-light);
}
.footer-btn {
  display: block;
  width: 100%;
  justify-content: flex-start;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
.footer-btn:hover {
  color: var(--el-color-primary);
}
.powered {
  margin-top: 8px;
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  text-align: center;
}
.collapsed-icon {
  display: block;
  margin: 0 auto;
  font-size: 18px;
  color: var(--el-text-color-secondary);
  cursor: pointer;
}
</style>
