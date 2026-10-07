<template>
  <div class="app-shell">
    <!-- 桌面宽屏（≥1024px）左侧固定侧边栏：登录页不显示 -->
    <aside v-if="route.path !== '/login'" class="sidebar frosted" aria-label="侧边导航">
      <div class="sidebar-header">
        <span class="sidebar-mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2.5" y="4" width="19" height="13" rx="2.75" />
            <path d="M8 20.5h8" />
          </svg>
        </span>
        <div class="sidebar-copy">
          <h1 class="sidebar-title">{{ appTitle }}</h1>
          <p class="sidebar-subtitle">番剧导视 · 收藏 · 检索</p>
        </div>
      </div>

      <nav class="sidebar-nav" aria-label="侧边菜单">
        <p class="sidebar-section-label">浏览</p>
        <RouterLink to="/seasons" class="sidebar-item" :class="{ 'is-active': isTabActive('/seasons') }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <rect x="2.5" y="4" width="19" height="13" rx="2.75" />
            <path d="M8 20.5h8" />
          </svg>
          <span>导视</span>
        </RouterLink>
        <RouterLink to="/collection" class="sidebar-item" :class="{ 'is-active': isTabActive('/collection') }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
          </svg>
          <span>收藏</span>
        </RouterLink>
        <RouterLink to="/search" class="sidebar-item" :class="{ 'is-active': isTabActive('/search') }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <circle cx="11" cy="11" r="7.5" />
            <path d="m20.5 20.5-4.6-4.6" />
          </svg>
          <span>搜索</span>
        </RouterLink>

        <p class="sidebar-section-label">管理</p>
        <RouterLink to="/settings" class="sidebar-item" :class="{ 'is-active': isTabActive('/settings') }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33h.01a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51h.01a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82v.01a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
          </svg>
          <span>系统设置</span>
        </RouterLink>
        <RouterLink to="/logs" class="sidebar-item" :class="{ 'is-active': isTabActive('/logs') }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" />
          </svg>
          <span>运行日志</span>
        </RouterLink>
      </nav>
    </aside>

    <main class="app-body no-scrollbar">
      <div class="app-body-inner">
        <RouterView v-slot="{ Component, route: viewRoute }">
          <Transition :name="transitionName" mode="out-in">
            <!-- 缓存主 Tab 视图：搜索条件/结果在 Tab 切换与详情页往返时不丢失 -->
            <KeepAlive :include="['SearchView', 'CollectionView']">
              <component :is="Component" :key="viewRoute.name" />
            </KeepAlive>
          </Transition>
        </RouterView>
      </div>
    </main>

    <nav v-if="!route.meta.hideTabbar" class="tabbar frosted" aria-label="主导航">
      <RouterLink to="/seasons" class="tabbar-item" :class="{ 'is-active': isTabActive('/seasons') }">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <rect x="2.5" y="4" width="19" height="13" rx="2.75" />
          <path d="M8 20.5h8" />
        </svg>
        <span class="tabbar-label">导视</span>
      </RouterLink>
      <RouterLink to="/collection" class="tabbar-item" :class="{ 'is-active': isTabActive('/collection') }">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
        </svg>
        <span class="tabbar-label">收藏</span>
      </RouterLink>
      <RouterLink to="/search" class="tabbar-item" :class="{ 'is-active': isTabActive('/search') }">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <circle cx="11" cy="11" r="7.5" />
          <path d="m20.5 20.5-4.6-4.6" />
        </svg>
        <span class="tabbar-label">搜索</span>
      </RouterLink>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthSession } from './auth'

const route = useRoute()
const router = useRouter()
const session = useAuthSession()

const TAB_PATHS = new Set(['/seasons', '/collection', '/search'])

const transitionName = ref('fade')

/** 侧边栏应用名：优先取后端设置里的 app_name */
const appTitle = computed(() => session.state.status?.app_name || '番剧收藏')

function pathDepth(path: string): number {
  return path.split('/').filter(Boolean).length
}

function isTabActive(tabPath: string): boolean {
  return route.path === tabPath || route.path.startsWith(`${tabPath}/`)
}

router.afterEach((to, from) => {
  // 管理页（设置 / 日志）不使用 iOS 滑动动画，统一淡入淡出
  if (to.meta.adminPage || from.meta.adminPage) {
    transitionName.value = 'fade'
    return
  }

  if (TAB_PATHS.has(to.path) && TAB_PATHS.has(from.path)) {
    transitionName.value = 'fade'
    return
  }

  if (to.path === '/login' || from.path === '/login') {
    transitionName.value = 'fade'
    return
  }

  const depthDelta = pathDepth(to.path) - pathDepth(from.path)
  transitionName.value = depthDelta > 0 ? 'slide-forward' : depthDelta < 0 ? 'slide-back' : 'fade'
})
</script>

<style>
.app-shell {
  height: 100dvh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.app-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

/* 桌面侧边栏：移动端默认隐藏 */
.sidebar {
  display: none;
}

.tabbar {
  flex-shrink: 0;
  display: flex;
  border-top: 0.5px solid var(--separator);
  padding-bottom: env(safe-area-inset-bottom);
}

.tabbar-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  height: 49px;
  color: var(--text-tertiary);
  transition: color 200ms ease;
}

.tabbar-item.is-active {
  color: var(--accent);
}

.tabbar-item svg {
  width: 26px;
  height: 26px;
}

.tabbar-label {
  font-size: 10px;
  line-height: 1;
}

/* 桌面宽屏（≥1024px）：左侧固定侧边栏 + 居中内容区，隐藏底部 TabBar */
@media (min-width: 1024px) {
  .app-shell {
    flex-direction: row;
  }

  .tabbar {
    display: none;
  }

  .sidebar {
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
    width: 240px;
    height: 100dvh;
    padding: 20px 14px 16px;
    border-right: 0.5px solid var(--separator);
    overflow-y: auto;
  }

  .app-body-inner {
    max-width: 1100px;
    margin: 0 auto;
    width: 100%;
  }
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 2px 8px 18px;
}

.sidebar-mark {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  border-radius: 12px;
  background: var(--accent);
  color: #ffffff;
}

.sidebar-mark svg {
  width: 22px;
  height: 22px;
}

.sidebar-copy {
  min-width: 0;
}

.sidebar-title {
  margin: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 0.2px;
}

.sidebar-subtitle {
  margin: 2px 0 0;
  color: var(--text-tertiary);
  font-size: 12px;
  white-space: nowrap;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
}

.sidebar-section-label {
  margin: 14px 10px 6px;
  color: var(--text-tertiary);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.6px;
  text-transform: uppercase;
}

.sidebar-item {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 42px;
  margin-bottom: 2px;
  padding: 0 12px;
  border-radius: 12px;
  color: var(--text-secondary);
  font-size: 15px;
  font-weight: 500;
  transition:
    background-color 200ms ease,
    color 200ms ease;
}

.sidebar-item svg {
  width: 21px;
  height: 21px;
  flex-shrink: 0;
}

.sidebar-item:hover {
  background: var(--fill);
  color: var(--text-primary);
}

.sidebar-item.is-active {
  background: var(--accent);
  color: #ffffff;
  font-weight: 600;
}

/* Tab 间切换：淡入淡出 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 200ms ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 详情 push：新页从右滑入并淡入 */
.slide-forward-enter-active {
  transition:
    transform 250ms cubic-bezier(0.32, 0.72, 0, 1),
    opacity 250ms ease;
}

.slide-forward-enter-from {
  transform: translateX(35%);
  opacity: 0;
}

.slide-forward-leave-active {
  transition: opacity 150ms ease;
}

.slide-forward-leave-to {
  opacity: 0;
}

/* 返回 pop：新页从左滑入并淡入 */
.slide-back-enter-active {
  transition:
    transform 250ms cubic-bezier(0.32, 0.72, 0, 1),
    opacity 250ms ease;
}

.slide-back-enter-from {
  transform: translateX(-35%);
  opacity: 0;
}

.slide-back-leave-active {
  transition: opacity 150ms ease;
}

.slide-back-leave-to {
  opacity: 0;
}
</style>
