import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'layout',
    component: () => import('@/layout/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '仪表盘' }
      },
      {
        path: '/models',
        name: 'models',
        component: () => import('@/views/ModelManagement.vue'),
        meta: { title: '模型管理' }
      },
      {
        path: '/tasks',
        name: 'tasks',
        component: () => import('@/views/TaskManagement.vue'),
        meta: { title: '任务配置' }
      },
      {
        path: '/alerts',
        name: 'alerts',
        component: () => import('@/views/Alerts.vue'),
        meta: { title: '告警管理' }
      },
      {
        path: '/alerts/:id',
        name: 'alertDetail',
        component: () => import('@/views/AlertDetail.vue'),
        meta: { title: '告警详情' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next('/login')
  } else {
    next()
  }
})

export default router 