<template>
  <div class="purchase-form" ref="formRef">
    <div class="form-title">
      <div class="company">深圳市流形机器人科技有限公司</div>
      <div class="doc-type">采购申请单</div>
      <div class="unit">单位：元</div>
    </div>

    <!-- 一、基本信息 -->
    <div class="section-title">一、基本信息</div>
    <table class="info-table base-table">
      <tr>
        <td class="label">申请单号</td>
        <td class="bill-no">{{ p.req_no || '-' }}</td>
        <td class="label">申请日期</td>
        <td class="date-cell">{{ p.submit_date || '-' }}</td>
        <td class="label">申请人</td>
        <td>{{ p.applicant || '-' }}</td>
      </tr>
      <tr>
        <td class="label">部门</td>
        <td>{{ p.department || '-' }}</td>
        <td class="label">成本中心</td>
        <td>{{ p.department || '-' }}</td>
        <td class="label">归属研发</td>
        <td>{{ p.is_rd_project || '否' }}<template v-if="p.is_rd_project === '是'">（{{ p.rd_project_code || '-' }}）</template></td>
      </tr>
      <tr>
        <td class="label">采购事由</td>
        <td colspan="5">{{ p.reason || '-' }}</td>
      </tr>
      <tr>
        <td class="label">备注</td>
        <td colspan="5">{{ p.remark || '-' }}</td>
      </tr>
    </table>

    <!-- 二、采购明细 -->
    <div class="section-title">二、采购明细</div>
    <table class="detail-table">
      <thead>
        <tr>
          <th style="width: 40px">序号</th>
          <th>物品 / 服务名称</th>
          <th style="width: 120px">规格 / 型号</th>
          <th style="width: 60px">数量</th>
          <th style="width: 90px">单价(元)</th>
          <th style="width: 100px">金额(元)</th>
          <th style="width: 130px">建议供应商</th>
          <th>备注</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(it, idx) in rows" :key="idx">
          <td>{{ idx + 1 }}</td>
          <td class="left">{{ it.item_name }}</td>
          <td class="left">{{ it.spec || '-' }}</td>
          <td>{{ it.quantity }}</td>
          <td class="num">{{ it.unit_price != null ? it.unit_price.toFixed(2) : '-' }}</td>
          <td class="num">{{ (it.amount ?? 0).toFixed(2) }}</td>
          <td class="left">{{ it.supplier || '-' }}</td>
          <td class="left">{{ it.remark || '-' }}</td>
        </tr>
        <tr v-if="!rows.length">
          <td colspan="8" class="empty">暂无采购明细</td>
        </tr>
      </tbody>
    </table>

    <!-- 三、汇总与付款 -->
    <div class="section-title">三、汇总与付款</div>
    <table class="info-table summary-table">
      <tr>
        <td class="label">采购总金额<br><span class="unit-sub">（元）</span></td>
        <td class="num-strong" colspan="2">¥{{ (p.expected_amount != null ? Number(p.expected_amount) : 0).toFixed(2) }}</td>
        <td class="label">金额大写</td>
        <td colspan="3" class="cn-amount">{{ amountInWords }}</td>
      </tr>
      <tr>
        <td class="label">状态</td>
        <td>{{ p.status }}</td>
        <td class="label">审批人</td>
        <td>{{ p.approver || '-' }}</td>
        <td class="label">审批日期</td>
        <td class="date-cell" colspan="2">{{ p.approve_date || '-' }}</td>
      </tr>
      <tr>
        <td class="label">审批意见</td>
        <td colspan="6">{{ p.approve_remark || '-' }}</td>
      </tr>
    </table>

    <!-- 四、审批签章 -->
    <div class="section-title">四、审批签章</div>
    <table class="sign-table">
      <tr>
        <td class="label">申请人</td>
        <td class="label">项目负责人 / 部门负责人</td>
        <td class="label">财务负责人</td>
        <td class="label">总经理</td>
      </tr>
      <tr class="sign-row">
        <td>{{ p.applicant || '' }}</td>
        <td></td>
        <td></td>
        <td></td>
      </tr>
    </table>

    <div class="form-footer">
      备注：本单经审批通过后方可执行采购；金额以实际采购发票为准，差异应在审批意见中说明。
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PurchaseReq, PurchaseItem } from '@/types/purchase'

const props = defineProps<{ purchase: PurchaseReq }>()
const p = computed(() => props.purchase)

// 明细：优先用 items；无则按主表单条兼容旧数据
const rows = computed<PurchaseItem[]>(() => {
  const items = p.value.items || []
  if (items.length) {
    return items.map((it) => ({
      item_name: it.item_name,
      spec: it.spec,
      quantity: Number(it.quantity) || 0,
      unit_price: it.unit_price != null ? Number(it.unit_price) : null,
      amount: Number(it.amount != null ? it.amount : (Number(it.quantity) || 0) * (Number(it.unit_price) || 0)),
      supplier: it.supplier,
      remark: it.remark,
    }))
  }
  return [
    {
      item_name: p.value.item_name || '-',
      spec: p.value.spec,
      quantity: Number(p.value.quantity) || 0,
      unit_price: null,
      amount: Number(p.value.expected_amount != null ? p.value.expected_amount : 0),
      supplier: p.value.supplier,
      remark: p.value.remark,
    } as PurchaseItem,
  ]
})

// 金额大写（人民币）
const amountInWords = computed(() => {
  const v = Number(p.value.expected_amount != null ? p.value.expected_amount : 0)
  return moneyToChinese(v)
})

function moneyToChinese(n: number): string {
  if (!isFinite(n)) return '-'
  if (n < 0) return '负' + moneyToChinese(-n)
  if (n === 0) return '零元整'

  // 整数部分与小数部分分离（避免浮点误差）
  const intPart = Math.floor(n)
  const cents = Math.round((n - intPart) * 100)
  const digit = ['零', '壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖']
  const unit = ['', '拾', '佰', '仟']
  const secUnit = ['', '万', '亿', '兆']

  let intStr = ''
  if (intPart > 0) {
    const s = String(intPart)
    const secs: string[] = []
    // 每 4 位为一节，从低位到高位切分
    for (let i = s.length; i > 0; i -= 4) {
      secs.unshift(s.slice(Math.max(0, i - 4), i))
    }
    let needZero = false
    secs.forEach((sec, idx) => {
      const secPos = secs.length - 1 - idx
      let secStr = ''
      let zeroInSec = false
      for (let i = 0; i < sec.length; i++) {
        const d = sec.charCodeAt(i) - 48
        const unitPos = sec.length - 1 - i
        if (d === 0) {
          zeroInSec = true
        } else {
          if (zeroInSec || (needZero && secStr.length > 0)) secStr += digit[0]
          secStr += digit[d] + unit[unitPos]
          zeroInSec = false
        }
      }
      if (secStr.length > 0) {
        intStr += secStr + secUnit[secPos]
        needZero = zeroInSec
      } else if (needZero) {
        needZero = false
      }
    })
    intStr += '元'
  } else {
    intStr = '零元'
  }

  // 小数部分（角分）
  const jiao = Math.floor(cents / 10)
  const fen = cents % 10
  let decStr = ''
  if (jiao === 0 && fen === 0) {
    if (intPart > 0) decStr = '整'
  } else {
    if (jiao > 0) decStr += digit[jiao] + '角'
    else if (intPart > 0) decStr += digit[0]
    if (fen > 0) decStr += digit[fen] + '分'
  }
  return intStr + decStr
}
</script>

<style scoped>
/* ============ 打印控制 ============ */
@media print {
  @page {
    size: A4;
    margin: 8mm 12mm;
  }
  body {
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  .purchase-form {
    padding: 0;
    margin: 0;
    width: auto;
    min-height: auto;
    box-shadow: none;
  }
  /* 明细表自动重复表头 */
  .detail-table thead {
    display: table-header-group;
  }
  .detail-table tbody tr {
    page-break-inside: avoid;
  }
}

.purchase-form {
  width: 210mm;
  min-height: 297mm;
  margin: 0 auto;
  padding: 6mm 12mm;
  box-sizing: border-box;
  background: #fff;
  color: #000;
  font-size: 9pt;
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.form-title {
  position: relative;
  text-align: center;
  border-bottom: 2px solid #000;
  padding-bottom: 8px;
  margin-bottom: 12px;
}
.company { font-size: 15pt; font-weight: bold; letter-spacing: 2px; }
.doc-type { font-size: 17pt; font-weight: bold; margin-top: 3px; }
.unit { position: absolute; right: 0; top: 0; font-size: 9pt; color: #333; }

.section-title {
  font-weight: bold;
  margin: 12px 0 5px;
  font-size: 10pt;
}

table { width: 100%; border-collapse: collapse; table-layout: fixed; }

.info-table td,
.detail-table th,
.detail-table td,
.sign-table td {
  border: 1px solid #333;
  padding: 3px 5px;
  word-break: break-all;
  vertical-align: middle;
}

.label {
  background: #f2f2f2;
  font-weight: 600;
  text-align: center;
  width: 78px;
  font-size: 8.5pt;
}
.label .unit-sub { font-size: 7pt; font-weight: normal; color: #555; }

.base-table td { font-size: 9pt; }

.bill-no {
  word-break: break-all;
  line-height: 1.2;
  text-align: center;
  font-size: 8.5pt;
  font-family: 'Courier New', monospace;
}

.date-cell { white-space: nowrap; font-size: 8pt; text-align: center; }

.detail-table th { background: #f2f2f2; font-weight: 600; text-align: center; font-size: 8pt; }
.detail-table td { font-size: 8pt; }
.detail-table td.left { text-align: left; }

.num { text-align: right; font-family: 'Courier New', monospace; }
.num-strong { text-align: right; font-weight: bold; font-family: 'Courier New', monospace; font-size: 9pt; }
.cn-amount { font-size: 9pt; font-weight: 600; }

.summary-table .num-strong { font-size: 9pt; }

.empty { text-align: center; color: #999; padding: 20px; }

.sign-table td { text-align: center; height: 28px; }
.sign-row td { height: 56px; }

.form-footer { margin-top: 12px; font-size: 9pt; color: #333; }
</style>
