import request from './request'

// 登录
export function login(data) {
  return request({
    url: '/api/v1/auth/login',
    method: 'post',
    // axios的Content-Type默认就是application/json
    // 但登录接口通常需要application/x-www-form-urlencoded
    // 所以需要特殊处理一下
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    data
  })
}

// 获取用户信息
export function getUserInfo() {
  return request({
    url: '/api/v1/users/me/',
    method: 'get'
  })
}

// 登出
// 注意：后端没有提供登出接口，所以前端登出通常是清除本地token
export function logout() {
  // 此处不需要API调用，可以在store中直接清除token
  return Promise.resolve()
}

// 刷新token
export const refreshToken = () => {
  return request({
    url: '/api/v1/auth/refresh',
    method: 'post'
  })
}

// 修改密码
export const changePassword = (data) => {
  return request({
    url: '/api/v1/auth/password',
    method: 'put',
    data
  })
}

// 忘记密码
export const forgotPassword = (data) => {
  return request({
    url: '/api/v1/auth/forgot-password',
    method: 'post',
    data
  })
}

// 重置密码
export const resetPassword = (data) => {
  return request({
    url: '/api/v1/auth/reset-password',
    method: 'post',
    data
  })
}

// 验证token
export const verifyToken = () => {
  return request({
    url: '/api/v1/auth/verify',
    method: 'get'
  })
} 