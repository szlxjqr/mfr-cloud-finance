<script setup lang="ts">

const pageTitle = '原始凭证'
const pendingReason = '原始凭证需对接发票 / 附件扫描与影像归档，后端暂未建立原始凭证影像库，功能待启用，敬请期待。'
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
