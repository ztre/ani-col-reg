<template>
  <div class="pill-menu no-scrollbar" role="tablist">
    <button
      v-for="option in options"
      :key="option.value"
      type="button"
      class="pill-menu-item"
      :class="{ 'is-active': option.value === modelValue }"
      role="tab"
      :aria-selected="option.value === modelValue"
      @click="emit('update:modelValue', option.value)"
    >
      {{ option.label }}
    </button>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  options: { value: string; label: string }[]
  modelValue: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()
</script>

<style scoped>
.pill-menu {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 2px 16px;
  padding-left: calc(16px + env(safe-area-inset-left));
  padding-right: calc(16px + env(safe-area-inset-right));
}

/* 触控区 44px（iOS HIG 最小标准），视觉胶囊 32px 由 ::before 绘制（上下内缩 6px） */
.pill-menu-item {
  position: relative;
  /* 创建层叠上下文，让 ::before 沉到文字下方（否则白色胶囊会盖住文字） */
  isolation: isolate;
  flex-shrink: 0;
  height: 44px;
  padding: 0 16px;
  border-radius: 999px;
  background: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
}

.pill-menu-item::before {
  content: '';
  position: absolute;
  z-index: -1;
  inset: 6px 0;
  border-radius: 999px;
  background: var(--fill);
  transition:
    background-color 200ms ease,
    box-shadow 200ms ease;
}

.pill-menu-item.is-active {
  color: var(--text-primary);
}

.pill-menu-item.is-active::before {
  background: var(--bg-elevated);
  box-shadow: var(--card-shadow);
}
</style>
