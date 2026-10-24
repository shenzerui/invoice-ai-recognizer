/**
 * api/upload.js —— 上传识别接口
 */
import request from './index'

/** 单张图片上传识别 */
export function uploadSingle(file) {
  const fd = new FormData()
  fd.append('file', file)
  return request.post('/upload/single', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

/** 批量图片上传识别 */
export function uploadBatch(files) {
  const fd = new FormData()
  files.forEach((f) => fd.append('files', f))
  return request.post('/upload/batch', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
