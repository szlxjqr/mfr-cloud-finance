<script setup lang="ts">
/** 财务 · 概览：关键科目余额 + 待入账凭证（报销/支付等未审核凭证一键入账）。 */
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getSubjectBalance, listVouchers } from '@/api/ledger'
import { auditVoucher } from '@/api/voucher'
import type { SubjectBalance, Voucher } from '@/types/ledger'

const router = useRouter()
const loading = ref(false)
const balances = ref<SubjectBalance[]>([])
const vouchers = ref<Voucher[]>([])
const auditingId = ref<number | null>(null)

const TARGET_CODES = ['1002', '3001', '5001', '2221.01.02']
const CODE_LABELS: Record<string, string> = {
  '1002': '银行存款余额',
  '3001': '实收资本',
  '5001': '主营业务收入',
  '2221.01.02': '销项税额',
}

function balanceOf(code: string): number {
  const b = balances.value.find((x) => x.code === code)
  if (!b) return 0
  // 余额取借贷方向末端的绝对值
  return Number(b.ending_debit) || Number(b.ending_credit) || 0
}

const cards = computed(() =>
  TARGET_CODES.map((code) => ({ code, label: CODE_LABELS[code], value: balanceOf(code) })),
)

const pendingVouchers = computed(() => vouchers.value.filter((v) => v.status === '未审核'))

async function load() {
  loading.value = true
  try {
    const [balRes, vouRes] = await Promise.all([getSubjectBalance(), listVouchers()])
    balances.value = balRes.data || []
    vouchers.value = vouRes.data || []
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载财务概览失败')
  } finally {
    loading.value = false
  }
}
onMounted(load)

async function audit(v: Voucher) {
  auditingId.value = v.id
  try {
    await auditVoucher(v.id)
    ElMessage.success(`凭证 ${v.voucher_no} 已入账`)
    load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '入账失败')
  } finally {
    auditingId.value = null
  }
}

function go(path: string) {
  router.push(path)
}
</script>

<template>
  <div style="padding: 16px;">
    <el-card shadow="never" style="margin-bottom: 16px;">
      <div style="display: flex; align-items: center; gap: 16px; flex-wrap: wrap;">
        <h2 style="margin: 0; font-size: 20px;">财务概览</h2>
        <div style="margin-left: auto; display: flex; gap: 8px;">
          <el-button type="primary" @click="go('/finance/capital')">股东入资</el-button>
          <el-button type="primary" @click="go('/finance/revenue')">收入</el-button>
          <el-button @click="load">刷新</el-button>
        </div>
      </div>
    </el-card>

    <!-- 关键科目余额卡片 -->
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px;">
      <el-card v-for="c in cards" :key="c.code" shadow="hover">
        <div style="color: #909399; font-size: 13px;">{{ c.label }}</div>
        <div style="font-size: 22px; font-weight: 600; margin-top: 6px; color: #303133;">
          ¥{{ c.value.toFixed(2) }}
        </div>
        <div style="color: #c0c4cc; font-size: 12px; margin-top: 4px;">科目 {{ c.code }}</div>
      </el-card>
    </div>

    <!-- 待入账凭证 -->
    <el-card shadow="never">
      <template #header>
        <div style="display: flex; align-items: center;">
          <span style="font-weight: 600;">待入账凭证</span>
          <el-tag type="warning" style="margin-left: 8px;">{{ pendingVouchers.length }} 张</el-tag>
          <span style="color: #909399; font-size: 12px; margin-left: 12px;">
            报销单/报销支付等凭证在生成后处于「未审核」，需在此一键入账后方在账簿与报表体现
          </span>
        </div>
      </template>

      <DataLoader :loading="loading" :is-empty="!pendingVouchers.length">
        <el-table :data="pendingVouchers" border stripe height="420">
          <el-table-column prop="voucher_no" label="凭证号" width="180" />
          <el-table-column prop="period" label="期间" width="100" />
          <el-table-column prop="source_type" label="来源" width="120" />
          <el-table-column prop="summary" label="摘要" min-width="200" show-overflow-tooltip />
          <el-table-column prop="maker" label="制单人" width="120" />
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button
                type="success"
                size="small"
                :loading="auditingId === row.id"
                @click="audit(row)"
              >入账</el-button>
            </template>
          </el-table-column>
        </el-table>
      </DataLoader>

      <el-empty v-if="!loading && !pendingVouchers.length" description="暂无待入账凭证" />
    </el-card>
  </div>
</template>
