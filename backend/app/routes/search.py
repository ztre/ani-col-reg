import logging
from datetime import datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.database import get_db
from app.models import AnimeMaster
from app.routes.common import build_series_group, require_auth
from app.schemas import ImportOut, ImportRequest, SeriesGroupOut, SourceSearchOut
from app.services.scraper import AnimeSourceRecord, YourAnimesScraper
from app.services.sync import upsert_records


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api', dependencies=[Depends(require_auth)])

SOURCE_SEARCH_MAX_PAGE_SIZE = 50


@router.get('/search', response_model=list[SeriesGroupOut])
def global_search(q: str | None = None, db: Session = Depends(get_db)) -> list[SeriesGroupOut]:
    query = (q or '').strip()
    if not query:
        return []

    like = f'%{query}%'
    title_match = or_(
        AnimeMaster.title_cn.like(like),
        AnimeMaster.title_jp.like(like),
        AnimeMaster.title_en.like(like),
        AnimeMaster.aliases.like(like),
    )
    series_match = AnimeMaster.series_title.like(like)

    hits = db.scalars(
        select(AnimeMaster)
        .options(joinedload(AnimeMaster.collection_item))
        .where(or_(title_match, series_match))
        .order_by(AnimeMaster.year.desc(), AnimeMaster.season.desc(), AnimeMaster.title_cn)
        .limit(500)
    ).unique().all()
    if not hits:
        return []

    grouped: dict[str, list[AnimeMaster]] = {}
    for anime in hits:
        grouped.setdefault(anime.series_key, []).append(anime)

    # 系列名本身命中时，entries 展开为该系列全部条目（不只命中的）。
    matched_series_keys = {
        series_key
        for series_key in db.scalars(select(AnimeMaster.series_key).where(series_match)).all()
        if series_key in grouped
    }
    if matched_series_keys:
        series_rows = db.scalars(
            select(AnimeMaster)
            .options(joinedload(AnimeMaster.collection_item))
            .where(AnimeMaster.series_key.in_(matched_series_keys))
        ).unique().all()
        expanded: dict[str, list[AnimeMaster]] = {}
        for anime in series_rows:
            expanded.setdefault(anime.series_key, []).append(anime)
        grouped.update(expanded)

    groups = [build_series_group(entries) for entries in grouped.values()]
    groups.sort(key=lambda group: (-group.latest_year, -group.latest_season, group.series_title))
    return groups


@router.get('/search/source', response_model=SourceSearchOut)
async def search_source(query: str, page: int = 1, page_size: int = 20) -> SourceSearchOut:
    keyword = (query or '').strip()
    page = max(1, page)
    page_size = min(SOURCE_SEARCH_MAX_PAGE_SIZE, max(1, page_size))
    if not keyword:
        return SourceSearchOut(items=[], total=0, page=page, page_size=page_size)

    scraper = YourAnimesScraper(get_settings().youranimes_base_url)
    try:
        result = await scraper.search_source(keyword, page=page, size=page_size)
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail='数据源搜索暂不可用')

    return SourceSearchOut(items=result['items'], total=result['total'], page=page, page_size=page_size)


@router.post('/search/import', response_model=ImportOut)
async def import_anime(payload: ImportRequest, db: Session = Depends(get_db)) -> ImportOut:
    source_id = payload.source_id
    existing = db.scalar(select(AnimeMaster).where(AnimeMaster.source_id == source_id))
    if existing is not None:
        return ImportOut(anime_id=existing.id)

    base_url = get_settings().youranimes_base_url.rstrip('/')
    source_url = f'{base_url}/animes/{source_id}'
    fallback = AnimeSourceRecord(
        title_cn='',
        source_id=source_id,
        source_url=source_url,
        year=_current_year(),
        season=_current_season(),
    )
    try:
        record = await YourAnimesScraper(base_url).fetch_detail(source_url, fallback=fallback)
    except httpx.HTTPStatusError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            raise HTTPException(status_code=404, detail='数据源中未找到该作品')
        raise HTTPException(status_code=502, detail='数据源搜索暂不可用')
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail='数据源搜索暂不可用')

    # 待播条目（源站仅给出首播年份）：年份采信源站，季度未定置 0，不猜测。
    if record.unaired_year is not None:
        record.year, record.season = record.unaired_year, 0
    else:
        record.year, record.season = _resolve_year_season(record.premiere_date)
    created, updated = upsert_records(db, [record], source='youranimes')
    logger.info('数据源导入 source_id=%s 完成: 新增 %d 条，更新 %d 条', source_id, created, updated)

    anime = db.scalar(select(AnimeMaster).where(AnimeMaster.source_id == source_id))
    return ImportOut(anime_id=anime.id)


def _resolve_year_season(premiere_date: str | None) -> tuple[int, int]:
    if premiere_date:
        try:
            premiere = datetime.strptime(premiere_date[:10], '%Y-%m-%d')
            return premiere.year, (premiere.month - 1) // 3 + 1
        except ValueError:
            pass
    return _current_year(), _current_season()


def _current_year() -> int:
    return datetime.now().year


def _current_season() -> int:
    return (datetime.now().month - 1) // 3 + 1
