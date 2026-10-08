<template>
  <article class="poster-card" @click="emit('open', anime)">
    <div class="poster-card-cover">
      <img
        v-if="anime.cover_url && !coverFailed"
        class="poster-card-image"
        :src="anime.cover_url"
        :alt="anime.title_cn"
        loading="lazy"
        @error="coverFailed = true"
      />
      <div v-else class="poster-card-fallback">
        <span>{{ fallbackInitial }}</span>
      </div>
      <button
        type="button"
        class="poster-card-collect"
        :class="{ 'is-collected': anime.is_collected }"
        :aria-label="anime.is_collected ? '取消收藏' : '收藏'"
        @click.stop="emit('collect', anime)"
      >
        <svg
          viewBox="0 0 24 24"
          :fill="anime.is_collected ? 'currentColor' : 'none'"
          stroke="currentColor"
          stroke-width="1.8"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
        </svg>
      </button>
    </div>
    <h3 class="poster-card-title">{{ anime.title_cn }}</h3>
  </article>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import type { Anime } from '../types'

const props = defineProps<{
  anime: Anime
}>()

const emit = defineEmits<{
  collect: [anime: Anime]
  open: [anime: Anime]
}>()

const coverFailed = ref(false)

watch(
  () => props.anime.cover_url,
  () => {
    coverFailed.value = false
  }
)

const fallbackInitial = computed(() => props.anime.title_cn.trim().charAt(0) || '?')
</script>

<style scoped>
.poster-card {
  min-width: 0;
}

.poster-card-cover {
  position: relative;
  aspect-ratio: 2 / 3;
  border-radius: 12px;
  overflow: hidden;
  background: var(--fill);
}

.poster-card-image {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.poster-card-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: linear-gradient(145deg, var(--fill), var(--bg-elevated));
  color: var(--text-tertiary);
}

.poster-card-fallback span {
  font-size: 34px;
  font-weight: 600;
}

/* 触控区 44×44（iOS 最小标准），视觉圆 28px 由 ::before 绘制（内缩 8px），
   避免点偏落到卡片上误触进入详情页 */
.poster-card-collect {
  position: absolute;
  top: 0;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 999px;
  color: rgba(255, 255, 255, 0.92);
  transition: color 200ms ease, transform 200ms ease;
}

.poster-card-collect::before {
  content: '';
  position: absolute;
  inset: 8px;
  border-radius: 999px;
  background: var(--blur-bg);
  -webkit-backdrop-filter: blur(12px) saturate(180%);
  backdrop-filter: blur(12px) saturate(180%);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
}

.poster-card-collect svg {
  position: relative;
  width: 15px;
  height: 15px;
  filter: drop-shadow(0 1px 1px rgba(0, 0, 0, 0.25));
}

.poster-card-collect.is-collected {
  color: var(--accent);
}

.poster-card-collect:active {
  transform: scale(0.88);
}

.poster-card-title {
  margin: 6px 2px 0;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  overflow: hidden;
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 500;
  line-height: 1.35;
}
</style>
