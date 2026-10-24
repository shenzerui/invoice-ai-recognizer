<!--
  Dashboard.vue —— 首页
  展示系统状态：票据总数、各类型分布、金额校验异常数量。
-->
<template>
  <div>
    <el-row :gutter="16" class="card-row">
      <!-- 总数统计卡片 -->
      <el-col :span="6" class="card-col">
        <el-card class="stat-card">
          <div class="stat">
            <div class="stat-icon bg-blue"><el-icon :size="22"><Tickets /></el-icon></div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total }}</div>
              <div class="stat-label">票据总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <!-- 校验异常数 -->
      <el-col :span="6" class="card-col">
        <el-card class="stat-card">
          <div class="stat">
            <div class="stat-icon bg-red"><el-icon :size="22"><Warning /></el-icon></div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.errors }}</div>
              <div class="stat-label">金额校验异常</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <!-- 总金额 -->
      <el-col :span="6" class="card-col">
        <el-card class="stat-card">
          <div class="stat">
            <div class="stat-icon bg-green"><el-icon :size="22"><Money /></el-icon></div>
            <div class="stat-info">
              <div class="stat-value">¥ {{ stats.totalAmount.toFixed(2) }}</div>
              <div class="stat-label">价税合计</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <!-- OCR 适配器状态 -->
      <el-col :span="6" class="card-col">
        <el-card class="stat-card">
          <div class="stat">
            <div class="stat-icon" :class="ocrReady ? 'bg-orange' : 'bg-gray'">
              <el-icon :size="22"><Cpu /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value adapter">{{ ocrInfo.adapter_class || '未配置' }}</div>
              <div class="stat-label">OCR 适配器</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="card-row">
      <!-- 最近 10 条 -->
      <el-col :span="16" class="card-col">
        <el-card>
          <template #header>
            <span>最近识别的票据</span>
            <el-button link type="primary" @click="$router.push('/history')">查看全部</el-button>
          </template>
          <el-table :data="recentList" stripe size="default">
            <el-table-column label="类型" prop="ticket_type_label" width="120">
              <template #default="{ row }">
                <el-tag :type="tagType(row.ticket_type)" size="small">{{ row.ticket_type_label }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="invoice_number" label="发票号码" width="160" />
            <el-table-column prop="invoice_date" label="开票日期" width="120" />
            <el-table-column prop="buyer" label="购买方" show-overflow-tooltip />
            <el-table-column label="价税合计" width="120">
              <template #default="{ row }">
                <span :class="{ 'amount-cell': !row.validation_passed }">¥ {{ row.total_amount.toFixed(2) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.validation_passed ? 'success' : 'danger'" size="small">
                  {{ row.validation_passed ? '正常' : '异常' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 快速入口 -->
      <el-col :span="8" class="card-col">
        <el-card>
          <template #header><span>快速操作</span></template>
          <div class="quick-actions">
            <el-button type="primary" @click="$router.push('/upload')">
              <el-icon><Upload /></el-icon>
              上传票据识别
            </el-button>
            <el-button @click="$router.push('/history')">
              <el-icon><Document /></el-icon>
              历史记录查询
            </el-button>
            <el-button @click="$router.push('/settings')">
              <el-icon><Setting /></el-icon>
              配置 OCR / LLM 密钥
            </el-button>
          </div>

          <el-alert
            class="quick-alert"
            type="warning"
            :closable="false"
            show-icon
            title="系统提示"
            description="本系统仅辅助识别，不对接国税查验接口，识别结果仅供参考。未配置 OCR 密钥时，将使用内置 Mock 数据演示流程。"
          />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { listInvoices, listTypes } from '@/api/invoices'
import { testAdapter } from '@/api/settings'

const recentList = ref([])
const ocrInfo = ref({})
const allList = ref([])

const stats = computed(() => {
  const errors = allList.value.filter((r) => !r.validation_passed).length
  const totalAmount = allList.value.reduce((s, r) => s + (r.total_amount || 0), 0)
  return {
    total: allList.value.length,
    errors,
    totalAmount,
  }
})

function tagType(type) {
  const map = { vat_special: '', vat_normal: 'success', vat_electronic: 'primary', fixed: 'warning', train: 'info', bus: 'info', toll: 'info' }
  return map[type] || ''
}

onMounted(async () => {
  try {
    const { data } = await listInvoices({ page: 1, page_size: 500 })
    allList.value = data.items
    recentList.value = data.items.slice(0, 10)
  } catch {}
  try {
    const { data: info } = await testAdapter()
    ocrInfo.value = info
  } catch {}
})
</script>

<style scoped>
/* ===== 统计卡片 ===== */
.stat-card {
  transition: transform var(--ac-dur) var(--ac-ease),
              box-shadow var(--ac-dur) var(--ac-ease);
  cursor: default;
}
.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.07),
              0 1px 3px rgba(0, 0, 0, 0.05) !important;
}

.stat {
  display: flex;
  align-items: center;
  gap: var(--ac-4);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--ac-radius-icon);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
}
/* 浅色底配彩色图标（苹果风） */
.stat-icon.bg-blue   { background: var(--ac-blue-soft);   color: var(--ac-blue);   }
.stat-icon.bg-red    { background: var(--ac-red-soft);     color: var(--ac-red);    }
.stat-icon.bg-green  { background: var(--ac-green-soft);  color: var(--ac-green);  }
.stat-icon.bg-orange { background: var(--ac-orange-soft); color: var(--ac-orange); }
.stat-icon.bg-gray   { background: var(--ac-gray-soft);    color: var(--ac-gray);   }

.stat-info .stat-value {
  font-size: 30px;
  font-weight: 700;
  color: var(--ac-text);
  line-height: 1.1;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.02em;
}
.stat-info .stat-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--ac-text-tertiary);
  margin-top: 4px;
}

/* OCR 适配器名过长时 —— 截断 + 灰色胶囊 */
.stat-info .stat-value.adapter {
  font-size: 15px;
  font-weight: 500;
  color: var(--ac-text-secondary);
  font-family: inherit;
}

.amount-cell { color: var(--ac-red); font-weight: 600; font-variant-numeric: tabular-nums; }

/* ===== 快速操作区 ===== */
.quick-actions { display: flex; flex-direction: column; gap: var(--ac-3); }
.quick-actions .el-button { width: 100%; height: 44px; }

.quick-alert { margin-top: var(--ac-4); }

/* el-row / el-col 卡片间距 */
.card-col { padding: 0 var(--ac-3) !important; }
.card-row { margin: 0 calc(var(--ac-3) * -1); }
.card-row + .card-row { margin-top: var(--ac-4); }

/* 卡片内 header "查看全部" 蓝色文字 + chevron */
.el-card__header .el-button.el-button--primary.is-link {
  color: var(--ac-blue) !important;
  display: inline-flex;
  align-items: center;
  gap: 2px;
  font-weight: 500;
  font-size: 13px;
}
</style>
