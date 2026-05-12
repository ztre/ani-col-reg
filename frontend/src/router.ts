import { createRouter, createWebHistory } from 'vue-router'

import { useAuthSession } from './auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/anime' },
    { path: '/login', component: () => import('./views/LoginView.vue'), meta: { title: '登录', public: true } },
    { path: '/anime', component: () => import('./views/AnimeList.vue'), meta: { title: '番剧库' } },
    { path: '/anime/:id', component: () => import('./views/AnimeDetail.vue'), props: true, meta: { title: '番剧详情' } },
    { path: '/collection', component: () => import('./views/CollectionView.vue'), meta: { title: '收藏管理' } },
    { path: '/settings', component: () => import('./views/SettingsView.vue'), meta: { title: '系统设置' } }
  ]
})

router.beforeEach(async (to) => {
  const session = useAuthSession()
  const authenticated = await session.ensureStatus()

  if (to.meta.public) {
    if (authenticated && to.path === '/login') {
      return '/anime'
    }
    return true
  }

  if (!authenticated) {
    return {
      path: '/login',
      query: to.fullPath === '/anime' ? undefined : { redirect: to.fullPath }
    }
  }

  return true
})

export default router
