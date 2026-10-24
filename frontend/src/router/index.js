/**
 * router/index.js —— 前端路由配置
 * 新增 /login 页 + beforeEach 登录守卫
 */
import { createRouter, createWebHashHistory } from 'vue-router'
import { isLoggedIn } from '@/api/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', public: true },
  },
  {
    path: '/',
    redirect: '/dashboard',
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '首页', requiresAuth: true },
  },
  {
    path: '/upload',
    name: 'Upload',
    component: () => import('@/views/Upload.vue'),
    meta: { title: '上传识别', requiresAuth: true },
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('@/views/History.vue'),
    meta: { title: '历史记录', requiresAuth: true },
  },
  {
    path: '/history/:id',
    name: 'InvoiceDetail',
    component: () => import('@/views/InvoiceDetail.vue'),
    meta: { title: '票据详情', requiresAuth: true },
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: { title: '系统设置', requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

// ====== 全局守卫 ======
router.beforeEach((to, from, next) => {
  const logged = isLoggedIn()

  if (to.path === '/login' && logged) {
    // 已登录还去登录页 → 回首页
    next('/dashboard')
    return
  }

  if (to.meta.requiresAuth !== false && !to.meta.public && !logged) {
    // 需要登录但未登录
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }

  next()
})

export default router
