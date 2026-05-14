<template>
  <section class="login-page">
    <div class="login-card">
      <div class="login-copy">
        <p class="login-eyebrow">Anime Library</p>
        <h1>{{ session.state.status?.app_name || '番剧收藏登记系统' }}</h1>
        <p>{{ session.state.status?.library_subcopy || '请登录后继续使用。' }}</p>
      </div>

      <el-form :model="form" class="login-form" @submit.prevent>
        <el-form-item label="管理员账号">
          <el-input v-model="form.username" size="large" placeholder="admin" />
        </el-form-item>

        <el-form-item label="登录密码">
          <el-input v-model="form.password" size="large" show-password placeholder="请输入密码" @keyup.enter="submit" />
        </el-form-item>

        <div v-if="session.state.status?.requires_password_change" class="login-hint">
          默认账号为 admin / ani-col-reg，首次登录后请在设置页修改。
        </div>

        <el-button type="primary" size="large" class="login-submit" :loading="loading" @click="submit">登录并进入</el-button>
      </el-form>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthSession } from '../auth'

const router = useRouter()
const route = useRoute()
const session = useAuthSession()
const loading = ref(false)
const form = reactive({
  username: 'admin',
  password: ''
})

onMounted(async () => {
  const authenticated = await session.ensureStatus(true)
  if (authenticated) {
    await router.replace('/anime')
  }
})

async function submit() {
  loading.value = true
  try {
    await session.login(form.username, form.password)
    ElMessage.success('登录成功')
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/anime'
    await router.replace(redirect)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: grid;
  min-height: 100vh;
  place-items: center;
  padding: 24px;
  background:
    radial-gradient(circle at top left, rgba(87, 144, 225, 0.24), transparent 24%),
    radial-gradient(circle at bottom right, rgba(77, 149, 214, 0.18), transparent 26%),
    linear-gradient(135deg, #07101c, #091423 52%, #050b15 100%);
}

.login-card {
  width: min(960px, 100%);
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(320px, 420px);
  gap: 28px;
  padding: 32px;
  background: var(--surface-card);
  border: 1px solid var(--surface-line);
  border-radius: 32px;
  box-shadow: 0 30px 68px rgba(2, 7, 15, 0.38);
  backdrop-filter: blur(18px);
}

.login-copy {
  display: grid;
  align-content: center;
  gap: 12px;
  padding-right: 18px;
}

.login-eyebrow {
  margin: 0;
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.login-copy h1 {
  margin: 0;
  color: var(--text-strong);
  font-size: clamp(34px, 5vw, 52px);
  line-height: 1.04;
}

.login-copy p:last-child {
  margin: 0;
  color: var(--text-muted);
  line-height: 1.75;
}

.login-form {
  padding: 24px;
  background: var(--surface-card-soft);
  border: 1px solid rgba(144, 173, 214, 0.12);
  border-radius: 24px;
}

.login-hint {
  margin-bottom: 16px;
  color: var(--text-muted);
  font-size: 13px;
  line-height: 1.6;
}

.login-submit {
  width: 100%;
  border-radius: 16px;
  box-shadow: 0 18px 34px rgba(40, 101, 161, 0.32);
}

.login-form :deep(.el-form-item__label) {
  color: rgba(224, 233, 247, 0.84);
  font-weight: 700;
}

.login-form :deep(.el-input__wrapper) {
  min-height: 48px;
  border-radius: 16px;
  background: var(--surface-input);
  box-shadow: 0 0 0 1px var(--surface-line) inset;
}

@media (max-width: 860px) {
  .login-card {
    grid-template-columns: 1fr;
    padding: 22px;
  }

  .login-copy {
    padding-right: 0;
  }
}
</style>
