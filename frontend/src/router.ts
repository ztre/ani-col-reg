import { createRouter, createWebHistory } from 'vue-router'

import { useAuthSession } from './auth'

declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    public?: boolean
    hideTabbar?: boolean
    /** 管理页（设置 / 日志）：不参与 iOS 滑动切换动画 */
    adminPage?: boolean
  }
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/seasons' },
    {
      path: '/login',
      component: () => import('./views/LoginView.vue'),
      meta: { title: '登录', public: true, hideTabbar: true }
    },
    {
      path: '/seasons',
      component: () => import('./views/SeasonsView.vue'),
      meta: { title: '导视' }
    },
    {
      path: '/collection',
      component: () => import('./views/CollectionView.vue'),
      meta: { title: '收藏' }
    },
    {
      path: '/collection/:seriesKey',
      component: () => import('./views/SeriesDetailView.vue'),
      props: true,
      meta: { title: '系列详情', hideTabbar: true }
    },
    {
      path: '/search',
      component: () => import('./views/SearchView.vue'),
      meta: { title: '搜索' }
    },
    {
      path: '/anime/:id',
      component: () => import('./views/AnimeDetailView.vue'),
      props: true,
      meta: { title: '番剧详情', hideTabbar: true }
    },
    {
      path: '/settings',
      component: () => import('./views/SettingsView.vue'),
      meta: { title: '系统设置', adminPage: true }
    },
    {
      path: '/logs',
      component: () => import('./views/LogsView.vue'),
      meta: { title: '运行日志', adminPage: true }
    }
  ]
})

router.beforeEach(async (to) => {
  const session = useAuthSession()
  const authenticated = await session.ensureStatus()

  if (to.meta.public) {
    if (authenticated && to.path === '/login') {
      return '/seasons'
    }
    return true
  }

  if (!authenticated) {
    return {
      path: '/login',
      query: to.fullPath === '/seasons' ? undefined : { redirect: to.fullPath }
    }
  }

  return true
})

export default router
