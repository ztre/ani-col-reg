import type { Anime, PaginatedAnime, SeasonSummary } from '../types'

import { buildSearchParams, request } from './http'

export interface AnimeQuery {
  year?: number
  season?: number
  keyword?: string
  collected?: boolean
  series_key?: string
  page?: number
  page_size?: number
}

export function fetchAnime(params: AnimeQuery): Promise<PaginatedAnime> {
  const search = buildSearchParams(params)
  return request<PaginatedAnime>(`/api/anime?${search.toString()}`)
}

export function fetchAnimeDetail(id: number): Promise<Anime> {
  return request<Anime>(`/api/anime/${id}`)
}

export async function fetchSeasons(): Promise<SeasonSummary[]> {
  const seasons = await request<SeasonSummary[]>('/api/seasons')
  return seasons.sort((a, b) => b.year - a.year || b.season - a.season)
}

export function syncSeason(year: number, season: number | null): Promise<PaginatedAnime> {
  return request<PaginatedAnime>('/api/anime/search', {
    method: 'POST',
    body: JSON.stringify({ year, season, page: 1, page_size: 24 })
  })
}
