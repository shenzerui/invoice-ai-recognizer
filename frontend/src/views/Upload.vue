<!--
  Upload.vue —— 上传识别页面
  支持单张、批量上传 jpg/png 图片，实时展示识别结果。
-->
<template>
  <div>
    <el-card>
      <template #header>
        <span>上传票据图片</span>
        <el-tag type="warning" effect="plain" size="small" class="tag-ml">
          仅辅助识别，结果仅供参考
        </el-tag>
      </template>

      <!-- 模式切换 -->
      <el-radio-group v-model="mode" class="mode-switch">
        <el-radio-button value="single">单张上传</el-radio-button>
        <el-radio-button value="batch">批量上传</el-radio-button>
      </el-radio-group>

      <!-- 单张 -->
      <div v-if="mode === 'single'">
        <el-upload
          class="upload-area"
          drag
          :auto-upload="false"
          :limit="1"
          accept=".jpg,.jpeg,.png"
          :on-change="handleSinglePick"
          :file-list="singleFileList"
        >
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">将文件拖到此处，或 <em>点击上传</em></div>
          <template #tip>
            <div class="el-upload__tip">支持 jpg / png，单文件 ≤ 10MB</div>
          </template>
        </el-upload>

        <div class="btn-row">
          <el-button type="primary" :loading="singleLoading" :disabled="!singleFile" @click="doSingleUpload">
            <el-icon><Promotion /></el-icon>
            开始识别并入库
          </el-button>
        </div>
      </div>

      <!-- 批量 -->
      <div v-else>
        <el-upload
          class="upload-area"
          drag
          multiple
          :auto-upload="false"
          accept=".jpg,.jpeg,.png"
          :on-change="handleBatchPick"
          :file-list="batchFileList"
          :limit="20"
        >
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">将多张文件拖到此处，或 <em>点击上传</em></div>
          <template #tip>
            <div class="el-upload__tip">最多 20 张，支持 jpg / png，单文件 ≤ 10MB</div>
          </template>
        </el-upload>

        <div class="btn-row">
          <el-button type="primary" :loading="batchLoading" :disabled="!batchFiles.length" @click="doBatchUpload">
            <el-icon><Promotion /></el-icon>
            批量识别并入库（{{ batchFiles.length }} 张）
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 识别结果展示 -->
    <el-card v-if="resultVisible" class="result-card">
      <template #header>
        <span>识别结果</span>
        <el-tag v-if="currentIsBatch" size="small" class="tag-ml-sm">
          共 {{ batchResults.length }} 张 · 成功 {{ summary.saved }} · 重复 {{ summary.duplicates }} · 失败 {{ summary.failed }}
        </el-tag>
      </template>

      <!-- 批量结果表格 -->
      <el-table v-if="currentIsBatch" :data="batchResults" stripe size="small">
        <el-table-column prop="filename" label="文件名" show-overflow-tooltip />
        <el-table-column label="结果" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.is_duplicate" type="warning" size="small">重复</el-tag>
            <el-tag v-else-if="row.success && row.invoice_id" type="success" size="small">已入库 #{{ row.invoice_id }}</el-tag>
            <el-tag v-else-if="row.success" type="info" size="small">识别成功</el-tag>
            <el-tag v-else type="danger" size="small">失败</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="校验" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.validation_passed === false" type="danger" size="small">金额异常</el-tag>
            <span v-else>—</span>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="说明" show-overflow-tooltip />
      </el-table>

      <!-- 单张结果详情 -->
      <div v-else-if="singleResult.invoice_data">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="票据类型">
            {{ singleResult.invoice_data.ticket_type || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="发票代码">{{ singleResult.invoice_data.invoice_code || '-' }}</el-descriptions-item>
          <el-descriptions-item label="发票号码">{{ singleResult.invoice_data.invoice_number || '-' }}</el-descriptions-item>
          <el-descriptions-item label="开票日期">{{ singleResult.invoice_data.invoice_date || '-' }}</el-descriptions-item>
          <el-descriptions-item label="购买方">{{ singleResult.invoice_data.buyer || '-' }}</el-descriptions-item>
          <el-descriptions-item label="销售方">{{ singleResult.invoice_data.seller || '-' }}</el-descriptions-item>
          <el-descriptions-item label="金额（不含税）">¥ {{ singleResult.invoice_data.amount?.toFixed(2) || '0.00' }}</el-descriptions-item>
          <el-descriptions-item label="税额">¥ {{ singleResult.invoice_data.tax?.toFixed(2) || '0.00' }}</el-descriptions-item>
          <el-descriptions-item label="价税合计">¥ {{ singleResult.invoice_data.total_amount?.toFixed(2) || '0.00' }}</el-descriptions-item>
          <el-descriptions-item label="金额校验">
            <el-tag v-if="singleResult.validation_passed" type="success">通过</el-tag>
            <el-tag v-else type="danger">异常</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="校验说明" :span="2">
            {{ singleResult.message }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 特有字段 -->
        <el-alert
          v-if="singleResult.invoice_data.type_extra && Object.keys(singleResult.invoice_data.type_extra).length"
          class="extra-alert"
          title="扩展字段（各票据类型特有）"
          :description="formatExtra(singleResult.invoice_data.type_extra)"
          type="info"
          show-icon
          :closable="false"
        />

        <div class="result-action">
          <el-button type="primary" @click="goDetail(singleResult.invoice_id)">查看详情 →</el-button>
        </div>
      </div>

      <!-- 单张失败提示 -->
      <el-alert v-else type="error" :closable="false" show-icon :title="singleResult.message" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { uploadSingle, uploadBatch } from '@/api/upload'

const router = useRouter()

const mode = ref('single')

// 单张
const singleFile = ref(null)
const singleFileList = ref([])
const singleLoading = ref(false)
const singleResult = reactive({ success: false, message: '', invoice_data: null, invoice_id: null, validation_passed: true })

// 批量
const batchFiles = ref([])
const batchFileList = ref([])
const batchLoading = ref(false)
const batchResults = ref([])
const summary = reactive({ total: 0, saved: 0, duplicates: 0, failed: 0 })
const currentIsBatch = ref(false)
const resultVisible = ref(false)

function handleSinglePick(file) {
  singleFile.value = file.raw
  singleFileList.value = [file]
}

function handleBatchPick(file, fileList) {
  batchFiles.value = fileList.map((f) => f.raw)
  batchFileList.value = fileList
}

async function doSingleUpload() {
  if (!singleFile.value) return
  singleLoading.value = true
  resultVisible.value = true
  currentIsBatch.value = false
  try {
    const { data } = await uploadSingle(singleFile.value)
    Object.assign(singleResult, {
      success: data.success,
      message: data.message,
      invoice_data: data.invoice_data,
      invoice_id: data.invoice_id,
      validation_passed: data.validation_passed,
    })
    if (data.is_duplicate) ElMessage.warning(data.message)
    else if (!data.success) ElMessage.error(data.message)
    else ElMessage.success('识别完成')
  } catch (e) {
    singleResult.success = false
    singleResult.message = e.message || '识别失败'
  } finally {
    singleLoading.value = false
  }
}

async function doBatchUpload() {
  if (!batchFiles.value.length) return
  batchLoading.value = true
  resultVisible.value = true
  currentIsBatch.value = true
  try {
    const { data } = await uploadBatch(batchFiles.value)
    batchResults.value = data.results
    Object.assign(summary, data.summary)
    ElMessage.success(`批量识别完成，成功入库 ${data.summary.saved} 张`)
  } catch (e) {
    ElMessage.error(e.message || '批量识别失败')
  } finally {
    batchLoading.value = false
  }
}

function formatExtra(obj) {
  return Object.entries(obj).map(([k, v]) => `${k}: ${v}`).join(' | ')
}

function goDetail(id) {
  router.push(`/history/${id}`)
}
</script>

<style scoped>
/* 模式切换：iOS 分段控件 */
.mode-switch { margin-bottom: 16px; }
.tag-ml      { margin-left: 12px; }
.tag-ml-sm   { margin-left: 8px; }

/* iOS 分段控件：灰底凹槽 + 选中项白色胶囊 + 浅阴影 + 蓝字 */
:deep(.el-radio-group) {
  display: inline-flex;
  padding: 4px;
  background: var(--ac-field);
  border-radius: 10px;
  gap: 0;
}
:deep(.el-radio-button__inner) {
  border: none !important;
  background: transparent !important;
  color: var(--ac-text-secondary) !important;
  font-weight: 500;
  padding: 6px 20px;
  border-radius: 7px !important;
  box-shadow: none !important;
  transition: all var(--ac-dur) var(--ac-ease);
  font-size: 14px;
}
:deep(.el-radio-button__original-radio:checked + .el-radio-button__inner),
:deep(.el-radio-button__inner.is-active) {
  background: var(--ac-card) !important;
  color: var(--ac-blue) !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.05) !important;
  font-weight: 600;
}

/* 按钮区 */
.btn-row { margin-top: var(--ac-4); display: flex; gap: var(--ac-3); }
.btn-row .el-button { height: 44px; flex: 1; font-size: 15px; }

/* 卡片间距 */
.result-card { margin-top: var(--ac-4); }
.result-action { margin-top: var(--ac-4); }

/* 识别结果说明 alert */
.extra-alert { margin-top: var(--ac-3); }
</style>
