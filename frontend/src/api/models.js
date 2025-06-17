import request from './request'

// 获取模型列表（分页）
export function getModels(params) {
  return request({
    url: '/models',
    method: 'get',
    params
  })
}

// 获取模型详情
export function getModel(id) {
  return request({
    url: `/models/${id}`,
    method: 'get'
  })
}

// 创建模型
export const createModel = (data) => {
  return request({
    url: '/models',
    method: 'post',
    data
  })
}

// 更新模型
export function updateModel(id, data) {
  return request({
    url: `/models/${id}`,
    method: 'put',
    data
  })
}

// 删除模型
export function deleteModel(id) {
  return request({
    url: `/models/${id}`,
    method: 'delete'
  })
}

// 上传模型
export function uploadModel(data) {
  return request({
    url: '/models/upload',
    method: 'post',
    data,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 部署模型
export function deployModel(id) {
  return request({
    url: `/models/${id}/deploy`,
    method: 'post'
  })
}

// 取消部署模型
export const undeployModel = (id) => {
  return request({
    url: `/models/${id}/undeploy`,
    method: 'post'
  })
}

// 获取模型版本列表
export const getModelVersions = (id) => {
  return request({
    url: `/models/${id}/versions`,
    method: 'get'
  })
}

// 获取模型性能指标
export const getModelMetrics = (id, params) => {
  return request({
    url: `/models/${id}/metrics`,
    method: 'get',
    params
  })
}

// 批量操作模型
export const batchUpdateModels = (data) => {
  return request({
    url: '/models/batch',
    method: 'put',
    data
  })
}

// 导出模型配置
export const exportModel = (id) => {
  return request({
    url: `/models/${id}/export`,
    method: 'get',
    responseType: 'blob'
  })
}

// 导入模型配置
export const importModel = (data) => {
  return request({
    url: '/models/import',
    method: 'post',
    data,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 获取单个模型详情
export function getModelById(id) {
  return request({
    url: `/models/${id}`,
    method: 'get'
  })
}

export function updateModelStatus(id, status) {
  return request({
    url: `/models/${id}/status`,
    method: 'put',
    data: { status },
  });
} 