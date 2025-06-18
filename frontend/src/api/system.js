import request from '@/api/request'

export function getSystemConfigs() {
  return request({
    url: '/system/configs',
    method: 'get'
  })
}

export function updateSystemConfigs(data) {
  return request({
    url: '/system/configs',
    method: 'put',
    data
  })
} 