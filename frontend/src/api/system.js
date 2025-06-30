import request from './request'

// 获取系统配置
export function getSystemConfigs() {
  return request({
    url: '/api/v1/config',
    method: 'get'
  })
}

// 更新系统配置
export function updateSystemConfigs(data) {
  return request({
    url: '/api/v1/config',
    method: 'put',
    data
  })
}

// 获取告警图片（需要token验证）
export function getAlertImage(imageName) {
  return request({
    url: `/system/image/${imageName}`,
    method: 'get',
    responseType: 'blob' // Important for image data
  });
} 