<template>
  <article class="series-row" @click="open">
    <div class="series-row-cover">
      <img
        v-if="group.cover_url && !coverFailed"
        class="series-row-image"
        :src="group.cover_url"
        :alt="group.series_title"
        loading="lazy"
        @error="coverFailed = true"
      />
      <div v-else class="series-row-fallback">
        <span>{{ fallbackInitial }}</span>
      </div>
    </div>
    <div class="series-row-body">
      <h3 class="series-row-title">{{ group.series_title }}</h3>
      <p class="series-row-sub">{{ subtitle }}</p>
    </div>
    <svg
      class="series-row-chevron"
      viewBox="8 4 9 16"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
      aria-hidden="true"
    >
      <path d="M9 5l7 7-7 7" />
    </svg>
  </article>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import type { SeriesGroup } from '../types'

const props = defineProps<{
  group: SeriesGroup
}>()

const SEASON_NAMES: Record<number, string> = { 1: '冬', 2: '春', 3: '夏', 4: '秋' }

const router = useRouter()
const coverFailed = ref(false)

watch(
  () => props.group.cover_url,
  () => {
    coverFailed.value = false
  }
)

const fallbackInitial = computed(() => props.group.series_title.trim().charAt(0) || '?')

const subtitle = computed(() => {
  const season = SEASON_NAMES[props.group.latest_season] ?? ''
  return `共 ${props.group.entry_count} 部 · 最新 ${props.group.latest_year} ${season}`.trim()
})

function open() {
  router.push(`/collection/${props.group.series_key}`)
}
</script>

<style scoped>
.series-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  cursor: pointer;
  transition: background-color 120ms ease;
}

.series-row:active {
  background: var(--fill);
}

.series-row-cover {
  flex-shrink: 0;
  width: 56px;
  height: 74px;
  border-radius: 8px;
  overflow: hidden;
  background: var(--fill);
}

.series-row-image {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.series-row-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: linear-gradient(145deg, var(--fill), var(--bg-elevated));
  color: var(--text-tertiary);
  font-size: 20px;
  font-weight: 600;
}

.series-row-body {
  flex: 1;
  min-width: 0;
}

.series-row-title {
  margin: 0;
  overflow: hidden;
  color: var(--text-primary);
  font-size: 16px;
  font-weight: 600;
  line-height: 1.3;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.series-row-sub {
  margin: 3px 0 0;
  overflow: hidden;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.4;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.series-row-chevron {
  flex-shrink: 0;
  width: 9px;
  height: 16px;
  color: var(--text-tertiary);
}
</style>
