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

import { getAnime } from '../api'
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
  padding: 0 4px;
}

@media (max-width: 640px) {
  .detail-toolbar {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
