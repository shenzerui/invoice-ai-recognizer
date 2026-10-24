/**
 * router/index.js —— 前端路由配置
 */
import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/dashboard',
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '首页' },
  },
  {
    path: '/upload',
    name: 'Upload',
    component: () => import('@/views/Upload.vue'),
    meta: { title: '上传识别' },
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('@/views/History.vue'),
    meta: { title: '历史记录' },
  },
  {
    path: '/history/:id',
    name: 'InvoiceDetail',
    component: () => import('@/views/InvoiceDetail.vue'),
    meta: { title: '票据详情' },
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: { title: '系统设置' },
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

export default router
