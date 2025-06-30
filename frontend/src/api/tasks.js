import request from './request'

// 获取任务列表
export function getTasks(params) {
  return request({
    url: '/api/v1/tasks',
    method: 'get',
    params
  })
}

// 获取单个任务详情
export function getTask(id) {
  return request({
    url: `/api/v1/tasks/${id}`,
    method: 'get'
  })
}

// 创建新任务
export function createTask(data) {
  return request({
    url: '/api/v1/tasks',
    method: 'post',
    data
  })
}

// 更新任务
export function updateTask(id, data) {
  return request({
    url: `/api/v1/tasks/${id}`,
    method: 'put',
    data
  })
}

// 删除任务
export function deleteTask(id) {
  return request({
    url: `/api/v1/tasks/${id}`,
    method: 'delete'
  })
}

// 启动任务
export function startTask(id) {
  return request({
    url: `/api/v1/tasks/${id}/start`,
    method: 'post'
  })
}

// 停止任务
export function stopTask(id) {
  return request({
    url: `/api/v1/tasks/${id}/stop`,
    method: 'post'
  })
}

// 获取任务状态
export function getTaskStatus(id) {
  return request({
    url: `/api/v1/tasks/${id}/status`,
    method: 'get'
  })
}

// 批量操作任务
export function batchUpdateTasks(data) {
  return request({
    url: '/api/v1/tasks/batch',
    method: 'put',
    data
  })
}

// 获取任务统计信息
export function getTaskStats() {
  return request({
    url: '/api/v1/tasks/stats',
    method: 'get'
  })
}

// 获取任务日志
export function getTaskLogs(id, params) {
  return request({
    url: `/api/v1/tasks/${id}/logs`,
    method: 'get',
    params
  })
}

// 导出任务数据
export function exportTasks(params) {
  return request({
    url: '/api/v1/tasks/export',
    method: 'get',
    params,
    responseType: 'blob'
  })
}

// 导入任务数据
export function importTasks(data) {
  return request({
    url: '/api/v1/tasks/import',
    method: 'post',
    data,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 获取视频帧用于ROI选择
export function getTaskFrame(sourceUrl) {
  return request({
    url: '/api/v1/tasks/frame',
    method: 'post',
    data: { source: sourceUrl }
  })
} 