<template>
  <header class="anime-hero-banner">
    <div class="anime-hero-banner__copy">
      <p class="anime-hero-banner__eyebrow">Immersive Library</p>
      <h1>番剧海报墙</h1>
      <p>{{ subcopy }}</p>
    </div>

    <div class="anime-hero-banner__panel">
      <div class="anime-hero-banner__stat">
        <span>当前浏览</span>
        <strong>{{ activeSeasonLabel }}</strong>
      </div>

      <div class="anime-hero-banner__stat">
        <span>本地条目</span>
        <strong>{{ total }}</strong>
      </div>

      <div v-if="keyword" class="anime-hero-banner__keyword">关键词：{{ keyword }}</div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import { seasonLabel } from '../animePresentation'

const props = defineProps<{
  subcopy: string
  total: number
  year?: number
  season?: number
  keyword?: string
}>()

const activeSeasonLabel = computed(() => {
  const yearLabel = props.year ? String(props.year) : '全部年份'
  const seasonText = props.season ? seasonLabel(props.season) : '全部季度'
  return `${yearLabel} · ${seasonText}`
})
</script>

<style scoped>
.anime-hero-banner {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(260px, 360px);
  gap: 20px;
  padding: 28px;
  overflow: hidden;
  background: var(--hero-surface);
  border: 1px solid var(--surface-line);
  border-radius: 30px;
  box-shadow: 0 26px 54px rgba(2, 7, 15, 0.42);
}

.anime-hero-banner::after {
  position: absolute;
  inset: auto -6% -34% auto;
  width: 340px;
  height: 340px;
  background: radial-gradient(circle, rgba(97, 180, 255, 0.24), transparent 70%);
  content: '';
  pointer-events: none;
}

.anime-hero-banner__copy,
.anime-hero-banner__panel {
  position: relative;
  z-index: 1;
}

.anime-hero-banner__copy {
  display: grid;
  gap: 10px;
  align-content: center;
}

.anime-hero-banner__eyebrow {
  margin: 0;
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.anime-hero-banner__copy h1,
.anime-hero-banner__copy p,
.anime-hero-banner__stat span,
.anime-hero-banner__stat strong,
.anime-hero-banner__keyword {
  margin: 0;
}

.anime-hero-banner__copy h1 {
  color: var(--text-strong);
  font-size: clamp(2rem, 4vw, 3.3rem);
  line-height: 0.98;
}

.anime-hero-banner__copy p:last-child {
  max-width: 720px;
  color: var(--text-muted);
  line-height: 1.7;
}

.anime-hero-banner__panel {
  display: grid;
  gap: 12px;
  align-content: end;
}

.anime-hero-banner__stat,
.anime-hero-banner__keyword {
  padding: 16px 18px;
  background: var(--surface-panel);
  border: 1px solid var(--surface-line);
  border-radius: 22px;
  backdrop-filter: blur(16px);
}

.anime-hero-banner__stat span {
  display: block;
  color: var(--text-muted);
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.anime-hero-banner__stat strong {
  display: block;
  margin-top: 8px;
  color: var(--text-strong);
  font-size: 1.2rem;
}

.anime-hero-banner__keyword {
  color: var(--text-soft);
  font-size: 0.9rem;
  font-weight: 600;
}

@media (max-width: 900px) {
  .anime-hero-banner {
    grid-template-columns: 1fr;
    padding: 24px;
  }
}

@media (max-width: 640px) {
  .anime-hero-banner {
    padding: 20px;
    border-radius: 24px;
  }
}
</style>