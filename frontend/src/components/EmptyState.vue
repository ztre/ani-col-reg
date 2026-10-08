<template>
  <div class="empty-state">
    <div class="empty-state-icon">
      <slot name="icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <template v-if="icon === 'tv'">
            <rect x="2.5" y="4" width="19" height="13" rx="2.75" />
            <path d="M8 20.5h8" />
          </template>
          <template v-else-if="icon === 'heart'">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
          </template>
          <template v-else-if="icon === 'search'">
            <circle cx="11" cy="11" r="7.5" />
            <path d="m20.5 20.5-4.6-4.6" />
          </template>
          <template v-else-if="icon === 'calendar'">
            <rect x="3.5" y="5" width="17" height="15.5" rx="2.5" />
            <path d="M8 2.75v4M16 2.75v4M3.5 10.5h17" />
          </template>
          <template v-else>
            <path d="M12 4.25 20.5 19h-17L12 4.25z" />
            <path d="M12 10.5v4" />
            <path d="M12 17.1h.01" />
          </template>
        </svg>
      </slot>
    </div>
    <p class="empty-state-title">{{ title }}</p>
    <p v-if="hint" class="empty-state-hint">{{ hint }}</p>
    <button
      v-if="action"
      type="button"
      class="empty-state-action"
      :disabled="actionLoading"
      @click="emit('action')"
    >
      <span v-if="actionLoading" class="empty-state-action-spinner" aria-hidden="true" />
      {{ actionLoading ? actionLoadingLabel : action }}
    </button>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    icon?: string
    title: string
    hint?: string
    /** 可选操作按钮文案（如“同步该季度数据”），传入才渲染按钮 */
    action?: string
    actionLoading?: boolean
    actionLoadingLabel?: string
  }>(),
  { icon: 'inbox', hint: '', action: '', actionLoading: false, actionLoadingLabel: '同步中…' }
)

const emit = defineEmits<{ action: [] }>()
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 56px 32px;
  text-align: center;
}

.empty-state-icon {
  display: flex;
  color: var(--text-tertiary);
  margin-bottom: 14px;
}

.empty-state-icon svg {
  width: 44px;
  height: 44px;
}

.empty-state-title {
  margin: 0;
  color: var(--text-secondary);
  font-size: 17px;
  font-weight: 600;
}

.empty-state-hint {
  margin: 6px 0 0;
  color: var(--text-tertiary);
  font-size: 13px;
  line-height: 1.5;
}

.empty-state-action {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  margin-top: 18px;
  padding: 0 22px;
  height: 44px;
  border: none;
  border-radius: 999px;
  background: var(--fill);
  -webkit-backdrop-filter: blur(15px);
  backdrop-filter: blur(15px);
  color: var(--accent, #007aff);
  font-family: inherit;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.15s ease, opacity 0.15s ease;
}

.empty-state-action:active {
  transform: scale(0.96);
}

.empty-state-action:disabled {
  opacity: 0.55;
  cursor: default;
}

.empty-state-action-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: empty-state-spin 0.7s linear infinite;
}

@keyframes empty-state-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
