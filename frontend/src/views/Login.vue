<!--
  Login.vue —— 登录 / 注册 页面
  Apple HIG 风格：28px 大标题 + 圆角卡片 + 浅灰背景 + 主色按钮
-->
<template>
  <div class="login-page">
    <div class="login-card">
      <!-- Logo 区 -->
      <div class="login-logo">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
             stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"
             width="44" height="44" class="login-logo-icon">
          <path d="M5 3h14v18l-2-1.5L15 21l-2-1.5L11 21 9 19.5 7 21 5 19.5 5 3Z"/>
          <path d="M9 8h6M9 12h6M9 16h4"/>
        </svg>
        <h1 class="login-title">票据识别管理系统</h1>
        <p class="login-sub">登录或注册以开始使用</p>
      </div>

      <!-- 分段控件：登录 / 注册 -->
      <div class="ac-segmented">
        <div
          class="ac-seg-item"
          :class="{ active: mode === 'login' }"
          @click="mode = 'login'"
        >登录</div>
        <div
          class="ac-seg-item"
          :class="{ active: mode === 'register' }"
          @click="mode = 'register'"
        >注册</div>
      </div>

      <!-- 表单 -->
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        @submit.prevent="onSubmit"
        size="large"
        class="login-form"
      >
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="用户名"
            clearable
            autocomplete="username"
          >
            <template #prefix>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                   stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"
                   width="18" height="18">
                <circle cx="12" cy="8" r="4"/>
                <path d="M4 21c0-4 4-7 8-7s8 3 8 7"/>
              </svg>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            :placeholder="mode === 'login' ? '密码' : '密码（至少 6 位）'"
            show-password
            autocomplete="current-password"
          >
            <template #prefix>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                   stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"
                   width="18" height="18">
                <rect x="4" y="10" width="16" height="11" rx="2"/>
                <path d="M8 10V7a4 4 0 1 1 8 0v3"/>
              </svg>
            </template>
          </el-input>
        </el-form-item>

        <el-button
          type="primary"
          class="login-submit"
          :loading="loading"
          @click="onSubmit"
        >
          {{ mode === 'login' ? '登录' : '创建账户' }}
        </el-button>
      </el-form>

      <!-- 底部提示 -->
      <div class="login-footer">
        <span v-if="mode === 'login'">还没有账户？</span>
        <span v-else>已经有账户？</span>
        <a class="login-switch" @click.prevent="mode = mode === 'login' ? 'register' : 'login'">
          {{ mode === 'login' ? '去注册' : '去登录' }}
        </a>
      </div>
    </div>

    <!-- 版本信息 -->
    <div class="login-version">v1.0.0 · 本地运行</div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login as apiLogin, register as apiRegister, setToken, setUser } from '@/api/auth'

const router = useRouter()
const formRef = ref(null)
const mode = ref('login')
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 32, message: '用户名长度 3-32 位', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
}

async function onSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    if (mode.value === 'login') {
      const res = await apiLogin(form.username, form.password)
      setToken(res.data.access_token)
      // 拉一下当前用户信息存起来
      try {
        const { me } = await import('@/api/auth')
        const userRes = await me()
        setUser(userRes.data)
      } catch { /* 不阻塞登录 */ }
      ElMessage.success('登录成功')
      router.replace('/dashboard')
    } else {
      await apiRegister(form.username, form.password)
      ElMessage.success('注册成功，请登录')
      mode.value = 'login'
      form.password = ''
    }
  } catch (e) {
    // 错误已经被 axios 拦截器弹过了
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 24px;
  background: var(--ac-bg, #f5f5f7);
}

.login-card {
  width: 100%;
  max-width: 400px;
  background: var(--ac-card, #fff);
  border-radius: var(--ac-radius-card, 18px);
  padding: 44px 36px 32px;
  box-shadow: 0 1px 3px rgba(0,0,0,.04), 0 20px 60px -20px rgba(0,0,0,.12);
}

.login-logo {
  text-align: center;
  margin-bottom: 32px;
}
.login-logo-icon { color: var(--ac-blue, #0071e3); margin-bottom: 16px; }
.login-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--ac-text, #1d1d1f);
  letter-spacing: -0.02em;
  margin: 0 0 6px;
}
.login-sub {
  font-size: 14px;
  color: var(--ac-text-tertiary, #86868b);
  margin: 0;
}

/* 分段控件 */
.ac-segmented {
  display: flex;
  background: var(--ac-field, #f2f2f7);
  border-radius: 980px;
  padding: 4px;
  margin-bottom: 28px;
  gap: 2px;
}
.ac-seg-item {
  flex: 1;
  text-align: center;
  padding: 8px 0;
  font-size: 14px;
  font-weight: 500;
  color: var(--ac-text-secondary, #6e6e73);
  border-radius: 980px;
  cursor: pointer;
  transition: all .2s cubic-bezier(.4,0,.2,1);
  user-select: none;
}
.ac-seg-item.active {
  background: #fff;
  color: var(--ac-blue, #0071e3);
  box-shadow: 0 1px 3px rgba(0,0,0,.08);
  font-weight: 600;
}

/* 表单 */
.login-form :deep(.el-form-item) { margin-bottom: 18px; }
.login-form :deep(.el-input__wrapper) {
  border-radius: var(--ac-radius-input, 10px);
  background: var(--ac-field, #f2f2f7);
  box-shadow: none;
  padding: 4px 12px;
}
.login-form :deep(.el-input__wrapper.is-focus) {
  background: #fff;
  box-shadow: 0 0 0 2px var(--ac-blue, #0071e3);
}

.login-submit {
  width: 100%;
  height: 46px;
  border-radius: var(--ac-radius-button, 12px);
  font-size: 15px;
  font-weight: 600;
  margin-top: 8px;
  letter-spacing: 0;
}

.login-footer {
  text-align: center;
  margin-top: 20px;
  font-size: 13px;
  color: var(--ac-text-tertiary, #86868b);
}
.login-switch {
  color: var(--ac-blue, #0071e3);
  cursor: pointer;
  font-weight: 500;
  margin-left: 4px;
}
.login-switch:hover { text-decoration: underline; }

.login-version {
  margin-top: 24px;
  font-size: 11px;
  color: var(--ac-text-tertiary, #86868b);
  letter-spacing: 0.02em;
}

/* 暗色模式适配 */
@media (prefers-color-scheme: dark) {
  .login-card { background: #1c1c1e; }
  .ac-segmented { background: #2c2c2e; }
  .ac-seg-item.active { background: #3a3a3c; color: var(--ac-blue, #0a84ff); }
  .login-form :deep(.el-input__wrapper) { background: #2c2c2e; }
  .login-form :deep(.el-input__wrapper.is-focus) { background: #3a3a3c; }
}
</style>
