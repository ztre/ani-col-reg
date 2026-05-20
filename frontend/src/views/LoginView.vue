<template>
  <section class="login-page">
    <div class="login-card">
      <div class="login-copy">
        <div class="login-copy-head">
          <p class="login-eyebrow">Anime Library</p>
          <h1>{{ session.state.status?.app_name || '番剧收藏登记系统' }}</h1>
          <p class="login-summary">{{ session.state.status?.library_subcopy || '请登录后继续使用。' }}</p>
        </div>
      </div>

      <div class="login-panel">
        <div class="login-panel-copy">
          <p class="login-panel-label">Access</p>
          <h2>管理员登录</h2>
          <p>输入当前管理员账号和密码，进入番剧库与系统配置中心。</p>
        </div>

        <el-form :model="form" label-position="top" class="login-form" @submit.prevent>
          <el-form-item label="管理员账号">
            <el-input v-model="form.username" size="large" placeholder="admin" autocomplete="username" />
          </el-form-item>

          <el-form-item label="登录密码">
            <el-input
              v-model="form.password"
              size="large"
              show-password
              placeholder="请输入密码"
              autocomplete="current-password"
              @keyup.enter="submit"
            />
          </el-form-item>

          <div class="login-hint" :class="{ 'login-hint--attention': session.state.status?.requires_password_change }">
            {{
              session.state.status?.requires_password_change
                ? '默认账号为 admin / ani-col-reg，首次登录后请尽快到设置页修改。'
                : '登录后可以在系统配置中心更新管理员账号和密码。'
            }}
          </div>

          <el-button type="primary" size="large" class="login-submit" :loading="loading" @click="submit">登录并进入</el-button>
        </el-form>
      </div>
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
  padding: clamp(20px, 4vw, 40px);
  background:
    radial-gradient(circle at top, rgba(116, 188, 255, 0.08), transparent 34%),
    linear-gradient(180deg, rgba(6, 12, 22, 0.2), rgba(6, 12, 22, 0.02));
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
  width: min(1100px, 100%);
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(340px, 420px);
  gap: 24px;
  padding: 32px;
  overflow: hidden;
  background: var(--surface-card);
  border: 1px solid var(--surface-line);
  border-radius: 34px;
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
  opacity: 0.8;
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

.login-card > * {
  position: relative;
  z-index: 1;
}

.login-copy {
  display: grid;
  --login-copy-offset: clamp(108px, 11vw, 148px);
  align-content: center;
  min-height: 360px;
  max-width: 100%;
  padding: 6px 6px 6px 0;
}

.login-copy-head {
  display: grid;
  gap: 16px;
  max-width: min(40rem, calc(100% - var(--login-copy-offset)));
  margin-left: var(--login-copy-offset);
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
  max-width: none;
  font-size: clamp(2.9rem, 4.7vw, 4.3rem);
  line-height: 0.98;
  text-wrap: pretty;
  letter-spacing: -0.04em;
}

.login-summary {
  margin: 0;
  max-width: 36rem;
  color: var(--text-muted);
  font-size: 1rem;
  line-height: 1.8;
}

.login-panel-label {
  margin: 0;
  color: var(--accent);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.login-panel {
  display: grid;
  align-content: start;
  gap: 20px;
  padding: 24px;
  background: linear-gradient(180deg, rgba(15, 28, 46, 0.92), rgba(9, 17, 30, 0.96));
  border: 1px solid rgba(144, 173, 214, 0.18);
  border-radius: 28px;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.06),
    0 20px 36px rgba(3, 8, 15, 0.18);
}

.login-panel-copy {
  display: grid;
  gap: 8px;
}

.login-panel-copy h2,
.login-panel-copy p {
  margin: 0;
}

.login-panel-copy h2 {
  color: var(--text-strong);
  font-size: clamp(1.6rem, 2vw, 2rem);
}

.login-panel-copy p {
  color: var(--text-muted);
  line-height: 1.7;
}

.login-form {
  display: grid;
  gap: 2px;
}

.login-hint {
  margin-bottom: 18px;
  padding: 14px 16px;
  color: var(--text-muted);
  font-size: 13px;
  line-height: 1.65;
  background: var(--notice-info-bg);
  border: 1px solid var(--notice-info-border);
  border-radius: 16px;
}

.login-hint--attention {
  color: var(--shell-warning-text);
  background: var(--shell-warning-bg);
  border-color: var(--shell-warning-border);
}

.login-form :deep(.el-form-item) {
  margin-bottom: 18px;
}

.login-submit {
  width: 100%;
  min-height: 54px;
  border-radius: 18px;
  color: var(--action-primary-text);
  font-weight: 800;
  letter-spacing: 0.02em;
  box-shadow: var(--action-primary-shadow);
}

.login-submit:hover,
.login-submit:focus-visible {
  box-shadow: var(--action-primary-shadow-hover);
  transform: translateY(-1px);
}

.login-form :deep(.el-form-item__label) {
  padding-bottom: 8px;
  color: var(--text-soft);
  font-size: 14px;
  font-weight: 700;
}

.login-form :deep(.el-form-item__content) {
  line-height: 1;
}

.login-form :deep(.el-input__wrapper) {
  min-height: 54px;
  padding-inline: 16px;
  border-radius: 18px;
  background: var(--surface-input);
  box-shadow:
    0 0 0 1px var(--surface-line) inset,
    0 12px 24px rgba(3, 8, 15, 0.08);
}

.login-form :deep(.el-input__wrapper.is-focus) {
  box-shadow:
    0 0 0 1px var(--accent-strong) inset,
    0 16px 28px rgba(32, 94, 151, 0.16);
}

.login-form :deep(.el-input__inner) {
  font-size: 16px;
}

@media (max-width: 960px) {
  .login-card {
    grid-template-columns: 1fr;
    gap: 20px;
    padding: 24px;
    border-radius: 28px;
  }

  .login-card::before {
    display: none;
  }

  .login-copy {
    --login-copy-offset: 0px;
    min-height: 0;
    max-width: none;
    padding: 0;
  }

  .login-copy-head {
    margin-left: 0;
    max-width: none;
  }

  .login-copy h1 {
    max-width: none;
    font-size: clamp(2.6rem, 8vw, 3.8rem);
  }

  .login-panel {
    padding: 22px;
  }
}

@media (max-height: 860px) and (min-width: 961px) {
  .login-page {
    padding: 16px;
  }

  .login-card {
    gap: 20px;
    padding: 24px;
  }

  .login-copy {
    --login-copy-offset: clamp(92px, 9vw, 124px);
    min-height: 0;
  }

  .login-copy-head {
    gap: 12px;
  }

  .login-copy h1 {
    font-size: clamp(2.5rem, 4vw, 3.7rem);
  }

  .login-summary,
  .login-panel-copy p {
    font-size: 0.94rem;
    line-height: 1.58;
  }

  .login-panel {
    gap: 16px;
    padding: 20px;
  }

  .login-form :deep(.el-form-item) {
    margin-bottom: 16px;
  }

  .login-form :deep(.el-form-item__label) {
    padding-bottom: 6px;
  }

  .login-form :deep(.el-input__wrapper) {
    min-height: 50px;
  }

  .login-hint {
    margin-bottom: 16px;
    padding: 12px 14px;
  }

  .login-submit {
    min-height: 50px;
  }
}

@media (max-width: 720px) {
  .login-page {
    padding: 18px 14px;
  }

  .login-card {
    gap: 18px;
    padding: 18px;
  }

  .login-copy-head {
    gap: 12px;
  }

  .login-summary {
    max-width: none;
    font-size: 0.96rem;
    line-height: 1.72;
  }

  .login-panel {
    border-radius: 22px;
  }
}

@media (max-width: 480px) {
  .login-page {
    align-items: start;
    padding-top: 16px;
  }

  .login-card {
    padding: 16px;
    border-radius: 22px;
  }

  .login-eyebrow,
  .login-panel-label {
    font-size: 10px;
    letter-spacing: 0.16em;
  }

  .login-copy h1 {
    max-width: none;
    font-size: clamp(2.3rem, 11vw, 3.1rem);
  }

  .login-panel {
    padding: 18px 16px;
    border-radius: 20px;
  }

  .login-form :deep(.el-form-item) {
    margin-bottom: 16px;
  }

  .login-form :deep(.el-input__wrapper) {
    min-height: 50px;
    border-radius: 16px;
  }

  .login-submit {
    min-height: 50px;
    border-radius: 16px;
  }
}
</style>
