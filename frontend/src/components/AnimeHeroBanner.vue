<template>
  <header class="anime-hero-banner">
    <div class="anime-hero-banner__copy">
      <p class="anime-hero-banner__eyebrow">Immersive Library</p>
      <h1>番剧海报墙</h1>
      <p>{{ subcopy }}</p>
    </div>

    <div class="anime-hero-banner__art" aria-hidden="true" />

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
  grid-template-columns: minmax(0, 1.55fr) minmax(160px, 240px) minmax(260px, 360px);
  gap: 20px;
  padding: 28px;
  overflow: hidden;
  isolation: isolate;
  background: var(--hero-surface);
  border: 1px solid var(--surface-line);
  border-radius: 30px;
  box-shadow: var(--elevation-hero);
}

.anime-hero-banner::before {
  position: absolute;
  inset: auto -6% -34% auto;
  width: 340px;
  height: 340px;
  background: var(--hero-art-glow);
  content: '';
  pointer-events: none;
}

.anime-hero-banner__art {
  align-self: stretch;
  min-height: 180px;
  background-image: var(--hero-library-image);
  background-repeat: no-repeat;
  background-size: contain;
  background-position: center 62%;
  opacity: 0.98;
  filter: drop-shadow(var(--hero-art-shadow));
}

.anime-hero-banner__copy,
.anime-hero-banner__art,
.anime-hero-banner__panel {
  position: relative;
  z-index: 1;
}

.anime-hero-banner__copy {
  display: grid;
  gap: 12px;
  align-content: center;
}

.anime-hero-banner__eyebrow {
  margin: 0;
  color: var(--accent);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.22em;
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
  max-width: 9ch;
  font-size: clamp(2.2rem, 4vw, 3.6rem);
  line-height: 0.94;
  letter-spacing: -0.04em;
}

.anime-hero-banner__copy p:last-child {
  max-width: 42rem;
  color: var(--text-muted);
  font-size: 1rem;
  line-height: 1.78;
}

.anime-hero-banner__panel {
  display: grid;
  gap: 12px;
  align-content: end;
  justify-items: stretch;
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
  font-size: 1.26rem;
}

.anime-hero-banner__keyword {
  color: var(--text-soft);
  font-size: 0.92rem;
  font-weight: 600;
}

@media (max-width: 900px) {
  .anime-hero-banner {
    grid-template-columns: 1fr;
    padding: 24px;
  }

  .anime-hero-banner__art {
    display: none;
  }
}

@media (max-width: 640px) {
  .anime-hero-banner {
    padding: 20px;
    border-radius: 24px;
  }

  .anime-hero-banner__copy {
    gap: 8px;
  }

  .anime-hero-banner__copy h1 {
    max-width: none;
    font-size: clamp(1.9rem, 10vw, 2.8rem);
  }

  .anime-hero-banner__copy p:last-child {
    font-size: 0.94rem;
    line-height: 1.65;
  }

  .anime-hero-banner__panel {
    gap: 10px;
  }

  .anime-hero-banner__stat,
  .anime-hero-banner__keyword {
    padding: 14px 16px;
    border-radius: 18px;
  }

  .anime-hero-banner__stat strong {
    font-size: 1.12rem;
  }
}
</style>