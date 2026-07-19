import { defineStore } from 'pinia'
import { ref } from 'vue'

/** 一个已打开的页面标签 */
export interface OpenTab {
  path: string
  title: string
  group?: string
}

const STORAGE_KEY = 'mfr-open-tabs'

interface TabRouteLike {
  path: string
  meta?: { title?: string; group?: string }
}

/**
 * 已打开页面（快速切换面板 / 程序坞）状态
 * - 记录用户访问过的页面，便于在主页面顶部长条快速切换
 * - 首次打开顺序固定，再次打开仅激活，不移动位置
 * - localStorage 持久化
 */
export const useTabsStore = defineStore('tabs', () => {
  const openedTabs = ref<OpenTab[]>([])
  const activePath = ref<string>('')

  /** 从 localStorage 初始化 */
  function init() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (raw) openedTabs.value = JSON.parse(raw)
    } catch {
      openedTabs.value = []
    }
  }

  function persist() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(openedTabs.value))
    } catch {
      /* 忽略持久化失败 */
    }
  }

  /** 打开（或激活）一个页面，不移动已有标签位置 */
  function openTab(route: TabRouteLike) {
    const path = route.path
    const title = route.meta?.title || '未命名'
    const group = route.meta?.group
    activePath.value = path
    const idx = openedTabs.value.findIndex((t) => t.path === path)
    if (idx >= 0) {
      // 只更新标题/分组，保持原有位置
      openedTabs.value[idx].title = title
      openedTabs.value[idx].group = group
    } else {
      openedTabs.value.push({ path, title, group })
    }
    persist()
  }

  /**
   * 关闭一个标签，返回需要跳转到的路径（若关闭的是当前标签）
   */
  function closeTab(path: string): string | null {
    const idx = openedTabs.value.findIndex((t) => t.path === path)
    if (idx < 0) return null
    openedTabs.value.splice(idx, 1)
    persist()
    if (activePath.value === path) {
      const next = openedTabs.value[idx] || openedTabs.value[idx - 1]
      return next ? next.path : '/dashboard'
    }
    return null
  }

  /** 关闭其他（仅保留指定标签） */
  function closeOthers(path: string) {
    openedTabs.value = openedTabs.value.filter((t) => t.path === path)
    activePath.value = path
    persist()
  }

  /** 关闭全部 */
  function closeAll() {
    openedTabs.value = []
    activePath.value = '/dashboard'
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
