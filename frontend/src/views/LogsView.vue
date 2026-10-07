<template>
  <div class="page">
    <h1 class="logs-heading">运行日志</h1>

    <!-- 毛玻璃 sticky 工具栏：级别筛选 + 刷新 -->
    <header class="logs-toolbar frosted">
      <div class="toolbar-inner">
        <label class="toolbar-label" for="logs-level">级别</label>
        <select id="logs-level" v-model="levelFilter" class="level-select">
          <option value="">全部</option>
          <option value="ERROR">ERROR</option>
          <option value="WARNING">WARNING</option>
          <option value="INFO">INFO</option>
          <option value="DEBUG">DEBUG</option>
        </select>

        <button type="button" class="refresh-button" :disabled="loading" @click="refresh">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <polyline points="23 4 23 10 17 10" />
            <polyline points="1 20 1 14 7 14" />
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
          </svg>
          <span>{{ loading ? '刷新中…' : '刷新' }}</span>
        </button>
      </div>
    </header>

    <!-- 加载中 -->
    <div v-if="loading && !logs.length" class="loading-section" role="status" aria-label="加载中">
      <span class="loading-spinner" aria-hidden="true" />
    </div>

    <!-- 加载失败 -->
    <div v-else-if="loadError" class="state-section">
      <EmptyState icon="warning" title="日志加载失败" hint="请检查网络连接后重试" />
      <button type="button" class="retry-button" @click="load">重试</button>
    </div>

    <!-- 空日志 -->
    <EmptyState v-else-if="!logs.length" title="暂无日志" hint="切换级别筛选或稍后刷新看看" />

    <!-- 日志表格 -->
    <div v-else class="logs-card card">
      <table class="logs-table">
        <thead>
          <tr>
            <th scope="col">时间</th>
            <th scope="col">级别</th>
            <th scope="col">来源</th>
            <th scope="col">消息</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="log in logs"
            :key="log.id"
            class="log-row"
            :class="{ 'is-expanded': expandedIds.has(log.id) }"
            @click="toggleExpanded(log.id)"
          >
            <td class="cell-time">{{ formatTime(log.created_at) }}</td>
            <td class="cell-level">
              <span class="level-badge" :class="levelClass(log.level)">{{ log.level }}</span>
            </td>
            <td class="cell-source" :title="log.source">{{ log.source }}</td>
            <td class="cell-message" :title="expandedIds.has(log.id) ? '点击收起' : '点击展开'">
              {{ log.message }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 分页 -->
    <div v-if="!loadError && (logs.length || page > 1)" class="logs-pagination">
      <button type="button" class="pagination-button" :disabled="page <= 1 || loading" @click="goToPage(page - 1)">
        上一页
      </button>
      <span class="pagination-info">第 {{ page }} / {{ totalPages }} 页 · 共 {{ total }} 条</span>
      <button
        type="button"
        class="pagination-button"
        :disabled="page >= totalPages || loading"
        @click="goToPage(page + 1)"
      >
        下一页
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import EmptyState from '../components/EmptyState.vue'
import { fetchLogs } from '../services/logService'
import type { AppLog } from '../types'

const PAGE_SIZE = 20

const logs = ref<AppLog[]>([])
const total = ref(0)
const page = ref(1)
const levelFilter = ref('')
const loading = ref(false)
const loadError = ref(false)
const expandedIds = ref<Set<number>>(new Set())

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))

async function load() {
  loading.value = true
  loadError.value = false
  try {
    const data = await fetchLogs({
      level: levelFilter.value || undefined,
      limit: PAGE_SIZE,
      offset: (page.value - 1) * PAGE_SIZE
    })
    logs.value = data.items
    total.value = data.total
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
}

function refresh() {
  expandedIds.value = new Set()
  load()
}

function goToPage(target: number) {
  if (loading.value || target < 1 || target > totalPages.value) {
    return
  }
  page.value = target
  expandedIds.value = new Set()
  load()
}

function toggleExpanded(id: number) {
  const next = new Set(expandedIds.value)
  if (next.has(id)) {
    next.delete(id)
  } else {
    next.add(id)
  }
  expandedIds.value = next
}

/** 级别徽章配色（iOS 系统色，深浅色通用） */
function levelClass(level: string): string {
  if (level === 'ERROR' || level === 'CRITICAL') {
    return 'level-badge--error'
  }
  if (level === 'WARNING') {
    return 'level-badge--warning'
  }
  if (level === 'INFO') {
    return 'level-badge--info'
  }
  if (level === 'DEBUG') {
    return 'level-badge--debug'
  }
  return 'level-badge--default'
}

/** 后端 SQLite 时间为 UTC 无时区字符串，补 Z 后转本地时间展示 */
function formatTime(value: string): string {
  const normalized = value.includes('T') ? value : value.replace(' ', 'T')
  const withZone = /[zZ]$|[+-]\d{2}:?\d{2}$/.test(normalized) ? normalized : `${normalized}Z`
  const date = new Date(withZone)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  const pad = (input: number) => String(input).padStart(2, '0')
  return (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ` +
    `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
  )
}

// 切换级别筛选时回到第一页
watch(levelFilter, () => {
  page.value = 1
  refresh()
})

onMounted(load)
</script>

<style scoped>
.page {
  padding-bottom: 24px;
}

.logs-heading {
  margin: 0;
  padding: calc(env(safe-area-inset-top) + 6px) 16px 6px;
  font-size: 34px;
  font-weight: 700;
  letter-spacing: 0.2px;
}

/* 毛玻璃 sticky 工具栏 */
.logs-toolbar {
  position: sticky;
  top: 0;
  z-index: 100;
  border-bottom: 0.5px solid var(--separator);
}

.toolbar-inner {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 52px;
  padding: 0 16px;
}

.toolbar-label {
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
}

.level-select {
  width: 132px;
  height: 36px;
  padding: 0 30px 0 12px;
  border: 1px solid transparent;
  border-radius: 10px;
  background: var(--fill);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%238e8e93' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 9px center;
  background-size: 14px 14px;
  appearance: none;
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
  transition: border-color 200ms ease;
}

.level-select:focus {
  border-color: var(--accent);
}

.refresh-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 36px;
  margin-left: auto;
  padding: 0 14px;
  border-radius: 10px;
  background: var(--fill);
  color: var(--accent);
  font-size: 14px;
  font-weight: 600;
  transition: opacity 200ms ease;
}

.refresh-button:not(:disabled):active {
  opacity: 0.6;
}

.refresh-button:disabled {
  opacity: 0.5;
  cursor: default;
}

.refresh-button svg {
  width: 15px;
  height: 15px;
}

.loading-section {
  display: flex;
  justify-content: center;
  padding: 96px 0;
}

.loading-spinner {
  width: 26px;
  height: 26px;
  border: 2.5px solid var(--fill);
  border-top-color: var(--accent);
  border-radius: 999px;
  animation: logs-spinner-rotate 0.8s linear infinite;
}

@keyframes logs-spinner-rotate {
  to {
    transform: rotate(360deg);
  }
}

.state-section {
  display: flex;
  flex-direction: column;
}

.retry-button {
  align-self: center;
  margin-top: -36px;
  padding: 8px 32px;
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

/* 日志表格卡片 */
.logs-card {
  margin: 12px 16px 0;
  overflow-x: auto;
}

.logs-table {
  width: 100%;
  min-width: 640px;
  border-collapse: collapse;
  font-size: 13px;
}

.logs-table th {
  padding: 11px 14px;
  border-bottom: 1px solid var(--separator);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.3px;
  text-align: left;
  white-space: nowrap;
}

.log-row {
  cursor: pointer;
  transition: background-color 150ms ease;
}

.log-row:hover {
  background: var(--fill);
}

.log-row:last-child td {
  border-bottom: none;
}

.logs-table td {
  padding: 10px 14px;
  border-bottom: 1px solid var(--separator);
  vertical-align: top;
  line-height: 1.45;
}

.cell-time {
  white-space: nowrap;
  color: var(--text-secondary);
  font-variant-numeric: tabular-nums;
}

.cell-level {
  white-space: nowrap;
}

.cell-source {
  max-width: 200px;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  color: var(--text-secondary);
}

.cell-message {
  max-width: 460px;
  color: var(--text-primary);
  word-break: break-word;
}

/* 长消息默认两行截断，点击行展开 */
.cell-message {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  overflow: hidden;
}

.log-row.is-expanded .cell-message {
  display: block;
  -webkit-line-clamp: unset;
  line-clamp: unset;
}

/* 级别徽章（iOS 系统色） */
.level-badge {
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.3px;
}

.level-badge--error {
  color: #ff453a;
  background: rgba(255, 69, 58, 0.14);
}

.level-badge--warning {
  color: #ff9f0a;
  background: rgba(255, 159, 10, 0.16);
}

.level-badge--info {
  color: #007aff;
  background: rgba(0, 122, 255, 0.12);
}

.level-badge--debug {
  color: var(--text-secondary);
  background: var(--fill);
}

.level-badge--default {
  color: var(--text-secondary);
  background: var(--fill);
}

/* 分页 */
.logs-pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin: 16px 16px 0;
}

.pagination-button {
  height: 36px;
  padding: 0 16px;
  border-radius: 12px;
  background: var(--fill);
  color: var(--accent);
  font-size: 14px;
  font-weight: 600;
  transition: opacity 200ms ease;
}

.pagination-button:not(:disabled):active {
  opacity: 0.6;
}

.pagination-button:disabled {
  opacity: 0.4;
  cursor: default;
}

.pagination-info {
  color: var(--text-secondary);
  font-size: 13px;
  font-variant-numeric: tabular-nums;
}
</style>
