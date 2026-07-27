<template>
  <div class="page">
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索单号/物品/事由" clearable style="width: 260px" @keyup.enter="load" @clear="load" />
      <el-select v-model="statusFilter" placeholder="全部状态" clearable style="width: 140px" @change="load">
        <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
      </el-select>
      <el-tag type="info" effect="plain">当前用户：{{ currentUser }}</el-tag>
    </div>

    <DataLoader :loading="loading" :is-empty="!list.length">
      <el-table :data="list" border stripe>
      <el-table-column prop="req_no" label="单号" width="160" />
      <el-table-column prop="applicant" label="申请人" width="100" />
      <el-table-column prop="department" label="部门" width="110" />
      <el-table-column label="采购物品" min-width="160" show-overflow-tooltip>
        <template #default="{ row }">{{ itemSummary(row) }}</template>
      </el-table-column>
      <el-table-column label="数量" width="80" align="center">
        <template #default="{ row }">{{ totalQty(row) }}</template>
      </el-table-column>
      <el-table-column label="预计金额" width="130" align="right">
        <template #default="{ row }">{{ row.expected_amount != null ? '¥' + Number(row.expected_amount).toFixed(2) : '-' }}</template>
      </el-table-column>
      <el-table-column prop="expected_date" label="预计日期" width="120" />
      <el-table-column prop="reason" label="事由" min-width="140" show-overflow-tooltip />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <StatusTag :status="row.status" />
        </template>
      </el-table-column>
      <el-table-column prop="approve_date" label="审批日期" width="120" />
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">查看</el-button>
          <el-button
            v-if="row.status === '已通过'"
            link
            type="primary"
            @click="payReq(row)"
          >报销</el-button>
        </template>
      </el-table-column>
    </el-table>
    </DataLoader>

    <!-- 采购申请单详情弹窗（A4 预览 + 打印） -->
    <el-dialog v-model="detailVisible" title="采购申请单" width="900px" :close-on-click-modal="false" class="detail-dialog">
      <div v-if="detailLoading" class="detail-loading">正在加载采购申请单…</div>
      <PurchasePrint v-else :purchase="detail" />
      <template #footer>
        <div class="detail-footer">
          <el-button @click="detailVisible = false">关闭</el-button>
          <el-button type="primary" @click="printPurchase">打印采购申请单</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 独立打印层：不放在 el-dialog 内，避免弹窗遮罩/transform/高度影响打印内容 -->
    <div class="print-layer">
      <PurchasePrint v-if="!detailLoading && detail.id" :purchase="detail" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { purchaseApi } from '@/api/purchase'
import { reimburseApi } from '@/api/reimburse'
import type { PurchaseReq } from '@/types/purchase'
import PurchasePrint from './PurchasePrint.vue'

const router = useRouter()
const currentUser = '沈雷'
const statusOptions = ['草稿', '待审批', '已通过', '已驳回']

const keyword = ref('')
const statusFilter = ref<string | null>(null)
const list = ref<PurchaseReq[]>([])
const loading = ref(false)

const detailVisible = ref(false)
const detailLoading = ref(false)
const detail = reactive<PurchaseReq>({
  id: 0,
  req_no: '',
  applicant: '',
  department: '',
  item_name: '',
  spec: '',
  quantity: 1,
  expected_amount: null,
  supplier: '',
  expected_date: '',
  reason: '',
  status: '草稿',
  is_rd_project: '否',
  rd_project_code: '',
  remark: '',
  items: [],
})

function itemSummary(row: PurchaseReq): string {
  const items = row.items && row.items.length ? row.items : null
  if (items) {
    const first = items[0].item_name || '-'
    return items.length > 1 ? `${first} 等${items.length}项` : first
  }
  return row.item_name || '-'
}
function totalQty(row: PurchaseReq): number {
  if (row.items && row.items.length) {
    return row.items.reduce((s, it) => s + (Number(it.quantity) || 0), 0)
  }
  return Number(row.quantity) || 0
}

async function load() {
  loading.value = true
  try {
    const params: { keyword?: string; status?: string; applicant: string } = { applicant: currentUser }
    if (keyword.value) params.keyword = keyword.value
    if (statusFilter.value) params.status = statusFilter.value
    const res = await purchaseApi.list(params)
    list.value = res.data
  } finally {
    loading.value = false
  }
}

async function openDetail(row: PurchaseReq) {
  // 列表数据可能不含完整 items，打开打印预览时必须重新取详情。
  detailLoading.value = true
  detailVisible.value = true
  try {
    const res = await purchaseApi.get(row.id)
    Object.assign(detail, res.data)
  } catch (e: any) {
    // 详情接口失败时仍展示列表行，避免弹窗白屏。
    Object.assign(detail, row)
    ElMessage.warning(e?.response?.data?.detail || '详情加载失败，已展示列表数据')
  } finally {
    detailLoading.value = false
  }
}

function printPurchase() {
  console.log('[print] printPurchase called', { detail })
  const p = detail
  const rows = (p.items && p.items.length) ? p.items : []

  // 金额安全格式化：兼容 number / 数字字符串 / null
  const fmtMoney = (v: any, fallback = '-'): string => {
    const n = Number(v)
    return Number.isFinite(n) ? n.toFixed(2) : fallback
  }

  const moneyToChinese = (n: number): string => {
    if (!isFinite(n)) return '-'
    if (n < 0) return '负' + moneyToChinese(-n)
    if (n === 0) return '零元整'
    const intPart = Math.floor(n)
    const cents = Math.round((n - intPart) * 100)
    const digit = ['零', '壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖']
    const unit = ['', '拾', '佰', '仟']
    const secUnit = ['', '万', '亿', '兆']
    let intStr = ''
    if (intPart > 0) {
      const s = String(intPart)
      const secs: string[] = []
      for (let i = s.length; i > 0; i -= 4) secs.unshift(s.slice(Math.max(0, i - 4), i))
      let needZero = false
      secs.forEach((sec, idx) => {
        const secPos = secs.length - 1 - idx
        let secStr = ''
        let zeroInSec = false
        for (let i = 0; i < sec.length; i++) {
          const d = sec.charCodeAt(i) - 48
          const unitPos = sec.length - 1 - i
          if (d === 0) { zeroInSec = true }
          else {
            if (zeroInSec || (needZero && secStr.length > 0)) secStr += digit[0]
            secStr += digit[d] + unit[unitPos]
            zeroInSec = false
          }
        }
        if (secStr.length > 0) { intStr += secStr + secUnit[secPos]; needZero = zeroInSec }
        else if (needZero) { needZero = false }
      })
      intStr += '元'
    } else { intStr = '零元' }
    const jiao = Math.floor(cents / 10)
    const fen = cents % 10
    let decStr = ''
    if (jiao === 0 && fen === 0) { if (intPart > 0) decStr = '整' }
    else {
      if (jiao > 0) decStr += digit[jiao] + '角'
      else if (intPart > 0) decStr += digit[0]
      if (fen > 0) decStr += digit[fen] + '分'
    }
    return intStr + decStr
  }

  const amountInWords = moneyToChinese(Number(p.expected_amount != null ? p.expected_amount : 0))

  const detailRows = rows.length
    ? rows.map((it, idx) => `
      <tr>
        <td style="text-align:center;width:40px">${idx + 1}</td>
        <td class="left">${it.item_name}</td>
        <td class="left">${it.spec || '-'}</td>
        <td style="text-align:center">${it.quantity}</td>
        <td class="num">${fmtMoney(it.unit_price)}</td>
        <td class="num">${fmtMoney(it.amount ?? 0, '0.00')}</td>
        <td class="left">${it.supplier || '-'}</td>
        <td class="left">${it.remark || '-'}</td>
      </tr>`).join('')
    : `<tr><td colspan="8" style="text-align:center;color:#999;padding:20px">暂无采购明细</td></tr>`

  const html = `<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>采购申请单</title>
<style>
@page { size: A4; margin: 8mm 12mm; }
body { font-family: 'PingFang SC','Microsoft YaHei',sans-serif; padding:0; margin:0; }
.purchase-form { width:210mm; min-height:297mm; margin:0 auto; padding:6mm 12mm; box-sizing:border-box; background:#fff; color:#000; font-size:9pt; }
.form-title { position:relative; text-align:center; border-bottom:2px solid #000; padding-bottom:8px; margin-bottom:12px; }
.company { font-size:15pt; font-weight:bold; letter-spacing:2px; }
.doc-type { font-size:17pt; font-weight:bold; margin-top:3px; }
.unit { position:absolute; right:0; top:0; font-size:9pt; color:#333; }
.section-title { font-weight:bold; margin:12px 0 5px; font-size:10pt; }
table { width:100%; border-collapse:collapse; table-layout:fixed; }
.info-table td, .detail-table th, .detail-table td, .sign-table td { border:1px solid #333; padding:3px 5px; word-break:break-all; vertical-align:middle; }
.label { background:#f2f2f2; font-weight:600; text-align:center; width:78px; font-size:8.5pt; }
.detail-table th { background:#f2f2f2; font-weight:600; text-align:center; font-size:8pt; }
.detail-table td { font-size:8pt; }
.num { text-align:right; font-family:'Courier New',monospace; }
.num-strong { text-align:right; font-weight:bold; font-family:'Courier New',monospace; font-size:9pt; }
.cn-amount { font-size:9pt; font-weight:600; }
.sign-table td { text-align:center; height:28px; }
.sign-row td { height:56px; }
.form-footer { margin-top:12px; font-size:9pt; color:#333; }
@media print { .no-print { display:none; } }
</style></head>
<body>
<div class="purchase-form">
  <div class="form-title">
    <div class="company">深圳市流形机器人科技有限公司</div>
    <div class="doc-type">采购申请单</div>
    <div class="unit">单位：元</div>
  </div>
  <div class="section-title">一、基本信息</div>
  <table class="info-table base-table">
    <tr>
      <td class="label">申请单号</td><td class="bill-no" style="word-break:break-all;text-align:center;font-family:'Courier New',monospace;font-size:8.5pt">${p.req_no || '-'}</td>
      <td class="label">申请日期</td><td style="white-space:nowrap;text-align:center;font-size:8pt">${p.submit_date || '-'}</td>
      <td class="label">申请人</td><td>${p.applicant || '-'}</td>
    </tr>
    <tr>
      <td class="label">部门</td><td>${p.department || '-'}</td>
      <td class="label">成本中心</td><td>${p.department || '-'}</td>
      <td class="label">归属研发</td><td>${p.is_rd_project || '否'}${p.is_rd_project === '是' && p.rd_project_code ? '（' + p.rd_project_code + '）' : ''}</td>
    </tr>
    <tr><td class="label">采购事由</td><td colspan="5">${p.reason || '-'}</td></tr>
    <tr><td class="label">备注</td><td colspan="5">${p.remark || '-'}</td></tr>
  </table>
  <div class="section-title">二、采购明细</div>
  <table class="detail-table">
    <thead><tr>
      <th style="width:40px">序号</th><th>物品/服务名称</th><th style="width:120px">规格/型号</th>
      <th style="width:60px">数量</th><th style="width:90px">单价(元)</th><th style="width:100px">预算金额(元)</th>
      <th style="width:130px">建议供应商</th><th>备注</th>
    </tr></thead>
    <tbody>${detailRows}</tbody>
  </table>
  <div class="section-title">三、汇总与付款</div>
  <table class="info-table summary-table">
    <tr>
      <td class="label">采购总金额<br><span style="font-size:7pt;font-weight:normal;color:#555">（元）</span></td>
      <td class="num-strong" colspan="2">¥${fmtMoney(p.expected_amount, '0.00')}</td>
      <td class="label">金额大写</td>
      <td colspan="3" class="cn-amount">${amountInWords}</td>
    </tr>
    <tr>
      <td class="label">状态</td><td>${p.status}</td>
      <td class="label">审批人</td><td>${p.approver || '-'}</td>
      <td class="label">审批日期</td><td style="white-space:nowrap;text-align:center;font-size:8pt" colspan="2">${p.approve_date || '-'}</td>
    </tr>
    <tr><td class="label">审批意见</td><td colspan="6">${p.approve_remark || '-'}</td></tr>
  </table>
  <div class="section-title">四、审批签章</div>
  <table class="sign-table">
    <tr><td class="label">申请人</td><td class="label">项目负责人/部门负责人</td><td class="label">财务负责人</td><td class="label">总经理</td></tr>
    <tr class="sign-row"><td>${p.applicant || ''}</td><td></td><td></td><td></td></tr>
  </table>
  <div class="form-footer">备注：本单经审批通过后方可执行采购；金额以实际采购发票为准，差异应在审批意见中说明。</div>
</div>
</body></html>`

  // 使用隐藏 iframe 打印，不被浏览器弹窗拦截
  const iframe = document.createElement('iframe')
  iframe.style.cssText = 'position:fixed;top:-9999px;left:-9999px;width:0;height:0;border:none;'
  document.body.appendChild(iframe)
  const doc = iframe.contentWindow!.document
  doc.open()
  doc.write(html)
  doc.close()
  // 等 iframe 加载完成后触发打印
  iframe.contentWindow!.focus()
  iframe.contentWindow!.print()
  // 打印完后清理 iframe
  setTimeout(() => { if (iframe.parentNode) iframe.parentNode.removeChild(iframe) }, 2000)
}

async function payReq(row: PurchaseReq) {
  try {
    await ElMessageBox.confirm(
      `确认将采购单「${row.req_no || ('#' + row.id)}」转为报销单？生成后进入草稿态，可挂接发票后提交审批。`,
      '转报销单确认',
      { type: 'warning', confirmButtonText: '确认转换', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  try {
    const res = await reimburseApi.fromPurchase(row.id)
    ElMessage.success(`已生成报销单「${res.data.bill_no}」，请挂接发票后提交`)
    router.push('/purchase/reimburse')
  } catch (e: any) {
    const status = e?.response?.status
    const detail = e?.response?.data?.detail || '操作失败'
    if (status === 409) {
      ElMessage.warning(detail + '，将跳转到采购报销列表')
      router.push('/purchase/reimburse')
    } else {
      ElMessage.error(detail)
    }
  }
}

onMounted(load)
</script>

<style scoped>
.page { padding: 16px; }
.toolbar { display: flex; gap: 12px; margin-bottom: 12px; align-items: center; }
.detail-footer { display: flex; justify-content: flex-end; gap: 12px; }
.detail-loading { padding: 80px 0; text-align: center; color: #909399; }
.print-layer { display: none; }
</style>
<style>
@media print {
  /* 不使用 visibility 隐藏：Chromium 打印预览会把继承层级一起裁掉。 */
  body > *:not(#app) { display: none !important; }
  #app > *:not(.print-layer) { display: none !important; }
  .print-layer {
    display: block !important;
    position: static !important;
    width: auto !important;
    min-height: 0 !important;
    background: #fff !important;
  }
  .el-overlay,
  .el-dialog__wrapper { display: none !important; }
}
</style>
