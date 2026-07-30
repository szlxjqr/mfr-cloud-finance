<script setup lang="ts">
/**
 * 首页（驾驶舱 + 对话窗）
 * - 左：经营驾驶舱，只放关键数据（5 个核心 KPI），不放其他任何内容
 * - 右：财务助手对话窗（方案 B 入口/镜像，真实业务对话由 WorkBuddy 承载）
 */
import { onMounted, reactive, ref } from 'vue'
import KpiCard from '@/components/KpiCard.vue'
import CopilotPanel from './components/CopilotPanel.vue'
import { getSubjectBalance, listVouchers } from '@/api/ledger'
import { getIncomeStatement } from '@/api/financial_statement'
import { formatCurrency, formatNumber } from '@/utils/format'

interface Kpi {
  key: string
  label: string
  number: string
  prefix: string
  suffix: string
  color: string
  isZero: boolean
}

const loading = ref(false)
const kpis = reactive<Kpi[]>([])

/** 科目期末余额：资产/费用取借方，负债/权益/收入取贷方 */
function balOf(rows: any[], code: string): number {
  const b = rows.find((r) => r.code === code)
  if (!b) return 0
  return Number(b.ending_debit) || Number(b.ending_credit) || 0
}

/** 科目本年累计（损益类用借贷累计差） */
function cumOf(rows: any[], code: string): number {
  const b = rows.find((r) => r.code === code)
  if (!b) return 0
  return Number(b.cum_credit) - Number(b.cum_debit)
}

async function load() {
  loading.value = true
  try {
    const now = new Date()
    const period = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
    const [balRes, vouRes, incRes] = await Promise.all([
      getSubjectBalance(),
      listVouchers(),
      getIncomeStatement(period),
    ])
    const balances = balRes.data || []
    const vouchers = vouRes.data || []
    const inc = incRes.data

    const pending = vouchers.filter((v: any) => v.status === '未审核').length
    const net = inc ? inc.operating_profit_cur : 0

    const bank = balOf(balances, '1002')
    const ar = balOf(balances, '1122')
    const rev = cumOf(balances, '5001')

    kpis.length = 0
    kpis.push(
      {
        key: 'bank',
        label: '银行存款余额',
        number: formatCurrency(bank).replace('元', ''),
        prefix: '¥',
        suffix: '',
        color: 'var(--kpi-bank)',
        isZero: Math.abs(bank) < 0.01,
      },
      {
        key: 'ar',
        label: '应收账款余额',
        number: formatCurrency(ar).replace('元', ''),
        prefix: '¥',
        suffix: '',
        color: 'var(--kpi-ar)',
        isZero: Math.abs(ar) < 0.01,
      },
      {
        key: 'rev',
        label: '主营业务收入 · 本年累计',
        number: formatCurrency(rev).replace('元', ''),
        prefix: '¥',
        suffix: '',
        color: 'var(--kpi-rev)',
        isZero: Math.abs(rev) < 0.01,
      },
      {
        key: 'pending',
        label: '待入账凭证',
        number: formatNumber(pending),
        prefix: '',
        suffix: '张',
        color: 'var(--kpi-pending)',
        isZero: pending === 0,
      },
      {
        key: 'net',
        label: '本月收支净额',
        number: formatCurrency(Math.abs(net)).replace('元', ''),
        prefix: net < 0 ? '-¥' : '¥',
        suffix: '',
        color: net < 0 ? 'var(--kpi-net-neg)' : 'var(--kpi-net-pos)',
        isZero: Math.abs(net) < 0.01,
      },
    )
  } catch {
    // 驾驶舱静默失败，保持空白而非报错打断
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="home">
    <!-- 左：经营驾驶舱（仅关键数据） -->
    <section class="home__left">
      <div class="cockpit">
        <header class="cockpit__head">
          <h2 class="cockpit__title">经营驾驶舱</h2>
          <span class="cockpit__hint">
            <i class="cockpit__dot"></i>关键数据 · 实时
          </span>
        </header>

        <div class="kpi-grid">
          <KpiCard
            v-for="k in kpis"
            :key="k.key"
            :label="k.label"
            :number="k.number"
            :prefix="k.prefix"
            :suffix="k.suffix"
            :color="k.color"
            :is-zero="k.isZero"
            :tint="k.key === 'bank'"
            :class="`kpi--${k.key}`"
          />
        </div>
      </div>
    </section>

    <!-- 右：财务助手对话窗 -->
    <section class="home__right">
      <CopilotPanel />
    </section>
  </div>
</template>

<style scoped>
.home {
  display: flex;
  gap: var(--space-5);
  height: 100%;
  min-height: 0;
  padding: var(--space-5);
  box-sizing: border-box;
}
.home__left {
  flex: 1 1 56%;
  min-width: 0;
  display: flex;
}
.home__right {
  flex: 1 1 44%;
  min-width: 0;
  min-height: 0;
}

/* 驾驶舱：标题 + 卡片区，顶部对齐不悬空 */
.cockpit {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
.cockpit__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.cockpit__title {
  margin: 0;
  font-size: var(--fs-lg);
  font-weight: 600;
  color: var(--text-strong);
  letter-spacing: -0.2px;
}
.cockpit__hint {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: var(--fs-xs);
  color: var(--text-muted);
}
.cockpit__dot {
  width: 7px;
  height: 7px;
  border-radius: var(--r-pill);
  background: var(--status-approved);
  box-shadow: 0 0 0 3px rgba(82, 196, 26, 0.16);
}

/* 驾驶舱网格：银行存款突出占整行（hero），下面 4 张 2×2 */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-auto-rows: 1fr;
  gap: var(--space-4);
  flex: 1;
  min-height: 0;
}
.kpi--bank {
  grid-column: span 2;
}
.kpi--bank .kpi-card__number {
  font-size: 46px;
}

/* 小屏：上下堆叠，对话窗置于下方 */
@media (max-width: 980px) {
  .home {
    flex-direction: column;
    height: auto;
    padding: var(--space-4);
  }
  .home__right {
    height: 520px;
  }
  .kpi-grid {
    grid-auto-rows: auto;
  }
  .kpi--bank {
    grid-column: span 1;
  }
  .kpi--bank .kpi-card__number {
    font-size: 38px;
  }
}
</style>
