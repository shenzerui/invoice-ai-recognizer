<!--
  Settings.vue —— 系统设置页面
  用户自行填入 OCR / LLM API 密钥，请求走用户自己的 key。
-->
<template>
  <div>
    <el-card>
      <template #header>
        <span>OCR / 大模型密钥配置</span>
        <el-tag type="warning" effect="light" size="small" class="tag-ml">
          密钥仅保存在本地 data/settings.json，不上传任何服务器
        </el-tag>
      </template>

      <!-- 当前状态 -->
      <el-alert
        class="status-alert"
        :title="statusText"
        :type="isMock ? 'warning' : 'success'"
        :closable="false"
        show-icon
      />

      <el-form :model="form" label-width="140px">
        <el-form-item label="OCR 服务提供商">
          <el-radio-group v-model="form.ocr_provider">
            <el-radio value="baidu">百度 OCR（推荐，增值税票识别成熟）</el-radio>
            <el-radio value="llm">通用大模型（兼容 OpenAI 请求格式）</el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- 百度 OCR 配置 -->
        <template v-if="form.ocr_provider === 'baidu'">
          <el-divider content-position="left">百度智能云 OCR</el-divider>
          <el-form-item label="API Key">
            <el-input v-model="form.baidu_api_key" placeholder="百度智能云控制台 → 应用列表 → API Key" show-password />
            <div class="form-tip">在百度智能云 OCR 服务页面（https://console.bce.baidu.com/ocr）开通"增值税发票识别"后获取</div>
          </el-form-item>
          <el-form-item label="Secret Key">
            <el-input v-model="form.baidu_secret_key" placeholder="百度智能云控制台 → 应用列表 → Secret Key" show-password />
          </el-form-item>
        </template>

        <!-- 通用 LLM 配置 -->
        <template v-else>
          <el-divider content-position="left">通用大模型 API</el-divider>
          <el-form-item label="API Key">
            <el-input v-model="form.llm_api_key" placeholder="sk-xxxxxx..." show-password />
            <div class="form-tip">兼容 OpenAI 请求格式，支持国产大模型（豆包、通义、文心等）的兼容端点</div>
          </el-form-item>
          <el-form-item label="API URL">
            <el-input v-model="form.llm_api_url" placeholder="留空默认 https://api.openai.com/v1/chat/completions" />
          </el-form-item>
          <el-form-item label="模型名称">
            <el-input v-model="form.llm_model" placeholder="如 gpt-4o / gpt-4o-mini / doubao-pro-32k" />
          </el-form-item>
        </template>

        <el-form-item>
          <el-button type="primary" :loading="saving" @click="save">保存设置</el-button>
          <el-button :loading="testing" @click="test">测试连接</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 说明卡片 -->
    <el-card class="usage-card">
      <template #header>使用说明</template>
      <el-steps direction="vertical" :active="4">
        <el-step title="1. 选择 OCR 提供商" description="推荐百度 OCR（票据专用接口，准确率高）或通用 LLM（一个适配器覆盖所有票据类型）" />
        <el-step title="2. 在对应平台开通服务" description="百度：智能云控制台开通增值税发票识别；LLM：获取 API Key" />
        <el-step title="3. 填入密钥并保存" description="密钥仅保存在 backend/data/settings.json，不会上传到任何地方" />
        <el-step title="4. 回到上传识别页面使用" description="未配置密钥时，系统会使用内置 Mock 数据演示全流程" />
      </el-steps>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getSettings, updateSettings, testAdapter } from '@/api/settings'

const form = reactive({
  ocr_provider: 'baidu',
  baidu_api_key: '',
  baidu_secret_key: '',
  llm_api_key: '',
  llm_api_url: '',
  llm_model: '',
})

const saving = ref(false)
const testing = ref(false)
const currentAdapter = ref('')

const isMock = computed(() => currentAdapter.value === 'MockAdapter')
const statusText = computed(() => {
  if (isMock.value) {
    return `当前使用 Mock 适配器（本地演示模式），请配置真实 OCR / LLM 密钥以启用真实识别`
  }
  return `当前适配器：${currentAdapter.value}`
})

async function load() {
  const { data } = await getSettings()
  form.ocr_provider = data.ocr_provider
  form.llm_api_url = data.llm_api_url
  form.llm_model = data.llm_model
  // 密钥不回传明文 —— 不覆盖用户输入，保持为空让用户自己填
  await refreshAdapter()
}

async function refreshAdapter() {
  try {
    const { data } = await testAdapter()
    currentAdapter.value = data.adapter_class || ''
  } catch {}
}

async function save() {
  saving.value = true
  try {
    await updateSettings(form)
    ElMessage.success('保存成功')
    await refreshAdapter()
  } finally {
    saving.value = false
  }
}

async function test() {
  testing.value = true
  try {
    // 先保存一下让适配器生效
    await updateSettings(form)
    const { data } = await testAdapter()
    currentAdapter.value = data.adapter_class
    if (data.adapter_class === 'MockAdapter') {
      ElMessage.warning('密钥未生效，仍在使用 Mock 适配器。请检查 Key 是否正确保存后刷新页面')
    } else {
      ElMessage.success(`适配器切换成功：${data.adapter_class}`)
    }
  } finally {
    testing.value = false
  }
}

onMounted(load)
</script>

<style scoped>
/* tag 左间距 */
.tag-ml { margin-left: 12px; }

/* 状态 alert 间距 */
.status-alert { margin-bottom: 20px; }

/* ========== 分组设置卡片（inset grouped）========== */
.settings-card {
  background: var(--ac-card-2) !important;
  border-radius: var(--ac-radius-card) !important;
  padding: var(--ac-5);
  box-shadow: none !important;
  border: none !important;
}
.settings-card :deep(.el-card__header) { display: none; }
.settings-card :deep(.el-card__body) { padding: 0; }

/* 状态条：绿底绿字胶囊 */
.status-bar {
  display: flex;
  align-items: center;
  gap: var(--ac-2);
  padding: var(--ac-3) var(--ac-5);
  border-radius: var(--ac-radius-input);
  background: var(--ac-green-soft);
  color: var(--ac-green);
  font-size: 14px;
  font-weight: 500;
  line-height: 1.4;
  margin-bottom: var(--ac-5);
}
.status-bar.warn { background: var(--ac-orange-soft); color: var(--ac-orange); }
.status-bar .status-dot {
  width: 10px; height: 10px; border-radius: 50%;
  background: currentColor; flex-shrink: 0;
  box-shadow: 0 0 0 4px currentColor;
  opacity: 0.25;
}

/* 表单：label 上方 + 宽输入框 */
:deep(.el-form) { max-width: 720px; }
:deep(.el-form-item) { margin-bottom: var(--ac-4); }
:deep(.el-form-item__label) {
  font-weight: 500;
  color: var(--ac-text);
  font-size: 14px;
  padding-bottom: var(--ac-2);
}

/* 服务商单选：行 + 右侧对勾 + 选中浅蓝底 */
.provider-row {
  display: flex;
  align-items: center;
  gap: var(--ac-3);
  padding: var(--ac-4) var(--ac-5);
  border-radius: var(--ac-radius-input);
  border: 1px solid var(--ac-separator-thick);
  background: var(--ac-card);
  cursor: pointer;
  transition: all var(--ac-dur) var(--ac-ease);
  margin-bottom: var(--ac-3);
}
.provider-row:hover { border-color: var(--ac-blue); }
.provider-row.is-active {
  background: var(--ac-blue-soft);
  border-color: var(--ac-blue);
}
.provider-row .provider-name { font-weight: 600; color: var(--ac-text); font-size: 15px; }
.provider-row .provider-desc  { color: var(--ac-text-secondary); font-size: 13px; margin-top: 2px; }

/* 按钮组 */
.action-row { display: flex; gap: var(--ac-3); margin-top: var(--ac-5); padding-top: var(--ac-5); border-top: 1px solid var(--ac-separator); }
.action-row .el-button { min-width: 120px; }

/* 子分区 el-divider：更轻的分隔 */
:deep(.el-divider) {
  margin: var(--ac-5) 0 var(--ac-4);
  border-color: var(--ac-separator);
}
:deep(.el-divider__text) {
  background: var(--ac-card-2) !important;
  font-size: 12px;
  font-weight: 600;
  color: var(--ac-text-tertiary);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

/* ========== 说明卡片 ========== */
.usage-card { margin-top: var(--ac-4); }
.usage-card :deep(.el-card__header) { font-size: 15px; }

/* 步骤列表：圆形数字 + 大步骤号 */
:deep(.el-step__icon) {
  font-weight: 700;
  font-size: 14px;
  width: 32px; height: 32px;
  border-radius: 50%;
  border: 1.5px solid var(--ac-blue);
  background: var(--ac-card);
  color: var(--ac-blue);
  display: flex;
  align-items: center;
  justify-content: center;
}
:deep(.el-step__title) { font-size: 15px; font-weight: 600; }
:deep(.el-step__description) { font-size: 13px; color: var(--ac-text-secondary); }

/* ========== 表单辅助说明 ========== */
.form-tip {
  font-size: 12px;
  color: var(--ac-text-tertiary);
  line-height: 1.5;
  margin-top: 6px;
}
</style>
