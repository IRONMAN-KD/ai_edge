import request from './request'

// 获取告警列表
export function getAlerts(params) {
  return request({
    url: '/api/v1/alerts',
    method: 'get',
    params
  })
}

// 获取单个告警详情
export function getAlert(id) {
  return request({
    url: `/api/v1/alerts/${id}`,
    method: 'get'
  })
}

// 更新告警状态
export function updateAlert(id, data) {
  return request({
    url: `/api/v1/alerts/${id}`,
    method: 'put',
    data
  })
}

// 删除告警
export function deleteAlert(id) {
  return request({
    url: `/api/v1/alerts/${id}`,
    method: 'delete'
  })
}

// 批量更新告警状态
export function batchUpdateAlerts({ ids, status, remark }) {
  return request({
    url: '/api/v1/alerts/batch',
    method: 'put',
    data: { ids, status, remark }
  })
}

// 处理告警
export function processAlert(id, data) {
  return updateAlert(id, data)
}

// 忽略告警
export function ignoreAlert(id, data) {
  return updateAlert(id, data)
}

// 获取告警统计
export function getAlertStats(params) {
  return request({
    url: '/api/v1/alerts/stats',
    method: 'get',
    params
  })
}

// 获取告警趋势
export function getAlertTrends(params) {
  return request({
    url: '/api/v1/alerts/trends',
    method: 'get',
    params
  })
}

// 导出告警数据
export function exportAlerts(params) {
  return request({
    url: '/api/v1/alerts/export',
    method: 'get',
    params,
    responseType: 'blob'
  })
}

// 获取告警日志
export function getAlertLogs(id, params) {
  return request({
    url: `/alerts/${id}/logs`,
    method: 'get',
    params
  })
}

// 添加告警备注
export function addAlertRemark(id, data) {
  return request({
    url: `/alerts/${id}/remark`,
    method: 'post',
    data
  })
}

// 获取告警配置
export function getAlertConfig() {
  return request({
    url: '/api/v1/alerts/config',
    method: 'get'
  })
}

// 更新告警配置
export function updateAlertConfig(data) {
  return request({
    url: '/api/v1/alerts/config',
    method: 'put',
    data
  })
} 