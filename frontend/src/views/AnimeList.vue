<template>
  <section class="anime-library-page">
    <AnimeHeroBanner
      :subcopy="librarySubcopy"
      :total="total"
      :year="filters.year"
      :season="filters.season"
      :keyword="filters.keyword || undefined"
    />

    <AnimeToolbar
      :total="total"
      :page="filters.page"
      :page-count="pageCount"
      :page-size="filters.page_size"
      :active-filters="activeFilterChips"
      :searching="searching"
    >
      <AnimeFilterBar
        v-model:year="yearFilterModel"
        v-model:season="seasonFilterModel"
        v-model:keyword="filters.keyword"
        apply-label="搜索并更新"
        :auto-apply-year-season="false"
        @apply="refreshFromSource"
        @clear="clearFilters"
      />
    </AnimeToolbar>

    <AnimeLoading v-if="loading" :count="Math.min(filters.page_size, 10)" />
    <AnimeEmpty v-else-if="items.length === 0" @clear="clearFilters" />
    <AnimeGrid v-else :items="items" @select="openDetail" />

    <AnimePagination
      v-model:page="filters.page"
      v-model:page-size="filters.page_size"
      :page-sizes="pageSizeOptions"
      :total="total"
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
import { ElMessage } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'

import { seasonLabel } from '../animePresentation'
import { useAuthSession } from '../auth'
import AnimeDialog from '../components/AnimeDialog.vue'
import AnimeEmpty from '../components/AnimeEmpty.vue'
import AnimeFilterBar from '../components/AnimeFilterBar.vue'
import AnimeGrid from '../components/AnimeGrid.vue'
import AnimeHeroBanner from '../components/AnimeHeroBanner.vue'
import AnimeLoading from '../components/AnimeLoading.vue'
import AnimePagination from '../components/AnimePagination.vue'
import AnimeToolbar from '../components/AnimeToolbar.vue'
import { listAnime, searchAnime } from '../services/animeService'
import type { Anime, CollectionItem } from '../types'

const session = useAuthSession()

interface LibraryFilters {
  keyword: string
  year: number | undefined
  season: number | undefined
  page: number
  page_size: number
}

function resolveCurrentSeason() {
  const month = new Date().getMonth() + 1
  if (month <= 3) return 1
  if (month <= 6) return 2
  if (month <= 9) return 3
  return 4
}

function createDefaultFilters(): LibraryFilters {
  const status = session.state.status
  return {
    keyword: '',
    year: status?.default_search_year ?? new Date().getFullYear(),
    season: status?.default_search_season ?? resolveCurrentSeason(),
    page: 1,
    page_size: status?.default_page_size ?? 24
  }
}

const filters = reactive<LibraryFilters>(createDefaultFilters())
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
const pageCount = computed(() => Math.max(1, Math.ceil(total.value / filters.page_size)))
const activeFilterChips = computed(() => {
  const chips = [
    filters.year ? `年份 ${filters.year}` : '',
    filters.season ? `季度 ${seasonLabel(filters.season)}` : '',
    filters.keyword ? `关键词 ${filters.keyword}` : ''
  ]
  return chips.filter(Boolean)
})

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
.anime-library-page {
  display: grid;
  gap: 22px;
}

@media (max-width: 640px) {
  .anime-library-page {
    gap: 16px;
  }
}
</style>
