import type { CollectionItem, SeriesGroup, SourceImportResult, SourceSearchResult } from '../types'

import { buildSearchParams, request } from './http'

export function collect(animeId: number): Promise<CollectionItem> {
  return request<CollectionItem>('/api/collection', {
    method: 'POST',
    body: JSON.stringify({ anime_id: animeId })
  })
}

export function uncollect(animeId: number): Promise<void> {
  return request<void>(`/api/collection/anime/${animeId}`, {
    method: 'DELETE'
  })
}

/** 标记/取消该季度在 Emby 中已整理 */
export function setEmbyOrganized(animeId: number, embyOrganized: boolean): Promise<CollectionItem> {
  return request<CollectionItem>(`/api/collection/anime/${animeId}/emby`, {
    method: 'PUT',
    body: JSON.stringify({ emby_organized: embyOrganized })
  })
}

export function fetchCollectedSeries(): Promise<SeriesGroup[]> {
  return request<SeriesGroup[]>('/api/collection/series')
}

export function searchSeries(q: string): Promise<SeriesGroup[]> {
  const search = buildSearchParams({ q })
  return request<SeriesGroup[]>(`/api/search?${search.toString()}`)
}

/** 从数据源实时搜索番剧（同关键词，独立于本地搜索） */
export function fetchSourceSearch(q: string, page = 1, pageSize = 20): Promise<SourceSearchResult> {
  const search = buildSearchParams({ query: q, page, page_size: pageSize })
  return request<SourceSearchResult>(`/api/search/source?${search.toString()}`)
}

/** 将数据源条目导入本地库（幂等），返回本地番剧 id */
export function importFromSource(sourceId: string): Promise<SourceImportResult> {
  return request<SourceImportResult>('/api/search/import', {
    method: 'POST',
    body: JSON.stringify({ source_id: sourceId })
  })
}
