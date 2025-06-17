import request from './request'

// 用户登录
export const login = (data) => {
  const params = new URLSearchParams()
  params.append('username', data.username)
  params.append('password', data.password)

  return request({
    url: '/auth/login',
    method: 'post',
    data: params
  })
}

// 用户登出
export const logout = () => {
  return request({
    url: '/auth/logout',
    method: 'post'
  })
}

// 获取用户信息
export const getUserInfo = () => {
  return request({
    url: '/users/me/',
    method: 'get'
  })
}

// 刷新token
export const refreshToken = () => {
  return request({
    url: '/auth/refresh',
    method: 'post'
  })
}

// 修改密码
export const changePassword = (data) => {
  return request({
    url: '/auth/password',
    method: 'put',
    data
  })
}

// 忘记密码
export const forgotPassword = (data) => {
  return request({
    url: '/auth/forgot-password',
    method: 'post',
    data
  })
}

// 重置密码
export const resetPassword = (data) => {
  return request({
    url: '/auth/reset-password',
    method: 'post',
    data
  })
}

// 验证token
export const verifyToken = () => {
  return request({
    url: '/auth/verify',
    method: 'get'
  })
} 