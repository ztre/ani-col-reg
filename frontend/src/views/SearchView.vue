<template>
  <div class="page">
    <h1 class="search-heading">搜索</h1>

    <header ref="headerRoot" class="search-header frosted" :class="{ 'is-stuck': stuck }">
      <div class="search-field">
        <svg
          class="search-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <circle cx="11" cy="11" r="7.5" />
          <path d="m20.5 20.5-4.6-4.6" />
        </svg>
        <input
          v-model="query"
          class="search-input"
          type="search"
          placeholder="搜索动漫或系列"
          autocomplete="off"
          autocorrect="off"
          autocapitalize="none"
          spellcheck="false"
          enterkeyhint="search"
          @keydown.enter="onEnter"
        />
        <span v-if="searching" class="search-spinner" aria-hidden="true" />
        <button
          v-else-if="query"
          type="button"
          class="search-clear"
          aria-label="清除搜索内容"
          @click="clearQuery"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" aria-hidden="true">
            <path d="M6 6l12 12M18 6L6 18" />
          </svg>
        </button>
      </div>
    </header>

    <div v-if="searching && !results.length" class="list-section">
      <div class="list-group" aria-hidden="true">
        <div v-for="index in 5" :key="index" class="skeleton-row">
          <div class="skeleton skeleton-thumb" />
          <div class="skeleton-row-lines">
            <div class="skeleton skeleton-line skeleton-line--wide" />
            <div class="skeleton skeleton-line skeleton-line--narrow" />
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="searchError" class="state-section">
      <EmptyState icon="warning" title="搜索失败" hint="请检查网络连接后重试" />
      <button type="button" class="retry-button" @click="searchNow">重试</button>
    </div>

    <!-- 双段结果：本地收藏库 + 数据源，两节互不影响 -->
    <div v-else-if="searched && hasResultSection" class="list-section">
      <!-- 第一节：本地收藏库（现有系列分组结果） -->
      <template v-if="results.length">
        <p class="section-label">本地收藏库</p>
        <div class="list-group">
          <SeriesRow v-for="group in results" :key="group.series_key" :group="group" />
        </div>
      </template>

      <!-- 第二节：数据源 YourAnimes（实时检索，点击导入） -->
      <template v-if="sourceVisible">
        <p class="section-label">数据源 YourAnimes</p>
        <div v-if="sourceSearching" class="source-loading">
          <span class="source-loading-spinner" aria-hidden="true" />
        </div>
        <p v-else-if="sourceError" class="source-hint">数据源搜索暂不可用</p>
        <div v-else class="list-group">
          <button
            v-for="item in sourceItems"
            :key="item.source_id"
            type="button"
            class="source-item"
            :class="{ 'is-local': item.isCollected }"
            :disabled="importingId !== null"
            :aria-label="item.isCollected ? '查看详情' : '收藏'"
            @click="onSourceItemClick(item)"
          >
            <span class="source-cover">
              <img
                v-if="item.cover_url && !failedCovers.has(item.source_id)"
                class="source-cover-image"
                :src="item.cover_url"
                :alt="item.title"
                loading="lazy"
                @error="markCoverFailed(item.source_id)"
              />
              <span v-else class="source-cover-fallback">{{ coverInitial(item.title) }}</span>
            </span>
            <span class="source-body">
              <span class="source-title">{{ item.title }}</span>
              <span class="source-sub" :class="{ 'is-error': importFailedId === item.source_id }">
                {{ importFailedId === item.source_id ? '操作失败，请重试' : item.title_jp }}
              </span>
            </span>
            <span v-if="importingId === item.source_id" class="source-spinner" aria-hidden="true" />
            <!-- 已收藏：对勾标识，点击直达详情 -->
            <svg
              v-else-if="item.isCollected"
              class="source-added"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2.4"
              stroke-linecap="round"
              stroke-linejoin="round"
              aria-hidden="true"
            >
              <path d="M4.5 12.5l5 5L19.5 7" />
            </svg>
            <!-- 未收藏：加号，点击收藏（在库直接收藏，未在库导入并收藏） -->
            <svg
              v-else
              class="source-add"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2.2"
              stroke-linecap="round"
              aria-hidden="true"
            >
              <path d="M12 5v14M5 12h14" />
            </svg>
          </button>
        </div>
      </template>
    </div>

    <!-- 空态：本地与源都无结果 -->
    <EmptyState
      v-else-if="searched"
      icon="search"
      title="没有找到相关内容"
      hint="换个关键词试试看"
    />

    <EmptyState v-else icon="search" title="搜索你感兴趣的动漫" />
  </div>
</template>

<script setup lang="ts">
import { computed, onActivated, onBeforeUnmount, onDeactivated, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import EmptyState from '../components/EmptyState.vue'
import SeriesRow from '../components/SeriesRow.vue'
import {
  collect,
  fetchCollectedSeries,
  fetchSourceSearch,
  importFromSource,
  searchSeries,
} from '../services/collectionService'
import type { SeriesGroup, SourceSearchItem } from '../types'

const DEBOUNCE_MS = 300
const STUCK_THRESHOLD = 40

const router = useRouter()

const query = ref('')
const results = ref<SeriesGroup[]>([])
const searching = ref(false)
const searched = ref(false)
const searchError = ref(false)
const stuck = ref(false)

// 数据源搜索状态（独立于本地搜索，失败互不影响）
const sourceResults = ref<SourceSearchItem[]>([])
const sourceSearching = ref(false)
const sourceError = ref(false)
const importingId = ref<string | null>(null)
const importFailedId = ref<string | null>(null)
const failedCovers = ref(new Set<string>())

const headerRoot = ref<HTMLElement | null>(null)

let debounceTimer: number | undefined
let requestSeq = 0
let scrollTarget: HTMLElement | Window = window

// 本地库已有的条目：source_id → 本地 anime_id。
// 用本地搜索结果 + 全量收藏共同构建（收藏页接口含 collected 条目，
// 覆盖“标题未命中搜索但已收藏/已在库”的情况），避免对已导入条目重复显示加号。
const localAnimeBySourceId = ref(new Map<string, number>())

// 已收藏的本地 anime_id 集合（区别于“仅在库未收藏”）
const collectedAnimeIds = ref(new Set<number>())

const collectedGroups = ref<SeriesGroup[]>([])

function rebuildLocalIndex() {
  const index = new Map<string, number>()
  for (const group of results.value) {
    for (const entry of group.entries) {
      if (entry.source_id) {
        index.set(entry.source_id, entry.id)
      }
    }
  }
  const collected = new Set<number>()
  for (const group of collectedGroups.value) {
    for (const entry of group.entries) {
      if (entry.source_id) {
        index.set(entry.source_id, entry.id)
      }
      collected.add(entry.id)
    }
  }
  localAnimeBySourceId.value = index
  collectedAnimeIds.value = collected
}

// 源结果三态：未在库（加号导入+收藏）/ 在库未收藏（加号直接收藏）/ 已收藏（对勾跳详情）
const sourceItems = computed(() =>
  sourceResults.value.map((item) => {
    const localAnimeId = localAnimeBySourceId.value.get(item.source_id) ?? null
    return {
      ...item,
      localAnimeId,
      isCollected: localAnimeId !== null && collectedAnimeIds.value.has(localAnimeId),
    }
  })
)

// 源结果区域可见：加载中 / 出错 / 有条目任一成立
const sourceVisible = computed(
  () => sourceSearching.value || sourceError.value || sourceItems.value.length > 0
)

// 双段结果整体可见（本地或源任一侧有内容）
const hasResultSection = computed(() => results.value.length > 0 || sourceVisible.value)

function resetResults() {
  requestSeq += 1
  results.value = []
  searching.value = false
  searched.value = false
  searchError.value = false
  sourceResults.value = []
  sourceSearching.value = false
  sourceError.value = false
  importingId.value = null
  importFailedId.value = null
  failedCovers.value = new Set()
}

watch(query, (value) => {
  window.clearTimeout(debounceTimer)
  const keyword = value.trim()
  if (!keyword) {
    resetResults()
    return
  }
  debounceTimer = window.setTimeout(() => runSearch(keyword), DEBOUNCE_MS)
})

function onEnter(event: KeyboardEvent) {
  if (event.isComposing) {
    return
  }
  searchNow()
}

function searchNow() {
  window.clearTimeout(debounceTimer)
  const keyword = query.value.trim()
  if (keyword) {
    runSearch(keyword)
  }
}

function clearQuery() {
  query.value = ''
}

// 双源并行搜索：本地收藏库与数据源同时请求，各自容错、互不阻塞
async function runSearch(keyword: string) {
  const current = ++requestSeq
  searching.value = true
  searchError.value = false
  sourceSearching.value = true
  sourceError.value = false
  importFailedId.value = null

  const localTask = (async () => {
    try {
      const groups = await searchSeries(keyword)
      if (current !== requestSeq) {
        return
      }
      results.value = groups
      rebuildLocalIndex()
      searched.value = true
    } catch {
      if (current !== requestSeq) {
        return
      }
      results.value = []
      searched.value = true
      searchError.value = true
    } finally {
      if (current === requestSeq) {
        searching.value = false
      }
    }
  })()

  const sourceTask = (async () => {
    try {
      const data = await fetchSourceSearch(keyword)
      if (current !== requestSeq) {
        return
      }
      sourceResults.value = data.items
    } catch {
      if (current !== requestSeq) {
        return
      }
      sourceResults.value = []
      sourceError.value = true
    } finally {
      if (current === requestSeq) {
        sourceSearching.value = false
      }
    }
  })()

  await Promise.all([localTask, sourceTask])
}

function markCoverFailed(sourceId: string) {
  failedCovers.value = new Set(failedCovers.value).add(sourceId)
}

function coverInitial(title: string): string {
  return title.trim().charAt(0) || '?'
}

// 源条目点击分流：已收藏 → 直达详情；在库未收藏 → 直接收藏；未在库 → 导入并收藏
type SourceDisplayItem = SourceSearchItem & { localAnimeId: number | null; isCollected: boolean }

function onSourceItemClick(item: SourceDisplayItem) {
  if (item.isCollected) {
    router.push(`/anime/${item.localAnimeId}`)
    return
  }
  if (item.localAnimeId !== null) {
    // 已在库未收藏：直接收藏，原地转对勾
    void collectOnly(item)
    return
  }
  void importAndCollect(item)
}

// 在库未收藏条目：加入收藏并更新状态
async function collectOnly(item: SourceDisplayItem) {
  if (importingId.value) {
    return
  }
  importingId.value = item.source_id
  importFailedId.value = null
  try {
    await collect(item.localAnimeId as number)
    collectedAnimeIds.value = new Set(collectedAnimeIds.value).add(item.localAnimeId as number)
  } catch (error) {
    console.error('收藏失败：', error)
    importFailedId.value = item.source_id
  } finally {
    importingId.value = null
  }
}

// 未在库条目：导入本地库（幂等）并直接收藏，加号原地转对勾，不跳详情页
async function importAndCollect(item: SourceDisplayItem) {
  if (importingId.value) {
    return
  }
  importingId.value = item.source_id
  importFailedId.value = null
  try {
    const data = await importFromSource(item.source_id)
    // 记入本地索引并立即收藏
    localAnimeBySourceId.value = new Map(localAnimeBySourceId.value).set(item.source_id, data.anime_id)
    await collect(data.anime_id)
    collectedAnimeIds.value = new Set(collectedAnimeIds.value).add(data.anime_id)
  } catch (error) {
    console.error('导入并收藏失败：', error)
    importFailedId.value = item.source_id
  } finally {
    importingId.value = null
  }
}

function onScroll() {
  const scrollTop = scrollTarget instanceof HTMLElement ? scrollTarget.scrollTop : window.scrollY
  stuck.value = scrollTop > STUCK_THRESHOLD
}

onMounted(() => {
  // 加载全量收藏系列，构建 source_id 索引用于“已收录”过滤
  fetchCollectedSeries()
    .then((groups) => {
      collectedGroups.value = groups
      rebuildLocalIndex()
    })
    .catch(() => {
      // 收藏列表拉取失败不阻塞搜索，仅“已收录”过滤可能不全
    })

  let el = headerRoot.value?.parentElement ?? null
  while (el) {
    const { overflowY } = window.getComputedStyle(el)
    if (overflowY === 'auto' || overflowY === 'scroll') {
      scrollTarget = el
      break
    }
    el = el.parentElement
  }
  scrollTarget.addEventListener('scroll', onScroll, { passive: true })
  onScroll()
})

// keep-alive 缓存态下用 deactivated 清理，避免残留滚动监听
onDeactivated(() => {
  window.clearTimeout(debounceTimer)
  requestSeq += 1
})

// keep-alive 返回本页时刷新收藏索引：详情/导视页可能已新增收藏或导入，
// 否则已入库作品会继续显示"待新增"加号
onActivated(() => {
  fetchCollectedSeries()
    .then((groups) => {
      collectedGroups.value = groups
      rebuildLocalIndex()
    })
    .catch(() => {
      // 拉取失败保留旧索引，仅状态标记可能滞后
    })
})

onBeforeUnmount(() => {
  window.clearTimeout(debounceTimer)
  requestSeq += 1
  scrollTarget.removeEventListener('scroll', onScroll)
})
</script>

<style scoped>
.page {
  padding-bottom: 24px;
}

.search-heading {
  margin: 0;
  padding: calc(env(safe-area-inset-top) + 6px) 16px 6px;
  font-size: 34px;
  font-weight: 700;
  line-height: 44px;
  letter-spacing: 0.2px;
}

.search-header {
  position: sticky;
  top: 0;
  z-index: 100;
  padding: 6px 16px 8px;
  border-bottom: 0.5px solid transparent;
  transition: border-color 240ms ease;
}

/* 桌面端搜索栏与结果列表同宽对齐 */
@media (min-width: 1024px) {
  .search-header {
    max-width: 828px; /* 780 + 左右 padding */
    margin: 0 auto;
    padding: 10px 24px 12px;
  }
}

.search-header.is-stuck {
  border-bottom-color: var(--separator);
}

.search-field {
  display: flex;
  align-items: center;
  gap: 7px;
  height: 36px;
  padding: 0 10px;
  border-radius: 10px;
  background: var(--fill);
}

.search-icon {
  flex-shrink: 0;
  width: 15px;
  height: 15px;
  color: var(--text-tertiary);
}

.search-input {
  flex: 1;
  min-width: 0;
  height: 100%;
  border: none;
  outline: none;
  background: transparent;
  color: var(--text-primary);
  font-size: 16px;
}

.search-input::placeholder {
  color: var(--text-tertiary);
}

.search-input::-webkit-search-cancel-button {
  display: none;
}

/* 触控区 44×44（iOS HIG 最小标准），负 margin 抵消超出 36px 输入框的部分，视觉保持紧凑 */
.search-clear {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  margin: -4px -10px -4px -8px;
  color: var(--text-tertiary);
  transition: opacity 200ms ease;
}

.search-clear svg {
  width: 14px;
  height: 14px;
}

.search-clear:active {
  opacity: 0.6;
}

.search-spinner {
  flex-shrink: 0;
  width: 16px;
  height: 16px;
  border: 2px solid var(--fill);
  border-top-color: var(--text-tertiary);
  border-radius: 999px;
  animation: search-spinner-rotate 0.8s linear infinite;
}

@keyframes search-spinner-rotate {
  to {
    transform: rotate(360deg);
  }
}

.list-section {
  padding: 6px 16px 0;
}

/* 双段结果的节间距 */
.list-section > * + * {
  margin-top: 14px;
}

/* iOS 分节小标题：13px 半透明 */
.section-label {
  margin: 0 0 8px;
  color: var(--text-tertiary);
  font-size: 13px;
  font-weight: 500;
  line-height: 1;
}

/* 源区域加载中：小菊花占位 */
.source-loading {
  display: flex;
  justify-content: center;
  padding: 12px 0;
}

.source-loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--fill);
  border-top-color: var(--text-tertiary);
  border-radius: 999px;
  animation: source-spinner-rotate 0.8s linear infinite;
}

/* 源搜索不可用：一行浅色提示，不影响本地结果 */
.source-hint {
  margin: 0;
  padding: 2px 0 10px;
  color: var(--text-tertiary);
  font-size: 13px;
  line-height: 1.4;
}

/* 源结果行：紧凑卡片行（高约 72px），点击导入本地库 */
.source-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 6px 16px;
  text-align: left;
  cursor: pointer;
  transition: background-color 120ms ease;
}

.source-item:active {
  background: var(--fill);
}

.source-item:disabled {
  cursor: default;
}

/* 封面缩略图：2:3，圆角 10px */
.source-cover {
  flex-shrink: 0;
  width: 40px;
  height: 60px;
  border-radius: 10px;
  overflow: hidden;
  background: var(--fill);
}

.source-cover-image {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.source-cover-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: linear-gradient(145deg, var(--fill), var(--bg-elevated));
  color: var(--text-tertiary);
  font-size: 15px;
  font-weight: 600;
}

.source-body {
  flex: 1;
  min-width: 0;
}

.source-title {
  display: block;
  overflow: hidden;
  color: var(--text-primary);
  font-size: 15px;
  font-weight: 600;
  line-height: 1.3;
  white-space: nowrap;
  text-overflow: ellipsis;
}

/* 副标题：13px 灰；导入失败时替换为提示文案 */
.source-sub {
  display: block;
  margin-top: 2px;
  overflow: hidden;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.4;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.source-sub.is-error {
  color: #ff3b30;
}

@media (prefers-color-scheme: dark) {
  .source-sub.is-error {
    color: #ff453a;
  }
}

/* 导入中：行内小菊花 */
.source-spinner {
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  border: 2px solid var(--fill);
  border-top-color: var(--accent);
  border-radius: 999px;
  animation: source-spinner-rotate 0.8s linear infinite;
}

@keyframes source-spinner-rotate {
  to {
    transform: rotate(360deg);
  }
}

/* 导入操作：加号图标 */
.source-add {
  flex-shrink: 0;
  width: 16px;
  height: 16px;
  color: var(--accent);
}

/* 本地已收录：对勾 + 绿色系统色，弱化按钮强调 */
.source-added {
  flex-shrink: 0;
  width: 17px;
  height: 17px;
  color: #34c759; /* iOS 系统绿，深浅色通用 */
}

.source-item.is-local .source-title {
  color: var(--text-secondary);
}

/* 桌面端结果列表限宽居中，与搜索栏视觉对齐 */
@media (min-width: 1024px) {
  .list-section {
    max-width: 780px;
    margin: 0 auto;
    padding: 10px 24px 0;
  }
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

.skeleton-thumb {
  flex-shrink: 0;
  width: 56px;
  height: 74px;
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
