/**
 * api/settings.js —— 用户设置（OCR / LLM 密钥）
 */
import request from './index'

export function getSettings() {
  return request.get('/settings')
}

export function updateSettings(data) {
  return request.put('/settings', data)
}

export function testAdapter() {
  return request.get('/settings/test')
}
