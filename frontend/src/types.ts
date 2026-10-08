export interface Anime {
  id: number
  source: string
  source_id: string | null
  source_url: string | null
  title_cn: string
  title_jp: string | null
  title_en: string | null
  aliases: string | null
  synopsis: string | null
  year: number
  season: number
  premiere_date: string | null
  platforms: string | null
  staff: string | null
  cast: string | null
  tags: string | null
  pv_url: string | null
  cover_url: string | null
  detail_refreshing: boolean
  series_key: string
  series_title: string
  season_label: string | null
  is_collected: boolean
  /** 该季度是否已在 Emby 中整理（媒体库归档标记） */
  emby_organized: boolean
}

export interface PaginatedAnime {
  items: Anime[]
  total: number
  page: number
  page_size: number
}

export interface SeasonSummary {
  year: number
  season: number
  count: number
}

export interface SeriesGroup {
  series_key: string
  series_title: string
  entry_count: number
  latest_year: number
  latest_season: number
  cover_url: string | null
  entries: Anime[]
}

/** 数据源搜索结果条目（YourAnimes 等源站实时检索，非本地库数据） */
export interface SourceSearchItem {
  source_id: string
  title: string
  title_jp: string | null
  cover_url: string | null
  source_url: string | null
}

export interface SourceSearchResult {
  items: SourceSearchItem[]
  total: number
  page: number
  page_size: number
}

/** 数据源条目导入结果：返回本地新建（或已存在）的番剧 id */
export interface SourceImportResult {
  anime_id: number
}

export interface CollectionItem {
  id: number
  user_id: string
  anime_id: number
  emby_organized: boolean
  created_at: string
}

export interface AuthStatus {
  authenticated: boolean
  user: { username: string } | null
  app_name: string
  library_subcopy: string
  default_search_year: number | null
  default_search_season: number | null
  default_page_size: number
  requires_password_change: boolean
}

export interface LoginResponse {
  token: string
  user: { username: string }
  status: AuthStatus
}

export interface AppSettings {
  app_name: string
  library_subcopy: string
  anime_source: 'youranimes' | 'mikan'
  default_search_year: number | null
  default_search_season: number | null
  default_page_size: number
  default_filter_collected: boolean
  default_filter_release_tag: string | null
  default_filter_group_tag: string | null
  sync_strategy: string
  admin_username: string
  youranimes_base_url: string
  mikan_base_url: string
  collection_count: number
  cover_cache_file_count: number
  cover_cache_total_bytes: number
  updated_at: string
  requires_password_change: boolean
}

export interface AppLog {
  id: number
  level: string
  source: string
  message: string
  created_at: string
}

export interface PaginatedAppLogs {
  items: AppLog[]
  total: number
}
