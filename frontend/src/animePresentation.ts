import type { Anime, CollectionItem } from './types'

const SEASON_LABELS: Record<number, string> = {
  1: '1月',
  2: '4月',
  3: '7月',
  4: '10月'
}

const SOURCE_LABELS: Record<string, string> = {
  youranimes: 'YourAnimes',
  mikan: 'Mikan'
}

type MaybeTagValue = string | string[] | null | undefined
type AnimeWithScore = Anime & {
  community_score?: number | string | null
  rating?: number | string | null
  score?: number | string | null
}

export type PosterStatusTone = 'new' | 'ongoing' | 'finished'

export function seasonLabel(season?: number | null) {
  if (!season) {
    return '未知季度'
  }
  return SEASON_LABELS[season] || String(season)
}

export function sourceLabel(source?: string | null) {
  if (!source) {
    return '未知来源'
  }
  return SOURCE_LABELS[source] || source
}

export function posterFallback(title: string) {
  return title.trim().slice(0, 2).toUpperCase() || 'AN'
}

export function animeSecondaryTitle(anime: Anime) {
  return anime.title_jp || anime.title_en || sourceLabel(anime.source)
}

export function animeSeasonCaption(anime: Pick<Anime, 'year' | 'season'>) {
  return `${anime.year} · ${seasonLabel(anime.season)}`
}

export function animeCardSummary(anime: Anime) {
  const summary = anime.synopsis?.trim() || anime.title_jp?.trim() || anime.title_en?.trim() || anime.platforms?.trim()
  return summary || '打开详情后可按需补全简介与制作信息。'
}

export function animeCollectionLabel(collection?: Pick<CollectionItem, 'organize_status'> | null) {
  if (!collection) {
    return '未收藏'
  }
  return collection.organize_status === 'emby' ? '✓ 已整理' : '✓ 已收藏'
}

export function animeScoreLabel(anime: Anime) {
  const raw = (anime as AnimeWithScore).community_score ?? (anime as AnimeWithScore).rating ?? (anime as AnimeWithScore).score
  if (raw === undefined || raw === null || raw === '') {
    return null
  }

  const numeric = typeof raw === 'string' ? Number(raw) : raw
  if (typeof numeric === 'number' && Number.isFinite(numeric)) {
    return numeric.toFixed(numeric >= 10 ? 0 : 1)
  }

  return String(raw)
}

export function animePosterStatus(anime: Pick<Anime, 'year' | 'season' | 'premiere_date'>, reference = new Date()) {
  const premiereAge = resolvePremiereAge(anime.premiere_date, reference)
  if (premiereAge !== null && premiereAge >= 0 && premiereAge <= 42) {
    return { label: 'NEW', tone: 'new' as PosterStatusTone }
  }

  const currentYear = reference.getFullYear()
  const currentSeason = resolveCurrentSeason(reference)
  const distance = (currentYear - anime.year) * 4 + (currentSeason - anime.season)

  if (distance <= 0) {
    return { label: '连载中', tone: 'ongoing' as PosterStatusTone }
  }
  if (distance === 1) {
    return { label: 'NEW', tone: 'new' as PosterStatusTone }
  }
  return { label: '完结', tone: 'finished' as PosterStatusTone }
}

export function animePillTags(anime: Anime, limit = 4) {
  const collectionTags = [
    ...splitTagValues(anime.collection_item?.release_tags),
    ...splitTagValues(anime.collection_item?.group_tags)
  ]
  const sourceTags = splitLooseTags(anime.tags)
  const platformTags = splitLooseTags(anime.platforms)

  return uniqueTags([...collectionTags, ...sourceTags, ...platformTags, sourceLabel(anime.source)]).slice(0, limit)
}

export function splitTagValues(value?: MaybeTagValue) {
  if (Array.isArray(value)) {
    return uniqueTags(value)
  }

  const normalized = (value || '').trim()
  if (!normalized) {
    return []
  }

  if (normalized.startsWith('[') && normalized.endsWith(']')) {
    try {
      const parsed = JSON.parse(normalized)
      if (Array.isArray(parsed)) {
        return uniqueTags(parsed.filter((item): item is string => typeof item === 'string'))
      }
    } catch {
      // 如果不是有效的 JSON 数组，就回退到旧数据使用的逗号分隔解析方式。
    }
  }

  return uniqueTags(normalized.split(/[，,]/))
}

function splitLooseTags(value?: string | null) {
  return uniqueTags((value || '').split(/[、，,/|]/))
}

function uniqueTags(values: string[]) {
  return [...new Set(values.map((item) => item.trim()).filter(Boolean))]
}

function resolveCurrentSeason(reference = new Date()) {
  const month = reference.getMonth() + 1
  if (month <= 3) {
    return 1
  }
  if (month <= 6) {
    return 2
  }
  if (month <= 9) {
    return 3
  }
  return 4
}

function resolvePremiereAge(premiereDate: string | null | undefined, reference: Date) {
  if (!premiereDate) {
    return null
  }

  const parsed = new Date(premiereDate)
  const time = parsed.getTime()
  if (Number.isNaN(time)) {
    return null
  }

  return Math.floor((reference.getTime() - time) / 86400000)
}