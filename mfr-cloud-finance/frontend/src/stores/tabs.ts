import { defineStore } from 'pinia'
import { ref } from 'vue'

/** 一个已打开的页面标签 */
export interface OpenTab {
  path: string
  title: string
  group?: string
  /** 固定标签（如首页）不可关闭 */
  fixed?: boolean
}

const STORAGE_KEY = 'mfr-open-tabs'

interface TabRouteLike {
  path: string
  meta?: { title?: string; group?: string }
}

/**
 * 已打开页面（快速切换面板 / 程序坞）状态
 * - 记录用户访问过的页面，便于在主页面顶部长条快速切换
 * - 去重 + 最近使用置尾，首页固定，localStorage 持久化
 */
export const useTabsStore = defineStore('tabs', () => {
  const openedTabs = ref<OpenTab[]>([])
  const activePath = ref<string>('')

  /** 从 localStorage 初始化（保证首页常驻） */
  function init() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (raw) openedTabs.value = JSON.parse(raw)
    } catch {
      openedTabs.value = []
    }
    if (!openedTabs.value.some((t) => t.path === '/dashboard')) {
      openedTabs.value.unshift({ path: '/dashboard', title: '仪表盘', fixed: true })
    }
  }

  function persist() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(openedTabs.value))
    } catch {
      /* 忽略持久化失败 */
    }
  }

  /** 打开（或激活）一个页面 */
  function openTab(route: TabRouteLike) {
    const path = route.path
    const title = route.meta?.title || '未命名'
    const group = route.meta?.group
    activePath.value = path
    const idx = openedTabs.value.findIndex((t) => t.path === path)
    if (idx >= 0) {
      const [t] = openedTabs.value.splice(idx, 1)
      t.title = title
      t.group = group
      openedTabs.value.push(t)
    } else {
      openedTabs.value.push({ path, title, group })
    }
    persist()
  }

  /**
   * 关闭一个标签，返回需要跳转到的路径（若关闭的是当前标签）
   * 固定标签不可关闭
   */
  function closeTab(path: string): string | null {
    const idx = openedTabs.value.findIndex((t) => t.path === path)
    if (idx < 0) return null
    if (openedTabs.value[idx].fixed) return null
    openedTabs.value.splice(idx, 1)
    persist()
    if (activePath.value === path) {
      const next = openedTabs.value[idx] || openedTabs.value[idx - 1]
      return next ? next.path : '/dashboard'
    }
    return null
  }

  /** 关闭其他（保留固定标签与指定标签） */
  function closeOthers(path: string) {
    openedTabs.value = openedTabs.value.filter((t) => t.fixed || t.path === path)
    activePath.value = path
    persist()
  }

  /** 关闭全部（仅保留固定标签） */
  function closeAll() {
    openedTabs.value = openedTabs.value.filter((t) => t.fixed)
    if (!openedTabs.value.some((t) => t.path === activePath.value)) {
      activePath.value = openedTabs.value[0]?.path || '/dashboard'
    }
    persist()
  }

  return {
    openedTabs,
    activePath,
    init,
    openTab,
    closeTab,
    closeOthers,
    closeAll,
  }
})
