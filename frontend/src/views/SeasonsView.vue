<template>
  <div ref="rootEl" class="page seasons-page">
    <div class="seasons-header">
      <NavBar :title="navTitle">
        <template #right>
          <div class="navbar-actions">
            <button
              type="button"
              class="icon-button"
              :class="{ 'is-spinning': navbarButtonSpinning }"
              :disabled="refreshing"
              aria-label="同步该季度数据"
              @click="runRefresh()"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M20 11.5A8 8 0 0 0 6.2 6.3L4 8.5" />
                <path d="M4 3.5v5h5" />
                <path d="M4 12.5a8 8 0 0 0 13.8 5.2l2.2-2.2" />
                <path d="M20 20.5v-5h-5" />
              </svg>
            </button>
            <button type="button" class="year-button" aria-haspopup="dialog" @click="openYearSheet">
              <span>{{ activeYear }}</span>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M6 9.5l6 6 6-6" />
              </svg>
            </button>
          </div>
        </template>
      </NavBar>
      <div class="season-bar">
        <PillMenu v-model="activeSeasonValue" :options="seasonOptions" />
      </div>
      <div class="refresh-indicator" :class="{ 'is-visible': showIndicator }" aria-hidden="true">
        <span class="refresh-spinner" />
      </div>
    </div>

    <div class="seasons-content" :class="{ 'is-released': !pulling }" :style="pullStyle">
      <LoadingSkeleton v-if="loading" :count="12" />

      <EmptyState
        v-else-if="!items.length"
        icon="tv"
        title="该季度暂无数据"
        hint="从数据源同步该季度的番剧列表"
        action="同步该季度数据"
        :action-loading="emptyActionLoading"
        @action="runRefresh()"
      />

      <template v-else>
        <div class="poster-grid">
          <PosterCard
            v-for="anime in items"
            :key="anime.id"
            :anime="anime"
            @collect="onCollect"
            @open="onOpen"
          />
        </div>
        <div ref="sentinelEl" class="grid-sentinel" aria-hidden="true">
          <span v-if="loadingMore" class="more-spinner" />
        </div>
      </template>
    </div>

    <!-- 年份选择弹层：iOS Action Sheet 风格，底部滑入 -->
    <Teleport to="body">
      <Transition name="year-sheet">
        <div v-if="yearSheetVisible" class="year-sheet-mask" @click="closeYearSheet">
          <div class="year-sheet" role="dialog" aria-modal="true" aria-label="选择年份" @click.stop>
            <div class="year-sheet-grabber" aria-hidden="true" />
            <p class="year-sheet-title">选择年份</p>
            <div class="year-grid no-scrollbar">
              <template v-for="group in yearGroups" :key="group.decade">
                <p class="year-group-title">{{ group.decade }}s</p>
                <button
                  v-for="year in group.years"
                  :key="year"
                  type="button"
                  class="year-grid-item"
                  :class="{ 'is-active': year === activeYear }"
                  @click="selectYear(year)"
                >
                  {{ year }}
                </button>
              </template>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onActivated, onBeforeUnmount, onDeactivated, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthSession } from '../auth'
import EmptyState from '../components/EmptyState.vue'
import LoadingSkeleton from '../components/LoadingSkeleton.vue'
import NavBar from '../components/NavBar.vue'
import PillMenu from '../components/PillMenu.vue'
import PosterCard from '../components/PosterCard.vue'
import { fetchAnime, fetchSeasons, syncSeason } from '../services/animeService'
import { collect, uncollect } from '../services/collectionService'
import type { Anime, PaginatedAnime, SeasonSummary } from '../types'

const SEASON_NAMES: Record<number, string> = { 1: '冬', 2: '春', 3: '夏', 4: '秋' }
const PILL_LABELS: Record<number, string> = { 1: '1月新番', 2: '4月新番', 3: '7月新番', 4: '10月新番' }
const PAGE_SIZE = 24
// 年份弹层候选范围：最早 1968 年（与后端校验一致），最新预留到下一年（数据源常提前放出次年预告）
const MIN_YEAR = 1968
const MAX_YEAR_OFFSET = 1
const PULL_THRESHOLD = 60
const PULL_DAMPING = 0.4
const MAX_PULL_DISTANCE = 96

const router = useRouter()
const session = useAuthSession()

const rootEl = ref<HTMLElement | null>(null)
const sentinelEl = ref<HTMLElement | null>(null)

// seasons 仅记录 DB 已同步的季度，用于年份候选与季度数据判断
const seasons = ref<SeasonSummary[]>([])
const initialQuarter = defaultQuarter()
const activeYear = ref(initialQuarter.year)
const activeSeason = ref(initialQuarter.season)
const yearSheetVisible = ref(false)

const items = ref<Anime[]>([])
const total = ref(0)
const page = ref(1)
const loading = ref(true)
const loadingMore = ref(false)
const refreshing = ref(false)
const pulling = ref(false)
const pullDistance = ref(0)

const seasonCache = new Map<string, PaginatedAnime>()
const pendingCollects = new Set<number>()

let requestSeq = 0
let scrollTarget: HTMLElement | Window = window
let loadObserver: IntersectionObserver | null = null
let touchId: number | null = null
let touchStartX = 0
let touchStartY = 0

const navTitle = computed(() => {
  const seasonName = SEASON_NAMES[activeSeason.value]
  return seasonName ? `${activeYear.value} ${seasonName}季新番` : `${activeYear.value} 新番`
})

// 胶囊栏固定展示当前年份的 1/4/7/10 月四个季度
const seasonOptions = [1, 2, 3, 4].map((season) => ({
  value: String(season),
  label: PILL_LABELS[season],
}))

// PillMenu 的 v-model 为字符串，桥接到数字季度
const activeSeasonValue = computed({
  get: () => String(activeSeason.value),
  set: (value: string) => {
    activeSeason.value = Number(value)
  },
})

// 可选年份 = 下一年份至 1968 全量年份 ∪ DB 已同步季度年份，去重降序
const availableYears = computed(() => {
  const currentYear = new Date().getFullYear()
  const years = new Set<number>()
  for (let year = currentYear + MAX_YEAR_OFFSET; year >= MIN_YEAR; year -= 1) {
    years.add(year)
  }
  for (const item of seasons.value) {
    years.add(item.year)
  }
  return [...years].sort((a, b) => b - a)
})

// 年份按十年分组，弹层内展示年代标题便于快速定位
const yearGroups = computed(() => {
  const groups: { decade: number; years: number[] }[] = []
  for (const year of availableYears.value) {
    const decade = Math.floor(year / 10) * 10
    const last = groups[groups.length - 1]
    if (last && last.decade === decade) {
      last.years.push(year)
    } else {
      groups.push({ decade, years: [year] })
    }
  }
  return groups
})

// 刷新来源：下拉手势 / 显式按钮（NavBar 刷新、空态同步）。
// 任一时刻只展示一处刷新标志：下拉 → 顶部指示器；按钮 → 按钮自身转圈。
const refreshSource = ref<'pull' | 'manual'>('manual')
const isPullRefresh = computed(() => refreshSource.value === 'pull')

const showIndicator = computed(() => pulling.value || (refreshing.value && isPullRefresh.value))

const navbarButtonSpinning = computed(() => refreshing.value && !isPullRefresh.value)

const emptyActionLoading = computed(() => refreshing.value && !isPullRefresh.value)

const pullStyle = computed(() => ({
  transform: `translateY(${pullDistance.value}px)`,
}))

watch([activeYear, activeSeason], () => {
  scrollToTop()
  void loadSeason(activeYear.value, activeSeason.value)
})

watch(
  () => items.value.length,
  () => {
    void nextTick(reattachObserver)
  }
)

function seasonCacheKey(year: number, season: number): string {
  return `${year}-${season}`
}

function defaultQuarter(): { year: number; season: number } {
  const status = session.state.status
  const now = new Date()
  // 年份/季度为 null（自动）时跟随当前日期
  return {
    year: status?.default_search_year ?? now.getFullYear(),
    season: status?.default_search_season ?? Math.floor(now.getMonth() / 3) + 1
  }
}

async function loadSeasonOptions() {
  try {
    seasons.value = await fetchSeasons()
  } catch (error) {
    console.error('加载季度列表失败：', error)
  }
}

// 选择年份：无当前季度数据时自动切到该年最新有数据的季度（无数据则 Q1，可下拉刷新同步）
function selectYear(year: number) {
  closeYearSheet()
  if (year === activeYear.value) {
    return
  }
  activeYear.value = year
  const syncedSeasons = seasons.value
    .filter((item) => item.year === year && item.count > 0)
    .map((item) => item.season)
  if (!syncedSeasons.includes(activeSeason.value)) {
    activeSeason.value = syncedSeasons.length ? Math.max(...syncedSeasons) : 1
  }
}

async function openYearSheet() {
  yearSheetVisible.value = true
  await nextTick()
  // 当前选中年份滚动到可见区域（历史年份较多时便于定位）
  document.querySelector<HTMLElement>('.year-grid-item.is-active')?.scrollIntoView({ block: 'center' })
}

function closeYearSheet() {
  yearSheetVisible.value = false
}

async function loadSeason(year: number, season: number) {
  const seq = ++requestSeq
  const key = seasonCacheKey(year, season)
  loadingMore.value = false

  const cached = seasonCache.get(key)
  if (cached) {
    items.value = cached.items.slice()
    total.value = cached.total
    page.value = 1
    loading.value = false
    return
  }

  loading.value = true
  items.value = []
  total.value = 0
  page.value = 1
  try {
    const data = await fetchAnime({ year, season, page: 1, page_size: PAGE_SIZE })
    if (seq !== requestSeq) {
      return
    }
    items.value = data.items
    total.value = data.total
    page.value = data.page || 1
    seasonCache.set(key, { ...data, items: data.items.slice() })
  } catch (error) {
    console.error('加载季度番剧失败：', error)
  } finally {
    if (seq === requestSeq) {
      loading.value = false
    }
  }
}

function canLoadMore(): boolean {
  return !loading.value && !loadingMore.value && !refreshing.value && page.value * PAGE_SIZE < total.value
}

async function loadMore() {
  if (!canLoadMore()) {
    return
  }
  const seq = requestSeq
  const nextPage = page.value + 1
  const year = activeYear.value
  const season = activeSeason.value
  loadingMore.value = true
  try {
    const data = await fetchAnime({ year, season, page: nextPage, page_size: PAGE_SIZE })
    if (seq !== requestSeq) {
      return
    }
    items.value.push(...data.items)
    page.value = data.page || nextPage
    total.value = data.total
  } catch (error) {
    console.error('加载更多番剧失败：', error)
  } finally {
    if (seq === requestSeq) {
      loadingMore.value = false
    }
  }
}

async function runRefresh(fromPull = false) {
  if (refreshing.value) {
    return
  }
  const seq = ++requestSeq
  const year = activeYear.value
  const season = activeSeason.value
  refreshSource.value = fromPull ? 'pull' : 'manual'
  refreshing.value = true
  pulling.value = false
  // 下拉刷新保持内容下沉（iOS 惯例）；按钮触发则内容不动，仅按钮转圈
  pullDistance.value = fromPull ? PULL_THRESHOLD : 0
  try {
    const data = await syncSeason(year, season)
    if (seq !== requestSeq) {
      return
    }
    items.value = data.items
    total.value = data.total
    page.value = data.page || 1
    seasonCache.set(seasonCacheKey(year, season), { ...data, items: data.items.slice() })
    void loadSeasonOptions()
  } catch (error) {
    console.error('同步季度数据失败：', error)
  } finally {
    refreshing.value = false
    pullDistance.value = 0
    if (seq === requestSeq) {
      loading.value = false
    }
  }
}

async function onCollect(anime: Anime) {
  if (pendingCollects.has(anime.id)) {
    return
  }
  const nextCollected = !anime.is_collected
  anime.is_collected = nextCollected
  pendingCollects.add(anime.id)
  try {
    if (nextCollected) {
      await collect(anime.id)
    } else {
      await uncollect(anime.id)
    }
  } catch (error) {
    anime.is_collected = !nextCollected
    console.error('更新收藏状态失败：', error)
  } finally {
    pendingCollects.delete(anime.id)
  }
}

function onOpen(anime: Anime) {
  void router.push(`/anime/${anime.id}`)
}

function findScrollTarget(): HTMLElement | Window {
  let el = rootEl.value?.parentElement ?? null
  while (el) {
    const { overflowY } = window.getComputedStyle(el)
    if (overflowY === 'auto' || overflowY === 'scroll') {
      return el
    }
    el = el.parentElement
  }
  return window
}

function getScrollTop(): number {
  return scrollTarget instanceof HTMLElement ? scrollTarget.scrollTop : window.scrollY
}

function scrollToTop() {
  if (scrollTarget instanceof HTMLElement) {
    scrollTarget.scrollTop = 0
  } else {
    window.scrollTo(0, 0)
  }
}

function findTrackedTouch(list: TouchList): Touch | null {
  if (touchId === null) {
    return null
  }
  for (let index = 0; index < list.length; index += 1) {
    if (list[index].identifier === touchId) {
      return list[index]
    }
  }
  return null
}

function cancelPull() {
  touchId = null
  pulling.value = false
  pullDistance.value = 0
}

function onTouchStart(event: TouchEvent) {
  if (pulling.value || refreshing.value || touchId !== null) {
    return
  }
  if (event.touches.length !== 1 || getScrollTop() > 0) {
    return
  }
  const touch = event.changedTouches[0]
  touchId = touch.identifier
  touchStartX = touch.clientX
  touchStartY = touch.clientY
  pulling.value = true
}

function onTouchMove(event: TouchEvent) {
  if (touchId === null) {
    return
  }
  const touch = findTrackedTouch(event.changedTouches)
  if (!touch) {
    return
  }
  const deltaX = touch.clientX - touchStartX
  const deltaY = touch.clientY - touchStartY
  if (deltaY <= 0) {
    pullDistance.value = 0
    return
  }
  if (getScrollTop() > 0 || Math.abs(deltaX) > deltaY) {
    cancelPull()
    return
  }
  event.preventDefault()
  pullDistance.value = Math.min(deltaY * PULL_DAMPING, MAX_PULL_DISTANCE)
}

function onTouchEnd(event: TouchEvent) {
  if (touchId === null) {
    return
  }
  if (!findTrackedTouch(event.changedTouches)) {
    return
  }
  touchId = null
  pulling.value = false
  if (pullDistance.value >= PULL_THRESHOLD && !refreshing.value) {
    void runRefresh(true)
    return
  }
  if (!refreshing.value) {
    pullDistance.value = 0
  }
}

function onTouchCancel(event: TouchEvent) {
  if (touchId === null) {
    return
  }
  if (!findTrackedTouch(event.changedTouches)) {
    return
  }
  cancelPull()
}

function attachTouchListeners() {
  const el = rootEl.value
  if (!el) {
    return
  }
  el.addEventListener('touchstart', onTouchStart, { passive: true })
  el.addEventListener('touchmove', onTouchMove, { passive: false })
  el.addEventListener('touchend', onTouchEnd, { passive: true })
  el.addEventListener('touchcancel', onTouchCancel, { passive: true })
}

function detachTouchListeners() {
  const el = rootEl.value
  if (!el) {
    return
  }
  el.removeEventListener('touchstart', onTouchStart)
  el.removeEventListener('touchmove', onTouchMove)
  el.removeEventListener('touchend', onTouchEnd)
  el.removeEventListener('touchcancel', onTouchCancel)
}

function createObserver() {
  loadObserver = new IntersectionObserver(
    (entries) => {
      if (entries.some((entry) => entry.isIntersecting)) {
        void loadMore()
      }
    },
    { rootMargin: '320px 0px' }
  )
  reattachObserver()
}

function reattachObserver() {
  if (!loadObserver || !sentinelEl.value) {
    return
  }
  loadObserver.disconnect()
  loadObserver.observe(sentinelEl.value)
}

onMounted(() => {
  scrollTarget = findScrollTarget()
  attachTouchListeners()
  createObserver()
  void loadSeason(activeYear.value, activeSeason.value)
  void loadSeasonOptions()
})

// KeepAlive 失活时记录滚动位置（滚动容器 .app-body 在组件外，切到详情页后会被改写）
let savedScrollTop = 0

onDeactivated(() => {
  savedScrollTop = scrollTarget instanceof HTMLElement ? scrollTarget.scrollTop : window.scrollY
})

// 激活时恢复：等 DOM 重新插入并渲染后再写回滚动位置
onActivated(() => {
  void nextTick().then(() => {
    requestAnimationFrame(() => {
      if (scrollTarget instanceof HTMLElement) {
        scrollTarget.scrollTop = savedScrollTop
      } else {
        window.scrollTo({ top: savedScrollTop })
      }
    })
  })
})

onBeforeUnmount(() => {
  requestSeq += 1
  detachTouchListeners()
  loadObserver?.disconnect()
  loadObserver = null
})
</script>

<style scoped>
.seasons-page {
  min-height: 100%;
  padding-bottom: 24px;
}

/* 吸顶头部：NavBar 大标题收缩时，胶囊栏跟随上移，整体钉在顶部 */
.seasons-header {
  position: sticky;
  top: 0;
  z-index: 100;
}

.season-bar {
  padding-bottom: 8px;
  background: linear-gradient(to bottom, var(--bg) calc(100% - 14px), transparent);
}

/* NavBar 右侧年份切换按钮：iOS 胶囊 + 半透明背景 + 下拉箭头 */
.navbar-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

/* 触控区 44×44（iOS HIG 最小标准），视觉圆 30px 由 ::before 绘制（内缩 7px） */
.icon-button {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  padding: 0;
  border: none;
  border-radius: 999px;
  background: transparent;
  color: var(--accent);
  cursor: pointer;
  transition: opacity 200ms ease;
}

.icon-button::before {
  content: '';
  position: absolute;
  inset: 7px;
  border-radius: 999px;
  background: var(--fill);
}

.icon-button:disabled {
  opacity: 0.55;
  cursor: default;
}

.icon-button svg {
  position: relative;
  width: 16px;
  height: 16px;
}

.icon-button.is-spinning svg {
  animation: icon-spin 0.8s linear infinite;
}

@keyframes icon-spin {
  to {
    transform: rotate(360deg);
  }
}

/* 触控区高度 44px（iOS HIG 最小标准），视觉胶囊 30px 由 ::before 绘制（上下内缩 7px） */
.year-button {
  position: relative;
  /* 创建层叠上下文，让 ::before 沉到文字下方 */
  isolation: isolate;
  display: inline-flex;
  align-items: center;
  gap: 2px;
  height: 44px;
  padding: 0 11px;
  border-radius: 999px;
  background: transparent;
  color: var(--accent);
  font-size: 15px;
  font-weight: 600;
  line-height: 1;
}

.year-button::before {
  content: '';
  position: absolute;
  z-index: -1;
  inset: 7px 0;
  border-radius: 999px;
  background: var(--fill);
}

.year-button svg {
  position: relative;
  width: 12px;
  height: 12px;
}

/* 年份弹层遮罩：点击空白处关闭 */
.year-sheet-mask {
  position: fixed;
  inset: 0;
  z-index: 300;
  display: flex;
  align-items: flex-end;
  background: rgba(0, 0, 0, 0.4);
  touch-action: none;
}

/* 深色模式下遮罩加深 */
@media (prefers-color-scheme: dark) {
  .year-sheet-mask {
    background: rgba(0, 0, 0, 0.55);
  }
}

/* 弹层本体：底部滑入、圆角顶部、毛玻璃半透明背景（随系统深浅色） */
.year-sheet {
  width: 100%;
  padding: 6px 18px calc(env(safe-area-inset-bottom) + 14px);
  border-radius: 16px 16px 0 0;
  background: var(--blur-bg);
  box-shadow: 0 -6px 32px rgba(0, 0, 0, 0.16);
  -webkit-backdrop-filter: blur(15px) saturate(180%);
  backdrop-filter: blur(15px) saturate(180%);
}

/* 桌面端：改为居中悬浮面板，全圆角、更宽、隐藏底部安全区留白 */
@media (min-width: 1024px) {
  .year-sheet-mask {
    align-items: center;
    justify-content: center;
    padding: 32px;
  }

  .year-sheet {
    width: 640px;
    max-width: 100%;
    max-height: min(70vh, 640px);
    display: flex;
    flex-direction: column;
    padding: 20px 24px 18px;
    border-radius: 16px;
    box-shadow: 0 18px 60px rgba(0, 0, 0, 0.28);
  }

  /* 底部抓手仅移动端有意义 */
  .year-sheet-grabber {
    display: none;
  }

  .year-sheet-title {
    margin: 0 0 14px;
    text-align: left;
    font-size: 15px;
    font-weight: 600;
    color: var(--text-primary);
  }

  .year-grid {
    grid-template-columns: repeat(6, 1fr);
    max-height: none;
    flex: 1;
    gap: 12px;
    overscroll-behavior: auto;
  }

  .year-grid-item {
    height: 38px;
    cursor: pointer;
  }
}

/* 顶部抓手 */
.year-sheet-grabber {
  width: 36px;
  height: 5px;
  margin: 4px auto 10px;
  border-radius: 999px;
  background: var(--separator);
}

.year-sheet-title {
  margin: 0 0 12px;
  color: var(--text-secondary);
  font-size: 13px;
  text-align: center;
}

/* 年份网格：4 列，可滚动，滚动不外溢 */
.year-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  max-height: 46vh;
  padding: 2px 2px 4px;
  overflow-y: auto;
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
  touch-action: pan-y;
}

/* 年代分组标题：横跨整行 */
.year-group-title {
  grid-column: 1 / -1;
  margin: 10px 0 0;
  color: var(--text-tertiary);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.4px;
}

.year-group-title:first-child {
  margin-top: 0;
}

.year-grid-item {
  height: 44px;
  border-radius: 12px;
  background: var(--fill);
  color: var(--text-primary);
  font-size: 16px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  transition:
    background-color 200ms ease,
    color 200ms ease;
}

.year-grid-item.is-active {
  background: var(--accent);
  color: #fff;
}

/* 弹层过渡：遮罩淡入淡出 + 面板底部滑入滑出 */
.year-sheet-enter-active,
.year-sheet-leave-active {
  transition: opacity 260ms ease;
}

.year-sheet-enter-active .year-sheet,
.year-sheet-leave-active .year-sheet {
  transition: transform 380ms cubic-bezier(0.32, 0.72, 0, 1);
}

.year-sheet-enter-from,
.year-sheet-leave-to {
  opacity: 0;
}

.year-sheet-enter-from .year-sheet,
.year-sheet-leave-to .year-sheet {
  transform: translateY(100%);
}

/* 桌面端弹层居中显示，改为缩放淡入（macOS 面板风格） */
@media (min-width: 1024px) {
  .year-sheet-enter-from .year-sheet,
  .year-sheet-leave-to .year-sheet {
    transform: scale(0.96);
  }

  .year-sheet-enter-active .year-sheet,
  .year-sheet-leave-active .year-sheet {
    transition: transform 220ms cubic-bezier(0.32, 0.72, 0, 1);
  }
}

/* 下拉刷新指示器：固定在吸顶头部下方居中的小菊花 */
.refresh-indicator {
  position: absolute;
  top: 100%;
  left: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  margin-top: 2px;
  border-radius: 999px;
  background: var(--blur-bg);
  box-shadow: var(--card-shadow);
  -webkit-backdrop-filter: blur(12px) saturate(180%);
  backdrop-filter: blur(12px) saturate(180%);
  opacity: 0;
  transform: translateX(-50%) scale(0.5);
  transition:
    opacity 200ms ease,
    transform 200ms ease;
  pointer-events: none;
}

.refresh-indicator.is-visible {
  opacity: 1;
  transform: translateX(-50%) scale(1);
}

.refresh-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--fill);
  border-top-color: var(--accent);
  border-radius: 999px;
  animation: refresh-spinner-rotate 0.75s linear infinite;
}

@keyframes refresh-spinner-rotate {
  to {
    transform: rotate(360deg);
  }
}

/* 内容区：下拉时跟随手指位移（无过渡），松手后弹性回位 */
.seasons-content.is-released {
  transition: transform 240ms cubic-bezier(0.32, 0.72, 0, 1);
}

/* 海报墙：3 列栅格，内容后退、海报前进 */
.poster-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  padding: 16px 16px 4px;
}

/* 桌面端随浏览器宽度增加列数，海报墙铺满内容区 */
@media (min-width: 640px) {
  .poster-grid {
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    padding: 20px 20px 6px;
  }

  .seasons-page :deep(.loading-skeleton) {
    grid-template-columns: repeat(4, 1fr);
    gap: 16px 14px;
    padding: 20px;
  }
}

@media (min-width: 1024px) {
  .poster-grid {
    grid-template-columns: repeat(6, 1fr);
    gap: 18px;
  }

  .seasons-page :deep(.loading-skeleton) {
    grid-template-columns: repeat(6, 1fr);
    gap: 20px 18px;
  }
}

@media (min-width: 1600px) {
  .poster-grid {
    grid-template-columns: repeat(8, 1fr);
  }

  .seasons-page :deep(.loading-skeleton) {
    grid-template-columns: repeat(8, 1fr);
  }
}

.seasons-page :deep(.poster-card-cover) {
  box-shadow: var(--card-shadow);
}

/* 骨架屏对齐海报墙栅格，避免加载完成时布局跳动 */
.seasons-page :deep(.loading-skeleton) {
  grid-template-columns: repeat(3, 1fr);
  gap: 14px 10px;
  padding: 16px 16px 0;
}

.grid-sentinel {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 48px;
}

.more-spinner {
  width: 22px;
  height: 22px;
  border: 2px solid var(--fill);
  border-top-color: var(--text-tertiary);
  border-radius: 999px;
  animation: more-spinner-rotate 0.8s linear infinite;
}

@keyframes more-spinner-rotate {
  to {
    transform: rotate(360deg);
  }
}
</style>
