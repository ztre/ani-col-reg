<template>
  <div class="page">
    <NavBar :title="navTitle" back hide-large-title />

    <div v-if="loading" class="detail-skeleton" aria-hidden="true">
      <div class="skeleton skeleton-hero" />
      <div class="list-section">
        <div class="list-group">
          <div v-for="index in 4" :key="index" class="skeleton-row">
            <div class="skeleton skeleton-thumb" />
            <div class="skeleton-row-lines">
              <div class="skeleton skeleton-line skeleton-line--wide" />
              <div class="skeleton skeleton-line skeleton-line--narrow" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="loadError" class="state-section">
      <EmptyState icon="warning" title="加载失败" hint="请检查网络连接后重试" />
      <button type="button" class="retry-button" @click="load">重试</button>
    </div>

    <EmptyState
      v-else-if="!group"
      icon="tv"
      title="没有找到该系列"
      hint="它可能还未被收录到资料库"
    />

    <template v-else>
      <!-- 氛围横幅：封面模糊压暗后全宽铺开，向页面底色渐隐 -->
      <header class="hero">
        <img
          v-if="group.cover_url && !heroFailed"
          class="hero-image"
          :src="group.cover_url"
          :alt="group.series_title"
        />
        <div v-else class="hero-fallback">
          <span>{{ fallbackInitial }}</span>
        </div>
        <div class="hero-fade" aria-hidden="true" />
      </header>

      <!-- 海报 + 标题卡片：跨坐在横幅底沿，承担主标题展示 -->
      <section class="series-head">
        <div class="series-head-poster">
          <img
            v-if="group.cover_url && !heroFailed"
            :src="group.cover_url"
            :alt="group.series_title"
          />
          <span v-else>{{ fallbackInitial }}</span>
        </div>
        <div class="series-head-info">
          <h2 class="series-head-title">{{ group.series_title }}</h2>
          <p class="series-head-meta">{{ headMeta }}</p>
        </div>
      </section>

      <div class="list-section">
        <div class="list-group">
          <article
            v-for="entry in sortedEntries"
            :key="entry.id"
            class="entry-row"
            @click="openEntry(entry)"
          >
            <div class="entry-cover">
              <img
                v-if="entry.cover_url && !failedCovers.has(entry.id)"
                class="entry-image"
                :src="entry.cover_url"
                :alt="entry.title_cn"
                loading="lazy"
                @error="failedCovers.add(entry.id)"
              />
              <div v-else class="entry-fallback">
                <span>{{ initialOf(entry) }}</span>
              </div>
            </div>
            <div class="entry-body">
              <p class="entry-title">{{ entry.title_cn }}</p>
              <p class="entry-meta">
                <span class="entry-pill">{{ entry.season_label || '第 1 季' }}</span>
                <span class="entry-date">{{ entry.year }} · {{ seasonName(entry.season) }}</span>
                <button
                  v-if="entry.emby_organized"
                  type="button"
                  class="emby-tag is-organized"
                  :class="{ 'is-actionable': isDesktop }"
                  :title="isDesktop ? '已在 Emby 整理，点击取消标记' : '已在 Emby 整理'"
                  @click.stop="toggleEmby(entry)"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                    <path d="M20 6L9 17l-5-5" />
                  </svg>
                  Emby
                </button>
                <button
                  v-else-if="isDesktop"
                  type="button"
                  class="emby-tag"
                  :disabled="togglingId === entry.id"
                  title="标记为已在 Emby 整理"
                  @click.stop="toggleEmby(entry)"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" aria-hidden="true">
                    <path d="M12 5v14M5 12h14" />
                  </svg>
                  Emby
                </button>
              </p>
            </div>
            <svg
              v-if="entry.is_collected"
              class="entry-heart"
              viewBox="0 0 24 24"
              fill="currentColor"
              aria-hidden="true"
            >
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
            </svg>
          </article>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import EmptyState from '../components/EmptyState.vue'
import NavBar from '../components/NavBar.vue'
import { fetchAnime } from '../services/animeService'
import { fetchCollectedSeries, setEmbyOrganized } from '../services/collectionService'
import type { Anime, SeriesGroup } from '../types'

const props = defineProps<{
  seriesKey: string
}>()

const SEASON_NAMES: Record<number, string> = { 1: '冬', 2: '春', 3: '夏', 4: '秋' }
// 后端 /api/anime 校验 page_size ≤ 100，超出会 422
const FALLBACK_PAGE_SIZE = 100
const MAX_FALLBACK_PAGES = 5

const router = useRouter()

const loading = ref(true)
const loadError = ref(false)
const group = ref<SeriesGroup | null>(null)
const heroFailed = ref(false)
const failedCovers = reactive(new Set<number>())

const navTitle = computed(() => group.value?.series_title || '系列详情')

// Emby 整理标记：移动端仅展示，桌面端（≥1024px）可点击切换
const isDesktop = ref(window.matchMedia('(min-width: 1024px)').matches)
const desktopQuery = window.matchMedia('(min-width: 1024px)')
function onDesktopChange(event: MediaQueryListEvent) {
  isDesktop.value = event.matches
}
desktopQuery.addEventListener('change', onDesktopChange)
onBeforeUnmount(() => desktopQuery.removeEventListener('change', onDesktopChange))

const togglingId = ref<number | null>(null)

async function toggleEmby(entry: Anime) {
  if (!isDesktop.value || togglingId.value !== null) return
  togglingId.value = entry.id
  try {
    await setEmbyOrganized(entry.id, !entry.emby_organized)
    entry.emby_organized = !entry.emby_organized
  } catch (error) {
    console.error('更新 Emby 整理标记失败：', error)
  } finally {
    togglingId.value = null
  }
}

const fallbackInitial = computed(() => group.value?.series_title.trim().charAt(0) || '?')

// 海报卡片下的元信息：收录部数 + 最新季度
const headMeta = computed(() => {
  const current = group.value
  if (!current) return ''
  const season = SEASON_NAMES[current.latest_season] ?? ''
  return `共 ${current.entry_count} 部 · 最新 ${current.latest_year} ${season}`.trim()
})

const sortedEntries = computed(() => {
  const entries = group.value?.entries ?? []
  return [...entries].sort((a, b) => a.year - b.year || a.season - b.season)
})

function seasonName(season: number): string {
  // 0 = 源站未确定季度（尚待播出）
  return SEASON_NAMES[season] ?? (season === 0 ? '待播' : '')
}

function initialOf(entry: Anime): string {
  return entry.title_cn.trim().charAt(0) || '?'
}

async function fetchAllSeriesEntries(seriesKey: string): Promise<{ items: Anime[]; total: number }> {
  const items: Anime[] = []
  let total = 0
  for (let page = 1; page <= MAX_FALLBACK_PAGES; page += 1) {
    const result = await fetchAnime({ series_key: seriesKey, page, page_size: FALLBACK_PAGE_SIZE })
    total = result.total
    items.push(...result.items)
    if (items.length >= result.total || result.items.length === 0) {
      break
    }
  }
  return { items, total: Math.max(total, items.length) }
}

function assembleGroup(seriesKey: string, entries: Anime[], total: number): SeriesGroup {
  const latest = entries.reduce((acc, cur) =>
    cur.year > acc.year || (cur.year === acc.year && cur.season > acc.season) ? cur : acc
  )
  return {
    series_key: seriesKey,
    series_title: entries[0].series_title || entries[0].title_cn,
    entry_count: total,
    latest_year: latest.year,
    latest_season: latest.season,
    cover_url: entries.find((entry) => entry.cover_url)?.cover_url ?? null,
    entries
  }
}

async function load() {
  loading.value = true
  loadError.value = false
  heroFailed.value = false
  failedCovers.clear()
  try {
    const collected = await fetchCollectedSeries()
    const matched = collected.find((item) => item.series_key === props.seriesKey)
    if (matched) {
      group.value = matched
      return
    }
    const { items, total } = await fetchAllSeriesEntries(props.seriesKey)
    group.value = items.length ? assembleGroup(props.seriesKey, items, total) : null
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
}

function openEntry(entry: Anime) {
  router.push(`/anime/${entry.id}`)
}

onMounted(load)
</script>

<style scoped>
.page {
  padding-bottom: calc(env(safe-area-inset-bottom) + 24px);
}

/* 氛围横幅：封面模糊压暗，高度收敛，向页面底色渐隐 */
.hero {
  position: relative;
  height: 190px;
  overflow: hidden;
  background: var(--fill);
}

.hero-image {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  /* 放大以隐藏模糊边缘，压暗保证导航栏可读 */
  filter: blur(26px) brightness(0.72) saturate(1.15);
  transform: scale(1.25);
}

.hero-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: linear-gradient(145deg, var(--fill), var(--bg-elevated));
  color: var(--text-tertiary);
  font-size: 44px;
  font-weight: 700;
}

.hero-fade {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(0, 0, 0, 0.16), transparent 42%, var(--bg) 92%);
}

/* 海报 + 标题卡片：负 margin 跨坐横幅底沿，标题落在已渐隐为底色的区域保证可读 */
.series-head {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: flex-end;
  gap: 16px;
  margin: -128px 16px 0;
  padding-bottom: 6px;
}

.series-head-poster {
  flex-shrink: 0;
  width: 108px;
  aspect-ratio: 3 / 4;
  overflow: hidden;
  border-radius: 12px;
  background: var(--fill);
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.28);
}

.series-head-poster img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.series-head-poster span {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: linear-gradient(145deg, var(--fill), var(--bg-elevated));
  color: var(--text-tertiary);
  font-size: 36px;
  font-weight: 700;
}

.series-head-info {
  flex: 1;
  min-width: 0;
  padding-bottom: 4px;
}

.series-head-title {
  display: -webkit-box;
  overflow: hidden;
  margin: 0;
  color: var(--text-primary);
  font-size: 22px;
  font-weight: 700;
  line-height: 1.25;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.series-head-meta {
  margin: 6px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.4;
}

/* 桌面端：横幅加高，头部卡片与列表同宽居中对齐 */
@media (min-width: 1024px) {
  .hero {
    height: 240px;
  }

  .series-head {
    max-width: 780px;
    margin: -172px auto 0;
    padding: 0 24px 6px;
  }

  .series-head-poster {
    width: 128px;
  }

  .series-head-title {
    font-size: 26px;
  }
}

@media (min-width: 1440px) {
  .series-head {
    max-width: 1100px;
  }
}

.list-section {
  padding: 12px 16px 0;
}

.state-section {
  display: flex;
  flex-direction: column;
}

.retry-button {
  align-self: center;
  margin-top: -36px;
  padding: 12px 32px;
  border-radius: 999px;
  background: var(--fill);
  color: var(--accent);
  font-size: 15px;
  font-weight: 600;
  transition: opacity 200ms ease;
}

.retry-button:active {
  opacity: 0.6;
}

.entry-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  cursor: pointer;
  transition: background-color 120ms ease;
}

.entry-row:active {
  background: var(--fill);
}

.entry-cover {
  flex-shrink: 0;
  width: 44px;
  height: 60px;
  border-radius: 6px;
  overflow: hidden;
  background: var(--fill);
}

.entry-image {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.entry-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: linear-gradient(145deg, var(--fill), var(--bg-elevated));
  color: var(--text-tertiary);
  font-size: 18px;
  font-weight: 600;
}

.entry-body {
  flex: 1;
  min-width: 0;
}

.entry-title {
  margin: 0;
  overflow: hidden;
  color: var(--text-primary);
  font-size: 15px;
  font-weight: 600;
  line-height: 1.3;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.entry-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 4px 0 0;
  min-width: 0;
}

.entry-pill {
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--fill);
  color: var(--accent);
  font-size: 11px;
  font-weight: 600;
  line-height: 1.4;
  white-space: nowrap;
}

.entry-date {
  overflow: hidden;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.4;
  white-space: nowrap;
  text-overflow: ellipsis;
}

/* Emby 整理标记：已整理为系统绿填充态，未整理（桌面端）为浅色可点击态 */
.emby-tag {
  display: inline-flex;
  flex-shrink: 0;
  align-items: center;
  gap: 3px;
  padding: 2px 8px;
  border: 1px solid var(--fill);
  border-radius: 999px;
  background: transparent;
  color: var(--text-tertiary);
  font-size: 11px;
  font-weight: 600;
  line-height: 1.4;
  white-space: nowrap;
  cursor: pointer;
  transition: opacity 200ms ease;
}

.emby-tag svg {
  width: 10px;
  height: 10px;
}

.emby-tag:active {
  opacity: 0.6;
}

.emby-tag:disabled {
  opacity: 0.4;
  cursor: default;
}

.emby-tag.is-organized {
  border-color: transparent;
  background: rgba(52, 199, 89, 0.16);
  color: #34c759;
}

/* 非桌面端的已整理标签仅作展示，不响应点击 */
.emby-tag.is-organized:not(.is-actionable) {
  cursor: default;
}

.entry-heart {
  flex-shrink: 0;
  width: 16px;
  height: 16px;
  color: var(--accent);
}

.detail-skeleton {
  padding-bottom: 16px;
}

.skeleton-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
}

.skeleton-row-lines {
  flex: 1;
  min-width: 0;
}

.skeleton {
  border-radius: 8px;
  background: linear-gradient(100deg, var(--fill) 40%, var(--bg-elevated) 50%, var(--fill) 60%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.4s ease-in-out infinite;
}

.skeleton-hero {
  height: 190px;
  min-height: 0;
  border-radius: 0;
}

.skeleton-thumb {
  flex-shrink: 0;
  width: 44px;
  height: 60px;
}

.skeleton-line {
  height: 12px;
  border-radius: 6px;
}

.skeleton-line--wide {
  width: 88%;
}

.skeleton-line--narrow {
  width: 54%;
  margin-top: 10px;
}

@keyframes skeleton-shimmer {
  0% {
    background-position: 200% 0;
  }

  100% {
    background-position: -200% 0;
  }
}
</style>
