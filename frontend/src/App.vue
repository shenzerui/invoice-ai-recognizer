<!--
  App.vue —— 应用根组件（Apple HIG 布局）
  只改视觉（CSS + 少量内联属性删除 + 线性 SVG 图标替换），
  不动任何事件绑定、路由、数据字段、JS 函数。
-->
<template>
  <el-container class="app-container">
    <!-- ========== 侧边栏（220px 毛玻璃） ========== -->
    <el-aside width="220px" class="ac-aside">
      <!-- 应用 Logo -->
      <div class="ac-logo">
        <!-- 线性 SVG：收据/票据图标 1.5px 描边 -->
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
             stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"
             class="ac-logo-icon" width="22" height="22">
          <path d="M5 3h14v18l-2-1.5L15 21l-2-1.5L11 21 9 19.5 7 21 5 19.5 5 3Z"/>
          <path d="M9 8h6M9 12h6M9 16h4"/>
        </svg>
        <span>票据识别</span>
      </div>

      <!-- 导航分组：概览 -->
      <div class="ac-nav-group">
        <div class="ac-nav-title">概览</div>
        <el-menu :default-active="$route.path" router>
          <el-menu-item index="/dashboard">
            <!-- SF Symbols 风格：方框图表 -->
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

      <!-- 导航分组：识别 -->
      <div class="ac-nav-group">
        <div class="ac-nav-title">识别</div>
        <el-menu :default-active="$route.path" router>
          <el-menu-item index="/upload">
            <!-- SF Symbols 风格：云 + 上传箭头 -->
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

      <!-- 导航分组：数据 -->
      <div class="ac-nav-group">
        <div class="ac-nav-title">数据</div>
        <el-menu :default-active="$route.path" router>
          <el-menu-item index="/history">
            <!-- SF Symbols 风格：文档列表 -->
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

      <!-- 导航分组：系统 -->
      <div class="ac-nav-group">
        <div class="ac-nav-title">系统</div>
        <el-menu :default-active="$route.path" router>
          <el-menu-item index="/settings">
            <!-- SF Symbols 风格：齿轮 -->
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

    <!-- ========== 主区域 ========== -->
    <el-container>
      <!-- 顶部（sticky 毛玻璃 + iOS 大标题） -->
      <el-header class="ac-header">
        <div class="ac-header-left">
          <div class="ac-header-title">{{ $route.meta.title || '票据识别管理系统' }}</div>
          <div class="ac-header-sub">票据识别管理系统 · 本地运行</div>
        </div>
        <!-- 橘色警告药丸（浅黄底 + i 线性图标）-->
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

      <!-- 主内容 -->
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
// App.vue 只负责整体布局，不承载业务逻辑
</script>

<style scoped>
/* ===== 容器 ===== */
.app-container { height: 100vh; }

/* ===== 侧边栏 ===== */
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

/* Logo 区 */
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

/* 导航分组 */
.ac-nav-group { padding: 0 var(--ac-3); margin-bottom: var(--ac-4); }
.ac-nav-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--ac-text-tertiary);
  padding: var(--ac-2) var(--ac-3);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

/* el-menu 覆写 —— 干掉 Element Plus 深灰底，用我们的毛玻璃 */
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

/* ===== 顶部（sticky 毛玻璃） ===== */
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

/* 警告药丸 */
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

/* ===== 主内容 ===== */
.ac-main {
  padding: var(--ac-6) var(--ac-7);
  overflow-y: auto;
  background: var(--ac-bg);
}

/* 过渡 */
.fade-enter-active, .fade-leave-active { transition: opacity var(--ac-dur) var(--ac-ease); }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
