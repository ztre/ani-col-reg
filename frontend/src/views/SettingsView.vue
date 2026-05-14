<template>
  <section class="settings-page">
    <header class="settings-hero">
      <div>
        <p class="settings-eyebrow">Settings</p>
        <h1>系统配置中心</h1>
        <p>集中管理数据源、同步方式、封面缓存和管理员账号，避免在不同页面来回切换。</p>
      </div>
      <el-button class="settings-refresh" :icon="RefreshRight" @click="load">重新获取</el-button>
    </header>

    <div v-loading="loading" class="settings-grid">
      <section class="settings-card">
        <div class="settings-card-copy">
          <p class="settings-label">Source</p>
          <h2>数据源</h2>
          <p>“搜索并更新”以及详情补抓都会使用这里选中的站点。切换后会清空当前番剧库，避免不同源的数据混在一起。</p>
        </div>

        <el-radio-group v-model="form.anime_source" class="sync-strategy-group">
          <label class="strategy-option" :class="{ 'strategy-option--active': form.anime_source === 'youranimes' }">
            <el-radio value="youranimes">YourAnimes</el-radio>
            <p>详情字段更完整，适合优先补全简介、制作阵容、声优和 PV 等信息。</p>
          </label>

          <label class="strategy-option" :class="{ 'strategy-option--active': form.anime_source === 'mikan' }">
            <el-radio value="mikan">Mikan</el-radio>
            <p>适合优先同步季度条目和封面，打开弹窗时再按需补抓详情并缓存。</p>
          </label>
        </el-radio-group>

        <div class="settings-readonly">
          <span>当前请求地址</span>
          <strong>{{ activeSourceBaseUrl }}</strong>
        </div>
      </section>

      <section class="settings-card">
        <div class="settings-card-copy">
          <p class="settings-label">Sync</p>
          <h2>源站同步策略</h2>
          <p>决定“搜索并更新”后，库里旧条目是继续保留，还是按源站的单季度结果收口。带关键词搜索，或没有明确选中单季度时，都会按增量同步处理。</p>
        </div>

        <el-radio-group v-model="form.sync_strategy" class="sync-strategy-group">
          <label class="strategy-option" :class="{ 'strategy-option--active': form.sync_strategy === 'incremental' }">
            <el-radio value="incremental">增量同步</el-radio>
            <p>以保留现有库内容为主，只补充或更新这次抓到的条目，不主动删除旧数据。适合日常搜索、关键词检索、全年范围刷新，以及需要先人工确认的场景。</p>
          </label>

          <label class="strategy-option" :class="{ 'strategy-option--active': form.sync_strategy === 'replace-season' }">
            <el-radio value="replace-season">单季度对齐</el-radio>
            <p>只在“无关键词 + 明确单季度”时生效，会以该季度的源站结果为准：新条目补入、已有条目更新、已不在结果中的未收藏旧条目移除；已收藏内容仍会保留。若选择全年或带关键词，会自动回退为增量同步。</p>
          </label>
        </el-radio-group>
      </section>

      <section class="settings-card settings-card--wide">
        <div class="settings-card-copy">
          <p class="settings-label">Tags</p>
          <h2>标签管理</h2>
          <p>管理当前浏览器里常用的资源标签和字幕组标签，收藏整理时可以直接复用。这里修改的是可选标签列表，不会直接改动已有收藏记录。</p>
        </div>

        <div class="tag-manager-grid">
          <section class="tag-manager-panel">
            <div class="tag-manager-heading">
              <div class="tag-manager-copy">
                <h3>资源标签</h3>
                <p>用于整理片源类型、编码或分辨率，例如 BDRip、WEB-DL、1080p。</p>
              </div>

              <el-button text class="tag-manager-reset" @click="resetManagedTags('release')">恢复默认</el-button>
            </div>

            <div class="tag-manager-entry">
              <el-input v-model="releaseTagDraft" size="large" placeholder="新增资源标签" @keyup.enter="addManagedTag('release')" />
              <el-button class="tag-manager-add" @click="addManagedTag('release')">添加</el-button>
            </div>

            <div v-if="releaseTagLibrary.length" class="tag-chip-list">
              <el-tag v-for="tag in releaseTagLibrary" :key="tag" closable @close="removeManagedTag('release', tag)">{{ tag }}</el-tag>
            </div>
            <div v-else class="tag-chip-empty">当前没有可复用的资源标签</div>
          </section>

          <section class="tag-manager-panel">
            <div class="tag-manager-heading">
              <div class="tag-manager-copy">
                <h3>字幕组 / 压制组</h3>
                <p>用于整理字幕组、压制组或发布团队，例如 ANi、Lilith-Raws、LoliHouse。</p>
              </div>

              <el-button text class="tag-manager-reset" @click="resetManagedTags('group')">恢复默认</el-button>
            </div>

            <div class="tag-manager-entry">
              <el-input v-model="groupTagDraft" size="large" placeholder="新增字幕组 / 压制组标签" @keyup.enter="addManagedTag('group')" />
              <el-button class="tag-manager-add" @click="addManagedTag('group')">添加</el-button>
            </div>

            <div v-if="groupTagLibrary.length" class="tag-chip-list">
              <el-tag v-for="tag in groupTagLibrary" :key="tag" type="info" closable @close="removeManagedTag('group', tag)">{{ tag }}</el-tag>
            </div>
            <div v-else class="tag-chip-empty">当前没有可复用的字幕组标签</div>
          </section>
        </div>
      </section>

      <section class="settings-card">
        <div class="settings-card-copy">
          <p class="settings-label">Maintenance</p>
          <h2>缓存与数据维护</h2>
          <p>这里可以清理本地封面缓存，或重置收藏管理里的本地收藏记录。重置收藏只会删除整理状态、标签和备注，不会移除番剧库条目和封面文件。</p>
        </div>

        <div class="maintenance-metrics">
          <div class="metric-card">
            <span>收藏记录数</span>
            <strong>{{ settingsSnapshot?.collection_count ?? 0 }}</strong>
          </div>

          <div class="metric-card">
            <span>缓存文件数</span>
            <strong>{{ settingsSnapshot?.cover_cache_file_count ?? 0 }}</strong>
          </div>

          <div class="metric-card">
            <span>缓存体积</span>
            <strong>{{ coverCacheSizeLabel }}</strong>
          </div>
        </div>

        <div class="settings-readonly">
          <span>当前使用数据源</span>
          <strong>{{ activeSourceLabel }}</strong>
        </div>

        <div class="settings-readonly">
          <span>最近一次保存</span>
          <strong>{{ updatedAtLabel }}</strong>
        </div>

        <div class="settings-readonly settings-readonly--danger">
          <span>数据重置范围</span>
          <strong>仅清理收藏记录，不删除番剧库</strong>
        </div>

        <div class="maintenance-actions">
          <el-button :loading="clearingCache" @click="clearCache">清理封面缓存</el-button>
          <el-button class="maintenance-reset" :loading="resettingCollectionData" @click="resetCollectionData">重置收藏数据</el-button>
        </div>
      </section>

      <section class="settings-card">
        <div class="settings-card-copy">
          <p class="settings-label">Security</p>
          <h2>登录与账号</h2>
          <p>修改管理员账号或密码后会立即要求重新登录，避免旧登录态继续使用过期凭据。</p>
        </div>

        <el-form label-position="top" class="settings-form">
          <el-form-item label="管理员账号">
            <el-input v-model="form.admin_username" size="large" />
          </el-form-item>

          <el-form-item label="当前密码">
            <el-input v-model="form.current_password" size="large" show-password placeholder="仅在修改密码时填写" />
          </el-form-item>

          <el-form-item label="新密码">
            <el-input v-model="form.new_password" size="large" show-password placeholder="至少 6 位，留空则不修改" />
          </el-form-item>
        </el-form>
      </section>
    </div>

    <div class="settings-actions">
      <el-button class="settings-cancel" size="large" @click="load">恢复当前设置</el-button>
      <el-button class="settings-submit" type="primary" size="large" :loading="saving" @click="submit">保存并应用</el-button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { RefreshRight } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthSession } from '../auth'
import { clearCoverCache, getSettings, resetCollectionData as resetCollectionDataRequest, updateSettings } from '../services/settingsService'
import {
  loadManagedTagEntries,
  loadManagedTags,
  resetManagedTags as resetStoredManagedTags,
  saveManagedTags,
  type TagLibraryKind,
} from '../services/tagService'
import type { AppSettings } from '../types'

const router = useRouter()
const session = useAuthSession()
const loading = ref(false)
const saving = ref(false)
const clearingCache = ref(false)
const resettingCollectionData = ref(false)
const currentAdminUsername = ref('admin')
const settingsSnapshot = ref<AppSettings | null>(null)
const releaseTagLibrary = ref<string[]>(loadManagedTags('release'))
const groupTagLibrary = ref<string[]>(loadManagedTags('group'))
const releaseTagEntries = ref(loadManagedTagEntries('release'))
const groupTagEntries = ref(loadManagedTagEntries('group'))
const releaseTagDraft = ref('')
const groupTagDraft = ref('')
const form = reactive({
  anime_source: 'youranimes' as AppSettings['anime_source'],
  sync_strategy: 'incremental' as AppSettings['sync_strategy'],
  admin_username: 'admin',
  current_password: '',
  new_password: ''
})

const activeSourceLabel = computed(() => (form.anime_source === 'mikan' ? 'Mikan' : 'YourAnimes'))
const activeSourceBaseUrl = computed(() => {
  if (!settingsSnapshot.value) return '-'
  return form.anime_source === 'mikan' ? settingsSnapshot.value.mikan_base_url : settingsSnapshot.value.youranimes_base_url
})
const updatedAtLabel = computed(() => {
  if (!settingsSnapshot.value?.updated_at) return '-'
  return new Date(settingsSnapshot.value.updated_at).toLocaleString()
})
const coverCacheSizeLabel = computed(() => formatBytes(settingsSnapshot.value?.cover_cache_total_bytes || 0))
const tagLibraryLabels: Record<TagLibraryKind, string> = {
  release: '资源标签',
  group: '字幕组标签'
}

function applySnapshot(settings: AppSettings) {
  settingsSnapshot.value = settings
  currentAdminUsername.value = settings.admin_username
  form.anime_source = settings.anime_source
  form.sync_strategy = settings.sync_strategy
  form.admin_username = settings.admin_username
  form.current_password = ''
  form.new_password = ''
}

function formatBytes(value: number) {
  if (value <= 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let size = value
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex += 1
  }
  return `${size.toFixed(size >= 10 || unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`
}

async function load() {
  loading.value = true
  try {
    const settings = await getSettings()
    session.applySettings(settings)
    applySnapshot(settings)
    releaseTagLibrary.value = loadManagedTags('release')
    groupTagLibrary.value = loadManagedTags('group')
    releaseTagEntries.value = loadManagedTagEntries('release')
    groupTagEntries.value = loadManagedTagEntries('group')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载设置失败')
  } finally {
    loading.value = false
  }
}

function getTagLibraryRef(kind: TagLibraryKind) {
  return kind === 'release' ? releaseTagLibrary : groupTagLibrary
}

function getTagDraftRef(kind: TagLibraryKind) {
  return kind === 'release' ? releaseTagDraft : groupTagDraft
}

function addManagedTag(kind: TagLibraryKind) {
  const draftRef = getTagDraftRef(kind)
  const libraryRef = getTagLibraryRef(kind)
  const value = draftRef.value.trim()
  if (!value) {
    ElMessage.warning(`请输入${tagLibraryLabels[kind]}`)
    return
  }

  const next = saveManagedTags(kind, [...libraryRef.value, value])
  if (next.length === libraryRef.value.length) {
    ElMessage.info(`${tagLibraryLabels[kind]}已存在`)
    return
  }

  libraryRef.value = next
  syncTagEntries(kind)
  draftRef.value = ''
  ElMessage.success(`已添加${tagLibraryLabels[kind]}`)
}

function removeManagedTag(kind: TagLibraryKind, tag: string) {
  const libraryRef = getTagLibraryRef(kind)
  libraryRef.value = saveManagedTags(kind, libraryRef.value.filter((item) => item !== tag))
  syncTagEntries(kind)
  ElMessage.success(`已移除${tag}`)
}

function resetManagedTags(kind: TagLibraryKind) {
  const libraryRef = getTagLibraryRef(kind)
  libraryRef.value = resetStoredManagedTags(kind)
  syncTagEntries(kind)
  ElMessage.success(`已恢复默认${tagLibraryLabels[kind]}`)
}

function syncTagEntries(kind: TagLibraryKind) {
  if (kind === 'release') {
    releaseTagEntries.value = loadManagedTagEntries('release')
    return
  }
  groupTagEntries.value = loadManagedTagEntries('group')
}

async function clearCache() {
  try {
    await ElMessageBox.confirm('这会删除本地封面缓存文件，并重置所有指向本地缓存的封面引用。番剧条目、收藏记录和同步映射不会被删除。是否继续？', '确认清理封面缓存', {
      type: 'warning',
      confirmButtonText: '继续清理',
      cancelButtonText: '取消'
    })
  } catch {
    return
  }

  clearingCache.value = true
  try {
    const result = await clearCoverCache()
    await load()
    ElMessage.success(`已清理 ${result.deleted_files} 个缓存文件，释放 ${formatBytes(result.deleted_bytes)}，并重置 ${result.reset_cover_urls} 条封面记录`)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '清理缓存失败')
  } finally {
    clearingCache.value = false
  }
}

async function resetCollectionData() {
  try {
    await ElMessageBox.confirm(
      '这会清空收藏管理中的本地收藏记录，包括整理状态、资源标签、字幕组标签和备注，但不会删除番剧库条目、封面缓存或同步映射。是否继续？',
      '确认重置收藏数据',
      {
        type: 'warning',
        confirmButtonText: '继续',
        cancelButtonText: '取消'
      }
    )
    await ElMessageBox.confirm(
      '该操作不可撤销。重置后，收藏页中的所有本地整理信息都会被清空。是否确认执行重置？',
      '二次确认',
      {
        type: 'error',
        confirmButtonText: '确认重置',
        cancelButtonText: '取消'
      }
    )
  } catch {
    return
  }

  resettingCollectionData.value = true
  try {
    const result = await resetCollectionDataRequest()
    await load()
    ElMessage.success(`已清理 ${result.deleted_collections} 条收藏记录`)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '重置收藏数据失败')
  } finally {
    resettingCollectionData.value = false
  }
}

async function submit() {
  const previousSource = settingsSnapshot.value?.anime_source
  const sourceChanged = Boolean(previousSource && previousSource !== form.anime_source)
  if (sourceChanged) {
    try {
      await ElMessageBox.confirm(
        `即将切换到 ${activeSourceLabel.value}。保存后会清空当前番剧库条目并清理本地封面缓存，避免不同源的数据继续混用。切换完成后，请重新执行一次“搜索并更新”从新源拉取数据。是否继续？`,
        '确认切换数据源',
        {
          type: 'warning',
          confirmButtonText: '继续切换',
          cancelButtonText: '取消'
        }
      )
    } catch {
      return
    }
  }

  saving.value = true
  try {
    const previousUsername = currentAdminUsername.value
    const requireRelogin = Boolean(form.new_password) || form.admin_username !== previousUsername
    const settings = await updateSettings({
      anime_source: form.anime_source,
      sync_strategy: form.sync_strategy,
      admin_username: form.admin_username,
      current_password: form.current_password || undefined,
      new_password: form.new_password || undefined
    })
    session.applySettings(settings)
    applySnapshot(settings)
    const successMessage = requireRelogin
      ? '设置已保存，请重新登录'
      : sourceChanged
        ? '设置已保存，番剧库和本地封面缓存已按新数据源重置'
        : '设置已保存并生效'
    ElMessage.success(successMessage)

    if (requireRelogin) {
      await session.logout()
      await router.replace('/login')
    }
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '保存设置失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  void load()
})
</script>

<style scoped>
.settings-page {
  display: grid;
  gap: 22px;
}

.settings-hero {
  position: relative;
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: flex-end;
  justify-content: space-between;
  padding: 28px clamp(240px, 34vw, 360px) 28px 30px;
  overflow: hidden;
  isolation: isolate;
  background: var(--hero-surface);
  border: 1px solid var(--surface-line);
  border-radius: 28px;
  box-shadow: var(--elevation-hero);
}

.settings-hero::before {
  position: absolute;
  inset: 14px 12px 10px auto;
  width: min(40%, 280px);
  background-image: var(--hero-settings-image);
  background-repeat: no-repeat;
  background-size: contain;
  background-position: right center;
  content: '';
  pointer-events: none;
  opacity: 0.96;
  z-index: 0;
}

.settings-hero::after {
  position: absolute;
  inset: auto -6% -34% auto;
  width: 300px;
  height: 300px;
  background: var(--hero-art-glow);
  content: '';
  pointer-events: none;
}

.settings-hero > * {
  position: relative;
  z-index: 1;
}

.settings-eyebrow,
.settings-label {
  margin: 0;
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.settings-hero h1,
.settings-card-copy h2 {
  margin: 0;
}

.settings-hero p:last-child,
.settings-card-copy p:last-child,
.metric-card span,
.settings-readonly span,
.strategy-option p,
.switch-row span {
  color: var(--text-muted);
}

.settings-refresh {
  border-radius: 16px;
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.settings-card {
  display: grid;
  gap: 18px;
  padding: 24px;
  background: var(--surface-card);
  border: 1px solid var(--surface-line);
  border-radius: 24px;
  box-shadow: var(--elevation-card);
}

.settings-card--wide {
  grid-column: 1 / -1;
}

.settings-card-copy {
  display: grid;
  gap: 6px;
}

.settings-form {
  display: grid;
}

.tag-manager-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.tag-manager-panel {
  display: grid;
  gap: 14px;
  padding: 18px;
  background: var(--surface-card-soft);
  border: 1px solid rgba(144, 173, 214, 0.12);
  border-radius: 20px;
}

.tag-manager-heading {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: flex-start;
  justify-content: space-between;
}

.tag-manager-copy {
  display: grid;
  gap: 4px;
}

.tag-manager-copy h3,
.tag-manager-copy p {
  margin: 0;
}

.tag-manager-copy h3 {
  color: var(--text-strong);
  font-size: 18px;
}

.tag-manager-copy p,
.tag-chip-empty {
  color: var(--text-muted);
  line-height: 1.65;
}

.tag-manager-reset {
  min-height: 40px;
  padding-inline: 0;
  color: var(--tag-manager-muted-text);
}

.tag-manager-reset:hover,
.tag-manager-reset:focus-visible {
  color: var(--text-soft);
}

.tag-manager-entry {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
}

.tag-manager-add {
  min-width: 96px;
  min-height: 46px;
  color: var(--text-soft);
  background: var(--tag-manager-add-bg);
  border-color: var(--tag-manager-add-border);
}

.tag-manager-add:hover,
.tag-manager-add:focus-visible {
  color: var(--text-strong);
  background: var(--tag-manager-add-hover-bg);
  border-color: var(--tag-manager-add-hover-border);
}

.tag-chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-chip-list :deep(.el-tag) {
  min-height: 40px;
  padding-inline: 14px;
  color: var(--text-soft);
  background: var(--tag-manager-chip-bg);
  border-color: var(--tag-manager-chip-border);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
}

.tag-chip-list :deep(.el-tag.el-tag--primary) {
  color: var(--tag-manager-chip-primary-text);
  background: var(--tag-manager-chip-primary-bg);
  border-color: var(--tag-manager-chip-primary-border);
}

.tag-chip-list :deep(.el-tag.el-tag--info) {
  color: var(--tag-manager-chip-info-text);
  background: var(--tag-manager-chip-info-bg);
  border-color: var(--tag-manager-chip-info-border);
}

.tag-chip-list :deep(.el-tag__close) {
  color: currentColor;
  background: transparent;
}

.tag-chip-list :deep(.el-tag__close:hover) {
  color: var(--text-strong);
  background: var(--button-text-hover-bg);
}

.tag-chip-empty {
  padding: 14px 16px;
  background: var(--tag-manager-empty-bg);
  border: 1px dashed var(--tag-manager-empty-border);
  border-radius: 16px;
  font-size: 13px;
}

.settings-inline-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.settings-inline-grid--triple {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.sync-strategy-group {
  display: grid;
  gap: 12px;
}

.strategy-option {
  display: grid;
  gap: 8px;
  padding: 16px;
  background: var(--surface-card-soft);
  border: 1px solid var(--panel-soft-border);
  border-radius: 18px;
}

.strategy-option--active {
  border-color: var(--notice-info-border);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--notice-info-border) 65%, transparent) inset;
}

.strategy-option p {
  margin: 0;
  line-height: 1.65;
}

.switch-row {
  display: inline-flex;
  gap: 12px;
  align-items: center;
  min-height: 46px;
  padding: 0 14px;
  background: var(--surface-card-soft);
  border: 1px solid var(--panel-soft-border);
  border-radius: 18px;
}

.maintenance-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.metric-card,
.settings-readonly {
  display: grid;
  gap: 4px;
  padding: 14px 16px;
  background: var(--surface-card-soft);
  border: 1px solid var(--panel-soft-border);
  border-radius: 18px;
}

.metric-card strong,
.settings-readonly strong {
  color: var(--text-strong);
}

.settings-readonly--danger {
  border-color: var(--danger-panel-border);
  background: var(--danger-panel-bg);
}

.maintenance-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: flex-start;
}

.maintenance-reset {
  color: var(--danger-button-text);
  background: var(--danger-button-bg);
  border-color: var(--danger-button-border);
}

.maintenance-reset:hover,
.maintenance-reset:focus-visible {
  color: var(--text-strong);
  border-color: var(--danger-button-hover-border);
  background: var(--danger-button-hover-bg);
}

.settings-actions {
  position: sticky;
  bottom: 18px;
  z-index: 12;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: var(--action-bar-bg);
  border: 1px solid var(--surface-line);
  border-radius: 22px;
  box-shadow: var(--elevation-card);
  backdrop-filter: blur(14px);
}

.settings-cancel,
.settings-submit {
  min-width: 148px;
  height: 50px;
  border-radius: 18px;
  font-weight: 700;
}

.settings-cancel {
  border-color: var(--surface-line-strong);
}

.settings-submit {
  color: var(--action-primary-text);
  border: none;
  background: var(--action-primary-bg);
  box-shadow: var(--action-primary-shadow);
}

.settings-submit:hover,
.settings-submit:focus-visible {
  transform: translateY(-1px);
  box-shadow: var(--action-primary-shadow-hover);
}

.settings-form :deep(.el-input__wrapper),
.settings-form :deep(.el-select__wrapper),
.settings-form :deep(.el-textarea__inner),
.settings-form :deep(.el-input-number) {
  border-radius: 16px;
  background: var(--surface-input);
  box-shadow: 0 0 0 1px var(--surface-line) inset;
}

.settings-form :deep(.el-input__wrapper),
.settings-form :deep(.el-select__wrapper) {
  min-height: 48px;
}

.tag-manager-panel :deep(.el-input__wrapper) {
  min-height: 48px;
  border-radius: 16px;
  background: var(--surface-input);
  box-shadow: 0 0 0 1px var(--surface-line) inset;
}

.tag-manager-panel :deep(.el-button),
.tag-manager-panel :deep(.el-tag) {
  border-radius: 14px;
}

.sync-strategy-group :deep(.el-radio__label) {
  color: var(--text-strong);
  font-weight: 600;
}

@media (max-width: 1080px) {
  .settings-hero {
    padding-right: 30px;
  }

  .settings-hero::before {
    width: 180px;
    opacity: 0.28;
  }

  .settings-grid,
  .settings-inline-grid,
  .settings-inline-grid--triple,
  .maintenance-metrics,
  .tag-manager-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .settings-actions {
    flex-direction: column;
    align-items: stretch;
    bottom: 12px;
  }

  .settings-cancel,
  .settings-submit {
    width: 100%;
  }

  .tag-manager-entry {
    grid-template-columns: 1fr;
  }
}
</style>
