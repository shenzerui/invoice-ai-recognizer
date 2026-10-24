/**
 * api/auth.js —— 注册 / 登录 / 当前用户
 */
import request from './index'

export function register(username, password) {
  return request.post('/auth/register', { username, password })
}

export function login(username, password) {
  return request.post('/auth/login', { username, password })
}

export function me() {
  return request.get('/auth/me')
}

// ====== localStorage 操作（纯函数，和 axios 解耦）======
const TOKEN_KEY = 'invoice_auth_token'
const USER_KEY = 'invoice_auth_user'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY) || ''
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export function getUser() {
  try {
    const raw = localStorage.getItem(USER_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function setUser(user) {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function isLoggedIn() {
  return !!getToken()
}
