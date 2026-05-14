<template>
  <section class="anime-empty-state">
    <div class="anime-empty-state__panel">
      <p class="anime-empty-state__eyebrow">No Result</p>
      <h2>这一页还没有海报</h2>
      <p>当前筛选下没有匹配条目。你可以切换年份、季度，或者重新执行一次搜索并更新。</p>
      <el-button type="primary" @click="emit('clear')">重置筛选</el-button>
    </div>
  </section>
</template>

<script setup lang="ts">
const emit = defineEmits<{
  clear: []
}>()
</script>

<style scoped>
.anime-empty-state {
  display: grid;
  place-items: center;
  min-height: 320px;
}

.anime-empty-state__panel {
  width: min(520px, 100%);
  display: grid;
  gap: 10px;
  justify-items: center;
  padding: 32px 28px;
  text-align: center;
  background: rgba(7, 14, 26, 0.82);
  border: 1px solid var(--surface-line);
  border-radius: 28px;
  box-shadow: 0 24px 46px rgba(3, 8, 15, 0.34);
}

.anime-empty-state__eyebrow,
.anime-empty-state__panel h2,
.anime-empty-state__panel p {
  margin: 0;
}

.anime-empty-state__eyebrow {
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.anime-empty-state__panel h2 {
  color: var(--text-strong);
}

.anime-empty-state__panel p {
  color: var(--text-muted);
  line-height: 1.7;
}
</style>