<template>
  <button type="button" class="anime-poster-card" :aria-label="`查看 ${anime.title_cn}`" @click="emit('select', anime)">
    <div class="anime-poster-card__media">
      <img v-if="anime.cover_url" :src="anime.cover_url" :alt="`${anime.title_cn} 封面`" loading="lazy" />
      <div v-else class="anime-poster-card__fallback">{{ posterFallback(anime.title_cn) }}</div>
    </div>

    <span :class="['anime-poster-card__badge', `anime-poster-card__badge--${status.tone}`]">{{ status.label }}</span>
    <span v-if="scoreLabel" class="anime-poster-card__score">{{ scoreLabel }}</span>

    <div class="anime-poster-card__overlay">
      <div class="anime-poster-card__content">
        <div class="anime-poster-card__heading">
          <h2>{{ anime.title_cn }}</h2>
          <p>{{ secondaryTitle }}</p>
        </div>

        <p class="anime-poster-card__summary">{{ summary }}</p>

        <div class="anime-poster-card__meta">{{ seasonCaption }}</div>

        <div v-if="tagPills.length" class="anime-poster-card__tags">
          <span v-for="tag in tagPills" :key="tag" class="anime-poster-card__tag">{{ tag }}</span>
        </div>

        <div class="anime-poster-card__footer">
          <span :class="['anime-poster-card__collection', { 'anime-poster-card__collection--active': Boolean(anime.collection_item) }]">
            {{ collectionLabel }}
          </span>
        </div>
      </div>
    </div>
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import {
  animeCardSummary,
  animeCollectionLabel,
  animePillTags,
  animePosterStatus,
  animeScoreLabel,
  animeSeasonCaption,
  animeSecondaryTitle,
  posterFallback,
} from '../animePresentation'
import type { Anime } from '../types'

const props = defineProps<{
  anime: Anime
}>()

const emit = defineEmits<{
  select: [anime: Anime]
}>()

const status = computed(() => animePosterStatus(props.anime))
const scoreLabel = computed(() => animeScoreLabel(props.anime))
const secondaryTitle = computed(() => animeSecondaryTitle(props.anime))
const seasonCaption = computed(() => animeSeasonCaption(props.anime))
const summary = computed(() => animeCardSummary(props.anime))
const tagPills = computed(() => animePillTags(props.anime))
const collectionLabel = computed(() => animeCollectionLabel(props.anime.collection_item))
</script>

<style scoped>
.anime-poster-card {
  position: relative;
  display: block;
  width: 100%;
  aspect-ratio: 2 / 3;
  padding: 0;
  overflow: hidden;
  color: var(--poster-overlay-text);
  text-align: left;
  cursor: pointer;
  background: var(--poster-card-bg);
  border: 1px solid var(--poster-card-border);
  border-radius: 24px;
  box-shadow: var(--elevation-card-soft);
  isolation: isolate;
}

.anime-poster-card::before {
  position: absolute;
  inset: 0;
  background: var(--poster-overlay);
  content: '';
  pointer-events: none;
  z-index: 1;
}

.anime-poster-card::after {
  position: absolute;
  inset: 0;
  background: var(--poster-sheen);
  opacity: 0;
  content: '';
  transition: opacity 220ms ease;
  pointer-events: none;
  z-index: 2;
}

.anime-poster-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--elevation-hover);
  border-color: var(--poster-hover-border);
}

.anime-poster-card:hover::after,
.anime-poster-card:focus-visible::after {
  opacity: 1;
}

.anime-poster-card:focus-visible {
  outline: 2px solid var(--poster-focus-outline);
  outline-offset: 4px;
}

.anime-poster-card__media,
.anime-poster-card__media img,
.anime-poster-card__fallback {
  width: 100%;
  height: 100%;
}

.anime-poster-card__media img {
  display: block;
  object-fit: cover;
  object-position: center;
  transform: scale(1.01);
  transition: transform 260ms ease;
}

.anime-poster-card:hover .anime-poster-card__media img,
.anime-poster-card:focus-visible .anime-poster-card__media img {
  transform: scale(1.04);
}

.anime-poster-card__fallback {
  display: grid;
  place-items: center;
  color: var(--poster-overlay-text);
  background:
    radial-gradient(circle at top, color-mix(in srgb, var(--accent) 42%, transparent), transparent 42%),
    var(--poster-fallback-gradient);
  font-size: clamp(28px, 6vw, 44px);
  font-weight: 800;
  letter-spacing: 0.08em;
}

.anime-poster-card__badge,
.anime-poster-card__score {
  position: absolute;
  top: 14px;
  z-index: 3;
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 10px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
  border: 1px solid var(--badge-border);
  border-radius: 999px;
  backdrop-filter: blur(14px);
}

.anime-poster-card__badge {
  left: 14px;
}

.anime-poster-card__badge--ongoing {
  color: var(--badge-ongoing-text);
  background: var(--badge-ongoing-bg);
}

.anime-poster-card__badge--finished {
  color: var(--badge-finished-text);
  background: var(--badge-finished-bg);
}

.anime-poster-card__badge--new {
  color: var(--badge-new-text);
  background: var(--badge-new-bg);
}

.anime-poster-card__score {
  right: 14px;
  color: var(--poster-score-text);
  background: var(--poster-score-bg);
}

.anime-poster-card__overlay {
  position: absolute;
  inset: 0;
  z-index: 3;
  display: flex;
  align-items: flex-end;
}

.anime-poster-card__content {
  width: 100%;
  display: grid;
  gap: 10px;
  padding: 18px;
}

.anime-poster-card__heading {
  display: grid;
  gap: 6px;
}

.anime-poster-card__heading h2,
.anime-poster-card__heading p,
.anime-poster-card__summary,
.anime-poster-card__meta,
.anime-poster-card__footer {
  margin: 0;
}

.anime-poster-card__heading h2 {
  color: var(--poster-overlay-text);
  font-size: 1.12rem;
  line-height: 1.25;
  text-shadow: var(--poster-title-shadow);
}

.anime-poster-card__heading p {
  color: color-mix(in srgb, var(--poster-overlay-text) 86%, transparent);
  font-size: 0.82rem;
  line-height: 1.45;
}

.anime-poster-card__summary {
  display: -webkit-box;
  overflow: hidden;
  max-width: 92%;
  color: color-mix(in srgb, var(--poster-overlay-text) 84%, transparent);
  font-size: 0.78rem;
  line-height: 1.55;
  opacity: 0;
  transform: translateY(6px);
  transition: opacity 220ms ease, transform 220ms ease;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.anime-poster-card:hover .anime-poster-card__summary,
.anime-poster-card:focus-visible .anime-poster-card__summary {
  opacity: 1;
  transform: translateY(0);
}

.anime-poster-card__meta {
  color: color-mix(in srgb, var(--poster-overlay-text) 78%, transparent);
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.03em;
}

.anime-poster-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.anime-poster-card__tag {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  padding: 0 10px;
  color: var(--poster-tag-text);
  background: var(--poster-tag-bg);
  border: 1px solid var(--poster-tag-border);
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
  backdrop-filter: blur(14px);
}

.anime-poster-card__footer {
  display: flex;
  justify-content: flex-end;
}

.anime-poster-card__collection {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  color: color-mix(in srgb, var(--poster-overlay-text) 82%, transparent);
  font-size: 0.76rem;
  font-weight: 700;
}

.anime-poster-card__collection--active {
  color: var(--poster-overlay-text);
}

@media (max-width: 640px) {
  .anime-poster-card {
    border-radius: 20px;
  }

  .anime-poster-card__content {
    gap: 8px;
    padding: 14px;
  }

  .anime-poster-card__heading h2 {
    font-size: 1rem;
  }
}
</style>