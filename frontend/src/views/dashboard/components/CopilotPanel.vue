<script setup lang="ts">
/**
 * 首页右侧 · 财务助手对话面板（方案 B 入口/镜像）
 * 按既定方案 B：本 app 不内置大模型，对话编排由 WorkBuddy 承载；
 * 此面板为「对话窗」的视觉载体与入口预览，真实业务对话在 WorkBuddy 侧完成。
 */
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import AppIcon from '@/components/AppIcon.vue'

const input = ref('')

const examples = [
  '记一笔采购报销',
  '本月收支怎么样？',
  '把这张发票入池',
  '生成一张工资单',
]

function openInWorkBuddy() {
  ElMessage.info('业务对话由 WorkBuddy 承载，连接器配置后将自动接入本窗')
}

function send() {
  const text = input.value.trim()
  if (!text) return
  ElMessage.info('请在 WorkBuddy 中继续该对话（本窗为入口预览）')
  input.value = ''
}
</script>

<template>
  <div class="copilot">
    <!-- 头部 -->
    <div class="copilot__header">
      <div class="copilot__avatar">
        <AppIcon name="ChatDotRound" :size="18" color="#ffffff" />
      </div>
      <div class="copilot__heading">
        <div class="copilot__title">财务助手</div>
        <div class="copilot__sub">自然语言办理业务 · 由 WorkBuddy 承载</div>
      </div>
      <span class="copilot__badge">入口预览</span>
    </div>

    <!-- 对话区 -->
    <div class="copilot__body">
      <div class="bubble bubble--bot">
        你好，我是你的财务助手 👋<br />
        未来你只需用一句话，就能办理报销、采购、查账、出报表。
      </div>

      <div class="copilot__examples">
        <span
          v-for="e in examples"
          :key="e"
          class="chip"
          @click="input = e"
        >{{ e }}</span>
      </div>

      <div class="copilot__hint">
        <AppIcon name="InfoFilled" :size="14" color="#909399" />
        <span>对话能力由 WorkBuddy 承载，本窗为入口预览。连接器配置完成后，业务将在此窗实时办理。</span>
      </div>
    </div>

    <!-- 输入区 -->
    <div class="copilot__footer">
      <el-input
        v-model="input"
        placeholder="在 WorkBuddy 中继续对话…"
        @keyup.enter="send"
      >
        <template #prefix>
          <AppIcon name="Promotion" :size="16" color="#909399" />
        </template>
      </el-input>
      <el-button type="primary" @click="openInWorkBuddy">在 WorkBuddy 中打开</el-button>
    </div>
  </div>
</template>

<style scoped>
.copilot {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-surface);
  border: 1px solid var(--border-soft);
  border-radius: var(--r-lg);
  box-shadow: var(--sh-card);
  overflow: hidden;
}

/* 头部 */
.copilot__header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  background: linear-gradient(120deg, #2f6fed 0%, #5b8def 100%);
  color: #fff;
}
.copilot__avatar {
  width: 36px;
  height: 36px;
  border-radius: var(--r-pill);
  background: rgba(255, 255, 255, 0.18);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.copilot__heading {
  flex: 1;
  min-width: 0;
}
.copilot__title {
  font-size: var(--fs-md);
  font-weight: 600;
  line-height: var(--lh-tight);
}
.copilot__sub {
  font-size: var(--fs-xs);
  opacity: 0.85;
  margin-top: 2px;
}
.copilot__badge {
  font-size: var(--fs-xs);
  padding: 2px 8px;
  border-radius: var(--r-pill);
  background: rgba(255, 255, 255, 0.18);
  white-space: nowrap;
}

/* 对话区 */
.copilot__body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  background: var(--el-fill-color-light);
}
.bubble {
  max-width: 86%;
  padding: 10px 14px;
  border-radius: 4px 14px 14px 14px;
  font-size: var(--fs-base);
  line-height: var(--lh-base);
}
.bubble--bot {
  align-self: flex-start;
  background: var(--bg-surface);
  border: 1px solid var(--border-soft);
  color: var(--el-text-color-primary);
}
.copilot__examples {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-top: 2px;
}
.chip {
  font-size: var(--fs-sm);
  padding: 6px 12px;
  border-radius: var(--r-pill);
  background: var(--bg-surface);
  border: 1px solid var(--border-soft);
  color: var(--el-color-primary);
  cursor: pointer;
  transition: all var(--motion-base) var(--ease);
}
.chip:hover {
  border-color: var(--el-color-primary);
  box-shadow: var(--sh-brand);
}
.copilot__hint {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-top: auto;
  padding: 10px 12px;
  border-radius: var(--r-md);
  background: rgba(22, 103, 255, 0.06);
  font-size: var(--fs-xs);
  color: var(--text-muted);
  line-height: var(--lh-base);
}

/* 输入区 */
.copilot__footer {
  display: flex;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border-top: 1px solid var(--border-soft);
  background: var(--bg-surface);
}
.copilot__footer :deep(.el-input) {
  flex: 1;
}
</style>
