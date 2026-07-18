import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './style.css'

const app = createApp(App)

// 注册 Pinia 状态管理
app.use(createPinia())

// 注册 Vue Router 路由
app.use(router)

// 注册 Element Plus（完整引入 + 中文语言包）
app.use(ElementPlus, { locale: zhCn })

// 全局注册 Element Plus 图标组件，方便在各处通过组件名直接使用
for (const [name, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(name, component)
}

app.mount('#app')
