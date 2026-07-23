<template>
  <div class="print-page">
    <!-- 操作栏（打印时不显示） -->
    <div class="toolbar no-print">
      <el-button type="primary" @click="doPrint">🖨 打印</el-button>
      <el-button @click="goBack">返回</el-button>
      <span style="margin-left: 12px; color: #909399">{{ contract?.employee_name }} ｜ {{ contract?.contract_type }} ｜ {{ contract?.status }}</span>
    </div>

    <!-- A4 打印页 -->
    <div v-if="data" class="a4-page">
      <h1 class="doc-title">深圳市劳动合同（适用全日制用工）</h1>
      <p class="doc-subtitle">（深圳市人力资源和社会保障局编制）</p>

      <div class="party-block">
        <div class="party-line"><strong>甲方（用人单位）：</strong>{{ data.company?.company_name || contract?.party_a || '________' }}</div>
        <div class="party-line"><strong>法定代表人（主要负责人）或委托代理人：</strong>{{ data.company?.legal_rep || '________' }}</div>
        <div class="party-line"><strong>注册地址：</strong>{{ data.company?.address || '________' }}</div>
        <div class="party-line"><strong>联系电话：</strong>{{ data.company?.phone || '________' }}</div>
      </div>
      <div class="party-block">
        <div class="party-line"><strong>乙方（劳动者）：</strong>{{ contract?.employee_name || contract?.party_b || '________' }}</div>
        <div class="party-line"><strong>身份证号码：</strong>{{ contract?.id_number || '________' }}</div>
        <div class="party-line"><strong>联系电话：</strong>{{ contract?.phone || '________' }}</div>
      </div>

      <p class="preamble">根据《中华人民共和国劳动法》、《中华人民共和国劳动合同法》及国家、省、市有关规定，甲乙双方遵循合法、公平、平等自愿、协商一致、诚实信用的原则，订立本劳动合同。</p>

      <h3>一、合同期限</h3>
      <p>（一）甲乙双方同意按以下第 <strong>{{ termIndex(contract?.contract_term) }}</strong> 种方式确定本合同期限：</p>
      <p>1.有固定期限：从 <strong>{{ contract?.start_date || '____年__月__日' }}</strong> 起至 <strong>{{ contract?.end_date || '____年__月__日' }}</strong> 止。</p>
      <p>2.无固定期限：从 ____年__月__日 起至法定终止条件出现时止。</p>
      <p>3.以完成一定工作任务为期限：从 ____年__月__日 起至 ____ 工作任务完成时止。</p>
      <p>（二）试用期：<strong>{{ contract?.probation_months || '_' }}</strong> 个月。（试用期最长不得超过6个月，且不得单独约定试用期。）</p>

      <h3>二、工作内容和工作地点</h3>
      <p>（一）乙方的工作岗位（工种）为 <strong>{{ contract?.work_content || contract?.position || '________' }}</strong>。</p>
      <p>（二）乙方的工作地点为 <strong>{{ contract?.work_location || '________' }}</strong>。</p>

      <h3>三、工作时间和休息休假</h3>
      <p>（一）甲乙双方同意按以下第 <strong>{{ workHoursIndex(contract?.work_hours_type) }}</strong> 种方式确定乙方的工作时间：</p>
      <p>1.标准工时制：每日工作不超过8小时，每周工作不超过40小时。</p>
      <p>2.综合计算工时工作制：经人力资源行政部门批准，以 ____（周/月/季/年）为周期综合计算工作时间。</p>
      <p>3.不定时工作制：经人力资源行政部门批准，实行不定时工作制。</p>
      <p>（二）乙方依法享有法定节假日、年休假、婚假、产假、丧假等假期。</p>

      <h3>四、劳动报酬</h3>
      <p>（一）乙方正常工作时间的工资按下列第 <strong>{{ payMethodIndex(contract?.pay_method) }}</strong> 种形式执行，并不得低于深圳市最低工资标准：</p>
      <p>
        1.计时工资：乙方试用期工资为 <strong>¥{{ fmt(contract?.probation_salary) }}</strong> 元/月；
        试用期满后，基本工资为 <strong>¥{{ fmt(contract?.salary) }}</strong> 元/月。
      </p>
      <p>2.计件工资：甲方应当科学合理确定劳动定额和计件单价，并予以公布。</p>
      <p>（二）甲方每月 <strong>{{ contract?.pay_day || '_' }}</strong> 日前发放工资。甲方至少每月以货币形式支付乙方工资，不得克扣或者无故拖欠。</p>
      <p>（三）甲方安排乙方延长工作时间的，应按《劳动法》第四十四条的规定支付加班工资。</p>

      <h3>五、社会保险和福利待遇</h3>
      <p>（一）甲乙双方按照国家和省、市有关规定，参加社会保险，缴纳社会保险费。</p>
      <p>（二）乙方患病或非因工负伤，甲方应按国家和省、市的有关规定给予医疗期和医疗期待遇。</p>
      <p>（三）乙方患职业病、因工负伤的，甲方按《职业病防治法》、《工伤保险条例》等有关法律法规的规定执行。</p>
      <p>（四）甲方为乙方提供以下福利待遇：<strong>{{ contract?.benefits || '无' }}</strong>。</p>

      <h3>六、劳动保护、劳动条件和职业危害防护</h3>
      <p>（一）甲方按国家和省、市有关劳动保护规定，提供符合国家安全卫生标准的劳动作业场所和必要的劳动防护用品，切实保护乙方在生产工作中的安全和健康。</p>
      <p>（二）甲方按国家和省、市有关规定，做好女员工和未成年工的特殊劳动保护工作。</p>

      <h3>七、规章制度的告知与遵守</h3>
      <p>甲方应依法建立和完善劳动规章制度，并将规章制度告知乙方。乙方应遵守甲方的劳动规章制度。</p>

      <h3>八、劳动合同的变更</h3>
      <p>甲乙双方协商一致，可以变更本合同约定的内容，并采用书面形式确定。</p>

      <h3>九、劳动合同的解除、终止和经济补偿</h3>
      <p>（一）甲乙双方解除、终止本合同，应当按照《劳动合同法》第三十六条至第四十五条、第四十六条、第四十七条的规定执行。</p>
      <p>（二）甲方应当在解除或者终止本合同时，为乙方出具解除或者终止劳动合同的证明，并在十五日内为乙方办理档案和社会保险关系转移手续。</p>
      <p>（三）乙方应当按照双方约定，办理工作交接。</p>

      <h3>十、违约责任</h3>
      <p>（一）甲方违法解除或终止本合同，应向乙方支付赔偿金。</p>
      <p>（二）乙方违反服务期约定的，应当按照约定向甲方支付违约金。违约金的数额不得超过甲方提供的培训费用。</p>
      <p>（三）乙方违反竞业限制约定的，应当按照约定向甲方支付违约金。</p>

      <h3>十一、争议处理</h3>
      <p>甲乙双方因履行本合同发生劳动争议，可以协商解决；不愿协商或者协商不成的，可以向劳动争议仲裁委员会申请仲裁。对仲裁裁决不服的，可以向人民法院提起诉讼。</p>

      <h3>十二、其他</h3>
      <p>（一）本合同未尽事宜，按国家和省、市有关法律法规规定执行。</p>
      <p>（二）本合同一式两份，甲乙双方各执一份，具有同等法律效力。</p>

      <div class="sign-block">
        <div class="sign-line">甲方（盖章）：<span>{{ data.company?.company_name }}</span></div>
        <div class="sign-line">法定代表人（签名）：<span>{{ data.company?.legal_rep || '________' }}</span></div>
        <div class="sign-line">签订日期：<span>{{ contract?.sign_date || '____年__月__日' }}</span></div>
        <div class="sign-line" style="margin-top: 16px">乙方（签名）：<span>{{ contract?.employee_name || '________' }}</span></div>
        <div class="sign-line">签订日期：<span>{{ contract?.sign_date || '____年__月__日' }}</span></div>
      </div>

      <p v-if="contract?.status === '已生效' && contract?.approver" class="approval-stamp">
        【已生效】审批人：{{ contract.approver }} ｜ 审批日期：{{ contract.approve_date }}
      </p>
    </div>

    <el-empty v-else description="合同数据加载中..." />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { hrApi } from '@/api/contract'
import type { HRContract, HRContractPrintData } from '@/types/contract'

const route = useRoute()
const router = useRouter()
const data = ref<HRContractPrintData | null>(null)
const contract = ref<HRContract | null>(null)

function toNum(v: any): number {
  if (v === null || v === undefined || v === '') return 0
  const n = Number(v)
  return Number.isFinite(n) ? n : 0
}
function fmt(v: any): string {
  return toNum(v).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function termIndex(t: string | null | undefined): string {
  const map: Record<string, string> = {
    '有固定期限': '1',
    '无固定期限': '2',
    '以完成一定工作任务为期限': '3',
  }
  return map[t || ''] || '_'
}
function workHoursIndex(t: string | null | undefined): string {
  const map: Record<string, string> = {
    '标准工时制': '1',
    '综合计算工时制': '2',
    '不定时工作制': '3',
  }
  return map[t || ''] || '_'
}
function payMethodIndex(t: string | null | undefined): string {
  const map: Record<string, string> = { '计时工资': '1', '计件工资': '2' }
  return map[t || ''] || '_'
}

async function load() {
  const id = Number(route.params.id)
  if (!id) return
  try {
    const res = await hrApi.print(id)
    data.value = res.data
    contract.value = res.data.contract
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载失败')
  }
}

function doPrint() {
  window.print()
}
function goBack() {
  router.back()
}

onMounted(load)
</script>

<style scoped>
.print-page {
  background: #e9ecef;
  min-height: 100vh;
  padding: 16px;
}
.toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  max-width: 794px;
  margin: 0 auto 12px;
}
.a4-page {
  width: 210mm;
  min-height: 297mm;
  padding: 20mm 18mm;
  margin: 0 auto;
  background: #fff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  font-family: 'SimSun', '宋体', serif;
  font-size: 13px;
  line-height: 1.8;
  color: #1a1a1a;
}
.doc-title {
  text-align: center;
  font-size: 20px;
  font-weight: 700;
  margin: 0 0 4px;
  letter-spacing: 2px;
}
.doc-subtitle {
  text-align: center;
  font-size: 12px;
  color: #666;
  margin: 0 0 16px;
}
.party-block {
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px dashed #dcdfe6;
}
.party-line {
  margin: 2px 0;
}
.preamble {
  text-indent: 2em;
  margin: 12px 0;
}
h3 {
  font-size: 14px;
  font-weight: 700;
  margin: 14px 0 6px;
  color: #1a1a1a;
}
p {
  margin: 4px 0;
  text-indent: 2em;
}
.sign-block {
  margin-top: 32px;
  padding-top: 16px;
  border-top: 1px solid #dcdfe6;
}
.sign-line {
  text-indent: 0;
  margin: 8px 0;
}
.sign-line span {
  display: inline-block;
  min-width: 200px;
  border-bottom: 1px solid #999;
  padding: 0 8px;
}
.approval-stamp {
  margin-top: 24px;
  text-align: center;
  color: #c00;
  font-weight: 600;
  text-indent: 0;
}
</style>

<style>
/* 打印时只显示 A4 页面，隐藏工具栏和背景 */
@media print {
  body {
    background: #fff !important;
    margin: 0;
  }
  .no-print, .el-alert, .el-message, .el-message-box {
    display: none !important;
  }
  .print-page {
    background: #fff !important;
    padding: 0 !important;
  }
  .a4-page {
    box-shadow: none !important;
    margin: 0 !important;
    width: 100% !important;
    min-height: auto !important;
    padding: 15mm 12mm !important;
  }
  @page {
    size: A4;
    margin: 0;
  }
}
</style>
