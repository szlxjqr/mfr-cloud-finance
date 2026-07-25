<template>
  <el-dialog
    :model-value="visible"
    title="发票识别"
    width="520px"
    @update:model-value="$emit('update:visible', $event)"
  >
    <input
      ref="fileInput"
      type="file"
      accept=".pdf,.ofd,.png,.jpg,.jpeg"
      style="display: none"
      @change="onFile"
    />
    <el-button :loading="parsing" @click="fileInput?.click()">选择发票文件</el-button>
    <el-alert
      type="info"
      :closable="false"
      style="margin: 10px 0"
    >
      支持 PDF / OFD / 图片；图片类走浏览器 OCR，无需上传后端做识别。
    </el-alert>

    <template v-if="parsed">
      <el-form label-width="92px" class="fields">
        <el-form-item label="发票号码">
          <el-input :model-value="parsed.no" @update:model-value="setField('no', $event)" placeholder="发票号码" />
        </el-form-item>
        <el-form-item label="开票日期">
          <el-input :model-value="parsed.date" @update:model-value="setField('date', $event)" placeholder="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="销售方">
          <el-input :model-value="parsed.sellerName" @update:model-value="setField('sellerName', $event)" placeholder="销售方名称" />
        </el-form-item>
        <el-form-item label="销售方税号">
          <el-input :model-value="parsed.sellerTaxNo" @update:model-value="setField('sellerTaxNo', $event)" placeholder="纳税人识别号" />
        </el-form-item>
        <el-form-item label="金额(不含税)">
          <el-input :model-value="parsed.amount" @update:model-value="setField('amount', $event)" placeholder="金额" />
        </el-form-item>
        <el-form-item label="税额">
          <el-input :model-value="parsed.tax" @update:model-value="setField('tax', $event)" placeholder="税额" />
        </el-form-item>
        <el-form-item label="价税合计">
          <el-input :model-value="parsed.total" @update:model-value="setField('total', $event)" placeholder="价税合计" />
        </el-form-item>
      </el-form>
    </template>
    <el-empty v-else description="选择文件后自动识别" />

    <template #footer>
      <el-button @click="$emit('update:visible', false)">取消</el-button>
      <el-button @click="saveToInbox">存入发票箱</el-button>
      <el-button type="primary" :disabled="!parsed" @click="confirm">确认填入</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { parseInvoiceFile, type ParsedInvoice } from '@/utils/invoiceParser'
import { inboxApi } from '@/api/inboxApi'

const props = defineProps<{ visible: boolean; initialFile?: File | null }>()
const emit = defineEmits<{
  (e: 'update:visible', v: boolean): void
  (e: 'confirm', parsed: ParsedInvoice): void
}>()

const parsed = ref<ParsedInvoice | null>(null)
const parsing = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const pickedFile = ref<File | null>(null)

async function onFile(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0]
  if (!f) return
  pickedFile.value = f
  await doParse(f)
}

async function doParse(f: File) {
  parsing.value = true
  try {
    parsed.value = await parseInvoiceFile(f)
  } catch {
    ElMessage.error('解析失败，请检查文件格式')
    parsed.value = null
  } finally {
    parsing.value = false
  }
}

// 字段可编辑：直接改 parsed（保持与 invoiceFields 输出结构一致）
function setField(k: keyof ParsedInvoice, v: any) {
  if (parsed.value) (parsed.value as any)[k] = v
}

// 确认填入：把识别结果交给父组件（报销/采购单字段回填）
function confirm() {
  if (!parsed.value) return
  emit('confirm', parsed.value)
  emit('update:visible', false)
}

// 存入发票箱：仅存档，不回填表单
async function saveToInbox() {
  if (!parsed.value || !pickedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }
  try {
    await inboxApi.upload(pickedFile.value, JSON.stringify(parsed.value))
    ElMessage.success('已存入发票箱')
    emit('update:visible', false)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '存入失败')
  }
}

// 每次打开重置（若有 initialFile 则自动解析）
watch(() => props.visible, (v) => {
  if (v) {
    parsed.value = null
    pickedFile.value = null
    if (fileInput.value) fileInput.value.value = ''
    if (props.initialFile) {
      pickedFile.value = props.initialFile
      doParse(props.initialFile)
    }
  }
})
</script>

<style scoped>
.fields { margin-top: 8px; }
</style>
