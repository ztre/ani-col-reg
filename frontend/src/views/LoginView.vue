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
  position: relative;
  isolation: isolate;
  padding: 32px 24px;
  background: transparent;
}

.login-page::before {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at top left, rgba(255, 178, 213, 0.14), transparent 24%),
    radial-gradient(circle at bottom right, rgba(124, 183, 255, 0.12), transparent 26%);
  content: '';
  pointer-events: none;
}

.login-card {
  position: relative;
  width: min(1040px, 100%);
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(320px, 396px);
  gap: 22px;
  padding: 28px;
  overflow: hidden;
  background: var(--surface-card);
  border: 1px solid var(--surface-line);
  border-radius: 32px;
  box-shadow: var(--elevation-hero);
  backdrop-filter: blur(18px);
}

.login-card::before {
  position: absolute;
  inset: 18px auto 18px 18px;
  width: min(34%, 260px);
  background-image: var(--hero-auth-image);
  background-repeat: no-repeat;
  background-size: contain;
  background-position: left 78%;
  content: '';
  pointer-events: none;
  opacity: 0.88;
  z-index: 0;
}

.login-card::after {
  position: absolute;
  inset: auto -8% -36% auto;
  width: 280px;
  height: 280px;
  background: var(--hero-art-glow);
  content: '';
  pointer-events: none;
}

.login-copy {
  display: grid;
  align-content: center;
  gap: 14px;
  min-height: 340px;
  max-width: 510px;
  padding-right: 8px;
}

.login-copy,
.login-form {
  position: relative;
  z-index: 1;
}

.login-eyebrow {
  margin: 0;
  color: var(--accent);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.24em;
  text-transform: uppercase;
}

.login-copy h1 {
  margin: 0;
  color: var(--text-strong);
  max-width: 10ch;
  font-size: clamp(2.7rem, 4.8vw, 4.5rem);
  line-height: 0.94;
  letter-spacing: -0.04em;
}

.login-copy p:last-child {
  margin: 0;
  max-width: 32rem;
  color: var(--text-muted);
  font-size: 1rem;
  line-height: 1.8;
}

.login-form {
  padding: 22px;
  background: var(--surface-card-soft);
  border: 1px solid var(--panel-soft-border);
  border-radius: 24px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.38);
}

.login-hint {
  margin-bottom: 16px;
  color: var(--text-muted);
  font-size: 13px;
  line-height: 1.6;
}

.login-submit {
  width: 100%;
  min-height: 54px;
  border-radius: 16px;
  color: var(--action-primary-text);
  font-weight: 800;
  letter-spacing: 0.02em;
  box-shadow: var(--action-primary-shadow);
}

.login-form :deep(.el-form-item__label) {
  color: var(--text-soft);
  margin-bottom: 6px;
  font-size: 14px;
  font-weight: 700;
}

.login-form :deep(.el-input__wrapper) {
  min-height: 52px;
  border-radius: 16px;
  background: var(--surface-input);
  box-shadow: 0 0 0 1px var(--surface-line) inset;
}

.login-form :deep(.el-input__inner) {
  font-size: 16px;
}

@media (max-width: 860px) {
  .login-page {
    padding: 20px 14px;
  }

  .login-card {
    grid-template-columns: 1fr;
    gap: 18px;
    padding: 20px;
    border-radius: 26px;
  }

  .login-card::before {
    display: none;
  }

  .login-copy {
    min-height: 0;
    padding-right: 0;
    gap: 10px;
    max-width: none;
  }

  .login-copy h1 {
    max-width: none;
    font-size: clamp(2.2rem, 10vw, 3.4rem);
  }

  .login-copy p:last-child {
    max-width: none;
    font-size: 0.96rem;
    line-height: 1.7;
  }

  .login-form {
    padding: 18px;
  }
}

@media (max-width: 480px) {
  .login-page {
    align-items: start;
    padding-top: 18px;
  }

  .login-card {
    gap: 16px;
    padding: 16px;
    border-radius: 22px;
  }

  .login-copy {
    gap: 8px;
  }

  .login-eyebrow {
    font-size: 10px;
    letter-spacing: 0.2em;
  }

  .login-copy h1 {
    font-size: clamp(1.9rem, 11vw, 2.8rem);
    line-height: 0.96;
  }

  .login-copy p:last-child {
    font-size: 0.92rem;
  }

  .login-form {
    padding: 16px;
    border-radius: 20px;
  }

  .login-form :deep(.el-form-item) {
    margin-bottom: 16px;
  }

  .login-form :deep(.el-input__wrapper) {
    min-height: 50px;
  }

  .login-submit {
    min-height: 50px;
    border-radius: 14px;
  }
}
</style>
