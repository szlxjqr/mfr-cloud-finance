<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'

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
  {
    title: '发票',
    icon: 'Ticket',
    groups: [
      {
        title: '发票',
        icon: 'Ticket',
        color: '#409EFF',
        children: [
          { title: '进项发票', path: '/invoice/input' },
          { title: '销项发票', path: '/invoice/output' },
          { title: '费用发票', path: '/invoice/expense' },
        ],
      },
      {
        title: '发票设置',
        icon: 'Wallet',
        color: '#E6A23C',
        children: [
          { title: '发票抬头', path: '/invoice/title' },
          { title: '发票设置', path: '/invoice/setting' },
        ],
      },
    ],
  },
  {
    title: '结账',
    icon: 'CircleCheck',
    groups: [
      {
        title: '结账',
        icon: 'CircleCheck',
        color: '#E6A23C',
        children: [
          { title: '期末结转', path: '/closing/carry-forward' },
          { title: '结账', path: '/closing/close' },
        ],
      },
    ],
  },
  {
    title: '设置',
    icon: 'Setting',
    groups: [
      {
        title: '基础数据',
        icon: 'DataLine',
        color: '#409EFF',
        children: [
          { title: '科目', path: '/settings/account' },
          { title: '期初', path: '/settings/opening' },
          { title: '辅助字典', path: '/settings/aux-dict' },
          { title: '币别', path: '/settings/currency' },
          { title: '凭证摘要', path: '/settings/summary' },
          { title: '凭证字', path: '/settings/voucher-word' },
        ],
      },
      {
        title: '基础设置',
        icon: 'Setting',
        color: '#E6A23C',
        children: [
          { title: '凭证模板', path: '/settings/voucher-template' },
          { title: '凭证配置', path: '/settings/voucher-config' },
          { title: '日记账模板', path: '/settings/diary-template' },
          { title: '归档管理', path: '/settings/archive' },
          { title: '系统设置', path: '/settings/system' },
          { title: '审计接口文件导出', path: '/settings/audit-export' },
        ],
      },
    ],
  },
  { title: '新手指引', path: '/guide', icon: 'Notebook' },
]

/** 当前激活菜单项 */
const activeMenu = computed(() => route.path)

/** 总账/报表/出纳/资产/工资/发票/结账/设置子菜单是否默认展开 */
const defaultOpenedMenus = ref(['general-ledger', 'reports', 'cashier', 'assets', 'payroll', 'invoice', 'closing', 'settings'])

const asideWidth = computed(() => (appStore.sidebarCollapsed ? '64px' : '200px'))
</script>

<template>
  <el-aside :width="asideWidth" class="side-aside">
    <!-- 品牌区 -->
    <div class="side-logo">
      <img src="/logo.png" alt="云财务" class="logo-img" />
      <span v-show="!appStore.sidebarCollapsed" class="logo-text">云财务</span>
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

          <!-- 分组: 工资 + 工资设置（纵向堆叠） -->
          <div v-for="(group, gi) in menuItems[5].groups" :key="gi" class="menu-group">
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

        <!-- 发票：带子分组的 el-sub-menu（纵向堆叠） -->
        <el-sub-menu index="invoice">
          <template #title>
            <el-icon><component is="Ticket" /></el-icon>
            <span class="menu-title">发票</span>
          </template>

          <!-- 分组: 发票 + 发票设置（纵向堆叠） -->
          <div v-for="(group, gi) in menuItems[6].groups" :key="gi" class="menu-group">
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

        <!-- 结账：带子分组的 el-sub-menu -->
        <el-sub-menu index="closing">
          <template #title>
            <el-icon><component is="CircleCheck" /></el-icon>
            <span class="menu-title">结账</span>
          </template>

          <!-- 分组: 结账 -->
          <div v-for="(group, gi) in menuItems[7].groups" :key="gi" class="menu-group">
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

        <!-- 设置：带子分组的 el-sub-menu（双分组，两列布局） -->
        <el-sub-menu index="settings">
          <template #title>
            <el-icon><component is="Setting" /></el-icon>
            <span class="menu-title">设置</span>
          </template>

          <!-- 分组: 基础数据 + 基础设置（纵向堆叠） -->
          <div v-for="(group, gi) in menuItems[8].groups" :key="gi" class="menu-group">
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

        <!-- 其余：普通菜单项 -->
        <el-menu-item
          v-for="item in menuItems.slice(9)"
          :key="item.path"
          :index="item.path!"
        >
          <el-icon><component :is="item.icon!" /></el-icon>
          <span class="menu-title">{{ item.title }}</span>
        </el-menu-item>
      </el-menu>
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
</style>
