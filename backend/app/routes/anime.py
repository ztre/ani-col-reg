from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import AnimeMaster, CollectionItem
from app.routes.common import (
    get_app_settings_store,
    hydrate_anime_detail,
    hydrate_anime_detail_record,
    json_array_contains,
    load_anime_record,
    needs_detail_refresh,
    normalize_query_text_values,
    repair_missing_cover_urls,
    require_auth,
    serialize_anime,
)
from app.schemas import AnimeOut, PaginatedAnime


router = APIRouter(prefix='/api', dependencies=[Depends(require_auth)])


def list_anime(
    year: int | None = None,
    season: int | None = None,
    keyword: str | None = None,
    platform: str | None = None,
    collected: bool | None = None,
    release_tag: list[str] | str | None = None,
    group_tag: list[str] | str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = None,
) -> PaginatedAnime:
    stmt = select(AnimeMaster).options(joinedload(AnimeMaster.collection_item))
    release_tags = normalize_query_text_values(release_tag)
    group_tags = normalize_query_text_values(group_tag)

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
        like = f'%{keyword}%'
        stmt = stmt.where(
            or_(
                AnimeMaster.title_cn.like(like),
                AnimeMaster.title_jp.like(like),
                AnimeMaster.title_en.like(like),
                AnimeMaster.aliases.like(like),
            )
        )
    if platform:
        stmt = stmt.where(AnimeMaster.platforms.like(f'%{platform}%'))
    if release_tags:
        stmt = stmt.where(or_(*(json_array_contains(CollectionItem.release_tags, tag) for tag in release_tags)))
    if group_tags:
        stmt = stmt.where(or_(*(json_array_contains(CollectionItem.group_tags, tag) for tag in group_tags)))

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
    platform: str | None = None,
    collected: bool | None = None,
    release_tag: list[str] | None = Query(default=None),
    group_tag: list[str] | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedAnime:
    return list_anime(
        year=year,
        season=season,
        keyword=keyword,
        platform=platform,
        collected=collected,
        release_tag=release_tag,
        group_tag=group_tag,
        page=page,
        page_size=page_size,
        db=db,
    )


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