<!--
  InvoiceDetail.vue —— 单张票据详情页
  展示票据图片 + 全部识别字段，支持返回和编辑。
-->
<template>
  <div v-loading="loading">
    <el-page-header @back="$router.push('/history')" content="票据详情" class="detail-header" />

    <el-row :gutter="16" v-if="detail">
      <!-- 左侧图片 -->
      <el-col :span="10">
        <el-card>
          <template #header>票据图片</template>
          <el-image
            v-if="detail.image_path"
            :src="imageUrl(detail.id)"
            class="img-full"
            fit="contain"
            :preview-src-list="[imageUrl(detail.id)]"
          />
          <el-empty v-else description="无图片" />

          <!-- 标签和备注（内联编辑） -->
          <div class="mt-16">
            <el-divider content-position="left">标签</el-divider>
            <div class="mb-8">
              <el-tag v-for="t in detail.tags" :key="t" size="default" class="tag-mr">{{ t }}</el-tag>
              <span v-if="!detail.tags.length" class="muted">未添加标签</span>
            </div>
            <el-button size="small" @click="quickEdit('tags')">编辑标签</el-button>
          </div>

          <div class="mt-16">
            <el-divider content-position="left">备注</el-divider>
            <div class="remark-text">
              {{ detail.remark || '（暂无备注）' }}
            </div>
            <el-button size="small" @click="quickEdit('remark')" class="mt-8">编辑备注</el-button>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧字段 -->
      <el-col :span="14">
        <el-card>
          <template #header>
            识别结果
            <el-tag :type="detail.validation_passed ? 'success' : 'danger'" class="tag-ml-sm">
              {{ detail.validation_passed ? '金额校验通过' : '金额校验异常' }}
            </el-tag>
            <el-button size="small" link type="primary" class="float-right" @click="openEdit">编辑修正</el-button>
          </template>

          <el-descriptions :column="2" border>
            <el-descriptions-item label="ID">{{ detail.id }}</el-descriptions-item>
            <el-descriptions-item label="票据类型">{{ detail.ticket_type_label }}</el-descriptions-item>
            <el-descriptions-item label="发票代码">{{ detail.invoice_code || '-' }}</el-descriptions-item>
            <el-descriptions-item label="发票号码">{{ detail.invoice_number || '-' }}</el-descriptions-item>
            <el-descriptions-item label="开票日期">{{ detail.invoice_date || '-' }}</el-descriptions-item>
            <el-descriptions-item label="购买方">{{ detail.buyer || '-' }}</el-descriptions-item>
            <el-descriptions-item label="销售方">{{ detail.seller || '-' }}</el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ detail.created_at }}</el-descriptions-item>
          </el-descriptions>

          <el-divider content-position="left">金额</el-divider>
          <el-descriptions :column="3" border>
            <el-descriptions-item label="金额（不含税）">
              <span class="amount-num">¥ {{ detail.amount?.toFixed(2) }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="税额">
              <span class="amount-num">¥ {{ detail.tax?.toFixed(2) }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="价税合计">
              <span :class="['total-amount', detail.validation_passed ? 'ok' : 'err']">
                ¥ {{ detail.total_amount?.toFixed(2) }}
              </span>
            </el-descriptions-item>
          </el-descriptions>

          <el-alert
            v-if="!detail.validation_passed"
            class="alert-mt"
            type="error"
            show-icon
            :title="detail.validation_message"
            :closable="false"
          />
          <el-alert
            v-else-if="detail.validation_message"
            class="alert-mt"
            type="success"
            show-icon
            :title="detail.validation_message"
            :closable="false"
          />

          <!-- 扩展字段 -->
          <template v-if="detail.type_extra && Object.keys(detail.type_extra).length">
            <el-divider content-position="left">扩展字段（{{ detail.ticket_type_label }} 特有）</el-divider>
            <el-descriptions :column="2" border>
              <el-descriptions-item v-for="(v, k) in detail.type_extra" :key="k" :label="k">{{ v || '-' }}</el-descriptions-item>
            </el-descriptions>
          </template>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { getInvoice, updateInvoice, imageUrl as imgUrl } from '@/api/invoices'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const detail = ref(null)

function imageUrl(id) { return imgUrl(id) }

async function load() {
  loading.value = true
  try {
    const { data } = await getInvoice(route.params.id)
    detail.value = data
  } catch {
    ElMessage.error('加载失败')
    router.push('/history')
  } finally {
    loading.value = false
  }
}

function openEdit() {
  // 直接跳转 history 页的编辑功能
  ElMessageBox.alert('请到"历史记录"页面的编辑功能修改，支持同时预览多条对比。', '提示')
}

async function quickEdit(field) {
  // 快速编辑标签 / 备注
  if (field === 'tags') {
    // 简化：用 prompt 让用户输入逗号分隔的标签
    const val = prompt('请输入标签，用英文逗号分隔（如：交通,差旅,已报销）', (detail.value.tags || []).join(','))
    if (val === null) return
    const tags = val.split(',').map((s) => s.trim()).filter(Boolean)
    await updateInvoice(detail.value.id, { tags })
    ElMessage.success('标签已更新')
  } else if (field === 'remark') {
    const val = prompt('请输入备注', detail.value.remark || '')
    if (val === null) return
    await updateInvoice(detail.value.id, { remark: val })
    ElMessage.success('备注已更新')
  }
  load()
}

onMounted(load)
</script>

<style scoped>
/* header 间距 */
.detail-header { margin-bottom: var(--ac-4); }

/* 票据图片：100% 宽 + 圆角 */
.img-full { width: 100%; border-radius: var(--ac-radius-input); overflow: hidden; }

/* 间距工具类 */
.mt-16 { margin-top: var(--ac-4); }
.mt-12 { margin-top: 12px; }
.mt-8  { margin-top: 8px; }
.mb-8  { margin-bottom: 8px; }

/* 标签间距 */
.tag-mr    { margin-right: 6px; }
.tag-ml-sm { margin-left: 8px; }

/* 辅助文字 */
.muted { color: var(--ac-text-tertiary); }

/* 备注 */
.remark-text {
  white-space: pre-wrap;
  color: var(--ac-text);
  min-height: 40px;
  font-size: 15px;
  line-height: 1.5;
}

/* 标题按钮靠右 */
.float-right { float: right; }

/* 金额等宽 */
.amount-num {
  font-size: 16px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: var(--ac-text);
}

/* 价税合计：大字号 + 按校验结果上色 */
.total-amount {
  font-size: 18px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.01em;
}
.total-amount.ok { color: var(--ac-green); }
.total-amount.err { color: var(--ac-red); }

/* alert 上间距 */
.alert-mt { margin-top: 12px; }
</style>
