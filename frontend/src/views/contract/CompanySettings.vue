<template>
  <div class="page">
    <el-alert
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 16px"
      title="甲方（公司名称 / 法人 / 地址 / 联系方式）由本设置统一管理。所有合同、工资单、报表的甲方信息自动从此处取，无需在各单据重复填写。"
    />

    <el-card v-loading="loading" header="公司信息">
      <el-form :model="form" label-width="120px" style="max-width: 720px">
        <el-form-item label="公司名称" required>
          <el-input v-model="form.company_name" placeholder="如：深圳市流形机器人科技有限公司" />
        </el-form-item>
        <el-form-item label="法定代表人">
          <el-input v-model="form.legal_rep" placeholder="如：沈雷" />
        </el-form-item>
        <el-form-item label="注册地址">
          <el-input v-model="form.address" placeholder="如：深圳市南山区高新南一道XX号" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="form.phone" placeholder="如：0755-XXXXXXXX" />
        </el-form-item>
        <el-form-item label="税号">
          <el-input v-model="form.tax_no" placeholder="统一社会信用代码 / 纳税人识别号" />
        </el-form-item>
        <el-form-item label="开户行">
          <el-input v-model="form.bank_name" />
        </el-form-item>
        <el-form-item label="账号">
          <el-input v-model="form.bank_account" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="form.contact" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="save">保存</el-button>
          <el-button @click="load">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { companyApi } from '@/api/company'
import type { CompanySettings } from '@/types/company'

const form = reactive<CompanySettings>({
  id: 1,
  company_name: '',
  legal_rep: '',
  address: '',
  phone: '',
  tax_no: '',
  bank_name: '',
  bank_account: '',
  contact: '',
  email: '',
  remark: '',
})
const loading = ref(false)
const saving = ref(false)

async function load() {
  loading.value = true
  try {
    const res = await companyApi.get()
    Object.assign(form, res.data)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

async function save() {
  if (!form.company_name?.trim()) {
    ElMessage.warning('请填写公司名称')
    return
  }
  saving.value = true
  try {
    const res = await companyApi.update(form)
    Object.assign(form, res.data)
    ElMessage.success('已保存')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.page {
  padding: 16px;
}
</style>
