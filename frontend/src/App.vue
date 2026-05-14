<template>
  <router-view v-if="isLoginPage" />

  <el-container v-else class="app-shell">
    <el-aside width="248px" class="sidebar">
      <div class="brand">
        <span class="brand-mark">A</span>
        <div class="brand-copy">
          <strong>{{ appName }}</strong>
          <small>Poster Wall</small>
        </div>
      </div>

      <el-menu :default-active="$route.path" router class="nav">
        <el-menu-item index="/anime">
          <el-icon><Grid /></el-icon>
          <span>番剧库</span>
        </el-menu-item>
        <el-menu-item index="/collection">
          <el-icon><Star /></el-icon>
          <span>收藏管理</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>

      <div class="sidebar-note">
        <span class="sidebar-note-label">数据源</span>
        <strong>{{ activeSourceLabel }}</strong>
        <p>深色海报墙浏览与本地收藏整理并行。</p>
      </div>
    </el-aside>

    <el-container>
      <el-header class="topbar">
        <div class="topbar-actions">
          <span v-if="session.state.status?.requires_password_change" class="warning-chip">请修改默认密码</span>
          <el-button text class="topbar-link" :icon="Setting" @click="router.push('/settings')">设置</el-button>
          <span class="user-chip">
            <el-icon><User /></el-icon>
            {{ session.state.user?.username || 'admin' }}
          </span>
          <el-button text class="topbar-link" :icon="SwitchButton" @click="handleLogout">退出</el-button>
        </div>
      </el-header>

      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { Grid, Setting, Star, SwitchButton, User } from '@element-plus/icons-vue'
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthSession } from './auth'

const route = useRoute()
const router = useRouter()
const session = useAuthSession()

const isLoginPage = computed(() => route.path === '/login')
const appName = computed(() => session.state.settings?.app_name || session.state.status?.app_name || '番剧收藏')
const activeSourceLabel = computed(() => (session.state.settings?.anime_source === 'mikan' ? 'Mikan' : 'YourAnimes'))

async function handleLogout() {
  await session.logout()
  await router.push('/login')
}
</script>
