import {
  loadTagLibrary,
  loadTagLibraryEntries,
  rememberTagLibrary,
  resetTagLibrary,
  saveTagLibrary,
  type TagLibraryEntry,
  type TagLibraryKind,
} from '../tagLibrary'

export type { TagLibraryEntry, TagLibraryKind }

export function loadManagedTags(kind: TagLibraryKind) {
  return loadTagLibrary(kind)
}

export function loadManagedTagEntries(kind: TagLibraryKind): TagLibraryEntry[] {
  return loadTagLibraryEntries(kind)
}

export function saveManagedTags(kind: TagLibraryKind, tags: string[]) {
  return saveTagLibrary(kind, tags)
}

export function resetManagedTags(kind: TagLibraryKind) {
  return resetTagLibrary(kind)
}

export function rememberManagedTags(kind: TagLibraryKind, currentLibrary: string[], tags: string[]) {
  return rememberTagLibrary(kind, currentLibrary, tags)
}