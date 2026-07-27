<template>
  <div class="expense-form-wrap" v-html="rendered"></div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ReimbursementBill } from '@/types/reimburse'
import { buildReimbursePrintHtml } from '@/utils/reimbursePrint'

const props = defineProps<{ bill: ReimbursementBill }>()

// 弹窗直接复用打印 HTML：屏幕显示 = 打印输出，老板在弹窗里看到的和打印出来的完全一致
const rendered = computed(() => buildReimbursePrintHtml(props.bill))
</script>

<style scoped>
/* 弹窗容器：去除白边，让 A4 风格的表单在弹窗内看起来更紧凑 */
.expense-form-wrap {
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
  color: #000;
}
/* A4 风格包裹：屏幕预览也按 A4 尺寸 */
.expense-form-wrap :deep(.expense-form) {
  width: 210mm;
  min-height: 297mm;
  margin: 0 auto;
  padding: 8mm 12mm;
  box-sizing: border-box;
  background: #fff;
  font-size: 9pt;
}
.expense-form-wrap :deep(.form-title) {
  position: relative;
  text-align: center;
  border-bottom: 2px solid #000;
  padding-bottom: 8px;
  margin-bottom: 12px;
}
.expense-form-wrap :deep(.company) {
  font-size: 15pt;
  font-weight: bold;
  letter-spacing: 2px;
}
.expense-form-wrap :deep(.doc-type) {
  font-size: 17pt;
  font-weight: bold;
  margin-top: 3px;
}
.expense-form-wrap :deep(.unit) {
  position: absolute;
  right: 0;
  top: 0;
  font-size: 9pt;
  color: #333;
}
.expense-form-wrap :deep(.section-title) {
  font-weight: bold;
  margin: 12px 0 5px;
  font-size: 10pt;
}
.expense-form-wrap :deep(table) {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}
.expense-form-wrap :deep(.info-table td),
.expense-form-wrap :deep(.detail-table th),
.expense-form-wrap :deep(.detail-table td),
.expense-form-wrap :deep(.sign-table td) {
  border: 1px solid #333;
  padding: 3px 5px;
  word-break: break-all;
  vertical-align: middle;
}
.expense-form-wrap :deep(.label) {
  background: #f2f2f2;
  font-weight: 600;
  text-align: center;
  width: 78px;
  font-size: 8.5pt;
}
.expense-form-wrap :deep(.detail-table th) {
  background: #f2f2f2;
  font-weight: 600;
  text-align: center;
  font-size: 8pt;
}
.expense-form-wrap :deep(.detail-table td) {
  font-size: 8pt;
}
.expense-form-wrap :deep(.left) {
  text-align: left;
}
.expense-form-wrap :deep(.num) {
  text-align: right;
  font-family: 'Courier New', monospace;
  color: #000;
  font-weight: 600;
}
.expense-form-wrap :deep(.num-strong) {
  text-align: right;
  font-weight: bold;
  font-family: 'Courier New', monospace;
  font-size: 9pt;
}
.expense-form-wrap :deep(.cn-amount) {
  font-size: 9pt;
  font-weight: 600;
}
.expense-form-wrap :deep(.sign-table td) {
  text-align: center;
  height: 28px;
}
.expense-form-wrap :deep(.sign-row td) {
  height: 56px;
}
.expense-form-wrap :deep(.bill-no) {
  word-break: break-all;
  text-align: center;
  font-family: 'Courier New', monospace;
  font-size: 11pt;
  font-weight: 600;
}
.expense-form-wrap :deep(.invoice-total) {
  text-align: right;
  font-family: 'Courier New', monospace;
  color: #000;
  font-weight: bold;
  font-size: 10pt;
}
.expense-form-wrap :deep(.date-cell) {
  white-space: nowrap;
  text-align: center;
  font-size: 8pt;
}
.expense-form-wrap :deep(.form-footer) {
  margin-top: 12px;
  font-size: 9pt;
  color: #333;
}
</style>
