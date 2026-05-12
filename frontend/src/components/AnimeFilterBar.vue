<template>
  <section :class="['anime-filter-bar', { 'anime-filter-bar--keyword': showKeywordInput }]">
    <div class="year-filter">
      <el-date-picker
        v-model="yearModel"
        type="year"
        clearable
        value-format="YYYY"
        size="large"
        placeholder="全部年份"
        @change="handleYearChange"
      />
      <el-button text class="year-filter-action" @click="selectCurrentYear">今年</el-button>
    </div>

    <div class="season-filter" role="group" aria-label="季度筛选">
      <button
        v-for="option in seasonFilterOptions"
        :key="option.value ?? 'all'"
        type="button"
        :class="['season-filter-chip', { 'season-filter-chip--active': season === option.value }]"
        @click="selectSeason(option.value)"
      >
        {{ option.label }}
      </button>
    </div>

    <el-input
      v-if="showKeywordInput"
      v-model="keywordModel"
      clearable
      size="large"
      class="keyword-filter"
      :placeholder="keywordPlaceholder"
      @keyup.enter="emit('apply')"
    >
      <template #prefix><el-icon><Search /></el-icon></template>
    </el-input>

    <template v-else>
      <el-select
        v-model="releaseTagsModel"
        multiple
        clearable
        collapse-tags
        collapse-tags-tooltip
        filterable
        allow-create
        default-first-option
        size="large"
        placeholder="资源标签，如 BDRip"
      >
        <el-option v-for="tag in releaseTagOptions" :key="tag" :label="tag" :value="tag" />
      </el-select>

      <el-select
        v-model="groupTagsModel"
        multiple
        clearable
        collapse-tags
        collapse-tags-tooltip
        filterable
        allow-create
        default-first-option
        size="large"
        placeholder="字幕组 / 压制组"
      >
        <el-option v-for="tag in groupTagOptions" :key="tag" :label="tag" :value="tag" />
      </el-select>
    </template>

    <el-button text class="filter-reset" @click="emit('clear')">{{ clearLabel }}</el-button>
    <el-button type="primary" size="large" :icon="Search" @click="emit('apply')">{{ applyLabel }}</el-button>
  </section>
</template>

<script setup lang="ts">
import { Search } from '@element-plus/icons-vue'
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    year?: string
    season?: number
    keyword?: string
    keywordPlaceholder?: string
    releaseTags?: string[]
    groupTags?: string[]
    releaseTagOptions?: string[]
    groupTagOptions?: string[]
    applyLabel?: string
    clearLabel?: string
    autoApplyYearSeason?: boolean
  }>(),
  {
    year: undefined,
    season: undefined,
    keyword: undefined,
    keywordPlaceholder: '搜索标题 / 别名',
    releaseTags: () => [],
    groupTags: () => [],
    releaseTagOptions: () => [],
    groupTagOptions: () => [],
    applyLabel: '筛选',
    clearLabel: '清空筛选',
    autoApplyYearSeason: true,
  }
)

const emit = defineEmits<{
  'update:year': [value: string | undefined]
  'update:season': [value: number | undefined]
  'update:keyword': [value: string]
  'update:releaseTags': [value: string[]]
  'update:groupTags': [value: string[]]
  apply: []
  clear: []
}>()

const currentYear = new Date().getFullYear()
const seasonFilterOptions = [
  { label: '全部', value: undefined },
  { label: '1月', value: 1 },
  { label: '4月', value: 2 },
  { label: '7月', value: 3 },
  { label: '10月', value: 4 },
] as const

const yearModel = computed({
  get: () => props.year,
  set: (value: string | undefined) => emit('update:year', value),
})

const showKeywordInput = computed(() => props.keyword !== undefined)

const keywordModel = computed({
  get: () => props.keyword ?? '',
  set: (value: string) => emit('update:keyword', value),
})

const releaseTagsModel = computed({
  get: () => props.releaseTags ?? [],
  set: (value: string[]) => emit('update:releaseTags', value),
})

const groupTagsModel = computed({
  get: () => props.groupTags ?? [],
  set: (value: string[]) => emit('update:groupTags', value),
})

function handleYearChange() {
  if (props.autoApplyYearSeason) {
    emit('apply')
  }
}

function selectCurrentYear() {
  emit('update:year', String(currentYear))
  if (props.autoApplyYearSeason) {
    emit('apply')
  }
}

function selectSeason(value?: number) {
  emit('update:season', value)
  if (props.autoApplyYearSeason) {
    emit('apply')
  }
}
</script>

<style scoped>
.anime-filter-bar {
  display: grid;
  grid-template-columns: minmax(180px, 220px) minmax(280px, 1.2fr) minmax(0, 1fr) minmax(0, 1fr) auto auto;
  gap: 12px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(214, 222, 234, 0.84);
  border-radius: 24px;
  box-shadow: 0 16px 40px rgba(24, 33, 47, 0.05);
}

.anime-filter-bar--keyword .keyword-filter {
  grid-column: span 2;
}

.year-filter {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px;
  align-items: center;
}

.year-filter :deep(.el-date-editor.el-input) {
  width: 100%;
}

.year-filter-action {
  min-height: 42px;
  padding-inline: 10px;
  color: #4d7db3;
  border-radius: 14px;
}

.filter-reset {
  min-height: 42px;
  color: #5d6a7b;
  border-radius: 14px;
}

.season-filter {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  padding: 6px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(210, 219, 232, 0.88);
  border-radius: 18px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.72);
}

.season-filter-chip {
  min-height: 38px;
  padding: 0 14px;
  color: #5d6a7b;
  background: transparent;
  border: none;
  border-radius: 14px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease, box-shadow 0.2s ease;
}

.season-filter-chip:hover {
  color: #314254;
  background: rgba(238, 243, 249, 0.92);
}

.season-filter-chip--active {
  color: #ffffff;
  background: linear-gradient(135deg, #2f6fb5, #4d95d6);
  box-shadow: 0 10px 24px rgba(54, 111, 182, 0.22);
}

.anime-filter-bar :deep(.el-input__wrapper),
.anime-filter-bar :deep(.el-select__wrapper),
.anime-filter-bar :deep(.el-date-editor .el-input__wrapper) {
  min-height: 48px;
  border-radius: 16px;
  box-shadow: 0 0 0 1px rgba(214, 222, 234, 0.92) inset;
}

.anime-filter-bar :deep(.el-button) {
  border-radius: 16px;
}

@media (max-width: 960px) {
  .anime-filter-bar {
    grid-template-columns: 1fr;
  }

  .season-filter {
    justify-content: flex-start;
  }
}
</style>