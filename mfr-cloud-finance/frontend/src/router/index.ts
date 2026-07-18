import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'

/**
 * 路由配置
 * - 首页 /dashboard 使用 MainLayout 布局
 * - 总账模块含三级子菜单路由
 * - 其余业务模块预留占位
 */

/** 通用占位页面 — 用于尚未开发的子页面 */
const Placeholder = {
  template: `
    <div style="padding:40px;text-align:center;">
      <el-empty description="该功能正在开发中，敬请期待…" :image-size="160">
        <template #description>
          <p style="color:#909399;font-size:15px;margin-top:8px;">{{ title }}</p>
        </template>
      </el-empty>
    </div>
  `,
  props: { title: { type: String, default: '开发中' } },
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: MainLayout,
      redirect: '/dashboard',
      children: [
        /* ====== 首页仪表盘 ====== */
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/views/dashboard/Dashboard.vue'),
          meta: { title: '仪表盘', icon: 'Odometer' },
        },

        /* ====== 总账模块 — 三级子菜单 ====== */
        // --- 凭证管理 ---
        {
          path: 'general-ledger/voucher',
          name: 'Voucher',
          component: () => import('@/views/general-ledger/Voucher.vue'),
          meta: { title: '凭证录入', group: '凭证管理' },
        },
        {
          path: 'general-ledger/voucher-list',
          name: 'VoucherList',
          component: () => import('@/views/general-ledger/VoucherList.vue'),
          meta: { title: '查看凭证', group: '凭证管理' },
        },
        {
          path: 'general-ledger/original-voucher',
          name: 'OriginalVoucher',
          component: () => import('@/views/general-ledger/OriginalVoucher.vue'),
          meta: { title: '原始凭证', group: '凭证管理' },
        },

        // --- 账簿 ---
        {
          path: 'general-ledger/general',
          name: 'GeneralLedger',
          component: () => import('@/views/general-ledger/GeneralLedger.vue'),
          meta: { title: '总账', group: '账簿' },
        },
        {
          path: 'general-ledger/detail',
          name: 'DetailLedger',
          component: () => import('@/views/general-ledger/DetailLedger.vue'),
          meta: { title: '明细账', group: '账簿' },
        },
        {
          path: 'general-ledger/balance',
          name: 'BalanceSheet',
          component: () => import('@/views/general-ledger/BalanceSheet.vue'),
          meta: { title: '余额表', group: '账簿' },
        },
        {
          path: 'general-ledger/chronological',
          name: 'ChronologicalLedger',
          component: () => import('@/views/general-ledger/ChronologicalLedger.vue'),
          meta: { title: '序时账', group: '账簿' },
        },
        {
          path: 'general-ledger/columnar',
          name: 'ColumnarLedger',
          component: () => import('@/views/general-ledger/ColumnarLedger.vue'),
          meta: { title: '多栏账', group: '账簿' },
        },
        {
          path: 'general-ledger/account-summary',
          name: 'AccountSummary',
          component: () => import('@/views/general-ledger/AccountSummary.vue'),
          meta: { title: '科目汇总表', group: '账簿' },
        },

        // --- 辅助账簿 ---
        {
          path: 'general-ledger/aux-detail',
          name: 'AuxDetailLedger',
          component: Placeholder,
          props: { title: '科目辅助明细账' },
          meta: { title: '科目辅助明细账', group: '辅助账簿' },
        },
        {
          path: 'general-ledger/aux-balance',
          name: 'AuxBalanceSheet',
          component: Placeholder,
          props: { title: '科目辅助余额表' },
          meta: { title: '科目辅助余额表', group: '辅助账簿' },
        },
        {
          path: 'general-ledger/qty-fx-detail',
          name: 'QtyFxDetailLedger',
          component: Placeholder,
          props: { title: '数量外币明细账' },
          meta: { title: '数量外币明细账', group: '辅助账簿' },
        },
        {
          path: 'general-ledger/qty-fx-balance',
          name: 'QtyFxBalanceSheet',
          component: Placeholder,
          props: { title: '数量外币余额表' },
          meta: { title: '数量外币余额表', group: '辅助账簿' },
        },
        {
          path: 'general-ledger/project-detail',
          name: 'ProjectDetailLedger',
          component: Placeholder,
          props: { title: '核算项目明细账' },
          meta: { title: '核算项目明细账', group: '辅助账簿' },
        },
        {
          path: 'general-ledger/project-balance',
          name: 'ProjectBalanceSheet',
          component: Placeholder,
          props: { title: '核算项目余额表' },
          meta: { title: '核算项目余额表', group: '辅助账簿' },
        },

        /* ====== 其他模块（一级菜单）===== */
        { path: 'reports', name: 'Reports', component: Placeholder, props: { title: '财务报表' }, meta: { title: '报表' } },
        { path: 'cashier', name: 'Cashier', component: Placeholder, props: { title: '出纳管理' }, meta: { title: '出纳' } },
        { path: 'assets', name: 'Assets', component: Placeholder, props: { title: '资产管理' }, meta: { title: '资产' } },
        { path: 'payroll', name: 'Payroll', component: Placeholder, props: { title: '工资管理' }, meta: { title: '工资' } },
        { path: 'invoice', name: 'Invoice', component: Placeholder, props: { title: '发票管理（账免）' }, meta: { title: '发票' } },
        { path: 'closing', name: 'Closing', component: Placeholder, props: { title: '期间结账' }, meta: { title: '结账' } },
        { path: 'settings', name: 'Settings', component: Placeholder, props: { title: '系统设置' }, meta: { title: '设置' } },
        { path: 'guide', name: 'Guide', component: Placeholder, props: { title: '新手指引' }, meta: { title: '新手指引' } },
        { path: 'integration', name: 'Integration', component: Placeholder, props: { title: '业财一体' }, meta: { title: '业财一体' } },
      ],
    },

    // 兜底：未匹配路由统一回到仪表盘
    {
      path: '/:pathMatch(.*)*',
      redirect: '/dashboard',
    },
  ],
})

export default router
