<script setup lang="ts">

const pageTitle = '凭证录入'
const pendingReason = '当前凭证由业务单（采购 / 差旅 / 报销 / 合同）审批通过后自动生成，后端手工录入写入接口尚未与账务联动打通。为避免产生孤立手工凭证，凭证录入功能暂未开放，请以「查看凭证」为准。功能待启用，敬请期待。'
</script>

<template>
  <div class="pending-page">
    <el-card shadow="never" class="pending-card">
      <template #header>
        <div class="pending-header">
          <span class="pending-title">{{ pageTitle }}</span>
          <el-tag type="info" size="small" effect="plain">功能待启用</el-tag>
        </div>
      </template>
      <el-empty :description="`${pageTitle} · 功能待启用`">
        <template #default>
          <el-alert
            :title="`${pageTitle} 暂未开放`"
            :description="pendingReason"
            type="warning"
            :closable="false"
            show-icon
            class="pending-alert"
          />
        </template>
      </el-empty>
    </el-card>
  </div>
</template>

<style scoped>
.pending-page {
  padding: 16px;
}
.pending-card {
  max-width: 880px;
  margin: 0 auto;
}
.pending-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.pending-title {
  font-size: 16px;
  font-weight: 600;
}
.pending-alert {
  margin-top: 8px;
  text-align: left;
  white-space: normal;
}
</style>
