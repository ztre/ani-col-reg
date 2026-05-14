import type { Anime, PaginatedAnime } from '../types'

import { buildSearchParams, request } from './http'

export interface AnimeQuery {
  year?: number
  season?: number
  keyword?: string
  platform?: string
  collected?: boolean
  release_tag?: string | string[]
  group_tag?: string | string[]
  page?: number
  page_size?: number
}

export function listAnime(query: AnimeQuery): Promise<PaginatedAnime> {
  const params = buildSearchParams(query)
  return request<PaginatedAnime>(`/api/anime?${params.toString()}`)
}

export function searchAnime(query: {
  year: number
  season?: number
  keyword?: string
  page?: number
  page_size?: number
}): Promise<PaginatedAnime> {
  return request<PaginatedAnime>('/api/anime/search', {
    method: 'POST',
    body: JSON.stringify(query)
  })
}

export function getAnime(id: number): Promise<Anime> {
  return request<Anime>(`/api/anime/${id}`)
}