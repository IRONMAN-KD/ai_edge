import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

// 创建axios实例
const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 10000
})

// 请求拦截器
service.interceptors.request.use(
  config => {
    const userStore = useUserStore()
    console.log('Request Interceptor triggered for:', config.url)
    console.log('Headers before modification:', JSON.parse(JSON.stringify(config.headers)))
    
    if (userStore.token) {
      config.headers['Authorization'] = `Bearer ${userStore.token}`
      console.log('Authorization header set.')
    } else {
      console.log('No token found in store.')
    }
    
    console.log('Headers after modification:', JSON.parse(JSON.stringify(config.headers)))
    return config
  },
  error => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  response => {
    // API 响应的数据部分
    return response.data;
  },
  error => {
    console.error('Response error:', error)
    let message = '请求失败，请稍后重试'
    if (error.response) {
      // 后端返回的错误信息
      message = error.response.data.detail || `错误码: ${error.response.status}`
      if (error.response.status === 401) {
        // Token 失效或未授权
        const userStore = useUserStore()
        userStore.logout()
        // 跳转到登录页，这里可以结合路由实例来做
        window.location.href = '/login'
        message = '认证已过期，请重新登录'
      } else if (error.response.status === 404) {
        ElMessage.error('请求的资源不存在')
      } else if (error.response.status === 500) {
        ElMessage.error('服务器内部错误')
      }
    }
    ElMessage({
      message: message,
      type: 'error',
      duration: 5 * 1000
    })
    return Promise.reject(error)
  }
)

export default service 