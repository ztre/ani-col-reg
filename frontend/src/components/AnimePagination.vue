<template>
  <div class="anime-pagination">
    <el-pagination
      :current-page="page"
      :page-size="pageSize"
      :page-sizes="pageSizes"
      :total="total"
      background
      layout="prev, pager, next, sizes, total"
      @update:current-page="handlePageUpdate"
      @update:page-size="handlePageSizeUpdate"
      @change="emit('change')"
    />
  </div>
</template>

<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    page: number
    pageSize: number
    total: number
    pageSizes?: number[]
  }>(),
  {
    pageSizes: () => [12, 24, 36, 48]
  }
)

const emit = defineEmits<{
  'update:page': [value: number]
  'update:pageSize': [value: number]
  change: []
}>()

function handlePageUpdate(value: number) {
  emit('update:page', value)
}

function handlePageSizeUpdate(value: number) {
  emit('update:pageSize', value)
}
</script>

<style scoped>
.anime-pagination {
  display: flex;
  justify-content: flex-end;
}

.anime-pagination :deep(.el-pagination) {
  padding: 12px 16px;
  background: rgba(7, 14, 26, 0.76);
  border: 1px solid rgba(141, 170, 212, 0.14);
  border-radius: 24px;
  box-shadow: 0 18px 34px rgba(3, 8, 15, 0.3);
}

.anime-pagination :deep(.btn-prev),
.anime-pagination :deep(.btn-next),
.anime-pagination :deep(.el-pager li),
.anime-pagination :deep(.el-pagination__total),
.anime-pagination :deep(.el-pagination__sizes) {
  color: var(--text-soft);
}

.anime-pagination :deep(.btn-prev),
.anime-pagination :deep(.btn-next),
.anime-pagination :deep(.el-pager li) {
  background: rgba(18, 29, 47, 0.62);
  border-radius: 12px;
}

.anime-pagination :deep(.el-select__wrapper) {
  min-height: 36px;
  background: rgba(18, 29, 47, 0.82);
  box-shadow: 0 0 0 1px var(--surface-line) inset;
  border-radius: 14px;
}

.anime-pagination :deep(.el-select__placeholder),
.anime-pagination :deep(.el-select__selected-item) {
  color: var(--text-soft);
}

.anime-pagination :deep(.el-pager li.is-active) {
  color: #07121f;
  background: linear-gradient(135deg, #8fd7ff, #6fb7ff);
}

@media (max-width: 768px) {
  .anime-pagination {
    justify-content: stretch;
  }

  .anime-pagination :deep(.el-pagination) {
    width: 100%;
    justify-content: center;
  }
}
</style>