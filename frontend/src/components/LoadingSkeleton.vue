<template>
  <div class="loading-skeleton" aria-hidden="true">
    <div v-for="index in count" :key="index" class="loading-skeleton-card">
      <div class="skeleton skeleton-cover" />
      <div class="skeleton skeleton-line skeleton-line--wide" />
      <div class="skeleton skeleton-line skeleton-line--narrow" />
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    count?: number
  }>(),
  { count: 12 }
)
</script>

<style scoped>
.loading-skeleton {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(96px, 1fr));
  gap: 14px 12px;
  padding: 16px;
}

.skeleton {
  border-radius: 8px;
  background: linear-gradient(100deg, var(--fill) 40%, var(--bg-elevated) 50%, var(--fill) 60%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.4s ease-in-out infinite;
}

.skeleton-cover {
  aspect-ratio: 2 / 3;
  border-radius: 12px;
}

.skeleton-line {
  height: 12px;
  margin-top: 8px;
}

.skeleton-line--wide {
  width: 92%;
}

.skeleton-line--narrow {
  width: 58%;
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
