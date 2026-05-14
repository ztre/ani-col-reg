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
    var(--surface-card),
    linear-gradient(90deg, color-mix(in srgb, var(--accent-strong) 8%, transparent), transparent);
  border: 1px solid var(--surface-line);
  border-radius: 24px;
  box-shadow: var(--elevation-card-soft);
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