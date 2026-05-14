<template>
  <section v-loading="loading" class="detail-view">
    <div class="detail-toolbar">
      <el-button text @click="$router.push('/anime')">返回番剧库</el-button>
      <el-button v-if="anime?.source_url" text :href="anime.source_url" target="_blank">打开源站页面</el-button>
    </div>

    <AnimeInspector v-if="anime" :anime="anime" @saved="onSaved" @error="ElMessage.error" />
  </section>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, ref } from 'vue'

import { getAnime } from '../services/animeService'
import AnimeInspector from '../components/AnimeInspector.vue'
import type { Anime, CollectionItem } from '../types'

const props = defineProps<{ id: string }>()
const anime = ref<Anime | null>(null)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    anime.value = await getAnime(Number(props.id))
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载失败')
  } finally {
    loading.value = false
  }
}

function onSaved(collection: CollectionItem) {
  if (anime.value) {
    anime.value.collection_item = collection
  }
  ElMessage.success('已保存')
}

onMounted(load)
</script>

<style scoped>
.detail-view {
  display: grid;
  gap: 18px;
}

.detail-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: rgba(8, 15, 27, 0.82);
  border: 1px solid var(--surface-line);
  border-radius: 22px;
  box-shadow: 0 20px 40px rgba(2, 7, 15, 0.28);
  backdrop-filter: blur(18px);
}

.detail-toolbar :deep(.el-button) {
  min-height: 42px;
  padding-inline: 16px;
}

@media (max-width: 640px) {
  .detail-toolbar {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
