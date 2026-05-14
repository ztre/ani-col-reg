<template>
  <section class="anime-loading-wall" aria-label="加载中">
    <div v-for="index in count" :key="index" class="anime-loading-wall__card">
      <div class="anime-loading-wall__shine" />
      <div class="anime-loading-wall__content">
        <span class="anime-loading-wall__line anime-loading-wall__line--short" />
        <span class="anime-loading-wall__line" />
        <span class="anime-loading-wall__line anime-loading-wall__line--tiny" />
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    count?: number
  }>(),
  {
    count: 8
  }
)
</script>

<style scoped>
.anime-loading-wall {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 20px;
}

.anime-loading-wall__card {
  position: relative;
  aspect-ratio: 2 / 3;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgba(15, 24, 39, 0.92), rgba(8, 14, 26, 0.98)),
    linear-gradient(90deg, rgba(103, 140, 192, 0.08), rgba(103, 140, 192, 0.02));
  border: 1px solid var(--surface-line);
  border-radius: 24px;
  box-shadow: 0 20px 40px rgba(3, 8, 15, 0.32);
}

.anime-loading-wall__shine {
  position: absolute;
  inset: 0;
  background: var(--skeleton-shine);
  animation: shimmer 1.8s linear infinite;
}

.anime-loading-wall__content {
  position: absolute;
  inset: auto 18px 18px;
  display: grid;
  gap: 8px;
}

.anime-loading-wall__line {
  display: block;
  width: 100%;
  height: 12px;
  background: var(--skeleton-line);
  border-radius: 999px;
}

.anime-loading-wall__line--short {
  width: 58%;
}

.anime-loading-wall__line--tiny {
  width: 36%;
}

@keyframes shimmer {
  from {
    transform: translateX(-100%);
  }

  to {
    transform: translateX(100%);
  }
}

@media (max-width: 640px) {
  .anime-loading-wall {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
  }
}
</style>