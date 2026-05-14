from datetime import datetime
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Header, HTTPException
from sqlalchemy import delete, exists, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.database import SessionLocal, get_db
from app.models import AnimeMapping, AnimeMaster, CollectionItem, EpisodeProgress
from app.schemas import AppSettingsOut, AnimeOut, AnimeSearchRequest, AuthStatusOut, AuthUserOut, CollectionResetActionOut, MaintenanceActionOut, PaginatedAnime
from app.security import decode_token
from app.services.app_settings import AppSettingsStore, StoredAppSettings
from app.services.cover_cache import CoverCacheService, clear_cover_cache, clear_missing_cached_cover_references, cover_cache_stats, is_known_placeholder_cover_url, repair_cached_cover_url
from app.services.mikan import MikanScraper
from app.services.scraper import AnimeSourceRecord, YourAnimesScraper


LIBRARY_DEFAULT_SUBCOPY = '按年份和季度从源站刷新番剧，并把封面缓存到本地，减少重复请求，让浏览体验更稳定。'
DETAIL_REFRESH_INFLIGHT: set[int] = set()


@lru_cache
def get_app_settings_store() -> AppSettingsStore:
    settings = get_settings()
    return AppSettingsStore(
        settings.app_settings_path,
        default_app_name=settings.app_name,
        default_library_subcopy=LIBRARY_DEFAULT_SUBCOPY,
        default_search_year=datetime.now().year,
        default_admin_username=settings.auth_default_username,
        default_admin_password=settings.auth_default_password,
    )


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(' ')
    if scheme.lower() != 'bearer' or not token:
        return None
    return token.strip()


def _resolve_token_subject(token: str | None, store: AppSettingsStore) -> str | None:
    if not token:
        return None
    stored = store.load()
    try:
        payload = decode_token(token, stored.auth_secret)
    except ValueError:
        return None
    subject = payload.get('sub')
    if subject != stored.admin_username:
        return None
    return subject


def require_auth(
    authorization: Annotated[str | None, Header()] = None,
    store: AppSettingsStore = Depends(get_app_settings_store),
) -> str:
    token = _extract_bearer_token(authorization)
    subject = _resolve_token_subject(token, store)
    if not subject:
        raise HTTPException(status_code=401, detail='Unauthorized')
    return subject


def auth_status_out(stored: StoredAppSettings, store: AppSettingsStore, *, authenticated: bool) -> AuthStatusOut:
    return AuthStatusOut(
        authenticated=authenticated,
        user=AuthUserOut(username=stored.admin_username) if authenticated else None,
        app_name=stored.app_name,
        library_subcopy=stored.library_subcopy,
        default_search_year=stored.default_search_year,
        default_search_season=stored.default_search_season,
        default_page_size=stored.default_page_size,
        default_filter_collected=stored.default_filter_collected,
        default_filter_release_tag=stored.default_filter_release_tag,
        default_filter_group_tag=stored.default_filter_group_tag,
        requires_password_change=store.uses_default_credentials(stored),
    )


def settings_out(stored: StoredAppSettings, store: AppSettingsStore, db: Session) -> AppSettingsOut:
    settings = get_settings()
    collection_count = db.scalar(select(func.count()).select_from(CollectionItem)) or 0
    cache_files, cache_bytes = cover_cache_stats(settings.cover_cache_dir)
    return AppSettingsOut(
        app_name=stored.app_name,
        library_subcopy=stored.library_subcopy,
        anime_source=stored.anime_source,
        default_search_year=stored.default_search_year,
        default_search_season=stored.default_search_season,
        default_page_size=stored.default_page_size,
        default_filter_collected=stored.default_filter_collected,
        default_filter_release_tag=stored.default_filter_release_tag,
        default_filter_group_tag=stored.default_filter_group_tag,
        sync_strategy=stored.sync_strategy,
        admin_username=stored.admin_username,
        youranimes_base_url=settings.youranimes_base_url,
        mikan_base_url=settings.mikan_base_url,
        collection_count=collection_count,
        cover_cache_file_count=cache_files,
        cover_cache_total_bytes=cache_bytes,
        updated_at=stored.updated_at,
        requires_password_change=store.uses_default_credentials(stored),
    )


def clear_cover_cache_state(db: Session) -> MaintenanceActionOut:
    settings = get_settings()
    deleted_files, deleted_bytes = clear_cover_cache(settings.cover_cache_dir)
    reset_cover_urls = clear_missing_cached_cover_references(
        db,
        settings.cover_cache_dir,
        public_prefix=settings.cover_cache_public_path,
    )
    remaining_files, remaining_bytes = cover_cache_stats(settings.cover_cache_dir)
    return MaintenanceActionOut(
        deleted_files=deleted_files,
        deleted_bytes=deleted_bytes,
        reset_cover_urls=reset_cover_urls,
        remaining_files=remaining_files,
        remaining_bytes=remaining_bytes,
    )


def clear_library_state(db: Session) -> None:
    db.execute(delete(AnimeMapping))
    db.execute(delete(EpisodeProgress))
    db.execute(delete(CollectionItem))
    db.execute(delete(AnimeMaster))
    db.commit()


def clear_collection_state(db: Session) -> CollectionResetActionOut:
    deleted_collections = db.scalar(select(func.count()).select_from(CollectionItem)) or 0
    db.execute(delete(CollectionItem))
    db.commit()
    return CollectionResetActionOut(
        deleted_collections=deleted_collections,
        remaining_collections=0,
    )


def get_source_client(source_name: str, settings):
    if source_name == 'mikan':
        return MikanScraper(settings.mikan_base_url)
    return YourAnimesScraper(settings.youranimes_base_url)


def fallback_record_from_anime(anime: AnimeMaster) -> AnimeSourceRecord:
    return AnimeSourceRecord(
        title_cn=anime.title_cn,
        source_id=anime.source_id,
        source_url=anime.source_url,
        year=anime.year,
        season=anime.season,
        title_jp=anime.title_jp,
        title_en=anime.title_en,
        aliases=anime.aliases,
        synopsis=anime.synopsis,
        premiere_date=anime.premiere_date,
        platforms=anime.platforms,
        staff=anime.staff,
        cast=anime.cast,
        tags=anime.tags,
        pv_url=anime.pv_url,
        cover_url=anime.cover_url,
    )


def needs_detail_refresh(anime: AnimeMaster) -> bool:
    if not anime.source_url:
        return False
    if any(not value for value in [anime.synopsis, anime.staff, anime.cast, anime.tags, anime.cover_url]):
        return True

    settings = get_settings()
    return is_known_placeholder_cover_url(
        anime.cover_url,
        public_prefix=settings.cover_cache_public_path,
    )


def apply_detail_record(anime: AnimeMaster, detail: AnimeSourceRecord) -> None:
    anime.title_cn = detail.title_cn or anime.title_cn
    anime.title_jp = detail.title_jp or anime.title_jp
    anime.title_en = detail.title_en or anime.title_en
    anime.aliases = detail.aliases or anime.aliases
    anime.synopsis = detail.synopsis or anime.synopsis
    anime.premiere_date = detail.premiere_date or anime.premiere_date
    anime.platforms = detail.platforms or anime.platforms
    anime.staff = detail.staff or anime.staff
    anime.cast = detail.cast or anime.cast
    anime.tags = detail.tags or anime.tags
    anime.pv_url = detail.pv_url or anime.pv_url
    anime.cover_url = detail.cover_url or anime.cover_url
    anime.source_id = detail.source_id or anime.source_id
    anime.source_url = detail.source_url or anime.source_url


def repair_missing_cover_url(anime: AnimeMaster, settings) -> bool:
    if not anime.cover_url:
        return False

    repaired_url = repair_cached_cover_url(
        anime.cover_url,
        settings.cover_cache_dir,
        public_prefix=settings.cover_cache_public_path,
    )
    if repaired_url == anime.cover_url:
        return False

    anime.cover_url = repaired_url
    return True


def repair_missing_cover_urls(animes: list[AnimeMaster], db: Session) -> None:
    settings = get_settings()
    repaired = False
    for anime in animes:
        repaired = repair_missing_cover_url(anime, settings) or repaired
    if repaired:
        db.commit()


def load_anime_record(anime_id: int, db: Session) -> AnimeMaster | None:
    return db.scalar(
        select(AnimeMaster).options(joinedload(AnimeMaster.collection_item)).where(AnimeMaster.id == anime_id)
    )


def serialize_anime(anime: AnimeMaster, *, detail_refreshing: bool = False) -> AnimeOut:
    payload = AnimeOut.model_validate(anime)
    return payload.model_copy(update={'detail_refreshing': detail_refreshing})


async def hydrate_anime_detail_record(anime: AnimeMaster, db: Session) -> AnimeMaster | None:
    if not anime.source_url:
        return anime

    settings = get_settings()
    cover_cache = CoverCacheService(settings.cover_cache_dir, public_prefix=settings.cover_cache_public_path)
    detail = await get_source_client(anime.source, settings).fetch_detail(
        anime.source_url,
        fallback=fallback_record_from_anime(anime),
    )
    if detail is None:
        return anime

    await cover_cache.cache_records([detail])
    apply_detail_record(anime, detail)
    db.commit()
    return load_anime_record(anime.id, db)


async def hydrate_anime_detail(anime_id: int) -> None:
    if anime_id in DETAIL_REFRESH_INFLIGHT:
        return

    DETAIL_REFRESH_INFLIGHT.add(anime_id)
    try:
        with SessionLocal() as db:
            anime = load_anime_record(anime_id, db)
            if anime is None:
                return
            repair_missing_cover_urls([anime], db)
            if not needs_detail_refresh(anime):
                return
            await hydrate_anime_detail_record(anime, db)
    finally:
        DETAIL_REFRESH_INFLIGHT.discard(anime_id)


def json_array_contains(column, candidate: str):
    normalized = candidate.strip().lower()
    json_each_alias = func.json_each(column).table_valued('value').alias()
    return exists(
        select(1)
        .select_from(json_each_alias)
        .where(func.lower(json_each_alias.c.value) == normalized)
    )


def resolve_sync_mode(stored_sync_strategy: str, payload: AnimeSearchRequest) -> str:
    if stored_sync_strategy != 'replace-season':
        return stored_sync_strategy
    if payload.keyword:
        return 'incremental'
    if payload.season is None:
        return 'incremental'
    return 'replace-season'


def normalize_query_text_values(values: list[str] | str | None) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        values = [values]
    return [value.strip() for value in values if value and value.strip()]


def query_anime_page(
    db: Session,
    *,
    year: int,
    season: int | None,
    keyword: str | None,
    page: int,
    page_size: int,
) -> PaginatedAnime:
    stmt = select(AnimeMaster).options(joinedload(AnimeMaster.collection_item)).where(AnimeMaster.year == year)
    if season:
        stmt = stmt.where(AnimeMaster.season == season)
    if keyword:
        like = f'%{keyword}%'
        stmt = stmt.where(
            or_(
                AnimeMaster.title_cn.like(like),
                AnimeMaster.title_jp.like(like),
                AnimeMaster.title_en.like(like),
                AnimeMaster.aliases.like(like),
            )
        )

    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    items = db.scalars(
        stmt.order_by(AnimeMaster.season.desc(), AnimeMaster.title_cn)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).unique().all()
    repair_missing_cover_urls(items, db)
    return PaginatedAnime(items=[serialize_anime(item) for item in items], total=total, page=page, page_size=page_size)