import axios from 'axios'

/**
 * 共享 axios 实例 —— 全前端模块统一引用，避免每个 api 文件重复创建实例。
 * baseURL 支持通过 Vite 环境变量 VITE_API_BASE 覆盖（生产 / 云部署用）。
 */
const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE ?? 'http://localhost:8000/api',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器：自动携带鉴权 token
// 注：业务代码完成后将接入微信 / 支付宝扫码登录，token 改为 httpOnly Cookie 更安全
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

// 响应拦截器：统一处理错误（后续接入 ElMessage 全局提示）
http.interceptors.response.use(
  (response) => response,
  (error) => {
    return Promise.reject(error)
  },
)

export default http
