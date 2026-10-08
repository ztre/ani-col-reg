<template>
  <div class="page">
    <!-- 吸顶头部：NavBar 与筛选栏一起钉在滚动容器顶部 -->
    <div class="collection-header">
      <NavBar title="我的收藏" />

      <!-- 年份筛选栏：横向滚动胶囊，毛玻璃底，仅在有数据时展示 -->
      <div v-if="showFilterBar" class="filter-bar frosted">
        <PillMenu v-model="activeYear" :options="yearOptions" />
      </div>
    </div>

    <div v-if="loading" class="list-section">
      <div class="list-group" aria-hidden="true">
        <div v-for="index in 6" :key="index" class="skeleton-row">
          <div class="skeleton skeleton-thumb" />
          <div class="skeleton-row-lines">
            <div class="skeleton skeleton-line skeleton-line--wide" />
            <div class="skeleton skeleton-line skeleton-line--narrow" />
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="loadError" class="state-section">
      <EmptyState icon="warning" title="加载失败" hint="请检查网络连接后重试" />
      <button type="button" class="retry-button" @click="load">重试</button>
    </div>

    <EmptyState
      v-else-if="!groups.length"
      icon="heart"
      title="还没有收藏"
      hint="去导视页逛逛吧"
    />

    <div v-else class="list-section">
      <div class="list-group is-grid">
        <SeriesRow v-for="group in visibleGroups" :key="group.series_key" :group="group" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onActivated, onMounted, ref } from 'vue'

import EmptyState from '../components/EmptyState.vue'
import NavBar from '../components/NavBar.vue'
import PillMenu from '../components/PillMenu.vue'
import SeriesRow from '../components/SeriesRow.vue'
import { fetchCollectedSeries } from '../services/collectionService'
import type { SeriesGroup } from '../types'

const loading = ref(true)
const loadError = ref(false)
const groups = ref<SeriesGroup[]>([])

// 年份筛选：'all' 表示全部，其余为具体年份字符串（PillMenu 的 v-model 为字符串）
const activeYear = ref('all')

// 筛选栏仅在有数据时展示（加载中 / 出错 / 空收藏均不渲染）
const showFilterBar = computed(() => !loading.value && !loadError.value && groups.value.length > 0)

// 年份选项：全部 + 收藏系列覆盖的全部年份（降序去重，取各系列条目年份并集）
const yearOptions = computed(() => {
  const years = new Set<number>()
  for (const group of groups.value) {
    years.add(group.latest_year)
    for (const entry of group.entries) {
      years.add(entry.year)
    }
  }
  return [
    { value: 'all', label: '全部' },
    ...[...years].sort((a, b) => b - a).map((year) => ({ value: String(year), label: String(year) }))
  ]
})

// 过滤 + 排序：选中年份时保留“该年有任何季度条目”的系列（同一作品跨年份不拆散）；
// 数据无收藏时间字段（见 types.ts），排序固定按名字（series_title 升序）
const visibleGroups = computed(() => {
  const filtered =
    activeYear.value === 'all'
      ? groups.value
      : groups.value.filter((group) =>
          group.entries.some((entry) => entry.year === Number(activeYear.value))
        )
  return [...filtered].sort((a, b) => a.series_title.localeCompare(b.series_title, 'zh-Hans-CN'))
})

async function load() {
  loading.value = true
  loadError.value = false
  try {
    groups.value = await fetchCollectedSeries()
    // 数据刷新后选中年份可能已不存在，回退到全部
    if (
      activeYear.value !== 'all' &&
      !yearOptions.value.some((option) => option.value === activeYear.value)
    ) {
      activeYear.value = 'all'
    }
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
}

onMounted(load)

// keep-alive 缓存态：每次切回/返回时刷新（详情页可能新增了收藏）
onActivated(load)
</script>

<style scoped>
.page {
  padding-bottom: 24px;
}

/* 吸顶头部：NavBar 与筛选栏整体钉在滚动容器顶部 */
.collection-header {
  position: sticky;
  top: 0;
  z-index: 100;
}

/* 年份筛选栏：毛玻璃底，跟随 NavBar 下方（样式复用 PillMenu 胶囊） */
.filter-bar {
  padding-bottom: 4px;
}

/* 桌面端筛选栏与下方列表限宽对齐 */
@media (min-width: 1024px) {
  .filter-bar {
    max-width: 828px; /* 780 + 左右 padding */
    margin: 0 auto;
    padding-bottom: 6px;
  }

  .filter-bar :deep(.pill-menu) {
    padding-left: 24px;
    padding-right: 24px;
  }
}

.list-section {
  padding: 6px 16px 0;
}

/* 桌面端列表限宽居中，避免行宽过长难以扫读 */
@media (min-width: 1024px) {
  .list-section {
    max-width: 780px;
    margin: 0 auto;
    padding: 10px 24px 0;
  }

  /* 桌面端网格：行组件自适应列宽（内部 flex 弹性布局），套卡片皮肤 */
  .list-group.is-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
    background: transparent;
    border-radius: 0;
    overflow: visible;
  }

  /* 网格卡片：独立底色 + 圆角 + 阴影，覆盖默认分组列表分隔线 */
  .list-group.is-grid > * {
    border-top: none;
    background: var(--bg-elevated);
    border-radius: 12px;
    box-shadow: var(--card-shadow);
    overflow: hidden;
    transition: transform 200ms ease;
  }

  .list-group.is-grid > *:hover {
    transform: translateY(-2px);
  }
}

/* 超宽屏（≥1440px）：3 列网格，容器放宽与主内容区同宽 */
@media (min-width: 1440px) {
  .list-section {
    max-width: 1100px;
  }

  .list-group.is-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
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
