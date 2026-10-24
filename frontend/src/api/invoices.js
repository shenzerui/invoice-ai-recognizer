/**
 * api/invoices.js —— 票据 CRUD、搜索、导出
 */
import request from './index'

/** 列表（带分页 + 筛选） */
export function listInvoices(params) {
  return request.get('/invoices', { params })
}

/** 获取支持的票据类型枚举 */
export function listTypes() {
  return request.get('/invoices/types')
}

/** 详情 */
export function getInvoice(id) {
  return request.get(`/invoices/${id}`)
}

/** 更新 */
export function updateInvoice(id, data) {
  return request.put(`/invoices/${id}`, data)
}

/** 删除 */
export function deleteInvoice(id) {
  return request.delete(`/invoices/${id}`)
}

/** 导出 Excel —— 返回 blob，前端触发下载 */
export function exportExcel(params) {
  return request.get('/invoices/export/excel', {
    params,
    responseType: 'blob',
  })
}

/** 导出 JSON */
export function exportJson(params) {
  return request.get('/invoices/export/json', {
    params,
    responseType: 'blob',
  })
}

/** 图片 URL（直接拼到 window.location，不走 axios） */
export function imageUrl(id) {
  return `/api/invoices/${id}/image`
}
