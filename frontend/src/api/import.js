import { post, get } from '@/utils/request'

/** 上传文件并导入到指定目标 */
export const importData = (formData) => {
  return post('/import/upload', formData)
}
