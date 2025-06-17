import request from './request'

// 获取告警列表
export const getAlerts = (params) => {
  return request({
    url: '/alerts',
    method: 'get',
    params
  })
}

// 获取告警详情
export const getAlert = (id) => {
  return request({
    url: `/alerts/${id}`,
    method: 'get'
  })
}

// 更新告警
export const updateAlert = (id, data) => {
  return request({
    url: `/alerts/${id}`,
    method: 'put',
    data
  })
}

// 删除告警
export const deleteAlert = (id) => {
  return request({
    url: `/alerts/${id}`,
    method: 'delete'
  })
}

// 批量更新告警
export const batchUpdateAlerts = (data) => {
  return request({
    url: '/alerts/batch',
    method: 'put',
    data
  })
}

// 处理告警
export const processAlert = (id, data) => {
  return request({
    url: `/alerts/${id}/process`,
    method: 'post',
    data
  })
}

// 忽略告警
export const ignoreAlert = (id, data) => {
  return request({
    url: `/alerts/${id}/ignore`,
    method: 'post',
    data
  })
}

// 获取告警统计
export const getAlertStats = (params) => {
  return request({
    url: '/alerts/stats',
    method: 'get',
    params
  })
}

// 获取告警趋势
export const getAlertTrends = (params) => {
  return request({
    url: '/alerts/trends',
    method: 'get',
    params
  })
}

// 导出告警数据
export const exportAlerts = (params) => {
  return request({
    url: '/alerts/export',
    method: 'get',
    params,
    responseType: 'blob'
  })
}

// 获取告警日志
export const getAlertLogs = (id, params) => {
  return request({
    url: `/alerts/${id}/logs`,
    method: 'get',
    params
  })
}

// 添加告警备注
export const addAlertRemark = (id, data) => {
  return request({
    url: `/alerts/${id}/remark`,
    method: 'post',
    data
  })
}

// 获取告警配置
export const getAlertConfig = () => {
  return request({
    url: '/alerts/config',
    method: 'get'
  })
}

// 更新告警配置
export const updateAlertConfig = (data) => {
  return request({
    url: '/alerts/config',
    method: 'put',
    data
  })
} 