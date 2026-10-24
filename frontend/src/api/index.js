/**
 * api/index.js —— axios 实例 + 拦截器
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { getToken, clearToken } from './auth'

const request = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

// ====== 请求拦截器：自动带 Authorization ======
request.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ====== 响应拦截器：401 自动跳登录页 ======
request.interceptors.response.use(
  (res) => res,
  (err) => {
    const status = err?.response?.status
    const msg = err?.response?.data?.detail || err.message || '请求失败'

    if (status === 401) {
      clearToken()
      const url = err.config?.url || ''
      if (!url.includes('/auth/login') && !url.includes('/auth/register')) {
        ElMessage.warning('登录已失效，请重新登录')
        // 直接改 hash（hash history），避免循环依赖
        window.location.hash = '#/login'
      }
    } else {
      ElMessage.error(msg)
    }

    return Promise.reject(err)
  }
)

export default request
