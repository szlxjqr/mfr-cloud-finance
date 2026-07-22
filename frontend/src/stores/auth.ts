import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { CurrentUser, LoginResp } from '@/types/employee'

/**
 * 登录态全局存储：token + 当前用户。
 * 持久化到 localStorage，刷新不丢失；顶栏 / 路由守卫共享。
 */
export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const user = ref<CurrentUser | null>(
    JSON.parse(localStorage.getItem('user') || 'null'),
  )

  function setAuth(resp: LoginResp) {
    token.value = resp.token
    user.value = {
      username: resp.username,
      role: resp.role,
      employee_no: resp.employee_no,
      name: resp.name ?? null,
    }
    localStorage.setItem('token', resp.token)
    localStorage.setItem('user', JSON.stringify(user.value))
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  function isLoggedIn() {
    return !!token.value
  }

  return { token, user, setAuth, logout, isLoggedIn }
})
