<script setup lang="ts">
/** 诚实「功能待启用」页：用于尚无真实数据模型/后端支撑的子页面。
 * 与项目「不造假数据」原则一致——明确告知未开放原因，而非伪装「敬请期待」。
 */
defineProps<{
  title?: string
  reason?: string
}>()
</script>

<template>
  <div style="padding: 32px;">
    <el-card shadow="never" style="max-width: 760px; margin: 0 auto;">
      <el-empty :image-size="140" description="">
        <template #description>
          <div style="text-align: left;">
            <p style="color: #303133; font-size: 17px; font-weight: 600; margin: 0 0 6px;">
              {{ title || '该功能' }} · 待启用
            </p>
            <p style="color: #909399; font-size: 13px; margin: 0;">
              当前版本尚未开放，以下为未启用原因：
            </p>
          </div>
        </template>
      </el-empty>
      <el-alert
        :title="reason || '该模块需要配套的数据模型与后端支撑，目前尚未建模，故未开放。'"
        type="info"
        :closable="false"
        show-icon
        style="margin-top: 8px;"
      />
      <p style="color: #c0c4cc; font-size: 12px; text-align: center; margin: 16px 0 0;">
        如需启用，请联系实施方补全对应基础数据表与接口。
      </p>
    </el-card>
  </div>
</template>
