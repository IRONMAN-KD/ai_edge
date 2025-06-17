import request from './request'

// 获取任务列表
export function getTasks(params) {
  return request({
    url: '/tasks',
    method: 'get',
    params
  })
}

// 获取任务详情
export function getTask(id) {
  return request({
    url: `/tasks/${id}`,
    method: 'get'
  })
}

// 创建任务
export function createTask(data) {
  return request({
    url: '/tasks',
    method: 'post',
    data
  })
}

// 更新任务
export function updateTask(id, data) {
  return request({
    url: `/tasks/${id}`,
    method: 'put',
    data
  })
}

// 删除任务
export function deleteTask(id) {
  return request({
    url: `/tasks/${id}`,
    method: 'delete'
  })
}

// 启动任务
export function startTask(id) {
  return request({
    url: `/tasks/${id}/start`,
    method: 'post'
  })
}

// 停止任务
export function stopTask(id) {
  return request({
    url: `/tasks/${id}/stop`,
    method: 'post'
  })
}

// 获取任务状态
export function getTaskStatus(id) {
  return request({
    url: `/tasks/${id}/status`,
    method: 'get'
  })
}

// 批量操作任务
export function batchUpdateTasks(data) {
  return request({
    url: '/tasks/batch',
    method: 'put',
    data
  })
}

// 获取任务统计信息
export function getTaskStats() {
  return request({
    url: '/tasks/stats',
    method: 'get'
  })
}

// 获取任务日志
export function getTaskLogs(id, params) {
  return request({
    url: `/tasks/${id}/logs`,
    method: 'get',
    params
  })
}

// 导出任务数据
export function exportTasks(params) {
  return request({
    url: '/tasks/export',
    method: 'get',
    params,
    responseType: 'blob'
  })
}

// 导入任务数据
export function importTasks(data) {
  return request({
    url: '/tasks/import',
    method: 'post',
    data,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 获取视频源的一帧用于ROI选择
export function getTaskFrame(source) {
  return request({
    url: '/tasks/frame',
    method: 'post',
    data: { source }
  })
} 