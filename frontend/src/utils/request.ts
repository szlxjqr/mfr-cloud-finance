import axios from 'axios'

/**
 * 共享 axios 实例 —— 全前端模块统一引用，避免每个 api 文件重复创建实例。
 * baseURL 支持通过 Vite 环境变量 VITE_API_BASE 覆盖（生产 / 云部署用）。
 */
const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE ?? '/api',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器：自动携带鉴权 Authorization 头（修正原 Authorization 拼写）
http.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// 响应拦截器：401 未登录 / 过期自动清除凭据并跳登录页
http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (location.hash !== '#/login') {
        location.hash = '#/login'
      }
    }
    return Promise.reject(error)
  },
)

export default http
