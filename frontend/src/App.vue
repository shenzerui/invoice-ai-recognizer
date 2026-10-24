<!--
  App.vue —— 应用根组件（Apple HIG 布局）
  根据登录态切换：
    - 未登录：全屏 router-view（Login.vue 独占）
    - 已登录：侧边栏 + 主内容 + 顶部用户名/登出
-->
<template>
  <!-- ========== 未登录：只渲染路由（Login.vue 全屏） ========== -->
  <router-view v-if="!loggedIn" />

  <!-- ========== 已登录：侧边栏 + 主区域 ========== -->
  <el-container v-else class="app-container">
    <el-aside width="220px" class="ac-aside">
      <!-- Logo -->
      <div class="ac-logo">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
             stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"
             class="ac-logo-icon" width="22" height="22">
          <path d="M5 3h14v18l-2-1.5L15 21l-2-1.5L11 21 9 19.5 7 21 5 19.5 5 3Z"/>
          <path d="M9 8h6M9 12h6M9 16h4"/>
        </svg>
        <span>票据识别</span>
      </div>

      <!-- 用户信息（侧栏底部） -->
      <div class="ac-user-card">
        <div class="ac-avatar">{{ userInitial }}</div>
        <div class="ac-user-meta">
          <div class="ac-user-name">{{ userName }}</div>
          <div class="ac-user-role">已登录</div>
        </div>
        <el-tooltip content="退出登录" placement="right">
          <div class="ac-logout" @click="onLogout">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"
                 width="16" height="16">
              <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
              <path d="M10 17l-5-5 5-5"/>
              <path d="M15 12H5"/>
            </svg>
          </div>
        </el-tooltip>
      </div>

      <!-- 导航分组 -->
      <div class="ac-nav-group">
        <div class="ac-nav-title">概览</div>
        <el-menu :default-active="$route.path" router>
          <el-menu-item index="/dashboard">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"
                 class="ac-nav-icon" width="18" height="18">
              <rect x="3" y="4" width="18" height="16" rx="3"/>
              <path d="M7 14l2-3 2 3 2-4 2 4"/>
            </svg>
            <span>首页</span>
          </el-menu-item>
        </el-menu>
      </div>

      <div class="ac-nav-group">
        <div class="ac-nav-title">识别</div>
        <el-menu :default-active="$route.path" router>
          <el-menu-item index="/upload">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"
                 class="ac-nav-icon" width="18" height="18">
              <path d="M7 18a4 4 0 1 1 .7-7.94A6 6 0 0 1 19 12a4 4 0 0 1-1 7.87"/>
              <path d="M12 13v6M9 16l3-3 3 3"/>
            </svg>
            <span>上传识别</span>
          </el-menu-item>
        </el-menu>
      </div>

      <div class="ac-nav-group">
        <div class="ac-nav-title">数据</div>
        <el-menu :default-active="$route.path" router>
          <el-menu-item index="/history">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"
                 class="ac-nav-icon" width="18" height="18">
              <path d="M6 4h9l4 4v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Z"/>
              <path d="M14 4v5h5M9 13h7M9 17h7"/>
            </svg>
            <span>历史记录</span>
          </el-menu-item>
        </el-menu>
      </div>

      <div class="ac-nav-group">
        <div class="ac-nav-title">系统</div>
        <el-menu :default-active="$route.path" router>
          <el-menu-item index="/settings">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"
                 class="ac-nav-icon" width="18" height="18">
              <circle cx="12" cy="12" r="3"/>
              <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 0 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 0 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.6 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 0 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 0 1 0-4h.1a1.7 1.7 0 0 0 1.6-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 0 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 0 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 0 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 0 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z"/>
            </svg>
            <span>系统设置</span>
          </el-menu-item>
        </el-menu>
      </div>
    </el-aside>

    <!-- 主区域 -->
    <el-container>
      <el-header class="ac-header">
        <div class="ac-header-left">
          <div class="ac-header-title">{{ $route.meta.title || '票据识别管理系统' }}</div>
          <div class="ac-header-sub">票据识别管理系统 · {{ userName }}</div>
        </div>
        <div class="ac-warning-pill">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
               stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"
               width="14" height="14">
            <circle cx="12" cy="12" r="9"/>
            <path d="M12 8v5M12 16h.01"/>
          </svg>
          仅供辅助参考，不对接国税查验接口
        </div>
      </el-header>

      <el-main class="ac-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { getUser, isLoggedIn, clearToken, me } from '@/api/auth'
import { ref } from 'vue'

const router = useRouter()
const currentUser = ref(getUser())

const loggedIn = computed(() => isLoggedIn())

const userName = computed(() => currentUser.value?.username || '用户')
const userInitial = computed(() => {
  const name = currentUser.value?.username || 'U'
  return name.charAt(0).toUpperCase()
})

async function refreshUser() {
  if (!isLoggedIn()) return
  try {
    const { setUser } = await import('@/api/auth')
    const res = await me()
    currentUser.value = res.data
    setUser(res.data)
  } catch { /* token 可能过期，401 拦截器会处理 */ }
}

function onLogout() {
  ElMessageBox.confirm('确定要退出登录吗？', '退出登录', {
    confirmButtonText: '退出',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(() => {
    clearToken()
    currentUser.value = null
    ElMessage.success('已退出登录')
    router.replace('/login')
  }).catch(() => {})
}

onMounted(refreshUser)
</script>

<style scoped>
.app-container { height: 100vh; }

/* 侧边栏 */
.ac-aside {
  background: var(--ac-sidebar-bg);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-right: 1px solid var(--ac-separator);
  display: flex;
  flex-direction: column;
  padding: var(--ac-4) 0;
  overflow-y: auto;
}

.ac-logo {
  display: flex;
  align-items: center;
  gap: var(--ac-3);
  padding: var(--ac-3) var(--ac-5);
  margin-bottom: var(--ac-4);
  font-size: 20px;
  font-weight: 700;
  color: var(--ac-text);
  letter-spacing: -0.02em;
}
.ac-logo-icon { color: var(--ac-blue); flex-shrink: 0; }

/* 用户卡片（侧栏底部）*/
.ac-user-card {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: auto 12px 16px;
  padding: 10px 12px;
  background: var(--ac-field);
  border-radius: 12px;
}
.ac-avatar {
  width: 32px; height: 32px;
  border-radius: 50%;
  background: var(--ac-blue);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.ac-user-meta { flex: 1; min-width: 0; }
.ac-user-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--ac-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.ac-user-role {
  font-size: 11px;
  color: var(--ac-text-tertiary);
}
.ac-logout {
  width: 28px; height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: var(--ac-text-tertiary);
  cursor: pointer;
  transition: background-color .15s, color .15s;
  flex-shrink: 0;
}
.ac-logout:hover {
  background: var(--ac-red-soft);
  color: var(--ac-red);
}

.ac-nav-group { padding: 0 var(--ac-3); margin-bottom: var(--ac-4); }
.ac-nav-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--ac-text-tertiary);
  padding: var(--ac-2) var(--ac-3);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.ac-aside .el-menu {
  background: transparent !important;
  border-right: none !important;
  padding: 0;
}
.ac-aside .el-menu-item {
  height: 44px;
  margin: 2px 0;
  border-radius: 8px;
  color: var(--ac-text-secondary) !important;
  font-size: 14px;
  font-weight: 500;
  transition: background-color var(--ac-dur) var(--ac-ease),
              color var(--ac-dur) var(--ac-ease);
}
.ac-aside .el-menu-item .ac-nav-icon {
  margin-right: 12px;
  color: inherit;
  flex-shrink: 0;
}
.ac-aside .el-menu-item:hover {
  background: var(--ac-field);
  color: var(--ac-text) !important;
}
.ac-aside .el-menu-item.is-active {
  background: var(--ac-blue-soft) !important;
  color: var(--ac-blue) !important;
  font-weight: 600;
}
.ac-aside .el-menu-item.is-active .ac-nav-icon { color: var(--ac-blue); }

/* 顶部 */
.ac-header {
  height: auto !important;
  padding: var(--ac-5) var(--ac-7) var(--ac-4);
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--ac-4);
  background: var(--ac-header-bg);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 1px solid var(--ac-separator);
  position: sticky;
  top: 0;
  z-index: 100;
}
.ac-header-left { display: flex; flex-direction: column; gap: 2px; }
.ac-header-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--ac-text);
  letter-spacing: -0.02em;
  line-height: 1.2;
}
.ac-header-sub {
  font-size: 13px;
  font-weight: 500;
  color: var(--ac-text-tertiary);
}

.ac-warning-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  background: var(--ac-orange-soft);
  color: var(--ac-orange);
  border-radius: var(--ac-radius-tag);
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
  margin-top: 4px;
  flex-shrink: 0;
}

/* 主内容 */
.ac-main {
  padding: var(--ac-6) var(--ac-7);
  overflow-y: auto;
  background: var(--ac-bg);
}

.fade-enter-active, .fade-leave-active { transition: opacity var(--ac-dur) var(--ac-ease); }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
