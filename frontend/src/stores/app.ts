import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * 应用级全局状态
 * - 侧边栏折叠状态
 * - 当前公司
 */
export const useAppStore = defineStore('app', () => {
  /** 侧边栏是否折叠 */
  const sidebarCollapsed = ref<boolean>(false)
  /** 当前选中的公司名称 */
  const currentCompany = ref<string>('')

  /** 切换侧边栏折叠状态 */
  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  /** 设置侧边栏折叠状态 */
  function setSidebarCollapsed(value: boolean) {
    sidebarCollapsed.value = value
  }

  /** 设置当前公司 */
  function setCurrentCompany(company: string) {
    currentCompany.value = company
  }

  return {
    sidebarCollapsed,
    currentCompany,
    toggleSidebar,
    setSidebarCollapsed,
    setCurrentCompany,
  }
})
