<template>
  <section class="library-page">
    <header class="library-hero">
      <div class="library-hero-copy">
        <p class="library-eyebrow">Library Search</p>
        <h1>番剧库</h1>
        <p>{{ librarySubcopy }}</p>
      </div>
      <div class="library-hero-note">
        <span class="hero-note-label">当前浏览</span>
        <strong>{{ filters.year ?? '全部年份' }} · {{ filters.season ? seasonLabel(filters.season) : '全部季度' }}</strong>
        <span>{{ total }} 部条目</span>
      </div>
    </header>

    <section class="search-panel">
      <AnimeFilterBar
        v-model:year="yearFilterModel"
        v-model:season="seasonFilterModel"
        v-model:keyword="filters.keyword"
        apply-label="搜索并更新"
        :auto-apply-year-season="false"
        @apply="refreshFromSource"
        @clear="clearFilters"
      />

    </section>

    <section class="library-summary">
      <div class="summary-copy">
        <span class="summary-title">本地条目 {{ total }} 部</span>
        <span class="summary-subtitle">第 {{ filters.page }} / {{ pageCount }} 页 · 每页 {{ filters.page_size }} 条</span>
      </div>

      <div v-if="activeFilterChips.length" class="summary-chips">
        <span v-for="chip in activeFilterChips" :key="chip" class="summary-chip">{{ chip }}</span>
      </div>
    </section>

    <div v-loading="loading" class="library-grid">
      <article
        v-for="item in items"
        :key="item.id"
        class="library-card"
        role="button"
        tabindex="0"
        @click="openDetail(item)"
        @keyup.enter="openDetail(item)"
      >
        <div class="card-cover">
          <img v-if="item.cover_url" :src="item.cover_url" :alt="`${item.title_cn} 封面`" loading="lazy" />
          <div v-else class="card-cover-fallback">{{ posterFallback(item.title_cn) }}</div>
        </div>

        <span class="card-season-badge">{{ item.year }} · {{ seasonLabel(item.season) }}</span>
        <span class="card-source-badge">{{ sourceLabel(item.source) }}</span>

        <div class="card-overlay">
          <div class="card-topline">
            <div class="card-chip-row">
              <span :class="['overlay-chip', `overlay-chip--${collectionStatusTone(item.collection_item)}`]">{{ collectionStageLabel(item.collection_item) }}</span>
              <span class="overlay-chip">{{ typeLabel(item) }}</span>
            </div>

            <span class="overlay-meta">
              <el-icon><Calendar /></el-icon>
              {{ premiereLabel(item) }}
            </span>
          </div>

          <h2 class="card-title">{{ item.title_cn }}</h2>
          <p class="card-description">{{ summaryText(item) }}</p>

          <div class="card-resource-line">
            <span>{{ groupLabel(item) }}</span>
            <span :class="{ 'card-resource-line__web': isWebReleaseTag(releaseTagValue(item)) }">{{ releaseLabel(item) }}</span>
          </div>

          <div class="card-actions">
            <button type="button" class="card-action card-action--quiet" @click.stop="openDetail(item)">
              <el-icon><StarFilled /></el-icon>
              <span>{{ collectionActionLabel(item.collection_item) }}</span>
            </button>

            <button type="button" class="card-action card-action--link" @click.stop="openDetail(item)">
              <span>详情</span>
              <el-icon><ArrowRight /></el-icon>
            </button>
          </div>
        </div>
      </article>
    </div>

    <el-empty v-if="!loading && items.length === 0" description="暂无番剧，选择年份季度后搜索更新" class="library-empty" />

    <el-pagination
      v-model:current-page="filters.page"
      v-model:page-size="filters.page_size"
      background
      layout="prev, pager, next, sizes, total"
      :page-sizes="pageSizeOptions"
      :total="total"
      class="library-pager"
      @change="loadLocal"
    />

    <AnimeDialog
      v-model="detailDialogVisible"
      :anime-id="selectedAnimeId"
      :initial-anime="selectedAnimePreview"
      :detail-loaded="hydratedAnimeIds.has(selectedAnimeId || -1)"
      @saved="onDetailSaved"
      @removed="onDetailRemoved"
      @loaded="onDetailLoaded"
      @error="ElMessage.error"
    />
  </section>
</template>

<script setup lang="ts">
import { ArrowRight, Calendar, StarFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'

import { useAuthSession } from '../auth'
import { listAnime, searchAnime } from '../api'
import { collectionActionLabel, collectionStageLabel, collectionStatusTone, isWebReleaseTag } from '../collectionPresentation'
import AnimeDialog from '../components/AnimeDialog.vue'
import AnimeFilterBar from '../components/AnimeFilterBar.vue'
import type { Anime, CollectionItem } from '../types'

const currentYear = new Date().getFullYear()
const currentSeason = resolveCurrentSeason()
const session = useAuthSession()

function createDefaultFilters() {
  return {
    keyword: '',
    year: currentYear as number | undefined,
    season: currentSeason as number | undefined,
    page: 1,
    page_size: 24
  }
}

const filters = reactive(createDefaultFilters())
const items = ref<Anime[]>([])
const total = ref(0)
const loading = ref(false)
const searching = ref(false)
const detailDialogVisible = ref(false)
const selectedAnimeId = ref<number | null>(null)
const selectedAnimePreview = ref<Anime | null>(null)
const hydratedAnimeIds = reactive(new Set<number>())

const pageSizeOptions = [12, 24, 36, 48]
const librarySubcopy = computed(
  () => session.state.status?.library_subcopy || '按年份和季度从源站刷新番剧，并把封面缓存到本地，减少重复请求，让浏览体验更稳定。'
)

const yearFilterModel = computed({
  get: () => (filters.year ? String(filters.year) : undefined),
  set: (value: string | undefined) => {
    filters.year = value ? Number(value) : undefined
    applyLocalFilters()
  }
})
const seasonFilterModel = computed({
  get: () => filters.season,
  set: (value: number | undefined) => {
    filters.season = value
    applyLocalFilters()
  }
})
const pageCount = computed(() => Math.max(1, Math.ceil(total.value / filters.page_size)))
const activeFilterChips = computed(() => {
  const chips = [
    filters.year ? `年份 ${filters.year}` : '',
    filters.season ? `季度 ${seasonLabel(filters.season)}` : '',
    filters.keyword ? `关键词 ${filters.keyword}` : ''
  ]
  return chips.filter(Boolean)
})

function seasonLabel(season: number) {
  const labels: Record<number, string> = { 1: '1月', 2: '4月', 3: '7月', 4: '10月' }
  return labels[season] || String(season)
}

function resolveCurrentSeason() {
  const month = new Date().getMonth() + 1
  if (month <= 3) return 1
  if (month <= 6) return 2
  if (month <= 9) return 3
  return 4
}

function splitTags(value?: string | null) {
  return (value || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function firstTag(value?: string | null) {
  return splitTags(value)[0] || ''
}

function posterFallback(title: string) {
  return title.trim().slice(0, 2).toUpperCase() || 'AN'
}

function sourceLabel(source: string) {
  const labels: Record<string, string> = {
    youranimes: 'YourAnimes',
    mikan: 'Mikan'
  }
  return labels[source] || source
}

function typeLabel(item: Anime) {
  const platform = item.platforms?.split(/[、,/|]/)[0]?.trim()
  return platform || '季番'
}

function premiereLabel(item: Anime) {
  if (!item.premiere_date) return '日期待补'
  return item.premiere_date.slice(5).replace('-', '.')
}

function summaryText(item: Anime) {
  return item.synopsis || item.title_jp || item.title_en || item.platforms || '暂无简介'
}

function groupLabel(item: Anime) {
  const tag = firstTag(item.collection_item?.group_tags)
  return tag ? `字幕组 · ${tag}` : '字幕组待补充'
}

function releaseTagValue(item: Anime) {
  return firstTag(item.collection_item?.release_tags)
}

function releaseLabel(item: Anime) {
  const tag = releaseTagValue(item)
  return tag ? `资源 · ${tag}` : '资源标签待补充'
}

function openDetail(item: Anime) {
  selectedAnimeId.value = item.id
  selectedAnimePreview.value = { ...item, collection_item: item.collection_item ? { ...item.collection_item } : null }
  detailDialogVisible.value = true
}

function onDetailSaved(payload: { animeId: number; collection: CollectionItem }) {
  const target = items.value.find((item) => item.id === payload.animeId)
  if (target) {
    target.collection_item = payload.collection
  }
  if (selectedAnimePreview.value?.id === payload.animeId) {
    selectedAnimePreview.value = {
      ...selectedAnimePreview.value,
      collection_item: payload.collection,
    }
  }
}

function onDetailLoaded(anime: Anime) {
  hydratedAnimeIds.add(anime.id)
  const target = items.value.find((item) => item.id === anime.id)
  if (target) {
    Object.assign(target, anime)
  }
  if (selectedAnimePreview.value?.id === anime.id) {
    selectedAnimePreview.value = {
      ...anime,
      collection_item: anime.collection_item ? { ...anime.collection_item } : null,
    }
  }
}

function onDetailRemoved(payload: { animeId: number }) {
  const target = items.value.find((item) => item.id === payload.animeId)
  if (target) {
    target.collection_item = null
  }
  if (selectedAnimePreview.value?.id === payload.animeId) {
    selectedAnimePreview.value = {
      ...selectedAnimePreview.value,
      collection_item: null,
    }
  }

  ElMessage.success('已取消收藏')
}

function resetToFirstPage() {
  filters.page = 1
}

function applyLocalFilters() {
  resetToFirstPage()
  void loadLocal()
}

function clearFilters() {
  Object.assign(filters, createDefaultFilters())
  void loadLocal()
}

async function loadLocal() {
  loading.value = true
  try {
    const data = await listAnime({
      keyword: filters.keyword,
      year: filters.year,
      season: filters.season,
      page: filters.page,
      page_size: filters.page_size
    })
    items.value = data.items
    total.value = data.total
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载失败')
  } finally {
    loading.value = false
  }
}

async function refreshFromSource() {
  const searchYear = filters.year
  if (!searchYear) {
    ElMessage.warning('请先选择年份再搜索并更新')
    return
  }

  resetToFirstPage()
  searching.value = true
  loading.value = true
  try {
    const data = await searchAnime({
      keyword: filters.keyword,
      year: searchYear,
      season: filters.season,
      page: filters.page,
      page_size: filters.page_size
    })
    items.value = data.items
    total.value = data.total
    ElMessage.success('番剧库已更新')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '搜索更新失败')
  } finally {
    searching.value = false
    loading.value = false
  }
}

onMounted(() => {
  void loadLocal()
})
</script>

<style scoped>
.library-page {
  display: grid;
  gap: 22px;
}

.library-hero {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
  align-items: flex-end;
  justify-content: space-between;
  padding: 28px 30px;
  background:
    radial-gradient(circle at top right, rgba(72, 139, 203, 0.2), transparent 28%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.92), rgba(251, 253, 255, 0.86));
  border: 1px solid rgba(205, 214, 228, 0.72);
  border-radius: 28px;
  box-shadow: 0 20px 60px rgba(24, 33, 47, 0.08);
}

.library-hero-copy {
  display: grid;
  gap: 8px;
  max-width: 760px;
}

.library-eyebrow {
  margin: 0;
  color: #4d7db3;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.library-hero-copy h1 {
  margin: 0;
  color: #18212f;
  font-size: clamp(32px, 4vw, 44px);
  line-height: 1.05;
}

.library-hero-copy p:last-child {
  max-width: 680px;
  margin: 0;
  color: #5d6a7b;
  font-size: 15px;
  line-height: 1.7;
}

.library-hero-note {
  display: grid;
  gap: 4px;
  min-width: 180px;
  padding: 16px 18px;
  color: #314254;
  background: rgba(255, 255, 255, 0.74);
  border: 1px solid rgba(210, 219, 232, 0.88);
  border-radius: 22px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.72);
}

.library-hero-note strong {
  font-size: 18px;
  line-height: 1.3;
}

.hero-note-label {
  color: #6f7d90;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.search-panel {
  display: grid;
  gap: 12px;
}

.search-primary,
.library-summary {
  display: flex;
  gap: 12px;
  align-items: center;
}

.search-primary,
.library-summary {
  justify-content: space-between;
}

.search-primary {
  flex-wrap: nowrap;
  justify-content: flex-end;
  padding: 16px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(214, 222, 234, 0.84);
  border-radius: 24px;
  box-shadow: 0 16px 40px rgba(24, 33, 47, 0.05);
}

.primary-action,
.search-primary :deep(.el-button) {
  border-radius: 16px;
}

.primary-action {
  flex-shrink: 0;
  padding-inline: 18px;
  box-shadow: 0 12px 28px rgba(57, 122, 218, 0.22);
}

.library-summary {
  flex-wrap: wrap;
  gap: 14px;
  padding: 0 4px;
}

.summary-copy {
  display: grid;
  gap: 2px;
}

.summary-title {
  color: #233243;
  font-size: 18px;
  font-weight: 700;
}

.summary-subtitle {
  color: #6f7d90;
  font-size: 13px;
}

.summary-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.summary-chip {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 12px;
  color: #4b5a6d;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(215, 223, 235, 0.88);
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.library-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 20px;
  min-height: 320px;
}

.library-card {
  position: relative;
  display: flex;
  width: 100%;
  overflow: hidden;
  cursor: pointer;
  background: #eef3f8;
  border: 1px solid rgba(225, 232, 241, 0.72);
  border-radius: 22px;
  aspect-ratio: 4 / 5;
  box-shadow: 0 14px 36px rgba(24, 33, 47, 0.08);
  isolation: isolate;
}

.library-card::after {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(14, 19, 28, 0.04), rgba(14, 19, 28, 0.18));
  content: '';
  pointer-events: none;
}

.library-card:hover,
.library-card:focus-visible {
  transform: translateY(-4px);
  box-shadow: 0 22px 44px rgba(24, 33, 47, 0.14);
}

.card-cover,
.card-cover img,
.card-cover-fallback {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.card-cover img {
  display: block;
  object-fit: cover;
}

.card-cover-fallback {
  display: grid;
  place-items: center;
  color: rgba(255, 255, 255, 0.92);
  background:
    radial-gradient(circle at top, rgba(255, 255, 255, 0.2), transparent 30%),
    linear-gradient(135deg, #5577a5, #3a4b65 55%, #232d3d 100%);
  font-size: 32px;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.card-season-badge,
.card-source-badge {
  position: absolute;
  z-index: 2;
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 10px;
  color: #ffffff;
  background: rgba(17, 24, 39, 0.56);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 999px;
  backdrop-filter: blur(10px);
  font-size: 12px;
  font-weight: 700;
}

.card-season-badge {
  top: 14px;
  left: 14px;
}

.card-source-badge {
  top: 14px;
  right: 14px;
}

.card-overlay {
  position: absolute;
  inset: auto 0 0;
  z-index: 3;
  display: grid;
  gap: 10px;
  padding: 82px 18px 18px;
  background: linear-gradient(180deg, rgba(11, 16, 24, 0) 0%, rgba(11, 16, 24, 0.16) 16%, rgba(11, 16, 24, 0.78) 52%, rgba(11, 16, 24, 0.94) 100%);
}

.card-topline,
.card-chip-row,
.card-resource-line,
.card-actions {
  display: flex;
  align-items: center;
}

.card-topline,
.card-actions {
  justify-content: space-between;
}

.card-chip-row,
.card-resource-line {
  gap: 8px;
  flex-wrap: wrap;
}

.overlay-chip,
.overlay-meta {
  display: inline-flex;
  gap: 5px;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  color: rgba(248, 251, 255, 0.92);
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.overlay-chip--library {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.12);
}

.overlay-chip--pending {
  background: rgba(245, 158, 11, 0.2);
  border-color: rgba(251, 191, 36, 0.28);
}

.overlay-chip--emby {
  background: rgba(34, 197, 94, 0.22);
  border-color: rgba(74, 222, 128, 0.3);
}

.card-title {
  display: -webkit-box;
  min-height: calc(1.38em * 2);
  margin: 0;
  overflow: hidden;
  color: #ffffff;
  font-size: 22px;
  font-weight: 700;
  line-height: 1.38;
  text-shadow: 0 4px 18px rgba(0, 0, 0, 0.24);
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.card-description,
.card-resource-line span {
  display: -webkit-box;
  margin: 0;
  overflow: hidden;
  color: rgba(229, 236, 244, 0.84);
  font-size: 13px;
  line-height: 1.55;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 1;
}

.card-resource-line {
  color: rgba(229, 236, 244, 0.78);
  font-size: 13px;
}

.card-resource-line span {
  max-width: calc(50% - 4px);
}

.card-resource-line__web {
  color: #ffe2bf;
  text-shadow: 0 0 14px rgba(249, 115, 22, 0.22);
}

.card-actions {
  margin-top: 2px;
  min-height: 38px;
}

.card-action {
  display: inline-flex;
  gap: 8px;
  align-items: center;
  padding: 0;
  color: rgba(248, 251, 255, 0.92);
  background: transparent;
  border: none;
  border-radius: 999px;
  font: inherit;
  cursor: pointer;
}

.card-action--quiet {
  color: rgba(240, 246, 255, 0.82);
}

.card-action--link {
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.1);
}

.card-action:hover {
  color: #ffffff;
}

.library-empty {
  padding: 28px 0;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(214, 222, 234, 0.8);
  border-radius: 20px;
}

.library-pager {
  justify-content: flex-end;
}

.primary-action:deep(.el-button),
.primary-action {
  color: #ffffff;
  background: linear-gradient(135deg, #2e7df6, #1e62d8);
  border-color: transparent;
}

.primary-action:hover,
.primary-action:focus-visible {
  background: linear-gradient(135deg, #3a87fb, #2569df);
}

@media (max-width: 1480px) {
  .library-grid {
    grid-template-columns: repeat(auto-fill, minmax(232px, 1fr));
  }
}

@media (max-width: 960px) {
  .library-hero,
  .search-primary,
  .library-summary {
    align-items: stretch;
  }

  .search-primary,
  .library-summary {
    flex-direction: column;
  }

  .search-primary {
    flex-wrap: wrap;
  }

  .primary-action {
    width: 100%;
  }

  .library-grid {
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  }

  .card-title {
    font-size: 20px;
  }
}

@media (max-width: 640px) {
  .library-page {
    gap: 18px;
  }

  .library-hero,
  .search-primary {
    padding: 18px;
    border-radius: 20px;
  }

  .library-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
  }

  .library-card {
    border-radius: 18px;
  }

  .card-season-badge,
  .card-source-badge {
    min-height: 28px;
    font-size: 11px;
  }

  .card-overlay {
    padding: 62px 12px 12px;
  }

  .card-title {
    font-size: 18px;
  }

  .card-resource-line span {
    max-width: 100%;
  }

  .card-actions {
    flex-wrap: wrap;
    gap: 8px;
  }
}

@media (max-width: 420px) {
  .library-grid {
    grid-template-columns: 1fr;
  }
}
</style>
