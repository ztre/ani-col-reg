<template>
  <section :class="['anime-filter-bar', { 'anime-filter-bar--keyword': showKeywordInput }]">
    <div class="anime-filter-bar__field year-filter">
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

    <div class="anime-filter-bar__field season-filter" role="group" aria-label="季度筛选">
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
      class="anime-filter-bar__field anime-filter-bar__field--keyword keyword-filter"
      :placeholder="keywordPlaceholder"
      @keyup.enter="emit('apply')"
    >
      <template #prefix><el-icon><Search /></el-icon></template>
    </el-input>

    <template v-else>
      <el-select
        v-model="releaseTagsModel"
        class="anime-filter-bar__field anime-filter-bar__field--release"
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
        class="anime-filter-bar__field anime-filter-bar__field--group"
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

    <div class="anime-filter-bar__actions">
      <el-button text class="filter-reset" @click="emit('clear')">{{ clearLabel }}</el-button>
      <el-button type="primary" size="large" :icon="Search" @click="emit('apply')">{{ applyLabel }}</el-button>
    </div>
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
  gap: 12px;
  align-items: start;
}

.anime-filter-bar:not(.anime-filter-bar--keyword) {
  grid-template-columns: minmax(172px, 208px) minmax(260px, 1fr) auto;
  grid-template-areas:
    'year season actions'
    'release group actions';
}

.year-filter {
  grid-area: year;
}

.season-filter {
  grid-area: season;
}

.anime-filter-bar__field--release {
  grid-area: release;
}

.anime-filter-bar__field--group {
  grid-area: group;
}

.anime-filter-bar--keyword {
  grid-template-columns: minmax(172px, 208px) minmax(280px, 1fr) auto;
  grid-template-areas:
    'year season actions'
    'keyword keyword keyword';
}

.anime-filter-bar__field--keyword {
  grid-area: keyword;
}

.anime-filter-bar__field {
  min-width: 0;
}

.anime-filter-bar__actions {
  grid-area: actions;
  display: grid;
  grid-auto-flow: column;
  gap: 10px;
  align-self: stretch;
  justify-self: end;
}

.anime-filter-bar--keyword .anime-filter-bar__actions {
  align-self: center;
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
  min-height: 48px;
  padding-inline: 12px;
  color: var(--text-soft);
  background: var(--control-subtle-bg);
  border: 1px solid var(--surface-line);
  border-radius: 16px;
}

.filter-reset {
  min-height: 48px;
  color: var(--text-muted);
  background: var(--button-text-bg);
  border: 1px solid var(--control-subtle-border);
  border-radius: 16px;
}

.season-filter {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  min-height: 48px;
  padding: 6px;
  background: var(--surface-panel-strong);
  border: 1px solid var(--surface-line);
  border-radius: 18px;
}

.season-filter-chip {
  min-height: 38px;
  padding: 0 14px;
  color: var(--text-muted);
  background: transparent;
  border: 1px solid transparent;
  border-radius: 14px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease, box-shadow 0.2s ease;
}

.season-filter-chip:hover {
  color: var(--text-strong);
  background: var(--control-subtle-hover-bg);
}

.season-filter-chip--active {
  color: var(--shell-nav-active-text);
  background: var(--accent-gradient);
  border-color: var(--shell-nav-active-border);
  box-shadow: var(--accent-shadow);
}

.anime-filter-bar :deep(.el-input__wrapper),
.anime-filter-bar :deep(.el-select__wrapper),
.anime-filter-bar :deep(.el-date-editor .el-input__wrapper) {
  min-height: 48px;
  border-radius: 16px;
  color: var(--text-soft);
  background: var(--surface-panel-strong);
  box-shadow: 0 0 0 1px var(--surface-line) inset;
}

.anime-filter-bar :deep(.el-input__inner),
.anime-filter-bar :deep(.el-select__placeholder),
.anime-filter-bar :deep(.el-date-editor .el-range-input),
.anime-filter-bar :deep(.el-date-editor .el-input__inner),
.anime-filter-bar :deep(.el-icon) {
  color: var(--text-soft);
}

.anime-filter-bar :deep(.el-tag.el-tag--info) {
  background: var(--surface-chip);
  border-color: var(--surface-line);
}

.anime-filter-bar :deep(.el-button),
.anime-filter-bar__actions :deep(.el-button) {
  border-radius: 16px;
}

.anime-filter-bar__actions :deep(.el-button--primary) {
  min-height: 48px;
  padding-inline: 18px;
  color: var(--shell-nav-active-text);
  background: var(--accent-gradient);
  border-color: transparent;
  box-shadow: var(--accent-shadow);
}

.anime-filter-bar__actions :deep(.el-button--primary:hover) {
  background: var(--accent-gradient-hover);
}

@media (max-width: 960px) {
  .anime-filter-bar {
    grid-template-columns: 1fr;
    grid-template-areas: none;
  }

  .year-filter,
  .season-filter,
  .anime-filter-bar__field--keyword,
  .anime-filter-bar__field--release,
  .anime-filter-bar__field--group,
  .anime-filter-bar__actions {
    grid-area: auto;
  }

  .anime-filter-bar__actions {
    grid-auto-flow: row;
    justify-self: stretch;
  }

  .season-filter {
    justify-content: flex-start;
  }
}
</style>