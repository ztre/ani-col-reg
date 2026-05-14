<template>
  <section class="anime-toolbar">
    <div class="anime-toolbar__surface">
      <div class="anime-toolbar__filters">
        <slot />
      </div>

      <div class="anime-toolbar__meta">
        <div class="anime-toolbar__summary">
          <span class="anime-toolbar__summary-label">{{ loadingLabel }}</span>
          <strong>第 {{ page }} / {{ pageCount }} 页 · 每页 {{ pageSize }} 条</strong>
        </div>

        <div v-if="activeFilters.length" class="anime-toolbar__chips">
          <span v-for="chip in activeFilters" :key="chip" class="anime-toolbar__chip">{{ chip }}</span>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  total: number
  page: number
  pageCount: number
  pageSize: number
  activeFilters: string[]
  searching?: boolean
}>()

const loadingLabel = computed(() => (props.searching ? '源站同步中…' : `本地条目 ${props.total} 部`))
</script>

<style scoped>
.anime-toolbar {
  position: sticky;
  top: 14px;
  z-index: 8;
}

.anime-toolbar__surface {
  display: grid;
  gap: 14px;
  padding: 18px;
  background: var(--toolbar-surface);
  border: 1px solid var(--surface-line);
  border-radius: 26px;
  box-shadow: var(--elevation-card-soft);
  backdrop-filter: blur(20px);
}

.anime-toolbar__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
}

.anime-toolbar__summary {
  display: grid;
  gap: 4px;
}

.anime-toolbar__summary-label,
.anime-toolbar__chip {
  color: var(--text-muted);
  font-size: 0.78rem;
}

.anime-toolbar__summary strong {
  color: var(--text-strong);
  font-size: 0.96rem;
}

.anime-toolbar__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}

.anime-toolbar__chip {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  color: var(--text-soft);
  background: var(--surface-chip);
  border: 1px solid var(--surface-line);
  border-radius: 999px;
  backdrop-filter: blur(14px);
}

@media (max-width: 768px) {
  .anime-toolbar {
    position: static;
  }

  .anime-toolbar__surface {
    padding: 14px;
    border-radius: 22px;
  }

  .anime-toolbar__meta {
    align-items: flex-start;
    flex-direction: column;
  }

  .anime-toolbar__chips {
    justify-content: flex-start;
  }
}
</style>