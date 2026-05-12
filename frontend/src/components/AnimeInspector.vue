<template>
  <section class="inspector-shell">
    <div class="inspector-layout">
      <aside class="inspector-side">
        <div class="inspector-poster">
          <img
            v-if="showPoster"
            :key="`${anime.id}-${anime.cover_url}`"
            :src="anime.cover_url || undefined"
            :alt="`${anime.title_cn} 封面`"
            decoding="async"
            @error="imageBroken = true"
          />
          <div v-else class="inspector-poster-fallback">{{ posterFallback(anime.title_cn) }}</div>
        </div>

        <section class="inspector-panel inspector-panel--side">
          <div class="panel-copy">
            <p class="panel-eyebrow">Collection</p>
            <h3>收藏整理</h3>
            <p>直接在海报下方维护资源标签、字幕组和备注，处理时不需要再滚到弹窗底部。</p>
          </div>

          <CollectionEditor
            :anime-id="anime.id"
            :collection="anime.collection_item"
            @saved="emit('saved', $event)"
            @removed="emit('removed', $event)"
            @error="emit('error', $event)"
          />
        </section>
      </aside>

      <div class="inspector-copy">
        <div class="inspector-heading">
          <p class="inspector-eyebrow">{{ anime.year }} · {{ seasonLabel(anime.season) }} · {{ sourceLabel(anime.source) }}</p>
          <h2>{{ anime.title_cn }}</h2>
          <p class="inspector-summary">{{ anime.synopsis || anime.title_jp || anime.title_en || anime.platforms || '暂无简介' }}</p>
        </div>

        <div class="inspector-chip-row">
          <span :class="['chip', `chip--${collectionStatusTone(anime.collection_item)}`]">{{ collectionStageLabel(anime.collection_item) }}</span>
          <span class="chip">{{ anime.premiere_date || '日期待补' }}</span>
          <span v-for="tag in sourceTags" :key="tag" class="chip">{{ tag }}</span>
        </div>

        <div class="inspector-meta-grid">
          <div class="meta-card">
            <strong>来源</strong>
            <a v-if="anime.source_url" :href="anime.source_url" target="_blank" rel="noreferrer">{{ sourceLabel(anime.source) }}</a>
            <span v-else>{{ sourceLabel(anime.source) }}</span>
          </div>

          <div class="meta-card">
            <strong>平台</strong>
            <span>{{ anime.platforms || '暂无' }}</span>
          </div>

          <div class="meta-card">
            <strong>PV / 预告</strong>
            <a v-if="anime.pv_url" :href="anime.pv_url" target="_blank" rel="noreferrer">查看宣传影片</a>
            <span v-else>暂无</span>
          </div>

          <div class="meta-card meta-card--span-2">
            <strong>别名</strong>
            <span>{{ anime.aliases || anime.title_en || '暂无' }}</span>
          </div>

          <div class="meta-card meta-card--wide">
            <strong>制作</strong>
            <span>{{ anime.staff || '暂无' }}</span>
          </div>

          <div class="meta-card meta-card--wide">
            <strong>声优</strong>
            <span>{{ anime.cast || '暂无' }}</span>
          </div>

          <div class="meta-card meta-card--wide">
            <strong>作品元素</strong>
            <div class="meta-tags">
              <el-tag v-for="tag in allSourceTags" :key="`source-${tag}`" effect="plain" type="success">{{ tag }}</el-tag>
              <span v-if="!allSourceTags.length">暂无</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { collectionStageLabel, collectionStatusTone } from '../collectionPresentation'
import CollectionEditor from './CollectionEditor.vue'
import type { Anime, CollectionItem } from '../types'

const props = defineProps<{
  anime: Anime
}>()

const emit = defineEmits<{
  saved: [collection: CollectionItem]
  removed: [animeId: number]
  error: [message: string]
}>()

const imageBroken = ref(false)
const allSourceTags = computed(() => splitTags(props.anime.tags))
const sourceTags = computed(() => allSourceTags.value.slice(0, 6))
const showPoster = computed(() => Boolean(props.anime.cover_url && !imageBroken.value))

watch(
  () => `${props.anime.id}-${props.anime.cover_url || ''}`,
  () => {
    imageBroken.value = false
  },
  { immediate: true }
)

function seasonLabel(season: number) {
  const labels: Record<number, string> = { 1: '1月', 2: '4月', 3: '7月', 4: '10月' }
  return labels[season] || String(season)
}

function sourceLabel(source: string) {
  const labels: Record<string, string> = {
    youranimes: 'YourAnimes',
    mikan: 'Mikan'
  }
  return labels[source] || source
}

function splitTags(value?: string | null) {
  return (value || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function posterFallback(title: string) {
  return title.trim().slice(0, 2).toUpperCase() || 'AN'
}
</script>

<style scoped>
.inspector-shell {
  display: block;
}

.inspector-layout {
  display: grid;
  grid-template-columns: minmax(260px, 320px) minmax(0, 1fr);
  gap: 24px;
  align-items: start;
}

.inspector-side {
  display: grid;
  gap: 18px;
  align-self: start;
}

.inspector-poster {
  position: relative;
  width: 100%;
  min-height: 0;
  overflow: hidden;
  border-radius: 24px;
  aspect-ratio: 3 / 4;
  background: linear-gradient(135deg, #d7e2f1, #ecf1f8);
  box-shadow: 0 18px 36px rgba(15, 23, 42, 0.12);
}

.inspector-poster img,
.inspector-poster-fallback {
  width: 100%;
  height: 100%;
}

.inspector-poster img {
  display: block;
  object-fit: cover;
  object-position: center;
}

.inspector-poster-fallback {
  display: grid;
  place-items: center;
  color: #ffffff;
  background: linear-gradient(135deg, #5885c2, #253955);
  font-size: 38px;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.inspector-copy {
  min-width: 0;
  display: grid;
  gap: 14px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(214, 222, 234, 0.86);
  border-radius: 24px;
  box-shadow: 0 20px 40px rgba(24, 33, 47, 0.06);
}

.inspector-heading {
  min-width: 0;
  display: grid;
  gap: 10px;
}

.inspector-eyebrow,
.panel-eyebrow {
  margin: 0;
  color: #4d7db3;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.inspector-heading h2,
.panel-copy h3 {
  margin: 0;
  color: #18212f;
}

.inspector-heading h2 {
  font-size: clamp(22px, 2.7vw, 30px);
  line-height: 1.1;
  overflow-wrap: anywhere;
}

.inspector-summary,
.panel-copy p {
  margin: 0;
  color: #5e6b7d;
  line-height: 1.65;
}

.inspector-summary {
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 4;
}

.inspector-chip-row,
.meta-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.chip {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  color: #3c4f63;
  background: rgba(243, 247, 252, 0.94);
  border: 1px solid rgba(213, 222, 234, 0.9);
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
}

.chip--library {
  color: #3c4f63;
  background: rgba(243, 247, 252, 0.94);
  border-color: rgba(213, 222, 234, 0.9);
}

.chip--pending {
  color: #9a3412;
  background: rgba(255, 237, 213, 0.9);
  border-color: rgba(251, 191, 36, 0.28);
}

.chip--emby {
  color: #166534;
  background: rgba(220, 252, 231, 0.88);
  border-color: rgba(74, 222, 128, 0.3);
}

.inspector-meta-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  grid-auto-flow: dense;
}

.meta-card {
  display: grid;
  gap: 6px;
  padding: 12px 13px;
  background: linear-gradient(180deg, rgba(248, 250, 253, 0.96), rgba(244, 248, 252, 0.96));
  border: 1px solid rgba(218, 226, 237, 0.88);
  border-radius: 16px;
}

.meta-card--span-2 {
  grid-column: span 2;
}

.meta-card--wide {
  grid-column: 1 / -1;
}

.meta-card strong {
  color: #334155;
  font-size: 12px;
  line-height: 1.25;
}

.meta-card span,
.meta-card a {
  color: #5e6b7d;
  font-size: 13px;
  line-height: 1.45;
  word-break: break-word;
}

.inspector-panel {
  display: grid;
  gap: 18px;
  padding: 24px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(214, 222, 234, 0.86);
  border-radius: 24px;
  box-shadow: 0 20px 40px rgba(24, 33, 47, 0.06);
}

.inspector-panel--side {
  align-self: start;
}

.panel-copy {
  display: grid;
  gap: 8px;
}

@media (max-width: 1180px) {
  .inspector-meta-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .meta-card--span-2,
  .meta-card--wide {
    grid-column: 1 / -1;
  }
}

@media (max-width: 960px) {
  .inspector-layout {
    grid-template-columns: 1fr;
  }

  .inspector-poster {
    max-width: 360px;
  }

  .inspector-meta-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .inspector-meta-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .inspector-copy,
  .inspector-panel {
    padding: 18px;
    border-radius: 20px;
  }
}
</style>
