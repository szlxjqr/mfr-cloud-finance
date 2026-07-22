<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { login } from '@/api/employee'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const loading = ref(false)
const form = reactive({
  username: '',
  password: '',
})

async function handleLogin() {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const { data } = await login({ username: form.username, password: form.password })
    authStore.setAuth(data)
    ElMessage.success(`欢迎回来，${data.name || data.username}`)
    const redirect = (route.query.redirect as string) || '/dashboard'
    router.replace(redirect)
  } catch (e: any) {
    const msg = e?.response?.data?.detail || '登录失败，请重试'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-brand">
        <span class="brand-logo">MFR</span>
        <div class="brand-text">
          <div class="brand-title">智慧经营</div>
          <div class="brand-sub">MFR 企业管理系统</div>
        </div>
      </div>

      <h2 class="login-heading">账号登录</h2>

      <el-form :model="form" size="large" @keyup.enter="handleLogin">
        <el-form-item>
          <el-input v-model="form.username" placeholder="用户名" :prefix-icon="User" clearable />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        <el-button type="primary" class="login-btn" :loading="loading" @click="handleLogin">
          登 录
        </el-button>
      </el-form>

      <div class="login-tip">
        默认管理员账号 <b>admin</b> / 密码 <b>admin123</b>，请登录后及时修改。
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  height: 100vh;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background:
    radial-gradient(1200px 600px at 20% -10%, rgba(47, 107, 255, 0.18), transparent 60%),
    radial-gradient(900px 500px at 90% 110%, rgba(0, 194, 215, 0.16), transparent 55%),
    linear-gradient(135deg, #0e1726 0%, #16233b 100%);
}

.login-card {
  width: 380px;
  max-width: calc(100vw - 32px);
  background: #fff;
  border-radius: 16px;
  padding: 32px 32px 28px;
  box-shadow: 0 20px 60px rgba(8, 15, 30, 0.45);
}

.login-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
}
.brand-logo {
  font-size: 18px;
  font-weight: 800;
  letter-spacing: 0.5px;
  color: #fff;
  background: var(--brand-grad);
  border-radius: 8px;
  padding: 6px 12px;
  box-shadow: 0 2px 8px rgba(47, 107, 255, 0.28);
}
.brand-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--el-text-color-primary);
}
.brand-sub {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.login-heading {
  font-size: 20px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin: 6px 0 22px;
}

.login-btn {
  width: 100%;
  font-weight: 600;
  letter-spacing: 4px;
  margin-top: 4px;
}

.login-tip {
  margin-top: 18px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  text-align: center;
  line-height: 1.6;
}
.login-tip b {
  color: var(--el-color-primary);
}
</style>
