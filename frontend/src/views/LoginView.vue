<template>
  <section class="login-page">
    <div class="login-card card">
      <h1 class="login-title">{{ session.state.status?.app_name || '番剧收藏登记系统' }}</h1>
      <p class="login-subcopy">{{ session.state.status?.library_subcopy || '请登录后继续使用。' }}</p>

      <form class="login-form" @submit.prevent="submit">
        <label class="login-field-label" for="login-username">用户名</label>
        <input
          id="login-username"
          ref="usernameInput"
          v-model="form.username"
          class="login-field"
          type="text"
          placeholder="admin"
          autocomplete="username"
          autocapitalize="none"
          enterkeyhint="next"
          @keyup.enter="focusPassword"
        />

        <label class="login-field-label" for="login-password">密码</label>
        <input
          id="login-password"
          ref="passwordInput"
          v-model="form.password"
          class="login-field"
          type="password"
          placeholder="请输入密码"
          autocomplete="current-password"
          enterkeyhint="go"
          @keyup.enter="submit"
        />

        <p v-if="errorMessage" class="login-error">{{ errorMessage }}</p>

        <button type="submit" class="login-submit" :disabled="loading">
          <span v-if="loading" class="login-spinner" aria-hidden="true" />
          <span>{{ loading ? '登录中…' : '登录' }}</span>
        </button>

        <p class="login-hint" :class="{ 'login-hint--attention': requiresPasswordChange }">
          {{ requiresPasswordChange ? '默认账号为 admin / ani-col-reg，首次登录后请尽快修改密码。' : '登录后可在系统配置中更新管理员账号和密码。' }}
        </p>
      </form>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthSession } from '../auth'

const router = useRouter()
const route = useRoute()
const session = useAuthSession()

const loading = ref(false)
const errorMessage = ref('')
const usernameInput = ref<HTMLInputElement | null>(null)
const passwordInput = ref<HTMLInputElement | null>(null)

const form = reactive({
  username: 'admin',
  password: ''
})

const requiresPasswordChange = computed(() => session.state.status?.requires_password_change ?? false)

onMounted(async () => {
  const authenticated = await session.ensureStatus()
  if (authenticated) {
    await router.replace('/seasons')
  } else {
    usernameInput.value?.focus()
  }
})

function focusPassword() {
  passwordInput.value?.focus()
}

async function submit() {
  if (loading.value) {
    return
  }

  errorMessage.value = ''
  loading.value = true
  try {
    await session.login(form.username, form.password)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/seasons'
    await router.replace(redirect)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '登录失败，请重试。'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  /* 使用视口高度，避免受外层内容包裹层影响导致无法垂直居中 */
  min-height: 100dvh;
  padding: calc(env(safe-area-inset-top) + 24px) 24px calc(env(safe-area-inset-bottom) + 24px);
}

.login-card {
  width: min(320px, 86vw);
  padding: 28px 22px 22px;
  border-radius: 16px;
}

.login-title {
  margin: 0;
  font-size: 26px;
  font-weight: 700;
  letter-spacing: 0.2px;
  text-align: center;
}

.login-subcopy {
  margin: 8px 0 22px;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.5;
  text-align: center;
}

.login-form {
  display: flex;
  flex-direction: column;
}

.login-field-label {
  margin: 0 0 6px 2px;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
}

.login-form .login-field-label:not(:first-child) {
  margin-top: 14px;
}

.login-field {
  width: 100%;
  height: 44px;
  padding: 0 14px;
  border: 1px solid transparent;
  border-radius: 12px;
  background: var(--fill);
  color: var(--text-primary);
  font-size: 16px;
  outline: none;
  transition:
    border-color 200ms ease,
    background-color 200ms ease;
}

.login-field::placeholder {
  color: var(--text-tertiary);
}

.login-field:focus {
  border-color: var(--accent);
}

.login-error {
  margin: 12px 2px 0;
  color: #ff3b30;
  font-size: 13px;
  line-height: 1.4;
}

.login-submit {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  height: 44px;
  margin-top: 18px;
  border-radius: 12px;
  background: var(--accent);
  color: #ffffff;
  font-size: 16px;
  font-weight: 600;
  transition: opacity 200ms ease;
}

.login-submit:disabled {
  opacity: 0.6;
  cursor: default;
}

.login-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.35);
  border-top-color: #ffffff;
  border-radius: 999px;
  animation: login-spinner-rotate 0.8s linear infinite;
}

@keyframes login-spinner-rotate {
  to {
    transform: rotate(360deg);
  }
}

.login-hint {
  margin: 16px 2px 0;
  color: var(--text-tertiary);
  font-size: 12px;
  line-height: 1.5;
  text-align: center;
}

.login-hint--attention {
  color: var(--text-secondary);
}
</style>
