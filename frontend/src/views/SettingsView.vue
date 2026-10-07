<template>
  <div class="page">
    <NavBar title="系统设置" />

    <!-- 加载中 -->
    <div v-if="loading" class="loading-section" role="status" aria-label="加载中">
      <span class="loading-spinner" aria-hidden="true" />
    </div>

    <!-- 加载失败 -->
    <div v-else-if="loadError" class="state-section">
      <EmptyState icon="warning" title="加载失败" hint="请检查网络连接后重试" />
      <button type="button" class="retry-button" @click="load">重试</button>
    </div>

    <!-- 设置表单 -->
    <form v-else class="settings-section" novalidate @submit.prevent="save">
      <!-- 基本信息 -->
      <section class="settings-group">
        <h2 class="group-header">基本信息</h2>
        <div class="group-card">
          <div class="field-row">
            <label class="field-label" for="settings-app-name">应用名</label>
            <input
              id="settings-app-name"
              v-model="form.appName"
              class="field-input"
              type="text"
              placeholder="番剧收藏登记系统"
              autocomplete="off"
            />
          </div>
          <div class="field-row">
            <span class="field-label">数据源地址</span>
            <span class="field-value">
              {{ dataSourceUrl }}
              <span class="source-tag">{{ dataSourceName }}</span>
            </span>
          </div>
        </div>
        <p class="group-footer">数据源地址由服务端环境配置提供，仅供查看。</p>
      </section>

      <!-- 默认查询 -->
      <section class="settings-group">
        <h2 class="group-header">默认查询</h2>
        <div class="group-card">
          <div class="field-row">
            <label class="field-label" for="settings-year">默认年份</label>
            <input
              id="settings-year"
              v-model="form.year"
              class="field-input field-input--compact"
              type="number"
              min="1968"
              max="2100"
              inputmode="numeric"
            />
          </div>
          <div class="field-row">
            <label class="field-label" for="settings-season">默认季度</label>
            <select id="settings-season" v-model="form.season" class="field-select">
              <option value="">不限</option>
              <option value="1">冬（1 月）</option>
              <option value="2">春（4 月）</option>
              <option value="3">夏（7 月）</option>
              <option value="4">秋（10 月）</option>
            </select>
          </div>
          <div class="field-row">
            <label class="field-label" for="settings-page-size">每页数量</label>
            <input
              id="settings-page-size"
              v-model="form.pageSize"
              class="field-input field-input--compact"
              type="number"
              min="12"
              max="96"
              inputmode="numeric"
            />
          </div>
        </div>
        <p class="group-footer">进入导视与搜索页时的默认年份、季度与每页条数（12–96）。</p>
      </section>

      <!-- 安全 -->
      <section class="settings-group">
        <h2 class="group-header">安全</h2>
        <div class="group-card">
          <div class="field-row">
            <label class="field-label" for="settings-current-password">当前密码</label>
            <input
              id="settings-current-password"
              v-model="form.currentPassword"
              class="field-input"
              type="password"
              placeholder="请输入当前密码"
              autocomplete="current-password"
            />
          </div>
          <div class="field-row">
            <label class="field-label" for="settings-new-password">新密码</label>
            <input
              id="settings-new-password"
              v-model="form.newPassword"
              class="field-input"
              type="password"
              placeholder="至少 6 位"
              autocomplete="new-password"
            />
          </div>
          <div class="field-row">
            <label class="field-label" for="settings-confirm-password">确认新密码</label>
            <input
              id="settings-confirm-password"
              v-model="form.confirmPassword"
              class="field-input"
              type="password"
              placeholder="再次输入新密码"
              autocomplete="new-password"
            />
          </div>
        </div>
        <p v-if="requiresPasswordChange" class="group-footer group-footer--attention">
          当前仍在使用默认管理员账号密码，建议尽快修改。
        </p>
        <p v-else class="group-footer">留空则不修改密码；修改时需验证当前密码。</p>
      </section>

      <p v-if="errorMessage" class="settings-error" role="alert">{{ errorMessage }}</p>

      <button type="submit" class="save-button" :disabled="saving">
        {{ saving ? '保存中…' : '保存' }}
      </button>
    </form>

    <!-- 轻量 toast 提示 -->
    <Transition name="toast">
      <div v-if="toastMessage" class="settings-toast frosted" role="status">{{ toastMessage }}</div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'

import EmptyState from '../components/EmptyState.vue'
import NavBar from '../components/NavBar.vue'
import { useAuthSession } from '../auth'
import { fetchAppSettings, updateAppSettings } from '../services/settingsService'
import type { AppSettingsUpdatePayload } from '../services/settingsService'
import type { AppSettings } from '../types'

const session = useAuthSession()

const loading = ref(true)
const loadError = ref(false)
const saving = ref(false)
const errorMessage = ref('')
const settings = ref<AppSettings | null>(null)

const form = reactive({
  appName: '',
  year: '',
  season: '',
  pageSize: '',
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const toastMessage = ref('')
let toastTimer: number | undefined

/** 是否仍在使用默认账号密码（提示尽快修改） */
const requiresPasswordChange = computed(() => settings.value?.requires_password_change ?? false)

/** 当前启用数据源的访问地址（只读展示） */
const dataSourceUrl = computed(
  () =>
    (settings.value?.anime_source === 'mikan'
      ? settings.value.mikan_base_url
      : settings.value?.youranimes_base_url) || '—'
)

const dataSourceName = computed(() =>
  settings.value?.anime_source === 'mikan' ? 'mikan' : 'youranimes'
)

function applySettings(next: AppSettings) {
  settings.value = next
  form.appName = next.app_name
  form.year = String(next.default_search_year)
  form.season = next.default_search_season === null ? '' : String(next.default_search_season)
  form.pageSize = String(next.default_page_size)
}

async function load() {
  loading.value = true
  loadError.value = false
  try {
    applySettings(await fetchAppSettings())
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
}

/** 解析后端 400 响应中的 detail 文本，避免直接展示原始 JSON */
function extractErrorMessage(error: unknown): string {
  if (!(error instanceof Error) || !error.message) {
    return '保存失败，请重试'
  }
  try {
    const parsed = JSON.parse(error.message) as { detail?: unknown }
    if (typeof parsed.detail === 'string') {
      return parsed.detail
    }
  } catch {
    // 非 JSON 报文则原样展示
  }
  return error.message
}

function showToast(message: string) {
  toastMessage.value = message
  window.clearTimeout(toastTimer)
  toastTimer = window.setTimeout(() => {
    toastMessage.value = ''
  }, 2400)
}

/** 前端表单校验，返回错误文案；通过则返回空字符串 */
function validate(): string {
  if (!form.appName.trim()) {
    return '应用名不能为空'
  }

  const year = Number(form.year)
  if (!Number.isInteger(year) || year < 1968 || year > 2100) {
    return '默认年份需在 1968–2100 之间'
  }

  const pageSize = Number(form.pageSize)
  if (!Number.isInteger(pageSize) || pageSize < 12 || pageSize > 96) {
    return '每页数量需在 12–96 之间'
  }

  if (form.currentPassword || form.newPassword || form.confirmPassword) {
    if (!form.currentPassword) {
      return '修改密码前请输入当前密码'
    }
    if (form.newPassword.length < 6) {
      return '新密码至少需要 6 位'
    }
    if (form.newPassword !== form.confirmPassword) {
      return '两次输入的新密码不一致'
    }
  }

  return ''
}

async function save() {
  if (loading.value || saving.value) {
    return
  }

  errorMessage.value = ''
  const invalidMessage = validate()
  if (invalidMessage) {
    errorMessage.value = invalidMessage
    return
  }

  const payload: AppSettingsUpdatePayload = {
    app_name: form.appName.trim(),
    default_search_year: Number(form.year),
    default_search_season: form.season ? Number(form.season) : null,
    default_page_size: Number(form.pageSize)
  }

  // 仅在用户填写了密码时才提交改密字段
  if (form.currentPassword && form.newPassword) {
    payload.current_password = form.currentPassword
    payload.new_password = form.newPassword
  }

  saving.value = true
  try {
    applySettings(await updateAppSettings(payload))
    form.currentPassword = ''
    form.newPassword = ''
    form.confirmPassword = ''
    showToast('已保存')
    // 刷新会话状态，让侧边栏应用名同步更新
    session.ensureStatus(true).catch(() => undefined)
  } catch (error) {
    errorMessage.value = extractErrorMessage(error)
  } finally {
    saving.value = false
  }
}

onMounted(load)

onBeforeUnmount(() => {
  window.clearTimeout(toastTimer)
})
</script>

<style scoped>
.page {
  padding-bottom: 24px;
}

.loading-section {
  display: flex;
  justify-content: center;
  padding: 96px 0;
}

.loading-spinner {
  width: 26px;
  height: 26px;
  border: 2.5px solid var(--fill);
  border-top-color: var(--accent);
  border-radius: 999px;
  animation: settings-spinner-rotate 0.8s linear infinite;
}

@keyframes settings-spinner-rotate {
  to {
    transform: rotate(360deg);
  }
}

.state-section {
  display: flex;
  flex-direction: column;
}

.retry-button {
  align-self: center;
  margin-top: -36px;
  padding: 8px 32px;
  border-radius: 999px;
  background: var(--fill);
  color: var(--accent);
  font-size: 15px;
  font-weight: 600;
  transition: opacity 200ms ease;
}

.retry-button:active {
  opacity: 0.6;
}

/* iOS inset-grouped 分组表单 */
.settings-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 6px 16px 0;
}

.settings-group {
  display: flex;
  flex-direction: column;
}

.group-header {
  margin: 10px 14px 8px;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.3px;
}

.group-card {
  background: var(--bg-elevated);
  border-radius: 16px;
  box-shadow: var(--card-shadow);
  overflow: hidden;
}

.field-row {
  display: flex;
  align-items: center;
  gap: 16px;
  min-height: 52px;
  padding: 8px 18px;
}

.field-row + .field-row {
  border-top: 1px solid var(--separator);
}

.field-label {
  flex-shrink: 0;
  width: 96px;
  color: var(--text-primary);
  font-size: 15px;
  font-weight: 500;
}

.field-input {
  width: min(320px, 100%);
  height: 38px;
  margin-left: auto;
  padding: 0 12px;
  border: 1px solid transparent;
  border-radius: 10px;
  background: var(--fill);
  color: var(--text-primary);
  font-size: 15px;
  outline: none;
  transition: border-color 200ms ease;
}

.field-input--compact {
  width: 132px;
}

.field-input::placeholder {
  color: var(--text-tertiary);
}

.field-input:focus {
  border-color: var(--accent);
}

.field-select {
  width: 168px;
  height: 38px;
  margin-left: auto;
  padding: 0 30px 0 12px;
  border: 1px solid transparent;
  border-radius: 10px;
  background: var(--fill);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%238e8e93' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 9px center;
  background-size: 14px 14px;
  appearance: none;
  color: var(--text-primary);
  font-size: 15px;
  outline: none;
  transition: border-color 200ms ease;
}

.field-select:focus {
  border-color: var(--accent);
}

/* 只读信息行 */
.field-value {
  margin-left: auto;
  max-width: min(360px, 100%);
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.45;
  text-align: right;
  word-break: break-all;
}

.source-tag {
  display: inline-block;
  margin-left: 8px;
  padding: 1px 8px;
  border-radius: 999px;
  background: var(--fill);
  color: var(--accent);
  font-size: 11px;
  font-weight: 600;
  vertical-align: 1px;
  word-break: keep-all;
}

.group-footer {
  margin: 7px 14px 0;
  color: var(--text-tertiary);
  font-size: 12px;
  line-height: 1.5;
}

.group-footer--attention {
  color: var(--text-secondary);
}

.settings-error {
  margin: 12px 2px 0;
  color: #ff3b30;
  font-size: 13px;
  line-height: 1.4;
}

.save-button {
  height: 44px;
  margin-top: 16px;
  align-self: center;
  width: min(320px, 100%);
  border-radius: 12px;
  background: var(--accent);
  color: #ffffff;
  font-size: 16px;
  font-weight: 600;
  transition: opacity 200ms ease;
}

.save-button:disabled {
  opacity: 0.6;
  cursor: default;
}

.save-button:not(:disabled):active {
  opacity: 0.8;
}

/* 轻量 toast */
.settings-toast {
  position: fixed;
  left: 50%;
  bottom: calc(env(safe-area-inset-bottom) + 76px);
  transform: translateX(-50%);
  z-index: 200;
  max-width: 78vw;
  padding: 10px 22px;
  border-radius: 999px;
  box-shadow: var(--card-shadow);
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
}

.toast-enter-active,
.toast-leave-active {
  transition:
    opacity 240ms ease,
    transform 240ms ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translate(-50%, 8px);
}

/* 桌面端：表单列加宽间距更从容 */
@media (min-width: 1024px) {
  .settings-section {
    padding-top: 12px;
  }

  .group-header {
    margin-top: 18px;
  }

  .field-row {
    min-height: 56px;
  }
}
</style>
