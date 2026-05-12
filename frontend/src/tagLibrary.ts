export const DEFAULT_RELEASE_TAGS = ['BDRip', 'WebRip', 'WEB-DL', 'HDTV', '720p', '1080p', '2160p', 'HEVC', 'AVC']
export const DEFAULT_GROUP_TAGS = ['ANi', 'Lilith-Raws', 'NC-Raws', 'Skymoon-Raws', 'LoliHouse', '喵萌奶茶屋']

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
    defaults: DEFAULT_RELEASE_TAGS,
  },
  group: {
    key: 'ani-col-reg.group-tag-library',
    legacyKey: 'ani-col-reg.group-tags',
    defaults: DEFAULT_GROUP_TAGS,
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
  const config = TAG_LIBRARY_STORAGE[kind]
  if (typeof window === 'undefined') {
    return [...config.defaults]
  }

  const stored = readTagLibrary(config.key)
  if (stored !== null) {
    return saveTagLibrary(kind, [...config.defaults, ...stored])
  }

  const legacy = readTagLibrary(config.legacyKey) ?? []
  const migrated = uniqueTags([...config.defaults, ...legacy])
  return saveTagLibrary(kind, migrated)
}

export function saveTagLibrary(kind: TagLibraryKind, tags: string[]) {
  const config = TAG_LIBRARY_STORAGE[kind]
  const normalized = uniqueTags(tags)
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

export function resetTagLibrary(kind: TagLibraryKind) {
  return saveTagLibrary(kind, [...TAG_LIBRARY_STORAGE[kind].defaults])
}

export function rememberTagLibrary(kind: TagLibraryKind, currentLibrary: string[], tags: string[]) {
  return saveTagLibrary(kind, [...currentLibrary, ...tags])
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