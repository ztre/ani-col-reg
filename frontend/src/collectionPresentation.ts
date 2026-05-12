import type { CollectionItem } from './types'

export type CollectionOrganizeStatus = CollectionItem['organize_status']

export const ORGANIZE_STATUS_LABELS: Record<CollectionOrganizeStatus, string> = {
  pending: '待整理',
  emby: '已整理',
}

export const ORGANIZE_STATUS_OPTIONS = [
  { value: 'pending' as const, label: ORGANIZE_STATUS_LABELS.pending },
  { value: 'emby' as const, label: ORGANIZE_STATUS_LABELS.emby },
]

export function normalizeOrganizeStatus(collection?: Pick<CollectionItem, 'organize_status'> | null): CollectionOrganizeStatus {
  return collection?.organize_status === 'emby' ? 'emby' : 'pending'
}

export function collectionStageLabel(collection?: Pick<CollectionItem, 'organize_status'> | null) {
  if (!collection) {
    return '番剧库'
  }
  return ORGANIZE_STATUS_LABELS[normalizeOrganizeStatus(collection)]
}

export function collectionActionLabel(collection?: Pick<CollectionItem, 'organize_status'> | null) {
  if (!collection) {
    return '加入收藏'
  }
  return ORGANIZE_STATUS_LABELS[normalizeOrganizeStatus(collection)]
}

export function collectionStatusTone(collection?: Pick<CollectionItem, 'organize_status'> | null) {
  if (!collection) {
    return 'library'
  }
  return normalizeOrganizeStatus(collection)
}

export function collectionStatusTagType(collection?: Pick<CollectionItem, 'organize_status'> | null) {
  if (!collection) {
    return 'info'
  }
  return normalizeOrganizeStatus(collection) === 'emby' ? 'success' : 'warning'
}

export function isWebReleaseTag(tag?: string | null) {
  const normalized = (tag || '').trim().toLowerCase()
  if (!normalized) {
    return false
  }

  return normalized.includes('web-dl') || normalized.includes('webrip') || normalized.includes('web rip') || normalized.startsWith('web')
}