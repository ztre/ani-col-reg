from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import AnimeMaster, CollectionItem
from app.routes.common import (
    hydrate_anime_detail,
    hydrate_anime_detail_record,
    load_anime_record,
    needs_detail_refresh,
    repair_missing_cover_urls,
    require_auth,
    serialize_anime,
)
from app.schemas import AnimeOut, PaginatedAnime, SeasonSummaryOut


router = APIRouter(prefix='/api', dependencies=[Depends(require_auth)])


def list_anime(
    year: int | None = None,
    season: int | None = None,
    keyword: str | None = None,
    collected: bool | None = None,
    series_key: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = None,
) -> PaginatedAnime:
    stmt = select(AnimeMaster).options(joinedload(AnimeMaster.collection_item))

    if collected is True:
        stmt = stmt.join(CollectionItem, CollectionItem.anime_id == AnimeMaster.id)
    elif collected is False:
        stmt = stmt.outerjoin(CollectionItem, CollectionItem.anime_id == AnimeMaster.id)
        stmt = stmt.where(CollectionItem.id.is_(None))

    if year:
        stmt = stmt.where(AnimeMaster.year == year)
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
    if series_key:
        stmt = stmt.where(AnimeMaster.series_key == series_key)

    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = db.scalar(count_stmt) or 0
    items = db.scalars(
        stmt.order_by(AnimeMaster.year.desc(), AnimeMaster.season.desc(), AnimeMaster.title_cn)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).unique().all()
    repair_missing_cover_urls(items, db)
    return PaginatedAnime(items=[serialize_anime(item) for item in items], total=total, page=page, page_size=page_size)


@router.get('/anime', response_model=PaginatedAnime)
def list_anime_route(
    year: int | None = None,
    season: int | None = Query(default=None, ge=1, le=4),
    keyword: str | None = None,
    collected: bool | None = None,
    series_key: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedAnime:
    return list_anime(
        year=year,
        season=season,
        keyword=keyword,
        collected=collected,
        series_key=series_key,
        page=page,
        page_size=page_size,
        db=db,
    )


@router.get('/seasons', response_model=list[SeasonSummaryOut])
def list_seasons(db: Session = Depends(get_db)) -> list[SeasonSummaryOut]:
    rows = db.execute(
        select(AnimeMaster.year, AnimeMaster.season, func.count())
        .group_by(AnimeMaster.year, AnimeMaster.season)
        .order_by(AnimeMaster.year.desc(), AnimeMaster.season.desc())
    ).all()
    return [SeasonSummaryOut(year=year, season=season, count=count) for year, season, count in rows]


async def get_anime(
    anime_id: int,
    db: Session,
    background_tasks: BackgroundTasks | None = None,
) -> AnimeOut:
    anime = load_anime_record(anime_id, db)
    if not anime:
        raise HTTPException(status_code=404, detail='Anime not found')

    repair_missing_cover_urls([anime], db)

    if needs_detail_refresh(anime):
        if background_tasks is None:
            anime = await hydrate_anime_detail_record(anime, db) or anime
            refreshed = load_anime_record(anime_id, db) or anime
            return serialize_anime(refreshed)

        background_tasks.add_task(hydrate_anime_detail, anime_id)
        return serialize_anime(anime, detail_refreshing=True)

    return serialize_anime(anime)


@router.get('/anime/{anime_id}', response_model=AnimeOut)
async def get_anime_route(
    anime_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> AnimeOut:
    return await get_anime(anime_id, db, background_tasks)
