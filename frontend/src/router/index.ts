import { createRouter, createWebHashHistory } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'

/**
 * 路由配置
 * - 首页 /dashboard 使用 MainLayout 布局
 * - 一级目录：合同管理 / 税务管理 / 报销管理 / 工资管理 / 资产管理 / 账务管理（容器）
 * - 账务管理收编：总账 / 出纳 / 发票 / 结账 / 报表
 * - 未开发子页面用 Placeholder 占位
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

/** 科目管理页面 */
const SettingsAccount = () => import('@/views/settings/Account.vue')

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      component: MainLayout,
      redirect: '/dashboard',
      children: [
        /* ====== 首页 ====== */
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/views/dashboard/Dashboard.vue'),
          meta: { title: '仪表盘', icon: 'Odometer' },
        },

        /* ====== 合同管理模块 ====== */
        {
          path: 'contract',
          name: 'ContractOverview',
          component: () => import('@/layouts/components/MenuPanel.vue'),
          meta: { title: '合同管理', module: 'contract' },
        },
        {
          path: 'contract/hr',
          name: 'HRContractList',
          component: () => import('@/views/contract/ContractList.vue'),
          props: { type: 'hr' },
          meta: { title: '人事合同', group: '人事合同' },
        },
        {
          path: 'contract/hr-template',
          name: 'HRContractTemplate',
          component: () => import('@/views/contract/ContractTemplate.vue'),
          props: { type: 'hr' },
          meta: { title: '合同模板', group: '人事合同' },
        },
        {
          path: 'contract/sales',
          name: 'SalesContractList',
          component: () => import('@/views/contract/ContractList.vue'),
          props: { type: 'sales' },
          meta: { title: '销售合同', group: '销售合同' },
        },
        {
          path: 'contract/sales-template',
          name: 'SalesContractTemplate',
          component: () => import('@/views/contract/ContractTemplate.vue'),
          props: { type: 'sales' },
          meta: { title: '合同模板', group: '销售合同' },
        },
        {
          path: 'contract/purchase',
          name: 'PurchaseContractList',
          component: () => import('@/views/contract/ContractList.vue'),
          props: { type: 'purchase' },
          meta: { title: '采购合同', group: '采购合同' },
        },
        {
          path: 'contract/purchase-template',
          name: 'PurchaseContractTemplate',
          component: () => import('@/views/contract/ContractTemplate.vue'),
          props: { type: 'purchase' },
          meta: { title: '合同模板', group: '采购合同' },
        },
        {
          path: 'contract/parties',
          name: 'ContractParties',
          component: () => import('@/views/contract/PartyList.vue'),
          meta: { title: '往来单位', group: '往来单位' },
        },

        /* ====== 税务管理模块（占位） ====== */
        {
          path: 'tax',
          name: 'TaxOverview',
          component: () => import('@/layouts/components/MenuPanel.vue'),
          meta: { title: '税务管理', module: 'tax' },
        },
        { path: 'tax/workbench', name: 'TaxWorkbench', component: Placeholder, props: { title: '税务工作台' }, meta: { title: '工作台', group: '税务工作台' } },
        { path: 'tax/individual', name: 'TaxIndividual', component: Placeholder, props: { title: '个税申报' }, meta: { title: '个税申报', group: '个税' } },
        { path: 'tax/stamp', name: 'TaxStamp', component: Placeholder, props: { title: '印花税' }, meta: { title: '印花税', group: '印花税' } },
        { path: 'tax/summary', name: 'TaxSummary', component: Placeholder, props: { title: '发票税务汇总' }, meta: { title: '税务汇总', group: '发票税务汇总' } },

        /* ====== 报销管理模块 ====== */
        {
          path: 'reimburse',
          name: 'ReimburseOverview',
          component: () => import('@/layouts/components/MenuPanel.vue'),
          meta: { title: '报销管理', module: 'reimburse' },
        },
        { path: 'reimburse/bill', name: 'ReimburseBill', component: () => import('@/views/reimburse/BillList.vue'), meta: { title: '报销单', group: '报销单' } },
        { path: 'reimburse/mine', name: 'ReimburseMine', component: () => import('@/views/reimburse/MyReimburse.vue'), meta: { title: '我的报销', group: '报销单' } },
        { path: 'reimburse/approve', name: 'ReimburseApprove', component: Placeholder, props: { title: '待审批' }, meta: { title: '待审批', group: '审批' } },
        { path: 'reimburse/query', name: 'ReimburseQuery', component: Placeholder, props: { title: '报销查询' }, meta: { title: '报销查询', group: '报销查询' } },

        /* ====== 工资管理模块 ====== */
        {
          path: 'payroll',
          name: 'PayrollOverview',
          component: () => import('@/layouts/components/MenuPanel.vue'),
          meta: { title: '工资管理', module: 'payroll' },
        },
        { path: 'payroll/employee-info', name: 'PayrollEmployeeInfo', component: Placeholder, props: { title: '员工基本信息' }, meta: { title: '员工基本信息', group: '工资' } },
        { path: 'payroll/salary-list', name: 'PayrollSalaryList', component: Placeholder, props: { title: '工资列表' }, meta: { title: '工资列表', group: '工资' } },
        { path: 'payroll/dept-summary', name: 'PayrollDeptSummary', component: Placeholder, props: { title: '部门工资汇总表' }, meta: { title: '部门工资汇总表', group: '工资' } },
        { path: 'payroll/tax-report', name: 'PayrollTaxReport', component: Placeholder, props: { title: '个税报表' }, meta: { title: '个税报表', group: '工资' } },
        { path: 'payroll/social-fund-setting', name: 'PayrollSocialFundSetting', component: Placeholder, props: { title: '社保及公积金设置' }, meta: { title: '社保及公积金设置', group: '工资设置' } },
        { path: 'payroll/calc-setting', name: 'PayrollCalcSetting', component: Placeholder, props: { title: '工资计算设置' }, meta: { title: '工资计算设置', group: '工资设置' } },
        { path: 'payroll/allocation', name: 'PayrollAllocation', component: Placeholder, props: { title: '工资分摊' }, meta: { title: '工资分摊', group: '工资设置' } },

        /* ====== 资产管理模块 ====== */
        {
          path: 'assets',
          name: 'AssetsOverview',
          component: () => import('@/layouts/components/MenuPanel.vue'),
          meta: { title: '资产管理', module: 'assets' },
        },
        { path: 'assets/fixed-asset', name: 'FixedAsset', component: Placeholder, props: { title: '固定资产管理' }, meta: { title: '固定资产管理', group: '固定资产' } },

        /* ====== 账务管理模块（容器：收编总账/出纳/发票/结账/报表） ====== */
        {
          path: 'accounting',
          name: 'AccountingOverview',
          component: () => import('@/layouts/components/MenuPanel.vue'),
          meta: { title: '账务管理', module: 'accounting' },
        },
        // --- 总账 ---
        { path: 'general-ledger/voucher', name: 'Voucher', component: () => import('@/views/general-ledger/Voucher.vue'), meta: { title: '凭证录入', group: '总账', module: 'accounting' } },
        { path: 'general-ledger/voucher-list', name: 'VoucherList', component: () => import('@/views/general-ledger/VoucherList.vue'), meta: { title: '查看凭证', group: '总账', module: 'accounting' } },
        { path: 'general-ledger/original-voucher', name: 'OriginalVoucher', component: () => import('@/views/general-ledger/OriginalVoucher.vue'), meta: { title: '原始凭证', group: '总账', module: 'accounting' } },
        { path: 'general-ledger/general', name: 'GeneralLedger', component: () => import('@/views/general-ledger/GeneralLedger.vue'), meta: { title: '总账', group: '总账', module: 'accounting' } },
        { path: 'general-ledger/detail', name: 'DetailLedger', component: () => import('@/views/general-ledger/DetailLedger.vue'), meta: { title: '明细账', group: '总账', module: 'accounting' } },
        { path: 'general-ledger/balance', name: 'BalanceSheet', component: () => import('@/views/general-ledger/BalanceSheet.vue'), meta: { title: '余额表', group: '总账', module: 'accounting' } },
        { path: 'general-ledger/chronological', name: 'ChronologicalLedger', component: () => import('@/views/general-ledger/ChronologicalLedger.vue'), meta: { title: '序时账', group: '总账', module: 'accounting' } },
        { path: 'general-ledger/columnar', name: 'ColumnarLedger', component: () => import('@/views/general-ledger/ColumnarLedger.vue'), meta: { title: '多栏账', group: '总账', module: 'accounting' } },
        { path: 'general-ledger/account-summary', name: 'AccountSummary', component: () => import('@/views/general-ledger/AccountSummary.vue'), meta: { title: '科目汇总表', group: '总账', module: 'accounting' } },
        { path: 'general-ledger/aux-detail', name: 'AuxDetailLedger', component: () => import('@/views/general-ledger/AuxDetailLedger.vue'), meta: { title: '科目辅助明细账', group: '总账', module: 'accounting' } },
        { path: 'general-ledger/aux-balance', name: 'AuxBalanceSheet', component: () => import('@/views/general-ledger/AuxBalanceSheet.vue'), meta: { title: '科目辅助余额表', group: '总账', module: 'accounting' } },
        { path: 'general-ledger/qty-fx-detail', name: 'QtyFxDetailLedger', component: () => import('@/views/general-ledger/QtyFxDetaiLedger.vue'), meta: { title: '数量外币明细账', group: '总账', module: 'accounting' } },
        { path: 'general-ledger/qty-fx-balance', name: 'QtyFxBalanceSheet', component: () => import('@/views/general-ledger/QtyFxBalanceSheet.vue'), meta: { title: '数量外币余额表', group: '总账', module: 'accounting' } },
        { path: 'general-ledger/project-detail', name: 'ProjectDetailLedger', component: () => import('@/views/general-ledger/ProjectDetailLedger.vue'), meta: { title: '核算项目明细账', group: '总账', module: 'accounting' } },
        { path: 'general-ledger/project-balance', name: 'ProjectBalanceSheet', component: () => import('@/views/general-ledger/ProjectBalanceSheet.vue'), meta: { title: '核算项目余额表', group: '总账', module: 'accounting' } },
        // --- 出纳 ---
        { path: 'cashier/diary', name: 'CashierDiary', component: Placeholder, props: { title: '日记账' }, meta: { title: '日记账', group: '出纳', module: 'accounting' } },
        { path: 'cashier/biz-type', name: 'CashierBizType', component: Placeholder, props: { title: '业务类型' }, meta: { title: '业务类型', group: '出纳', module: 'accounting' } },
        { path: 'cashier/check-general', name: 'CashierCheckGeneral', component: Placeholder, props: { title: '核对总账' }, meta: { title: '核对总账', group: '出纳', module: 'accounting' } },
        // --- 发票 ---
        { path: 'invoice/input', name: 'InvoiceInput', component: () => import('@/views/invoice/InvoiceInput.vue'), meta: { title: '进项发票', group: '发票', module: 'accounting' } },
        { path: 'invoice/output', name: 'InvoiceOutput', component: Placeholder, props: { title: '销项发票' }, meta: { title: '销项发票', group: '发票', module: 'accounting' } },
        { path: 'invoice/expense', name: 'InvoiceExpense', component: Placeholder, props: { title: '费用发票' }, meta: { title: '费用发票', group: '发票', module: 'accounting' } },
        { path: 'invoice/title', name: 'InvoiceTitle', component: Placeholder, props: { title: '发票抬头' }, meta: { title: '发票抬头', group: '发票', module: 'accounting' } },
        { path: 'invoice/setting', name: 'InvoiceSetting', component: Placeholder, props: { title: '发票设置' }, meta: { title: '发票设置', group: '发票', module: 'accounting' } },
        // --- 结账 ---
        { path: 'closing/carry-forward', name: 'ClosingCarryForward', component: Placeholder, props: { title: '期末结转' }, meta: { title: '期末结转', group: '结账', module: 'accounting' } },
        { path: 'closing/close', name: 'ClosingClose', component: Placeholder, props: { title: '结账' }, meta: { title: '结账', group: '结账', module: 'accounting' } },
        // --- 报表 ---
        { path: 'reports/balance-sheet', name: 'BalanceSheetReport', component: Placeholder, props: { title: '资产负债表' }, meta: { title: '资产负债表', group: '报表', module: 'accounting' } },
        { path: 'reports/income-statement', name: 'IncomeStatement', component: Placeholder, props: { title: '利润表' }, meta: { title: '利润表', group: '报表', module: 'accounting' } },
        { path: 'reports/income-statement-quarterly', name: 'IncomeStatementQuarterly', component: Placeholder, props: { title: '利润表季报' }, meta: { title: '利润表季报', group: '报表', module: 'accounting' } },
        { path: 'reports/cash-flow', name: 'CashFlowStatement', component: Placeholder, props: { title: '现金流量表' }, meta: { title: '现金流量表', group: '报表', module: 'accounting' } },
        { path: 'reports/cash-flow-quarterly', name: 'CashFlowStatementQuarterly', component: Placeholder, props: { title: '现金流量表季报' }, meta: { title: '现金流量表季报', group: '报表', module: 'accounting' } },

        /* ====== 设置模块 ====== */
        {
          path: 'settings',
          name: 'SettingsOverview',
          component: () => import('@/layouts/components/MenuPanel.vue'),
          meta: { title: '设置', module: 'settings' },
        },
        { path: 'settings/account', name: 'SettingsAccount', component: SettingsAccount, meta: { title: '科目', group: '基础数据' } },
        { path: 'settings/opening', name: 'SettingsOpening', component: () => import('@/views/settings/Opening.vue'), meta: { title: '期初', group: '基础数据' } },
        { path: 'settings/aux-dict', name: 'SettingsAuxDict', component: () => import('@/views/settings/AuxDict.vue'), meta: { title: '辅助字典', group: '基础数据' } },
        { path: 'settings/currency', name: 'SettingsCurrency', component: () => import('@/views/settings/Currency.vue'), meta: { title: '币别', group: '基础数据' } },
        { path: 'settings/summary', name: 'SettingsSummary', component: () => import('@/views/settings/Summary.vue'), meta: { title: '凭证摘要', group: '基础数据' } },
        { path: 'settings/voucher-word', name: 'SettingsVoucherWord', component: () => import('@/views/settings/VoucherWord.vue'), meta: { title: '凭证字', group: '基础数据' } },
        { path: 'settings/voucher-template', name: 'SettingsVoucherTemplate', component: Placeholder, props: { title: '凭证模板' }, meta: { title: '凭证模板', group: '基础设置' } },
        { path: 'settings/voucher-config', name: 'SettingsVoucherConfig', component: Placeholder, props: { title: '凭证配置' }, meta: { title: '凭证配置', group: '基础设置' } },
        { path: 'settings/diary-template', name: 'SettingsDiaryTemplate', component: Placeholder, props: { title: '日记账模板' }, meta: { title: '日记账模板', group: '基础设置' } },
        { path: 'settings/archive', name: 'SettingsArchive', component: Placeholder, props: { title: '归档管理' }, meta: { title: '归档管理', group: '基础设置' } },
        { path: 'settings/system', name: 'SettingsSystem', component: Placeholder, props: { title: '系统设置' }, meta: { title: '系统设置', group: '基础设置' } },
        { path: 'settings/audit-export', name: 'SettingsAuditExport', component: Placeholder, props: { title: '审计接口文件导出' }, meta: { title: '审计接口文件导出', group: '基础设置' } },

        /* ====== 其他模块（一级菜单） ====== */
        { path: 'guide', name: 'Guide', component: Placeholder, props: { title: '新手指引' }, meta: { title: '新手指引' } },
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
