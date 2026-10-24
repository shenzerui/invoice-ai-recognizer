<!--
  History.vue —— 历史记录页面
  按时间/类型搜索、分页、批量导出、编辑标签备注。
-->
<template>
  <div>
    <!-- 搜索筛选区 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filters" @submit.prevent>
        <el-form-item label="票据类型">
          <el-select v-model="filters.ticket_type" placeholder="全部" clearable style="width:160px">
            <el-option v-for="t in types" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="开票日期">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始"
            end-placeholder="结束"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="号码/代码/购买方/销售方/标签" clearable style="width:220px" />
        </el-form-item>
        <el-form-item class="filter-actions">
          <el-button type="primary" :icon="Search" @click="loadList">搜索</el-button>
          <el-button :icon="Refresh" @click="resetFilters">重置</el-button>
        </el-form-item>
        <el-form-item class="export-group">
          <el-button type="success" :icon="Download" @click="handleExport('excel')">导出 Excel</el-button>
          <el-button type="info" :icon="Download" @click="handleExport('json')">导出 JSON</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 结果表格 -->
    <el-card class="content-card">
      <el-table :data="list" stripe @row-click="goDetail" :row-class-name="rowClassName">
        <el-table-column label="ID" prop="id" width="70" />
        <el-table-column label="图片" width="100">
          <template #default="{ row }">
            <el-image
              v-if="row.image_path"
              :src="imageUrl(row.id)"
              class="thumb-60"
              fit="cover"
              :preview-src-list="[imageUrl(row.id)]"
              preview-teleported
            />
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="类型" width="140">
          <template #default="{ row }">
            <el-tag :type="tagType(row.ticket_type)" size="small">{{ row.ticket_type_label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="发票代码" prop="invoice_code" width="160" />
        <el-table-column label="发票号码" prop="invoice_number" width="160" />
        <el-table-column label="开票日期" prop="invoice_date" width="120" />
        <el-table-column label="购买方" prop="buyer" show-overflow-tooltip />
        <el-table-column label="销售方" prop="seller" show-overflow-tooltip />
        <el-table-column label="金额(不含税)" width="110" align="right">
          <template #default="{ row }">¥ {{ row.amount?.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="税额" width="100" align="right">
          <template #default="{ row }">¥ {{ row.tax?.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="价税合计" width="120" align="right">
          <template #default="{ row }">
            <span :class="{ 'amount-cell': !row.validation_passed }">¥ {{ row.total_amount?.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="校验" width="90">
          <template #default="{ row }">
            <el-tag :type="row.validation_passed ? 'success' : 'danger'" size="small">
              {{ row.validation_passed ? '✓' : '✗' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="标签" width="160">
          <template #default="{ row }">
            <el-tag v-for="t in row.tags" :key="t" size="small" class="tag-mr">{{ t }}</el-tag>
            <span v-if="!row.tags?.length" class="muted">未添加</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" link type="primary" @click.stop="openDetail(row)">详情</el-button>
            <el-button size="small" link type="success" @click.stop="openEdit(row)">编辑</el-button>
            <el-button size="small" link type="danger" @click.stop="deleteRow(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        class="pagination-bar"
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @current-change="loadList"
        @size-change="loadList"
      />
    </el-card>

    <!-- 编辑弹窗（标签、备注、手动修正金额） -->
    <el-dialog v-model="editVisible" title="编辑票据信息" width="560px">
      <el-form v-if="editForm" :model="editForm" label-width="120px">
        <el-form-item label="票据类型">
          <el-select v-model="editForm.ticket_type" style="width:100%">
            <el-option v-for="t in types" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="金额（不含税）">
          <el-input-number v-model="editForm.amount" :precision="2" :min="0" />
        </el-form-item>
        <el-form-item label="税额">
          <el-input-number v-model="editForm.tax" :precision="2" :min="0" />
        </el-form-item>
        <el-form-item label="价税合计">
          <el-input-number v-model="editForm.total_amount" :precision="2" :min="0" />
        </el-form-item>
        <el-form-item label="开票日期">
          <el-input v-model="editForm.invoice_date" placeholder="如 2024-08-15" />
        </el-form-item>
        <el-form-item label="购买方">
          <el-input v-model="editForm.buyer" />
        </el-form-item>
        <el-form-item label="销售方">
          <el-input v-model="editForm.seller" />
        </el-form-item>
        <el-form-item label="标签">
          <el-select v-model="editForm.tags" multiple filterable allow-create style="width:100%">
            <el-option v-for="t in allTags" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="editForm.remark" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="editSaving" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Download } from '@element-plus/icons-vue'
import { listInvoices, listTypes, updateInvoice, deleteInvoice, exportExcel, exportJson, imageUrl as imgUrl } from '@/api/invoices'

const router = useRouter()

const types = ref([])
const list = ref([])
const dateRange = ref([])
const filters = reactive({
  ticket_type: '',
  keyword: '',
})
const pagination = reactive({ page: 1, page_size: 20, total: 0 })

// 收集所有已用标签，供编辑时下拉选择
const allTags = computed(() => {
  const s = new Set()
  list.value.forEach((r) => (r.tags || []).forEach((t) => s.add(t)))
  return Array.from(s)
})

function imageUrl(id) {
  return imgUrl(id)
}

function tagType(type) {
  const map = { vat_special: '', vat_normal: 'success', vat_electronic: 'primary', fixed: 'warning', train: 'info', bus: 'info', toll: 'info' }
  return map[type] || ''
}

function rowClassName({ row }) {
  return row.validation_passed ? '' : 'row-error'
}

async function loadList() {
  const params = {
    page: pagination.page,
    page_size: pagination.page_size,
    ticket_type: filters.ticket_type || undefined,
    keyword: filters.keyword || undefined,
    start_date: dateRange.value?.[0],
    end_date: dateRange.value?.[1],
  }
  const { data } = await listInvoices(params)
  list.value = data.items
  pagination.total = data.total
}

function resetFilters() {
  filters.ticket_type = ''
  filters.keyword = ''
  dateRange.value = []
  pagination.page = 1
  loadList()
}

async function handleExport(format) {
  const params = {
    ticket_type: filters.ticket_type || undefined,
    start_date: dateRange.value?.[0],
    end_date: dateRange.value?.[1],
  }
  const api = format === 'excel' ? exportExcel : exportJson
  const { data } = await api(params)
  const blob = new Blob([data], { type: format === 'excel' ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' : 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `invoices.${format === 'excel' ? 'xlsx' : 'json'}`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('导出成功')
}

function goDetail(row) {
  router.push(`/history/${row.id}`)
}
function openDetail(row) {
  router.push(`/history/${row.id}`)
}

// --- 编辑弹窗 ---
const editVisible = ref(false)
const editSaving = ref(false)
const editForm = ref(null)
const editingId = ref(null)

function openEdit(row) {
  editingId.value = row.id
  editForm.value = {
    ticket_type: row.ticket_type,
    amount: row.amount,
    tax: row.tax,
    total_amount: row.total_amount,
    invoice_date: row.invoice_date,
    buyer: row.buyer,
    seller: row.seller,
    tags: [...(row.tags || [])],
    remark: row.remark,
  }
  editVisible.value = true
}

async function saveEdit() {
  editSaving.value = true
  try {
    await updateInvoice(editingId.value, editForm.value)
    ElMessage.success('保存成功')
    editVisible.value = false
    loadList()
  } finally {
    editSaving.value = false
  }
}

async function deleteRow(row) {
  await ElMessageBox.confirm(`确认删除 #${row.id} ${row.ticket_type_label}？此操作会连同本地图片一起删除。`, '提示', { type: 'warning' })
  await deleteInvoice(row.id)
  ElMessage.success('已删除')
  loadList()
}

onMounted(async () => {
  try {
    const { data } = await listTypes()
    types.value = data
  } catch {}
  loadList()
})
</script>

<style scoped>
/* 筛选卡片：inset grouped 风格 */
.filter-card {
  margin-bottom: var(--ac-4);
  background: var(--ac-card-2) !important;
  border-radius: var(--ac-radius-card) !important;
  padding: var(--ac-5);
}
.filter-card :deep(.el-card__body) { padding: 0; }
.filter-card :deep(.el-form--inline) { display: flex; flex-wrap: wrap; gap: var(--ac-2) var(--ac-5); }
.filter-card :deep(.el-form-item) { margin-right: 0; margin-bottom: var(--ac-2); }
.filter-card :deep(.el-form-item__label) { color: var(--ac-text-secondary); font-size: 13px; font-weight: 500; padding-right: var(--ac-2); }

/* 筛选按钮靠右 */
.filter-actions { margin-left: auto; display: flex; gap: var(--ac-2); flex-wrap: wrap; }

/* 导出按钮 */
.export-group { display: flex; gap: var(--ac-2); }
.export-group .el-button--success { background: var(--ac-green-soft) !important; border-color: transparent !important; color: var(--ac-green) !important; }
.export-group .el-button--info    { background: var(--ac-blue-soft) !important;  border-color: transparent !important; color: var(--ac-blue)  !important; }

/* 主内容卡片间距 */
.content-card { margin-top: var(--ac-4); }

/* 图片缩略图：6px 圆角 */
.thumb-60 { width: 60px; height: 60px; border-radius: var(--ac-radius-input); overflow: hidden; }

/* 标签间距 */
.tag-mr { margin-right: 4px; }

/* 辅助文字 */
.muted { color: var(--ac-text-tertiary); }

/* 分页条靠右 */
.pagination-bar { margin-top: var(--ac-4); justify-content: flex-end; display: flex; }

/* 金额数字等宽 */
.amount-cell { color: var(--ac-red); font-weight: 600; font-variant-numeric: tabular-nums; }

/* 空状态提示 */
.empty-state { text-align: center; padding: var(--ac-9) 0; color: var(--ac-text-tertiary); font-size: 14px; }
</style>
