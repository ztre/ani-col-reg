from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.routes.common import get_app_settings_store, get_source_client, query_anime_page, require_auth, resolve_sync_mode
from app.schemas import AnimeSearchRequest, PaginatedAnime
from app.services.cover_cache import CoverCacheService
from app.services.sync import upsert_records


router = APIRouter(prefix='/api', dependencies=[Depends(require_auth)])


@router.post('/anime/search', response_model=PaginatedAnime)
async def search_anime(payload: AnimeSearchRequest, db: Session = Depends(get_db)) -> PaginatedAnime:
    settings = get_settings()
    stored_settings = get_app_settings_store().load()
    scraper = get_source_client(stored_settings.anime_source, settings)
    cover_cache = CoverCacheService(settings.cover_cache_dir, public_prefix=settings.cover_cache_public_path)
    seasons = [payload.season] if payload.season else [1, 2, 3, 4]
    sync_mode = resolve_sync_mode(stored_settings.sync_strategy, payload)
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
        sync_scopes=[(payload.year, season) for season in seasons] if sync_mode == 'replace-season' else None,
        source=stored_settings.anime_source,
    )
    return query_anime_page(
        db,
        year=payload.year,
        season=payload.season,
        keyword=payload.keyword,
        page=payload.page,
        page_size=payload.page_size,
    )