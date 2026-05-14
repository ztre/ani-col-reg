export interface CollectionItem {
  id: number
  user_id: string
  anime_id: number
  organize_status: 'pending' | 'emby'
  note: string | null
  release_tags: string[]
  group_tags: string[]
  updated_at?: string | null
}

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
  detail_refreshing?: boolean
  collection_item: CollectionItem | null
}

export interface PaginatedAnime {
  items: Anime[]
  total: number
  page: number
  page_size: number
}

export interface AuthUser {
  username: string
}

export interface AuthStatus {
  authenticated: boolean
  user: AuthUser | null
  app_name: string
  library_subcopy: string
  default_search_year: number
  default_search_season: number | null
  default_page_size: number
  default_filter_collected: boolean
  default_filter_release_tag: string | null
  default_filter_group_tag: string | null
  requires_password_change: boolean
}

export interface LoginResponse {
  token: string
  user: AuthUser
  status: AuthStatus
}

export interface AppSettings {
  app_name: string
  library_subcopy: string
  anime_source: 'youranimes' | 'mikan'
  default_search_year: number
  default_search_season: number | null
  default_page_size: number
  default_filter_collected: boolean
  default_filter_release_tag: string | null
  default_filter_group_tag: string | null
  sync_strategy: 'incremental' | 'replace-season'
  admin_username: string
  youranimes_base_url: string
  mikan_base_url: string
  collection_count: number
  cover_cache_file_count: number
  cover_cache_total_bytes: number
  updated_at: string
  requires_password_change: boolean
}

export interface AppSettingsUpdate {
  app_name?: string
  library_subcopy?: string
  anime_source?: 'youranimes' | 'mikan'
  default_search_year?: number
  default_search_season?: number | null
  default_page_size?: number
  default_filter_collected?: boolean
  default_filter_release_tag?: string | null
  default_filter_group_tag?: string | null
  sync_strategy?: 'incremental' | 'replace-season'
  admin_username?: string
  current_password?: string
  new_password?: string
}

export interface MaintenanceAction {
  deleted_files: number
  deleted_bytes: number
  reset_cover_urls: number
  remaining_files: number
  remaining_bytes: number
}

export interface CollectionResetAction {
  deleted_collections: number
  remaining_collections: number
}
