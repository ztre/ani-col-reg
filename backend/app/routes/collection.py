from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import AnimeMapping, AnimeMaster, CollectionItem
from app.routes.common import build_series_group, require_auth
from app.schemas import (
    CollectionCreate,
    CollectionOut,
    EmbyOrganizedUpdate,
    MappingCreate,
    MappingOut,
    SeriesGroupOut,
)


router = APIRouter(prefix='/api', dependencies=[Depends(require_auth)])


@router.post('/collection', response_model=CollectionOut)
def create_collection(payload: CollectionCreate, db: Session = Depends(get_db)) -> CollectionOut:
    anime = db.get(AnimeMaster, payload.anime_id)
    if not anime:
        raise HTTPException(status_code=404, detail='Anime not found')

    item = db.scalar(select(CollectionItem).where(CollectionItem.anime_id == payload.anime_id))
    if item is None:
        item = CollectionItem(anime_id=payload.anime_id)
        db.add(item)
        db.commit()
        db.refresh(item)
    return CollectionOut.model_validate(item)


@router.delete('/collection/anime/{anime_id}', status_code=204)
def delete_collection(anime_id: int, db: Session = Depends(get_db)) -> None:
    item = db.scalar(select(CollectionItem).where(CollectionItem.anime_id == anime_id))
    if item is not None:
        db.delete(item)
        db.commit()


@router.put('/collection/anime/{anime_id}/emby', response_model=CollectionOut)
def set_emby_organized(
    anime_id: int, payload: EmbyOrganizedUpdate, db: Session = Depends(get_db)
) -> CollectionOut:
    """标记/取消该季度在 Emby 中已整理。"""
    item = db.scalar(select(CollectionItem).where(CollectionItem.anime_id == anime_id))
    if item is None:
        raise HTTPException(status_code=404, detail='Anime not collected')
    item.emby_organized = payload.emby_organized
    db.commit()
    db.refresh(item)
    return CollectionOut.model_validate(item)


@router.get('/collection/series', response_model=list[SeriesGroupOut])
def list_collection_series(db: Session = Depends(get_db)) -> list[SeriesGroupOut]:
    rows = db.scalars(
        select(AnimeMaster)
        .options(joinedload(AnimeMaster.collection_item))
        .join(CollectionItem, CollectionItem.anime_id == AnimeMaster.id)
        .order_by(AnimeMaster.year.asc(), AnimeMaster.season.asc(), AnimeMaster.title_cn)
    ).unique().all()

    grouped: dict[str, list[AnimeMaster]] = defaultdict(list)
    for anime in rows:
        grouped[anime.series_key].append(anime)

    groups = [build_series_group(entries) for entries in grouped.values()]
    groups.sort(key=lambda group: (-group.latest_year, -group.latest_season, group.series_title))
    return groups


@router.post('/mapping/mgr-ani-ml', response_model=MappingOut)
def create_mapping(payload: MappingCreate, db: Session = Depends(get_db)) -> MappingOut:
    anime = db.get(AnimeMaster, payload.anime_id)
    if not anime:
        raise HTTPException(status_code=404, detail='Anime not found')

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
