export interface TagLibraryEntry {
  value: string
  label: string
  source: 'default' | 'user' | 'recent' | 'imported'
  color?: string
  recommended?: boolean
  popularity?: number
  lastUsedAt?: string | null
}

export interface TagLibraryState {
  version: 2
  entries: TagLibraryEntry[]
  recent: string[]
  popular: string[]
}

const DEFAULT_RELEASE_ENTRIES: TagLibraryEntry[] = [
  { value: 'BDRip', label: 'BDRip', source: 'default', color: 'ice', recommended: true },
  { value: 'WebRip', label: 'WebRip', source: 'default', color: 'cyan', recommended: true },
  { value: 'WEB-DL', label: 'WEB-DL', source: 'default', color: 'cyan', recommended: true },
  { value: 'HDTV', label: 'HDTV', source: 'default', color: 'slate' },
  { value: '720p', label: '720p', source: 'default', color: 'blue' },
  { value: '1080p', label: '1080p', source: 'default', color: 'blue', recommended: true },
  { value: '2160p', label: '2160p', source: 'default', color: 'amber' },
  { value: 'HEVC', label: 'HEVC', source: 'default', color: 'teal', recommended: true },
  { value: 'AVC', label: 'AVC', source: 'default', color: 'slate' },
]

const DEFAULT_GROUP_ENTRIES: TagLibraryEntry[] = [
  { value: 'ANi', label: 'ANi', source: 'default', color: 'mint', recommended: true },
  { value: 'Lilith-Raws', label: 'Lilith-Raws', source: 'default', color: 'sky', recommended: true },
  { value: 'NC-Raws', label: 'NC-Raws', source: 'default', color: 'sky' },
  { value: 'Skymoon-Raws', label: 'Skymoon-Raws', source: 'default', color: 'slate' },
  { value: 'LoliHouse', label: 'LoliHouse', source: 'default', color: 'blue', recommended: true },
  { value: '喵萌奶茶屋', label: '喵萌奶茶屋', source: 'default', color: 'mint' },
]

export const DEFAULT_RELEASE_TAGS = DEFAULT_RELEASE_ENTRIES.map((entry) => entry.value)
export const DEFAULT_GROUP_TAGS = DEFAULT_GROUP_ENTRIES.map((entry) => entry.value)

const RELEASE_TAG_EXCLUSIVE_GROUPS = {
  source: new Set(['bdrip', 'webrip', 'webdl', 'hdtv']),
  resolution: new Set(['720p', '1080p', '2160p']),
  codec: new Set(['hevc', 'avc']),
} as const

export type ReleaseTagGroup = keyof typeof RELEASE_TAG_EXCLUSIVE_GROUPS

export const RELEASE_TAG_GROUP_LABELS: Record<ReleaseTagGroup, string> = {
  source: '片源类型',
  resolution: '清晰度',
  codec: '编码格式',
}

const TAG_LIBRARY_STORAGE = {
  release: {
    key: 'ani-col-reg.release-tag-library',
    legacyKey: 'ani-col-reg.release-tags',
    defaults: DEFAULT_RELEASE_ENTRIES,
  },
  group: {
    key: 'ani-col-reg.group-tag-library',
    legacyKey: 'ani-col-reg.group-tags',
    defaults: DEFAULT_GROUP_ENTRIES,
  },
} as const

export type TagLibraryKind = keyof typeof TAG_LIBRARY_STORAGE

export function uniqueTags(values: string[]) {
  return [...new Set(values.map((item) => item.trim()).filter(Boolean))]
}

export function normalizeReleaseTags(tags: string[]) {
  const unique = uniqueTags(tags)
  const seenGroups = new Set<string>()
  const normalized: string[] = []

  for (let index = unique.length - 1; index >= 0; index -= 1) {
    const tag = unique[index]
    const group = releaseTagGroup(tag)
    if (group && seenGroups.has(group)) {
      continue
    }

    if (group) {
      seenGroups.add(group)
    }
    normalized.unshift(tag)
  }

  return normalized
}

export function mergeTagOptions(library: string[], current: string[]) {
  return uniqueTags([...library, ...current])
}

export function loadTagLibrary(kind: TagLibraryKind) {
  return loadTagLibraryState(kind).entries.map((entry) => entry.value)
}

export function saveTagLibrary(kind: TagLibraryKind, tags: string[]) {
  const nextState = applyTagValues(kind, loadTagLibraryState(kind), tags)
  return persistTagLibraryState(kind, nextState).entries.map((entry) => entry.value)
}

export function resetTagLibrary(kind: TagLibraryKind) {
  return persistTagLibraryState(kind, defaultTagLibraryState(kind)).entries.map((entry) => entry.value)
}

export function rememberTagLibrary(kind: TagLibraryKind, currentLibrary: string[], tags: string[]) {
  const state = applyTagValues(kind, loadTagLibraryState(kind), [...currentLibrary, ...tags], tags)
  return persistTagLibraryState(kind, state).entries.map((entry) => entry.value)
}

export function loadTagLibraryEntries(kind: TagLibraryKind) {
  return loadTagLibraryState(kind).entries
}

export function splitReleaseTagsByGroup(tags: string[]) {
  const grouped: Partial<Record<ReleaseTagGroup, string>> = {}
  const custom: string[] = []

  for (const tag of normalizeReleaseTags(tags)) {
    const group = releaseTagGroup(tag)
    if (group) {
      grouped[group] = tag
      continue
    }
    custom.push(tag)
  }

  return {
    source: grouped.source,
    resolution: grouped.resolution,
    codec: grouped.codec,
    custom,
  }
}

export function releaseTagGroup(tag: string): ReleaseTagGroup | null {
  const normalized = tag.trim().toLowerCase().replace(/[\s_.-]+/g, '')

  if (RELEASE_TAG_EXCLUSIVE_GROUPS.source.has(normalized)) {
    return 'source'
  }
  if (RELEASE_TAG_EXCLUSIVE_GROUPS.resolution.has(normalized)) {
    return 'resolution'
  }
  if (RELEASE_TAG_EXCLUSIVE_GROUPS.codec.has(normalized)) {
    return 'codec'
  }

  return null
}

function readTagLibrary(storageKey: string) {
  try {
    const raw = window.localStorage.getItem(storageKey)
    if (!raw) {
      return null
    }
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? uniqueTags(parsed.filter((item): item is string => typeof item === 'string')) : []
  } catch {
    return []
  }
}

function loadTagLibraryState(kind: TagLibraryKind): TagLibraryState {
  const config = TAG_LIBRARY_STORAGE[kind]

  if (typeof window === 'undefined') {
    return defaultTagLibraryState(kind)
  }

  const stored = readTagLibraryState(config.key)
  if (stored) {
    return persistTagLibraryState(kind, stored)
  }

  const legacy = readTagLibrary(config.legacyKey) ?? []
  if (legacy.length > 0) {
    return persistTagLibraryState(kind, applyTagValues(kind, defaultTagLibraryState(kind), [...config.defaults.map((entry) => entry.value), ...legacy]))
  }

  return persistTagLibraryState(kind, defaultTagLibraryState(kind))
}

function defaultTagLibraryState(kind: TagLibraryKind): TagLibraryState {
  const defaults = TAG_LIBRARY_STORAGE[kind].defaults.map((entry) => ({ ...entry }))
  return {
    version: 2,
    entries: defaults,
    recent: [],
    popular: defaults.filter((entry) => entry.recommended).map((entry) => entry.value).slice(0, 8)
  }
}

function applyTagValues(kind: TagLibraryKind, baseState: TagLibraryState, tags: string[], usedTags: string[] = []) {
  const previousEntries = new Map(baseState.entries.map((entry) => [normalizeTagKey(entry.value), entry]))
  const nextEntries = uniqueTags(tags)
    .map((value) => {
      const key = normalizeTagKey(value)
      const previous = previousEntries.get(key)
      const fallback = defaultTagEntry(kind, value)
      const entry = mergeTagEntry(fallback, previous)

      if (usedTags.some((used) => normalizeTagKey(used) === key)) {
        entry.popularity = (entry.popularity || 0) + 1
        entry.lastUsedAt = new Date().toISOString()
      }

      return entry
    })

  const recent = usedTags.length > 0 ? mergeRecentTags(baseState.recent, usedTags) : baseState.recent

  return finalizeTagLibraryState({
    version: 2,
    entries: nextEntries,
    recent,
    popular: baseState.popular
  })
}

function persistTagLibraryState(kind: TagLibraryKind, state: TagLibraryState) {
  const config = TAG_LIBRARY_STORAGE[kind]
  const normalized = finalizeTagLibraryState(state)

  if (typeof window === 'undefined') {
    return normalized
  }

  try {
    window.localStorage.setItem(config.key, JSON.stringify(normalized))
    window.localStorage.removeItem(config.legacyKey)
  } catch {
    return normalized
  }

  return normalized
}

function readTagLibraryState(storageKey: string): TagLibraryState | null {
  try {
    const raw = window.localStorage.getItem(storageKey)
    if (!raw) {
      return null
    }

    const parsed = JSON.parse(raw)
    if (Array.isArray(parsed)) {
      return null
    }
    if (!parsed || typeof parsed !== 'object' || !Array.isArray(parsed.entries)) {
      return null
    }

    return finalizeTagLibraryState({
      version: 2,
      entries: parsed.entries,
      recent: Array.isArray(parsed.recent) ? parsed.recent : [],
      popular: Array.isArray(parsed.popular) ? parsed.popular : []
    })
  } catch {
    return null
  }
}

function finalizeTagLibraryState(state: TagLibraryState): TagLibraryState {
  const entries = state.entries
    .map((entry) => normalizeTagEntry(entry))
    .filter((entry, index, all) => all.findIndex((candidate) => normalizeTagKey(candidate.value) === normalizeTagKey(entry.value)) === index)

  const entryKeySet = new Set(entries.map((entry) => normalizeTagKey(entry.value)))
  const recent = uniqueTags(state.recent).filter((value) => entryKeySet.has(normalizeTagKey(value))).slice(0, 8)
  const popular = uniqueTags([
    ...state.popular,
    ...entries
      .filter((entry) => entry.recommended || (entry.popularity || 0) > 0)
      .sort((left, right) => (right.popularity || 0) - (left.popularity || 0) || Number(Boolean(right.recommended)) - Number(Boolean(left.recommended)))
      .map((entry) => entry.value)
  ]).filter((value) => entryKeySet.has(normalizeTagKey(value))).slice(0, 8)

  return {
    version: 2,
    entries,
    recent,
    popular
  }
}

function defaultTagEntry(kind: TagLibraryKind, value: string): TagLibraryEntry {
  const key = normalizeTagKey(value)
  const defaults = TAG_LIBRARY_STORAGE[kind].defaults
  const matchedDefault = defaults.find((entry) => normalizeTagKey(entry.value) === key)
  if (matchedDefault) {
    return { ...matchedDefault }
  }

  return {
    value: value.trim(),
    label: value.trim(),
    source: 'user'
  }
}

function mergeTagEntry(base: TagLibraryEntry, override?: TagLibraryEntry | null): TagLibraryEntry {
  if (!override) {
    return normalizeTagEntry(base)
  }

  return normalizeTagEntry({
    ...base,
    ...override,
    value: override.value || base.value,
    label: override.label || base.label,
  })
}

function normalizeTagEntry(entry: TagLibraryEntry): TagLibraryEntry {
  const value = entry.value.trim()
  return {
    value,
    label: (entry.label || value).trim(),
    source: entry.source || 'user',
    color: entry.color,
    recommended: Boolean(entry.recommended),
    popularity: typeof entry.popularity === 'number' ? entry.popularity : undefined,
    lastUsedAt: entry.lastUsedAt || null,
  }
}

function mergeRecentTags(existing: string[], usedTags: string[]) {
  return uniqueTags([...usedTags.slice().reverse(), ...existing]).slice(0, 8)
}

function normalizeTagKey(value: string) {
  return value.trim().toLowerCase()
}