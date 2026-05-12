<template>
  <section class="collection-page">
    <div class="collection-hero">
      <div>
        <p class="collection-eyebrow">Collections</p>
        <h1>收藏管理</h1>
        <p class="collection-subcopy">按资源标签、字幕组和备注整理已收藏条目，直接在弹窗里更新本地记录。</p>
      </div>

    </div>

    <AnimeFilterBar
      v-model:year="year"
      v-model:season="season"
      v-model:release-tags="releaseTags"
      v-model:group-tags="groupTags"
      :release-tag-options="releaseTagOptions"
      :group-tag-options="groupTagOptions"
      @apply="load"
      @clear="resetFilters"
    />

    <section class="collection-summary">
      <div class="collection-summary-copy">
        <span class="collection-summary-title">当前收藏 {{ items.length }} 部</span>
        <span class="collection-summary-subtitle">按年份、季度和资源标签快速整理本地收藏记录。</span>
      </div>

      <div class="collection-summary-actions">
        <div v-if="activeFilterChips.length" class="collection-summary-chips">
          <span v-for="chip in activeFilterChips" :key="chip" class="collection-summary-chip">{{ chip }}</span>
        </div>

        <div class="collection-layout-switch">
          <div class="layout-switch-buttons">
            <el-button
              :type="viewMode === 'list' ? 'primary' : 'default'"
              :icon="List"
              circle
              aria-label="列表模式"
              title="列表模式"
              @click="setViewMode('list')"
            />
            <el-button
              :type="viewMode === 'cards' ? 'primary' : 'default'"
              :icon="Grid"
              circle
              aria-label="小卡片模式"
              title="小卡片模式"
              @click="setViewMode('cards')"
            />
          </div>
        </div>
      </div>
    </section>

    <div v-loading="loading" :class="['collection-stack', `collection-stack--${viewMode}`]">
      <article v-for="item in items" :key="item.id" :class="['collection-entry', `collection-entry--${viewMode}`]">
        <div class="entry-poster">
          <img v-if="item.cover_url" :src="item.cover_url" :alt="`${item.title_cn} 封面`" loading="lazy" />
          <div v-else class="entry-poster-fallback">{{ item.title_cn.slice(0, 2) }}</div>
        </div>

        <div class="entry-main">
          <div class="entry-meta">{{ item.year }} / {{ seasonLabel(item.season) }}</div>
          <h2>{{ item.title_cn }}</h2>
          <div class="entry-chip-row">
            <el-tag :type="collectionStatusTagType(item.collection_item)" effect="dark">{{ collectionStageLabel(item.collection_item) }}</el-tag>
            <el-tag v-for="tag in splitTags(item.collection_item?.release_tags)" :key="tag" :type="isWebReleaseTag(tag) ? 'danger' : undefined" effect="plain">{{ tag }}</el-tag>
            <el-tag v-for="tag in splitTags(item.collection_item?.group_tags)" :key="tag" type="info" effect="plain">{{ tag }}</el-tag>
          </div>
          <p class="entry-note">{{ item.collection_item?.note || '暂无备注，点击编辑收藏后补充。' }}</p>
        </div>

        <div class="entry-actions">
          <el-button :icon="Edit" @click="openDialog(item)">编辑收藏</el-button>
        </div>
      </article>
    </div>

    <el-empty v-if="!loading && items.length === 0" description="暂无收藏记录" />

    <AnimeDialog
      v-model="dialogVisible"
      :anime-id="dialogAnimeId"
      :initial-anime="dialogAnimePreview"
      :detail-loaded="hydratedAnimeIds.has(dialogAnimeId || -1)"
      @saved="handleDialogSaved"
      @removed="handleDialogRemoved"
      @loaded="handleDialogLoaded"
      @error="ElMessage.error"
    />
  </section>
</template>

<script setup lang="ts">
import { Edit, Grid, List } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'

import { listAnime } from '../api'
import { collectionStageLabel, collectionStatusTagType, isWebReleaseTag } from '../collectionPresentation'
import AnimeDialog from '../components/AnimeDialog.vue'
import AnimeFilterBar from '../components/AnimeFilterBar.vue'
import type { Anime, CollectionItem } from '../types'

type CollectionLayoutMode = 'list' | 'cards'

const COLLECTION_VIEW_MODE_KEY = 'ani-col-reg.collection-view-mode'
const year = ref<string | undefined>()
const season = ref<number | undefined>()
const releaseTags = ref<string[]>([])
const groupTags = ref<string[]>([])
const items = ref<Anime[]>([])
const loading = ref(false)
const viewMode = ref<CollectionLayoutMode>(loadCollectionViewMode())
const dialogVisible = ref(false)
const dialogAnimeId = ref<number | null>(null)
const dialogAnimePreview = ref<Anime | null>(null)
const hydratedAnimeIds = reactive(new Set<number>())
const releaseTagOptions = computed(() => uniqueOptions(items.value.flatMap((item) => splitTags(item.collection_item?.release_tags)), releaseTags.value))
const groupTagOptions = computed(() => uniqueOptions(items.value.flatMap((item) => splitTags(item.collection_item?.group_tags)), groupTags.value))
const activeFilterChips = computed(() => {
  const chips = [
    year.value ? `年份 ${year.value}` : '',
    season.value ? `季度 ${seasonLabel(season.value)}` : '',
    ...releaseTags.value.map((tag) => `资源 ${tag}`),
    ...groupTags.value.map((tag) => `字幕组 ${tag}`),
  ]
  return chips.filter(Boolean)
})

function loadCollectionViewMode(): CollectionLayoutMode {
  if (typeof window === 'undefined') {
    return 'list'
  }

  const saved = window.localStorage.getItem(COLLECTION_VIEW_MODE_KEY)
  return saved === 'cards' ? 'cards' : 'list'
}

function setViewMode(mode: CollectionLayoutMode) {
  viewMode.value = mode
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(COLLECTION_VIEW_MODE_KEY, mode)
  }
}

function seasonLabel(season: number) {
  const labels: Record<number, string> = { 1: '1月', 2: '4月', 3: '7月', 4: '10月' }
  return labels[season] || String(season)
}

function splitTags(value?: string | null) {
  return (value || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function uniqueOptions(values: string[], selected: string[]) {
  return [...new Set([...selected, ...values].map((item) => item.trim()).filter(Boolean))]
}

function resetFilters() {
  year.value = undefined
  season.value = undefined
  releaseTags.value = []
  groupTags.value = []
  void load()
}

async function load() {
  loading.value = true
  try {
    const data = await listAnime({
      collected: true,
      year: year.value ? Number(year.value) : undefined,
      season: season.value,
      release_tag: releaseTags.value,
      group_tag: groupTags.value,
      page_size: 100
    })
    items.value = data.items
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载失败')
  } finally {
    loading.value = false
  }
}

function openDialog(item: Anime) {
  dialogAnimeId.value = item.id
  dialogAnimePreview.value = { ...item, collection_item: item.collection_item ? { ...item.collection_item } : null }
  dialogVisible.value = true
}

function handleDialogSaved(payload: { animeId: number; collection: CollectionItem }) {
  const item = items.value.find((entry) => entry.id === payload.animeId)
  if (item) {
    item.collection_item = payload.collection
  }
  if (dialogAnimePreview.value?.id === payload.animeId) {
    dialogAnimePreview.value = {
      ...dialogAnimePreview.value,
      collection_item: payload.collection,
    }
  }
  ElMessage.success('已保存')
}

function handleDialogLoaded(anime: Anime) {
  hydratedAnimeIds.add(anime.id)
  const item = items.value.find((entry) => entry.id === anime.id)
  if (item) {
    Object.assign(item, anime)
  }
  if (dialogAnimePreview.value?.id === anime.id) {
    dialogAnimePreview.value = {
      ...anime,
      collection_item: anime.collection_item ? { ...anime.collection_item } : null,
    }
  }
}

function handleDialogRemoved(payload: { animeId: number }) {
  items.value = items.value.filter((entry) => entry.id !== payload.animeId)
  if (dialogAnimeId.value === payload.animeId) {
    dialogVisible.value = false
    dialogAnimeId.value = null
    dialogAnimePreview.value = null
  }
  ElMessage.success('已取消收藏')
}

onMounted(load)
</script>

<style scoped>
.collection-page {
  display: grid;
  gap: 20px;
}

.collection-hero {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: flex-end;
  justify-content: space-between;
  padding: 28px 30px;
  background:
    radial-gradient(circle at top right, rgba(72, 139, 203, 0.18), transparent 28%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.92), rgba(250, 252, 255, 0.88));
  border: 1px solid rgba(205, 214, 228, 0.72);
  border-radius: 28px;
  box-shadow: 0 20px 60px rgba(24, 33, 47, 0.08);
}

.collection-eyebrow {
  margin: 0 0 8px;
  color: #4d7db3;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.collection-hero h1,
.entry-main h2 {
  margin: 0;
}

.collection-subcopy,
.entry-main p {
  margin: 8px 0 0;
  color: #5e6b7d;
  line-height: 1.7;
}

.collection-layout-switch {
  display: flex;
  align-items: center;
}

.layout-switch-buttons {
  display: inline-flex;
  gap: 8px;
  padding: 6px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(210, 219, 232, 0.88);
  border-radius: 18px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.72);
}

.layout-switch-buttons :deep(.el-button) {
  width: 42px;
  height: 42px;
  margin: 0;
  border-radius: 14px;
}

.collection-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  align-items: center;
  justify-content: space-between;
  padding: 0 4px;
}

.collection-summary-copy {
  display: grid;
  gap: 2px;
}

.collection-summary-title {
  color: #233243;
  font-size: 18px;
  font-weight: 700;
}

.collection-summary-subtitle {
  color: #6f7d90;
  font-size: 13px;
}

.collection-summary-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.collection-summary-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  align-items: center;
  justify-content: flex-end;
}

.collection-summary-chip {
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

.collection-stack {
  display: grid;
  min-height: 240px;
}

.collection-stack--list {
  gap: 16px;
}

.collection-stack--cards {
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 18px;
}

.collection-entry {
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(214, 222, 234, 0.86);
  border-radius: 24px;
  box-shadow: 0 16px 40px rgba(24, 33, 47, 0.06);
}

.collection-entry--list {
  display: grid;
  grid-template-columns: 110px minmax(0, 1fr) auto;
  gap: 18px;
  align-items: center;
  padding: 18px;
}

.collection-entry--cards {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
  align-items: start;
  padding: 14px;
}

.entry-poster {
  width: 100%;
  overflow: hidden;
  border-radius: 18px;
  aspect-ratio: 4 / 5;
  background: linear-gradient(135deg, #d7e2f1, #ecf1f8);
}

.entry-poster img,
.entry-poster-fallback {
  width: 100%;
  height: 100%;
}

.entry-poster img {
  display: block;
  object-fit: cover;
}

.entry-poster-fallback {
  display: grid;
  place-items: center;
  color: #ffffff;
  background: linear-gradient(135deg, #5885c2, #253955);
  font-size: 26px;
  font-weight: 800;
}

.entry-main {
  display: grid;
  gap: 8px;
  min-width: 0;
}

.collection-entry--cards .entry-main {
  gap: 6px;
}

.entry-main h2 {
  color: #18212f;
  font-size: 22px;
}

.collection-entry--cards .entry-main h2 {
  font-size: 18px;
  line-height: 1.3;
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.entry-note {
  margin: 0;
}

.collection-entry--cards .entry-note {
  color: #607084;
  font-size: 13px;
  line-height: 1.55;
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

.entry-meta {
  color: #4d7db3;
  font-size: 13px;
  font-weight: 700;
}

.collection-entry--cards .entry-meta {
  font-size: 12px;
}

.entry-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.collection-entry--cards .entry-chip-row {
  gap: 6px;
}

.entry-actions {
  display: flex;
  justify-content: flex-end;
}

.collection-entry--cards .entry-actions {
  justify-content: stretch;
}

.collection-entry--cards .entry-actions :deep(.el-button) {
  width: 100%;
}

.entry-actions :deep(.el-button) {
  border-radius: 16px;
}

@media (max-width: 960px) {
  .collection-entry--list {
    grid-template-columns: 1fr;
  }

  .collection-hero,
  .collection-summary,
  .collection-summary-actions {
    align-items: stretch;
  }

  .collection-entry--list .entry-poster {
    width: 140px;
  }

  .entry-actions {
    justify-content: flex-start;
  }
}

@media (max-width: 640px) {
  .collection-summary-actions,
  .collection-summary-chips,
  .layout-switch-buttons {
    width: 100%;
  }

  .collection-summary-actions,
  .collection-summary-chips,
  .layout-switch-buttons {
    justify-content: flex-start;
  }

  .layout-switch-buttons :deep(.el-button) {
    flex: 0 0 auto;
  }
}
</style>
