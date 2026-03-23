import { get, del } from '@/utils/request'

export const getLogs = (params) => get('/clean-logs', params)
export const getTaskNames = () => get('/clean-logs/tasks')
export const clearLogs = (taskName) =>
  del(`/clean-logs${taskName ? `?task_name=${encodeURIComponent(taskName)}` : ''}`)
