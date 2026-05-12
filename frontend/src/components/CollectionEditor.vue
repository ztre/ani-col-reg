<template>
  <el-form label-position="top" class="collection-form">
    <el-form-item label="整理状态">
      <el-select v-model="organizeStatus" placeholder="选择整理状态">
        <el-option v-for="option in ORGANIZE_STATUS_OPTIONS" :key="option.value" :label="option.label" :value="option.value" />
      </el-select>
    </el-form-item>

    <el-form-item label="资源标签">
      <el-select
        class="collection-multi-select"
        v-model="releaseTagList"
        multiple
        clearable
        filterable
        allow-create
        default-first-option
        size="large"
        placeholder="按片源类型 / 清晰度 / 编码格式选择"
        @change="handleReleaseTagChange"
      >
        <el-option-group v-for="group in releaseOptionGroups" :key="group.key" :label="group.label">
          <el-option v-for="tag in group.options" :key="tag" :label="tag" :value="tag" />
        </el-option-group>
      </el-select>
    </el-form-item>

    <el-form-item label="字幕组 / 压制组">
      <el-select
        class="collection-multi-select"
        v-model="groupTagList"
        multiple
        clearable
        filterable
        allow-create
        default-first-option
        size="large"
        placeholder="ANi / Lilith-Raws / NC-Raws"
      >
        <el-option v-for="tag in groupOptions" :key="tag" :label="tag" :value="tag" />
      </el-select>
    </el-form-item>
    <el-form-item label="备注">
      <el-input v-model="draft.note" type="textarea" :rows="4" placeholder="收录版本、硬盘位置、补充说明" />
    </el-form-item>

    <el-form-item class="collection-form-actions">
      <div class="collection-action-row">
        <el-button
          v-if="props.collection?.id"
          class="collection-remove"
          type="danger"
          plain
          :loading="removing"
          @click="remove"
        >
          取消收藏
        </el-button>

        <el-button type="primary" :loading="saving" @click="submit">
          {{ props.collection?.id ? '保存整理' : '加入收藏' }}
        </el-button>
      </div>
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { ElMessageBox } from 'element-plus'

import { deleteCollection, saveCollection, updateCollection } from '../api'
import { ORGANIZE_STATUS_OPTIONS, type CollectionOrganizeStatus } from '../collectionPresentation'
import {
  RELEASE_TAG_GROUP_LABELS,
  loadTagLibrary,
  mergeTagOptions,
  normalizeReleaseTags,
  releaseTagGroup,
  rememberTagLibrary,
} from '../tagLibrary'
import type { CollectionItem } from '../types'

const props = defineProps<{
  animeId: number
  collection: CollectionItem | null
}>()

const emit = defineEmits<{
  saved: [collection: CollectionItem]
  removed: [animeId: number]
  error: [message: string]
}>()

const saving = ref(false)
const removing = ref(false)
const organizeStatus = ref<CollectionOrganizeStatus>('pending')
const releaseTagList = ref<string[]>([])
const groupTagList = ref<string[]>([])
const savedReleaseOptions = ref<string[]>(loadTagLibrary('release'))
const savedGroupOptions = ref<string[]>(loadTagLibrary('group'))
const draft = reactive({
  note: ''
})

const releaseOptions = computed(() => mergeTagOptions(savedReleaseOptions.value, releaseTagList.value))
const releaseOptionGroups = computed(() => {
  const groups = [
    {
      key: 'source',
      label: RELEASE_TAG_GROUP_LABELS.source,
      options: releaseOptions.value.filter((tag) => releaseTagGroup(tag) === 'source')
    },
    {
      key: 'resolution',
      label: RELEASE_TAG_GROUP_LABELS.resolution,
      options: releaseOptions.value.filter((tag) => releaseTagGroup(tag) === 'resolution')
    },
    {
      key: 'codec',
      label: RELEASE_TAG_GROUP_LABELS.codec,
      options: releaseOptions.value.filter((tag) => releaseTagGroup(tag) === 'codec')
    },
    {
      key: 'custom',
      label: '补充标签',
      options: releaseOptions.value.filter((tag) => releaseTagGroup(tag) === null)
    }
  ]

  return groups.filter((group) => group.options.length > 0)
})
const groupOptions = computed(() => mergeTagOptions(savedGroupOptions.value, groupTagList.value))

watch(
  () => props.collection,
  (collection) => {
    organizeStatus.value = collection?.organize_status || 'pending'
    draft.note = collection?.note || ''
    releaseTagList.value = normalizeReleaseTags(splitTags(collection?.release_tags))
    groupTagList.value = splitTags(collection?.group_tags)
    savedReleaseOptions.value = loadTagLibrary('release')
    savedGroupOptions.value = loadTagLibrary('group')
  },
  { immediate: true }
)

function splitTags(value?: string | null) {
  return (value || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function joinTags(tags: string[]) {
  return tags.map((item) => item.trim()).filter(Boolean).join(', ')
}

function handleReleaseTagChange(tags: string[]) {
  releaseTagList.value = normalizeReleaseTags(tags)
}

async function submit() {
  saving.value = true
  try {
    const normalizedReleaseTags = normalizeReleaseTags(releaseTagList.value)
    releaseTagList.value = normalizedReleaseTags

    const payload = {
      anime_id: props.animeId,
      organize_status: organizeStatus.value,
      note: draft.note || null,
      release_tags: joinTags(normalizedReleaseTags) || null,
      group_tags: joinTags(groupTagList.value) || null
    }
    const saved = props.collection?.id
      ? await updateCollection(props.collection.id, payload)
      : await saveCollection(payload)
    savedReleaseOptions.value = rememberTagLibrary('release', savedReleaseOptions.value, normalizedReleaseTags)
    savedGroupOptions.value = rememberTagLibrary('group', savedGroupOptions.value, groupTagList.value)
    emit('saved', saved)
  } catch (error) {
    emit('error', error instanceof Error ? error.message : '保存失败')
  } finally {
    saving.value = false
  }
}

async function remove() {
  if (!props.collection?.id) {
    return
  }

  try {
    await ElMessageBox.confirm('这会移除当前番剧的收藏记录，资源标签、字幕组和备注会一起删除。是否继续？', '确认取消收藏', {
      type: 'warning',
      confirmButtonText: '确认取消',
      cancelButtonText: '保留收藏'
    })
  } catch {
    return
  }

  removing.value = true
  try {
    await deleteCollection(props.collection.id)
    emit('removed', props.animeId)
  } catch (error) {
    emit('error', error instanceof Error ? error.message : '取消收藏失败')
  } finally {
    removing.value = false
  }
}
</script>

<style scoped>
.collection-form {
  display: grid;
  gap: 4px;
  max-width: none;
}

.collection-form :deep(.el-form-item__label) {
  color: #334155;
  font-weight: 700;
}

.collection-form-actions :deep(.el-form-item__content) {
  width: 100%;
}

.collection-action-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  width: 100%;
}

.collection-form :deep(.el-select__wrapper),
.collection-form :deep(.el-textarea__inner) {
  border-radius: 16px;
  box-shadow: 0 0 0 1px rgba(214, 222, 234, 0.92) inset;
}

.collection-form :deep(.el-select__wrapper) {
  min-height: 48px;
}

.collection-form :deep(.collection-multi-select .el-select__wrapper) {
  min-height: 48px;
  align-items: flex-start;
  overflow: hidden;
  padding-top: 6px;
  padding-bottom: 6px;
}

.collection-form :deep(.collection-multi-select .el-select__selection) {
  align-items: flex-start;
  align-content: flex-start;
  gap: 6px;
  min-height: 24px;
  max-height: 56px;
  overflow-y: auto;
  padding-right: 4px;
  scrollbar-gutter: stable;
}

.collection-form :deep(.collection-multi-select .el-select__selected-item) {
  min-width: 0;
  max-width: 100%;
}

.collection-form :deep(.collection-multi-select .el-select__input-wrapper) {
  flex: 0 1 40px;
  min-width: 24px;
}

.collection-form :deep(.collection-multi-select .el-tag) {
  margin: 0;
  max-width: 100%;
}

.collection-form :deep(.el-textarea__inner) {
  min-height: 116px;
}

.collection-form :deep(.el-button) {
  width: 100%;
  border-radius: 16px;
  box-shadow: 0 12px 28px rgba(57, 122, 218, 0.2);
}

.collection-remove:deep(.el-button) {
  box-shadow: none;
}

@media (max-width: 640px) {
  .collection-form :deep(.collection-multi-select .el-select__selection) {
    max-height: 52px;
  }

  .collection-action-row {
    grid-template-columns: 1fr;
  }
}
</style>
