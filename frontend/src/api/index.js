/**
 * api/index.js —— axios 实例 + 拦截器
 * 所有请求统一从这里发出，baseURL 会被 Vite 代理到后端 8000 端口。
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: '/api',
  timeout: 60000,  // OCR 识别可能慢一点
})

// 响应拦截器：统一错误提示
request.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err?.response?.data?.detail || err.message || '请求失败'
    ElMessage.error(msg)
    return Promise.reject(err)
  }
)

export default request
