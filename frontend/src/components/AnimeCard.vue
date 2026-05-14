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
  color: #f7f9ff;
  text-align: left;
  cursor: pointer;
  background: linear-gradient(180deg, rgba(8, 17, 32, 0.78), rgba(8, 17, 32, 0.98));
  border: 1px solid rgba(146, 173, 214, 0.18);
  border-radius: 24px;
  box-shadow: 0 22px 44px rgba(4, 10, 20, 0.42);
  isolation: isolate;
}

.anime-poster-card::before {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(7, 14, 28, 0.02) 0%, rgba(7, 14, 28, 0.12) 36%, rgba(7, 14, 28, 0.84) 100%);
  content: '';
  pointer-events: none;
  z-index: 1;
}

.anime-poster-card::after {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(133, 196, 255, 0.1), transparent 32%, rgba(5, 10, 18, 0.22));
  opacity: 0;
  content: '';
  transition: opacity 220ms ease;
  pointer-events: none;
  z-index: 2;
}

.anime-poster-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 28px 52px rgba(4, 10, 20, 0.5);
  border-color: rgba(148, 191, 241, 0.32);
}

.anime-poster-card:hover::after,
.anime-poster-card:focus-visible::after {
  opacity: 1;
}

.anime-poster-card:focus-visible {
  outline: 2px solid rgba(123, 188, 255, 0.92);
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
  color: rgba(248, 251, 255, 0.96);
  background:
    radial-gradient(circle at top, rgba(126, 206, 255, 0.36), transparent 42%),
    linear-gradient(135deg, #19314f, #10233d 54%, #0d1625 100%);
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
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 999px;
  backdrop-filter: blur(14px);
}

.anime-poster-card__badge {
  left: 14px;
}

.anime-poster-card__badge--ongoing {
  color: #dfffe7;
  background: rgba(88, 188, 121, 0.3);
}

.anime-poster-card__badge--finished {
  color: #d7e4ff;
  background: rgba(73, 109, 183, 0.32);
}

.anime-poster-card__badge--new {
  color: #fff4cf;
  background: rgba(212, 154, 59, 0.32);
}

.anime-poster-card__score {
  right: 14px;
  color: #fff4d1;
  background: rgba(13, 18, 30, 0.58);
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
  color: #f5f7ff;
  font-size: 1.12rem;
  line-height: 1.25;
  text-shadow: 0 6px 16px rgba(4, 10, 20, 0.42);
}

.anime-poster-card__heading p {
  color: rgba(219, 228, 242, 0.86);
  font-size: 0.82rem;
  line-height: 1.45;
}

.anime-poster-card__summary {
  display: -webkit-box;
  overflow: hidden;
  max-width: 92%;
  color: rgba(230, 237, 248, 0.84);
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
  color: rgba(194, 207, 227, 0.86);
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
  color: rgba(231, 238, 249, 0.88);
  background: rgba(17, 27, 43, 0.42);
  border: 1px solid rgba(198, 215, 241, 0.14);
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
  color: rgba(208, 219, 237, 0.82);
  font-size: 0.76rem;
  font-weight: 700;
}

.anime-poster-card__collection--active {
  color: #eff6ff;
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