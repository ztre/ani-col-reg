<template>
  <div ref="rootEl" class="page detail-page">
    <NavBar title="番剧详情" :compact-title="anime?.title_cn ?? ''" back />

    <div v-if="loading" class="detail-skeleton" aria-hidden="true">
      <div class="sk sk-hero" />
      <div class="sk-body">
        <div class="sk sk-line sk-line--title" />
        <div class="sk sk-line sk-line--sub" />
        <div class="sk sk-line sk-line--meta" />
        <div class="sk sk-card" />
      </div>
    </div>

    <div v-else-if="loadError" class="detail-error">
      <EmptyState icon="tv" title="加载失败" :hint="loadError" />
      <button type="button" class="retry-btn" @click="load">重试</button>
    </div>

    <template v-else-if="anime">
      <div class="hero">
        <img
          v-if="anime.cover_url && !coverFailed"
          :src="anime.cover_url"
          class="hero-img"
          alt=""
          @error="coverFailed = true"
        />
        <div v-else class="hero-placeholder" aria-hidden="true" />
        <div class="hero-fade" aria-hidden="true" />
      </div>

      <section class="info">
        <!-- 桌面端完整海报卡片（移动端隐藏，由 hero 大图承担） -->
        <div v-if="anime.cover_url && !coverFailed" class="info-poster" aria-hidden="true">
          <img :src="anime.cover_url" alt="" @error="coverFailed = true" />
        </div>
        <div class="info-main">
          <h1 class="info-title">{{ anime.title_cn }}</h1>
          <p v-if="subtitle" class="info-subtitle">{{ subtitle }}</p>
          <p v-if="metaLine" class="info-meta">{{ metaLine }}</p>
          <p v-if="anime.platforms" class="info-platforms">{{ anime.platforms }}</p>
          <p v-if="anime.detail_refreshing" class="refreshing-hint">
            <span class="refreshing-spinner" aria-hidden="true" />
            <span>详细信息刷新中…</span>
          </p>
          <div class="info-actions">
          <button
            type="button"
            class="collect-btn"
            :class="{ 'collect-btn--on': anime.is_collected }"
            :disabled="collectPending"
            @click="toggleCollect"
          >
            <svg v-if="anime.is_collected" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path
                d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"
              />
            </svg>
            <svg
              v-else
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
              aria-hidden="true"
            >
              <path
                d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"
              />
            </svg>
            <span>{{ anime.is_collected ? '已收藏' : '收藏' }}</span>
          </button>
          </div>
        </div>
      </section>

      <section v-if="anime.synopsis" class="section">
        <h2 class="section-header">简介</h2>
        <div class="card synopsis-card">
          <p ref="synopsisEl" class="synopsis" :class="{ 'synopsis--expanded': synopsisExpanded }">
            {{ anime.synopsis }}
          </p>
          <button
            v-if="synopsisClampable"
            type="button"
            class="expand-btn"
            @click="synopsisExpanded = !synopsisExpanded"
          >
            {{ synopsisExpanded ? '收起' : '展开' }}
          </button>
        </div>
      </section>

      <section v-if="anime.staff || anime.cast || anime.tags" class="section">
        <h2 class="section-header">制作信息</h2>
        <div class="list-group">
          <div v-if="anime.staff" class="info-row">
            <span class="info-label">制作</span>
            <span class="info-value">{{ anime.staff }}</span>
          </div>
          <div v-if="anime.cast" class="info-row">
            <span class="info-label">声优</span>
            <span class="info-value">{{ anime.cast }}</span>
          </div>
          <div v-if="anime.tags" class="info-row">
            <span class="info-label">标签</span>
            <span class="info-value">{{ anime.tags }}</span>
          </div>
        </div>
      </section>

      <section v-if="anime.pv_url || anime.source_url" class="section">
        <h2 class="section-header">链接</h2>
        <div class="list-group">
          <a v-if="anime.pv_url" :href="anime.pv_url" target="_blank" rel="noopener noreferrer" class="link-row">
            <span>观看 PV</span>
            <span class="link-arrow" aria-hidden="true">↗</span>
          </a>
          <a
            v-if="anime.source_url"
            :href="anime.source_url"
            target="_blank"
            rel="noopener noreferrer"
            class="link-row"
          >
            <span>在数据源查看</span>
            <span class="link-arrow" aria-hidden="true">↗</span>
          </a>
        </div>
      </section>

      <section v-if="seriesEntries.length" class="section">
        <h2 class="section-header">同系列其他季度</h2>
        <div class="list-group">
          <RouterLink
            v-for="entry in seriesEntries"
            :key="entry.id"
            :to="`/anime/${entry.id}`"
            class="series-row"
          >
            <img
              v-if="entry.cover_url && !failedSeriesCovers.has(entry.id)"
              :src="entry.cover_url"
              class="series-cover"
              alt=""
              loading="lazy"
              @error="failedSeriesCovers.add(entry.id)"
            />
            <div v-else class="series-cover series-cover--placeholder" aria-hidden="true" />
            <span class="series-title">{{ entry.title_cn }}</span>
            <span class="season-pill">{{ entry.season_label || '第 1 季' }}</span>
            <span class="series-year">{{ entry.year }}</span>
          </RouterLink>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

import EmptyState from '../components/EmptyState.vue'
import NavBar from '../components/NavBar.vue'
import { fetchAnime, fetchAnimeDetail } from '../services/animeService'
import { collect, uncollect } from '../services/collectionService'
import type { Anime } from '../types'

const props = defineProps<{ id: string }>()

const SEASON_NAMES: Record<number, string> = { 1: '冬', 2: '春', 3: '夏', 4: '秋' }

const rootEl = ref<HTMLElement | null>(null)
const anime = ref<Anime | null>(null)
const loading = ref(true)
const loadError = ref('')
const coverFailed = ref(false)
const synopsisEl = ref<HTMLParagraphElement | null>(null)
const synopsisExpanded = ref(false)
const synopsisClampable = ref(false)
const seriesEntries = ref<Anime[]>([])
const failedSeriesCovers = ref(new Set<number>())
const collectPending = ref(false)

const animeId = computed(() => Number(props.id))

const subtitle = computed(() => anime.value?.title_jp || anime.value?.title_en || '')

const metaLine = computed(() => {
  const current = anime.value
  if (!current) {
    return ''
  }
  const parts = [String(current.year)]
  const seasonName = SEASON_NAMES[current.season]
  if (seasonName) {
    parts.push(`${seasonName}季`)
  } else if (current.season === 0) {
    // 季度未定（源站仅给出首播年份，尚待播出）
    parts.push('待播')
  }
  if (current.premiere_date) {
    parts.push(`首播 ${current.premiere_date}`)
  }
  return parts.join(' · ')
})

async function load() {
  loading.value = true
  loadError.value = ''
  anime.value = null
  seriesEntries.value = []
  failedSeriesCovers.value = new Set()
  coverFailed.value = false
  synopsisExpanded.value = false
  synopsisClampable.value = false
  try {
    const detail = await fetchAnimeDetail(animeId.value)
    anime.value = detail
    if (detail.series_key) {
      void loadSeriesEntries(detail.series_key)
    }
    scheduleRefreshPolling(detail)
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : '番剧详情加载失败，请稍后重试。'
  } finally {
    loading.value = false
    await nextTick()
    measureSynopsis()
  }
}

// 后台补抓详情时轮询重取，避免“详细信息刷新中…”永远不消失。
const REFRESH_POLL_INTERVAL = 2000
const REFRESH_POLL_MAX = 15
let refreshPollTimer: ReturnType<typeof setTimeout> | null = null
let refreshPollCount = 0

function stopRefreshPolling() {
  if (refreshPollTimer !== null) {
    clearTimeout(refreshPollTimer)
    refreshPollTimer = null
  }
  refreshPollCount = 0
}

function scheduleRefreshPolling(detail: Anime) {
  stopRefreshPolling()
  if (!detail.detail_refreshing) return
  if (refreshPollCount >= REFRESH_POLL_MAX) return
  refreshPollCount += 1
  refreshPollTimer = setTimeout(async () => {
    try {
      const latest = await fetchAnimeDetail(animeId.value)
      if (anime.value && anime.value.id === latest.id) {
        anime.value = latest
        void measureSynopsisAfterUpdate()
      }
      scheduleRefreshPolling(latest)
    } catch {
      stopRefreshPolling()
    }
  }, REFRESH_POLL_INTERVAL)
}

async function measureSynopsisAfterUpdate() {
  await nextTick()
  measureSynopsis()
}

async function loadSeriesEntries(seriesKey: string) {
  try {
    const result = await fetchAnime({ series_key: seriesKey, page: 1, page_size: 50 })
    seriesEntries.value = result.items
      .filter((entry) => entry.id !== animeId.value)
      .sort((a, b) => a.year - b.year || a.season - b.season)
  } catch {
    seriesEntries.value = []
  }
}

function measureSynopsis() {
  const el = synopsisEl.value
  synopsisClampable.value = !!el && el.scrollHeight > el.clientHeight + 2
}

async function toggleCollect() {
  const current = anime.value
  if (!current || collectPending.value) {
    return
  }
  const nextCollected = !current.is_collected
  current.is_collected = nextCollected
  collectPending.value = true
  try {
    if (nextCollected) {
      await collect(current.id)
    } else {
      await uncollect(current.id)
    }
  } catch {
    current.is_collected = !nextCollected
  } finally {
    collectPending.value = false
  }
}

function resetScroll() {
  let el = rootEl.value?.parentElement ?? null
  while (el) {
    const { overflowY } = window.getComputedStyle(el)
    if (overflowY === 'auto' || overflowY === 'scroll') {
      el.scrollTop = 0
      return
    }
    el = el.parentElement
  }
}

onMounted(() => {
  resetScroll()
  void load()
})

onBeforeUnmount(() => {
  stopRefreshPolling()
})
</script>

<style scoped>
.detail-page {
  /* 使用视口高度（本页隐藏 TabBar，与滚动容器高度一致），避免受外层内容包裹层影响 */
  min-height: 100dvh;
  padding-bottom: calc(env(safe-area-inset-bottom) + 32px);
}

/* 沉浸式头部下的 NavBar 微调：隐藏大标题；未收缩时完全透明（去掉组件默认常驻的 backdrop 模糊） */
.detail-page :deep(.navbar-large-title) {
  display: none;
}

.detail-page :deep(.navbar:not(.navbar--collapsed)) {
  -webkit-backdrop-filter: none;
  backdrop-filter: none;
}

/* ---------- 沉浸式头部 ---------- */
.hero {
  position: relative;
  height: 46vh;
  min-height: 280px;
  margin-top: calc(-1 * (env(safe-area-inset-top) + 50px));
  overflow: hidden;
}

.hero-img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
}

.hero-placeholder {
  width: 100%;
  height: 100%;
  background: linear-gradient(165deg, var(--fill), var(--bg-elevated) 55%, var(--fill));
}

.hero-fade {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  height: 130px;
  background: linear-gradient(to bottom, transparent, var(--bg));
  pointer-events: none;
}

/* 桌面端：banner 作模糊氛围背景，完整海报以卡片形式并排展示（避免竖版海报全宽裁剪） */
@media (min-width: 1024px) {
  .hero {
    height: 250px;
    min-height: 0;
  }

  .hero-img {
    filter: blur(26px) brightness(0.72) saturate(1.15);
    transform: scale(1.25);
  }

  /* 有海报卡片时：上提跨坐 banner 底沿，海报左、标题右 */
  .info:has(.info-poster) {
    max-width: 828px;
    margin: -140px auto 0;
    padding: 0 24px;
    display: grid;
    grid-template-columns: 186px 1fr;
    column-gap: 28px;
  }

  /* 文字推到 banner 之下，保证落在纯底色区域可读 */
  .info:has(.info-poster) .info-main {
    min-width: 0;
    padding-top: 150px;
  }
}

/* ---------- 信息区 ---------- */
.info {
  position: relative;
  margin-top: -38px;
  padding: 0 20px;
}

/* 完整海报卡片：仅桌面端展示（移动端由 hero 大图承担） */
.info-poster {
  display: none;
}

/* 高度随图片自适应：竖版海报 2:3，横版宣传图也不裁剪 */
.info-poster img {
  display: block;
  width: 100%;
  height: auto;
  object-fit: contain;
}

@media (min-width: 1024px) {
  .info-poster {
    display: block;
    align-self: start;
    border-radius: 16px;
    overflow: hidden;
    background: var(--bg-elevated);
    box-shadow: var(--card-shadow);
  }
}

.info-title {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  line-height: 1.3;
  letter-spacing: 0.2px;
}

.info-subtitle {
  margin: 5px 0 0;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.45;
}

.info-meta,
.info-platforms {
  margin: 10px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.5;
}

.refreshing-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 12px 0 0;
  color: var(--text-tertiary);
  font-size: 12px;
}

.refreshing-spinner {
  width: 12px;
  height: 12px;
  border: 1.5px solid var(--fill);
  border-top-color: var(--text-secondary);
  border-radius: 999px;
  animation: refreshing-rotate 0.8s linear infinite;
}

@keyframes refreshing-rotate {
  to {
    transform: rotate(360deg);
  }
}

.info-actions {
  margin-top: 16px;
}

.collect-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  height: 44px;
  padding: 0 26px;
  border-radius: 999px;
  background: var(--fill);
  color: var(--accent);
  font-size: 15px;
  font-weight: 600;
  transition: background-color 200ms ease, color 200ms ease, opacity 200ms ease;
}

.collect-btn--on {
  background: var(--accent);
  color: #ffffff;
}

.collect-btn:disabled {
  opacity: 0.65;
  cursor: default;
}

.collect-btn svg {
  width: 16px;
  height: 16px;
}

/* ---------- 分组 ---------- */
.section {
  margin-top: 24px;
  padding: 0 16px;
}

/* 桌面端正文分组限宽居中，长文本行宽保持可读 */
@media (min-width: 1024px) {
  .section {
    max-width: 780px;
    margin-left: auto;
    margin-right: auto;
    padding: 0 24px;
  }
}

.section-header {
  margin: 0 0 8px;
  padding: 0 4px;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
}

.synopsis-card {
  padding: 14px 16px;
}

.synopsis {
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  margin: 0;
  white-space: pre-line;
  font-size: 15px;
  line-height: 1.6;
}

.synopsis--expanded {
  display: block;
  -webkit-line-clamp: unset;
}

.expand-btn {
  min-width: 44px;
  min-height: 44px;
  margin-top: 6px;
  padding: 12px 0;
  color: var(--accent);
  font-size: 14px;
  font-weight: 500;
}

.info-row {
  display: grid;
  grid-template-columns: 48px 1fr;
  column-gap: 12px;
  padding: 12px 16px;
}

.info-label {
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.55;
}

.info-value {
  min-width: 0;
  font-size: 14px;
  line-height: 1.55;
  word-break: break-word;
}

.link-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 13px 16px;
  color: var(--accent);
  font-size: 15px;
  font-weight: 500;
}

.link-row:active,
.series-row:active {
  background: var(--fill);
}

.link-arrow {
  color: var(--text-tertiary);
  font-size: 15px;
}

.series-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
}

.series-cover {
  flex-shrink: 0;
  width: 34px;
  height: 46px;
  border-radius: 6px;
  object-fit: cover;
  background: var(--fill);
}

.series-title {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  font-size: 15px;
  line-height: 1.35;
}

.season-pill {
  flex-shrink: 0;
  padding: 3px 9px;
  border-radius: 999px;
  background: var(--fill);
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 500;
  line-height: 1.25;
  white-space: nowrap;
}

.series-year {
  flex-shrink: 0;
  min-width: 30px;
  color: var(--text-tertiary);
  font-size: 13px;
  font-variant-numeric: tabular-nums;
  text-align: right;
}

/* ---------- 加载骨架 ---------- */
.sk {
  border-radius: 8px;
  background: linear-gradient(100deg, var(--fill) 40%, var(--bg-elevated) 50%, var(--fill) 60%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.4s ease-in-out infinite;
}

.sk-hero {
  height: 46vh;
  min-height: 280px;
  margin-top: calc(-1 * (env(safe-area-inset-top) + 50px));
  border-radius: 0;
}

.sk-body {
  padding: 30px 20px 0;
}

.sk-line {
  height: 13px;
  margin-top: 12px;
}

.sk-line--title {
  width: 68%;
  height: 22px;
  margin-top: 0;
}

.sk-line--sub {
  width: 46%;
}

.sk-line--meta {
  width: 56%;
}

.sk-card {
  height: 96px;
  margin-top: 26px;
  border-radius: 16px;
}

@keyframes skeleton-shimmer {
  0% {
    background-position: 200% 0;
  }

  100% {
    background-position: -200% 0;
  }
}

/* ---------- 加载失败 ---------- */
.detail-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
}

.retry-btn {
  padding: 9px 32px;
  border-radius: 999px;
  background: var(--fill);
  color: var(--accent);
  font-size: 15px;
  font-weight: 600;
}
</style>
