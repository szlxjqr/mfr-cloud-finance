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
          component: () => import('@/views/general-ledger/AuxDetailLedger.vue'),
          meta: { title: '科目辅助明细账', group: '辅助账簿' },
        },
        {
          path: 'general-ledger/aux-balance',
          name: 'AuxBalanceSheet',
          component: () => import('@/views/general-ledger/AuxBalanceSheet.vue'),
          meta: { title: '科目辅助余额表', group: '辅助账簿' },
        },
        {
          path: 'general-ledger/qty-fx-detail',
          name: 'QtyFxDetailLedger',
          component: () => import('@/views/general-ledger/QtyFxDetaiLedger.vue'),
          meta: { title: '数量外币明细账', group: '辅助账簿' },
        },
        {
          path: 'general-ledger/qty-fx-balance',
          name: 'QtyFxBalanceSheet',
          component: () => import('@/views/general-ledger/QtyFxBalanceSheet.vue'),
          meta: { title: '数量外币余额表', group: '辅助账簿' },
        },
        {
          path: 'general-ledger/project-detail',
          name: 'ProjectDetailLedger',
          component: () => import('@/views/general-ledger/ProjectDetailLedger.vue'),
          meta: { title: '核算项目明细账', group: '辅助账簿' },
        },
        {
          path: 'general-ledger/project-balance',
          name: 'ProjectBalanceSheet',
          component: () => import('@/views/general-ledger/ProjectBalanceSheet.vue'),
          meta: { title: '核算项目余额表', group: '辅助账簿' },
        },

        /* ====== 报表模块 ====== */
        {
          path: 'reports/balance-sheet',
          name: 'BalanceSheetReport',
          component: Placeholder,
          props: { title: '资产负债表' },
          meta: { title: '资产负债表', group: '财务报表' },
        },
        {
          path: 'reports/income-statement',
          name: 'IncomeStatement',
          component: Placeholder,
          props: { title: '利润表' },
          meta: { title: '利润表', group: '财务报表' },
        },
        {
          path: 'reports/income-statement-quarterly',
          name: 'IncomeStatementQuarterly',
          component: Placeholder,
          props: { title: '利润表季报' },
          meta: { title: '利润表季报', group: '财务报表' },
        },
        {
          path: 'reports/cash-flow',
          name: 'CashFlowStatement',
          component: Placeholder,
          props: { title: '现金流量表' },
          meta: { title: '现金流量表', group: '财务报表' },
        },
        {
          path: 'reports/cash-flow-quarterly',
          name: 'CashFlowStatementQuarterly',
          component: Placeholder,
          props: { title: '现金流量表季报' },
          meta: { title: '现金流量表季报', group: '财务报表' },
        },

        /* ====== 出纳模块 ====== */
        {
          path: 'cashier/diary',
          name: 'CashierDiary',
          component: Placeholder,
          props: { title: '日记账' },
          meta: { title: '日记账', group: '资金管理' },
        },
        {
          path: 'cashier/biz-type',
          name: 'CashierBizType',
          component: Placeholder,
          props: { title: '业务类型' },
          meta: { title: '业务类型', group: '资金管理' },
        },
        {
          path: 'cashier/check-general',
          name: 'CashierCheckGeneral',
          component: Placeholder,
          props: { title: '核对总账' },
          meta: { title: '核对总账', group: '资金管理' },
        },

        /* ====== 资产模块 ====== */
        {
          path: 'assets/fixed-asset',
          name: 'FixedAsset',
          component: Placeholder,
          props: { title: '固定资产管理' },
          meta: { title: '固定资产管理', group: '固定资产' },
        },

        /* ====== 工资模块 ====== */
        { path: 'payroll/employee-info', name: 'PayrollEmployeeInfo', component: Placeholder, props: { title: '员工基本信息' }, meta: { title: '员工基本信息', group: '工资' } },
        { path: 'payroll/salary-list', name: 'PayrollSalaryList', component: Placeholder, props: { title: '工资列表' }, meta: { title: '工资列表', group: '工资' } },
        { path: 'payroll/dept-summary', name: 'PayrollDeptSummary', component: Placeholder, props: { title: '部门工资汇总表' }, meta: { title: '部门工资汇总表', group: '工资' } },
        { path: 'payroll/tax-report', name: 'PayrollTaxReport', component: Placeholder, props: { title: '个税报表' }, meta: { title: '个税报表', group: '工资' } },
        { path: 'payroll/social-fund-setting', name: 'PayrollSocialFundSetting', component: Placeholder, props: { title: '社保及公积金设置' }, meta: { title: '社保及公积金设置', group: '工资设置' } },
        { path: 'payroll/calc-setting', name: 'PayrollCalcSetting', component: Placeholder, props: { title: '工资计算设置' }, meta: { title: '工资计算设置', group: '工资设置' } },
        { path: 'payroll/allocation', name: 'PayrollAllocation', component: Placeholder, props: { title: '工资分摊' }, meta: { title: '工资分摊', group: '工资设置' } },

        /* ====== 其他模块（一级菜单）===== */
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
