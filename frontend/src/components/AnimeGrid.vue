<template>
  <section class="anime-grid-wall" aria-label="番剧海报墙">
    <AnimeCard v-for="item in items" :key="item.id" :anime="item" @select="emit('select', $event)" />
  </section>
</template>

<script setup lang="ts">
import AnimeCard from './AnimeCard.vue'
import type { Anime } from '../types'

defineProps<{
  items: Anime[]
}>()

const emit = defineEmits<{
  select: [anime: Anime]
}>()
</script>

<style scoped>
.anime-grid-wall {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 20px;
}

@media (max-width: 640px) {
  .anime-grid-wall {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
  }
}
</style>