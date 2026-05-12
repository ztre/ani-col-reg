from datetime import datetime
from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.database import get_db
from app.models import AnimeMapping, AnimeMaster, CollectionItem, EpisodeProgress
from app.schemas import AppSettingsOut, AppSettingsUpdate, AuthStatusOut, AuthUserOut, LoginRequest, LoginResponse, MaintenanceActionOut
from app.schemas import (
    AnimeOut,
    AnimeSearchRequest,
    CollectionCreate,
    CollectionOut,
    CollectionUpdate,
    MappingCreate,
    MappingOut,
    PaginatedAnime,
)
from app.security import create_token, decode_token
from app.services.app_settings import AppSettingsStore, StoredAppSettings
from app.services.cover_cache import CoverCacheService, clear_cover_cache, clear_missing_cached_cover_references, cover_cache_stats, is_known_placeholder_cover_url, repair_cached_cover_url
from app.services.mikan import MikanScraper
from app.services.scraper import AnimeSourceRecord, YourAnimesScraper
from app.services.sync import upsert_records


LIBRARY_DEFAULT_SUBCOPY = "按年份和季度从源站刷新番剧，并把封面缓存到本地，减少重复请求，让浏览体验更稳定。"

public_router = APIRouter(prefix="/api")
protected_router = APIRouter(prefix="/api")
router = APIRouter()


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
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
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
    subject = payload.get("sub")
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
        raise HTTPException(status_code=401, detail="Unauthorized")
    return subject


protected_router.dependencies.append(Depends(require_auth))


def _auth_status_out(stored: StoredAppSettings, store: AppSettingsStore, *, authenticated: bool) -> AuthStatusOut:
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


def _settings_out(stored: StoredAppSettings, store: AppSettingsStore) -> AppSettingsOut:
    settings = get_settings()
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
        cover_cache_file_count=cache_files,
        cover_cache_total_bytes=cache_bytes,
        updated_at=stored.updated_at,
        requires_password_change=store.uses_default_credentials(stored),
    )


def _clear_cover_cache_state(db: Session) -> MaintenanceActionOut:
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


def _clear_library_state(db: Session) -> None:
    db.execute(delete(AnimeMapping))
    db.execute(delete(EpisodeProgress))
    db.execute(delete(CollectionItem))
    db.execute(delete(AnimeMaster))
    db.commit()


def _get_source_client(source_name: str, settings):
    if source_name == "mikan":
        return MikanScraper(settings.mikan_base_url)
    return YourAnimesScraper(settings.youranimes_base_url)


def _fallback_record_from_anime(anime: AnimeMaster) -> AnimeSourceRecord:
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


def _needs_detail_refresh(anime: AnimeMaster) -> bool:
    if not anime.source_url:
        return False
    if any(not value for value in [anime.synopsis, anime.staff, anime.cast, anime.tags, anime.cover_url]):
        return True

    settings = get_settings()
    return is_known_placeholder_cover_url(
        anime.cover_url,
        public_prefix=settings.cover_cache_public_path,
    )


def _apply_detail_record(anime: AnimeMaster, detail: AnimeSourceRecord) -> None:
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


def _repair_missing_cover_url(anime: AnimeMaster, settings) -> bool:
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


def _repair_missing_cover_urls(animes: list[AnimeMaster], db: Session) -> None:
    settings = get_settings()
    repaired = False
    for anime in animes:
        repaired = _repair_missing_cover_url(anime, settings) or repaired
    if repaired:
        db.commit()


@public_router.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, store: AppSettingsStore = Depends(get_app_settings_store)) -> LoginResponse:
    stored = store.authenticate(payload.username, payload.password)
    if stored is None:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_token(stored.admin_username, stored.auth_secret, expires_in_hours=get_settings().auth_token_ttl_hours)
    return LoginResponse(token=token, user=AuthUserOut(username=stored.admin_username), status=_auth_status_out(stored, store, authenticated=True))


@public_router.get("/auth/status", response_model=AuthStatusOut)
def auth_status(
    authorization: Annotated[str | None, Header()] = None,
    store: AppSettingsStore = Depends(get_app_settings_store),
) -> AuthStatusOut:
    stored = store.load()
    subject = _resolve_token_subject(_extract_bearer_token(authorization), store)
    return _auth_status_out(stored, store, authenticated=subject == stored.admin_username)


@protected_router.get("/settings", response_model=AppSettingsOut)
def get_app_settings(store: AppSettingsStore = Depends(get_app_settings_store)) -> AppSettingsOut:
    return _settings_out(store.load(), store)


@protected_router.put("/settings", response_model=AppSettingsOut)
def update_app_settings(
    payload: AppSettingsUpdate,
    store: AppSettingsStore = Depends(get_app_settings_store),
    db: Session = Depends(get_db),
) -> AppSettingsOut:
    previous = store.load()
    try:
        stored = store.update(payload.model_dump(exclude_unset=True))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if payload.anime_source is not None and payload.anime_source != previous.anime_source:
        _clear_library_state(db)
        _clear_cover_cache_state(db)
    return _settings_out(stored, store)


@protected_router.post("/settings/maintenance/clear-cover-cache", response_model=MaintenanceActionOut)
def clear_cover_cache_maintenance(db: Session = Depends(get_db)) -> MaintenanceActionOut:
    return _clear_cover_cache_state(db)


@protected_router.get("/anime", response_model=PaginatedAnime)
def list_anime(
    year: int | None = None,
    season: Annotated[int | None, Query(ge=1, le=4)] = None,
    keyword: str | None = None,
    platform: str | None = None,
    collected: bool | None = None,
    release_tag: Annotated[list[str] | None, Query()] = None,
    group_tag: Annotated[list[str] | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    db: Session = Depends(get_db),
) -> PaginatedAnime:
    stmt = select(AnimeMaster).options(joinedload(AnimeMaster.collection_item))
    release_tags = _normalize_query_text_values(release_tag)
    group_tags = _normalize_query_text_values(group_tag)

    if collected is True or release_tags or group_tags:
        stmt = stmt.join(CollectionItem, CollectionItem.anime_id == AnimeMaster.id)
    elif collected is False:
        stmt = stmt.outerjoin(CollectionItem, CollectionItem.anime_id == AnimeMaster.id)
        stmt = stmt.where(CollectionItem.id.is_(None))

    if year:
        stmt = stmt.where(AnimeMaster.year == year)
    if season:
        stmt = stmt.where(AnimeMaster.season == season)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                AnimeMaster.title_cn.like(like),
                AnimeMaster.title_jp.like(like),
                AnimeMaster.title_en.like(like),
                AnimeMaster.aliases.like(like),
            )
        )
    if platform:
        stmt = stmt.where(AnimeMaster.platforms.like(f"%{platform}%"))
    if release_tags:
        stmt = stmt.where(or_(*(CollectionItem.release_tags.like(f"%{tag}%") for tag in release_tags)))
    if group_tags:
        stmt = stmt.where(or_(*(CollectionItem.group_tags.like(f"%{tag}%") for tag in group_tags)))

    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = db.scalar(count_stmt) or 0
    items = db.scalars(
        stmt.order_by(AnimeMaster.year.desc(), AnimeMaster.season.desc(), AnimeMaster.title_cn)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).unique().all()
    _repair_missing_cover_urls(items, db)
    return PaginatedAnime(items=[AnimeOut.model_validate(item) for item in items], total=total, page=page, page_size=page_size)


@protected_router.post("/anime/search", response_model=PaginatedAnime)
async def search_anime(payload: AnimeSearchRequest, db: Session = Depends(get_db)) -> PaginatedAnime:
    settings = get_settings()
    stored_settings = get_app_settings_store().load()
    scraper = _get_source_client(stored_settings.anime_source, settings)
    cover_cache = CoverCacheService(settings.cover_cache_dir, public_prefix=settings.cover_cache_public_path)
    seasons = [payload.season] if payload.season else [1, 2, 3, 4]
    sync_mode = _resolve_sync_mode(stored_settings.sync_strategy, payload)
    records = []

    for season in seasons:
        if season is None:
            continue
        season_records = await scraper.fetch_season(payload.year, season)
        await cover_cache.cache_records(season_records)
        records.extend(season_records)

    upsert_records(
        db,
        records,
        mode=sync_mode,
        sync_scopes=[(payload.year, season) for season in seasons] if sync_mode == "replace-season" else None,
        source=stored_settings.anime_source,
    )
    return _query_anime_page(
        db,
        year=payload.year,
        season=payload.season,
        keyword=payload.keyword,
        page=payload.page,
        page_size=payload.page_size,
    )


@protected_router.get("/anime/{anime_id}", response_model=AnimeOut)
async def get_anime(anime_id: int, db: Session = Depends(get_db)) -> AnimeOut:
    anime = db.scalar(
        select(AnimeMaster).options(joinedload(AnimeMaster.collection_item)).where(AnimeMaster.id == anime_id)
    )
    if not anime:
        raise HTTPException(status_code=404, detail="Anime not found")

    _repair_missing_cover_urls([anime], db)

    if _needs_detail_refresh(anime):
        settings = get_settings()
        cover_cache = CoverCacheService(settings.cover_cache_dir, public_prefix=settings.cover_cache_public_path)
        detail = await _get_source_client(anime.source, settings).fetch_detail(
            anime.source_url,
            fallback=_fallback_record_from_anime(anime),
        )
        if detail is not None:
            await cover_cache.cache_records([detail])
            _apply_detail_record(anime, detail)
            db.commit()
            anime = db.scalar(
                select(AnimeMaster).options(joinedload(AnimeMaster.collection_item)).where(AnimeMaster.id == anime_id)
            )

    return AnimeOut.model_validate(anime)


@protected_router.post("/collection", response_model=CollectionOut)
def create_collection(payload: CollectionCreate, db: Session = Depends(get_db)) -> CollectionOut:
    anime = db.get(AnimeMaster, payload.anime_id)
    if not anime:
        raise HTTPException(status_code=404, detail="Anime not found")

    item = db.scalar(select(CollectionItem).where(CollectionItem.anime_id == payload.anime_id))
    if item is None:
        item = CollectionItem(anime_id=payload.anime_id)
        db.add(item)

    _apply_collection_payload(item, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(item)
    return CollectionOut.model_validate(item)


@protected_router.patch("/collection/{collection_id}", response_model=CollectionOut)
def update_collection(collection_id: int, payload: CollectionUpdate, db: Session = Depends(get_db)) -> CollectionOut:
    item = db.get(CollectionItem, collection_id)
    if not item:
        raise HTTPException(status_code=404, detail="Collection item not found")
    _apply_collection_payload(item, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(item)
    return CollectionOut.model_validate(item)


@protected_router.delete("/collection/{collection_id}", response_model=CollectionOut)
def delete_collection(collection_id: int, db: Session = Depends(get_db)) -> CollectionOut:
    item = db.get(CollectionItem, collection_id)
    if not item:
        raise HTTPException(status_code=404, detail="Collection item not found")

    deleted = CollectionOut.model_validate(item)
    db.delete(item)
    db.commit()
    return deleted


@protected_router.post("/mapping/mgr-ani-ml", response_model=MappingOut)
def create_mapping(payload: MappingCreate, db: Session = Depends(get_db)) -> MappingOut:
    anime = db.get(AnimeMaster, payload.anime_id)
    if not anime:
        raise HTTPException(status_code=404, detail="Anime not found")

    mapping = db.scalar(
        select(AnimeMapping).where(
            AnimeMapping.anime_id == payload.anime_id,
            AnimeMapping.mgr_item_id == payload.mgr_item_id,
        )
    )
    if mapping is None:
        mapping = AnimeMapping(anime_id=payload.anime_id, mgr_item_id=payload.mgr_item_id)
        db.add(mapping)

    mapping.match_method = payload.match_method
    mapping.confidence = payload.confidence
    db.commit()
    db.refresh(mapping)
    return MappingOut.model_validate(mapping)


def _apply_collection_payload(item: CollectionItem, values: dict) -> None:
    for key, value in values.items():
        setattr(item, key, value)


def _resolve_sync_mode(stored_sync_strategy: str, payload: AnimeSearchRequest) -> str:
    if stored_sync_strategy != "replace-season":
        return stored_sync_strategy
    if payload.keyword:
        return "incremental"
    if payload.season is None:
        return "incremental"
    return "replace-season"


def _normalize_query_text_values(values: list[str] | str | None) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        values = [values]
    return [value.strip() for value in values if value and value.strip()]


def _query_anime_page(
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
        like = f"%{keyword}%"
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
    _repair_missing_cover_urls(items, db)
    return PaginatedAnime(items=[AnimeOut.model_validate(item) for item in items], total=total, page=page, page_size=page_size)


router.include_router(public_router)
router.include_router(protected_router)
