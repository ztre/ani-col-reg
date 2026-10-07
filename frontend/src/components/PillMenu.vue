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
  padding: 6px 16px;
  padding-left: calc(16px + env(safe-area-inset-left));
  padding-right: calc(16px + env(safe-area-inset-right));
}

.pill-menu-item {
  flex-shrink: 0;
  height: 32px;
  padding: 0 16px;
  border-radius: 999px;
  background: var(--fill);
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  transition:
    background-color 200ms ease,
    color 200ms ease,
    box-shadow 200ms ease;
}

.pill-menu-item.is-active {
  background: var(--bg-elevated);
  color: var(--text-primary);
  box-shadow: var(--card-shadow);
}
</style>
