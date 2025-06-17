import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

import App from './App.vue'
import './style/index.scss'

async function bootstrap() {
  const app = createApp(App)

  app.use(createPinia())

  // Dynamically import router after Pinia is installed
  const router = (await import('./router')).default

  for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
  }

  app.use(router)
  app.use(ElementPlus, {
    locale: zhCn
  })

  app.mount('#app')
}

bootstrap() 