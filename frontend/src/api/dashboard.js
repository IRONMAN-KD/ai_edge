import request from './request'

// 获取仪表盘统计数据
export const getDashboardStats = () => {
  return request({
    url: '/dashboard/stats',
    method: 'get'
  })
}

// 获取最近告警
export const getRecentAlerts = (params) => {
  return request({
    url: '/dashboard/alerts',
    method: 'get',
    params
  })
}

// 获取任务运行状态
export const getTaskStatus = () => {
  return request({
    url: '/dashboard/tasks',
    method: 'get'
  })
}

// 获取系统性能指标
export const getSystemMetrics = (params) => {
  return request({
    url: '/dashboard/metrics',
    method: 'get',
    params
  })
}

// 获取告警趋势图数据
export const getAlertTrends = (params) => {
  return request({
    url: '/dashboard/alert-trends',
    method: 'get',
    params
  })
}

// 获取任务执行统计
export const getTaskExecutionStats = (params) => {
  return request({
    url: '/dashboard/task-execution',
    method: 'get',
    params
  })
}

// 获取模型使用统计
export const getModelUsageStats = (params) => {
  return request({
    url: '/dashboard/model-usage',
    method: 'get',
    params
  })
}

// 获取系统资源使用情况
export const getSystemResources = () => {
  return request({
    url: '/dashboard/resources',
    method: 'get'
  })
}

// 获取系统日志
export const getSystemLogs = (params) => {
  return request({
    url: '/dashboard/logs',
    method: 'get',
    params
  })
}

// 获取通知消息
export const getNotifications = (params) => {
  return request({
    url: '/dashboard/notifications',
    method: 'get',
    params
  })
}

// 标记通知为已读
export const markNotificationRead = (id) => {
  return request({
    url: `/dashboard/notifications/${id}/read`,
    method: 'put'
  })
}

// 获取快速操作菜单
export const getQuickActions = () => {
  return request({
    url: '/dashboard/quick-actions',
    method: 'get'
  })
}

// 获取仪表盘配置
export const getDashboardConfig = () => {
  return request({
    url: '/dashboard/config',
    method: 'get'
  })
}

// 更新仪表盘配置
export const updateDashboardConfig = (data) => {
  return request({
    url: '/dashboard/config',
    method: 'put',
    data
  })
} 