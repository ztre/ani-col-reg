<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="min(1040px, calc(100vw - 24px))"
    top="24px"
    class="anime-dialog"
    destroy-on-close
  >
    <div v-loading="blockingLoading" class="anime-dialog-body">
      <div v-if="refreshingBannerVisible" class="anime-dialog-refreshing">正在补全详情与封面…</div>
      <AnimeInspector v-if="anime" :anime="anime" @saved="onSaved" @removed="onRemoved" @error="emit('error', $event)" />
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { getAnime } from '../services/animeService'
import type { Anime, CollectionItem } from '../types'
import AnimeInspector from './AnimeInspector.vue'

const props = defineProps<{
  modelValue: boolean
  animeId: number | null
  initialAnime?: Anime | null
  detailLoaded?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  saved: [payload: { animeId: number; collection: CollectionItem }]
  removed: [payload: { animeId: number }]
  loaded: [anime: Anime]
  error: [message: string]
}>()

const anime = ref<Anime | null>(null)
const loading = ref(false)
const showRefreshBanner = ref(false)
let refreshBannerTimer: ReturnType<typeof setTimeout> | null = null
let refreshPollTimer: ReturnType<typeof setTimeout> | null = null
let requestSerial = 0

const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value)
})

const dialogTitle = computed(() => anime.value?.title_cn || '番剧详情')
const blockingLoading = computed(() => loading.value && !anime.value)
const refreshingBannerVisible = computed(() => Boolean(anime.value?.detail_refreshing) || (showRefreshBanner.value && Boolean(anime.value)))

watch(
  [() => props.modelValue, () => props.animeId],
  ([open, animeId]) => {
    if (!open || !animeId) {
      return
    }

    const initialAnime = props.initialAnime
    if (initialAnime && initialAnime.id === animeId) {
      anime.value = cloneAnime(initialAnime)
    } else if (anime.value?.id !== animeId) {
      anime.value = null
    }

    if (!shouldFetchDetail(initialAnime, props.detailLoaded)) {
      loading.value = false
      clearRefreshBanner()
      clearRefreshPoll()
      return
    }

    void load(animeId)
  },
  { immediate: true }
)

watch(
  () => props.initialAnime,
  (initialAnime) => {
    if (!props.modelValue || !props.animeId || !initialAnime || initialAnime.id !== props.animeId) {
      return
    }

    if (loading.value) {
      anime.value = cloneAnime(initialAnime)
    }
  }
)

function cloneAnime(source: Anime): Anime {
  return {
    ...source,
    collection_item: source.collection_item ? { ...source.collection_item } : null,
  }
}

function shouldFetchDetail(initialAnime?: Anime | null, detailLoaded?: boolean): boolean {
  if (!initialAnime) {
    return true
  }
  if (detailLoaded) {
    return false
  }

  const requiredFields = [
    initialAnime.synopsis,
    initialAnime.staff,
    initialAnime.cast,
    initialAnime.tags,
    initialAnime.cover_url,
  ]

  return requiredFields.some((value) => !value)
}

function scheduleRefreshBanner() {
  clearRefreshBanner()
  if (!anime.value) {
    return
  }

  refreshBannerTimer = setTimeout(() => {
    if (loading.value && anime.value) {
      showRefreshBanner.value = true
    }
  }, 180)
}

function clearRefreshBanner() {
  if (refreshBannerTimer !== null) {
    clearTimeout(refreshBannerTimer)
    refreshBannerTimer = null
  }
  showRefreshBanner.value = false
}

function clearRefreshPoll() {
  if (refreshPollTimer !== null) {
    clearTimeout(refreshPollTimer)
    refreshPollTimer = null
  }
}

async function load(animeId: number, pollAttempt = 0) {
  const currentRequest = ++requestSerial
  scheduleRefreshBanner()
  loading.value = true
  try {
    const detail = await getAnime(animeId)
    if (currentRequest !== requestSerial) {
      return
    }
    anime.value = detail
    if (detail.detail_refreshing) {
      scheduleRefreshPoll(animeId, pollAttempt)
      return
    }
    emit('loaded', detail)
  } catch (error) {
    if (currentRequest === requestSerial) {
      emit('error', error instanceof Error ? error.message : '加载详情失败')
    }
  } finally {
    if (currentRequest === requestSerial) {
      loading.value = false
      clearRefreshBanner()
    }
  }
}

function scheduleRefreshPoll(animeId: number, pollAttempt: number) {
  clearRefreshPoll()
  if (pollAttempt >= 5) {
    return
  }

  refreshPollTimer = setTimeout(() => {
    if (!visible.value || props.animeId !== animeId) {
      return
    }
    void load(animeId, pollAttempt + 1)
  }, pollAttempt === 0 ? 700 : 1100)
}

function onSaved(collection: CollectionItem) {
  if (anime.value) {
    anime.value.collection_item = collection
    emit('saved', { animeId: anime.value.id, collection })
  }
}

function onRemoved(animeId: number) {
  if (!anime.value || anime.value.id !== animeId) {
    return
  }

  anime.value.collection_item = null
  emit('removed', { animeId })
}
</script>

<style scoped>
.anime-dialog-body {
  min-height: 240px;
}

.anime-dialog-refreshing {
  margin-bottom: 12px;
  padding: 10px 14px;
  color: var(--text-soft);
  background: rgba(18, 31, 50, 0.72);
  border: 1px solid rgba(99, 182, 255, 0.24);
  border-radius: 14px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
  font-size: 13px;
  font-weight: 700;
}

:deep(.anime-dialog) {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  max-height: calc(100vh - 48px);
  color: var(--text-strong);
  background: var(--surface-card);
  border: 1px solid var(--surface-line);
  border-radius: 28px;
  box-shadow: 0 30px 80px rgba(1, 5, 11, 0.56);
  backdrop-filter: blur(22px);
}

:deep(.anime-dialog .el-dialog__header) {
  flex-shrink: 0;
  padding: 22px 24px 0;
  border-bottom: 1px solid rgba(144, 173, 214, 0.08);
}

:deep(.anime-dialog .el-dialog__title) {
  color: var(--text-strong);
  font-weight: 700;
  letter-spacing: 0.01em;
}

:deep(.anime-dialog .el-dialog__headerbtn) {
  top: 22px;
  right: 20px;
  color: var(--text-muted);
}

:deep(.anime-dialog .el-dialog__headerbtn:hover) {
  color: var(--text-strong);
}

:deep(.anime-dialog .el-dialog__body) {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding: 18px 24px 24px;
}

@media (max-width: 640px) {
  :deep(.anime-dialog .el-dialog__body) {
    padding: 14px;
  }
}
</style>
