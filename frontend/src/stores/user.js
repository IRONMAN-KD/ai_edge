import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, getUserInfo as getUserInfoApi } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('userInfo') || 'null'))
  console.log('User store initialized. Token from localStorage:', token.value)

  const isLoggedIn = computed(() => !!token.value)

  const login = async (credentials) => {
    try {
      const response = await loginApi(credentials)
      console.log('Login API response:', response)
      if (response.access_token) {
        token.value = response.access_token
        localStorage.setItem('token', token.value)
        console.log('Token set in store and localStorage:', token.value)
        await getUserInfo() // Fetch user info after successful login
        return { success: true }
      }
      return { success: false, message: response.message || '登录响应格式不正确' }
    } catch (error) {
      return { success: false, message: error.message }
    }
  }

  const getUserInfo = async () => {
    if (!token.value) return
    try {
      const data = await getUserInfoApi()
      userInfo.value = data
      localStorage.setItem('userInfo', JSON.stringify(data))
    } catch (error) {
      console.error('获取用户信息失败:', error)
      // Maybe logout if user info is critical and fails to load
      // logout() 
    }
  }

  const logout = () => {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    login,
    logout,
    getUserInfo
  }
}) 