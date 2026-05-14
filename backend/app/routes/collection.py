from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AnimeMapping, AnimeMaster, CollectionItem
from app.routes.common import require_auth
from app.schemas import CollectionCreate, CollectionOut, CollectionUpdate, MappingCreate, MappingOut


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

    apply_collection_payload(item, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(item)
    return CollectionOut.model_validate(item)


@router.patch('/collection/{collection_id}', response_model=CollectionOut)
def update_collection(collection_id: int, payload: CollectionUpdate, db: Session = Depends(get_db)) -> CollectionOut:
    item = db.get(CollectionItem, collection_id)
    if not item:
        raise HTTPException(status_code=404, detail='Collection item not found')

    apply_collection_payload(item, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(item)
    return CollectionOut.model_validate(item)


@router.delete('/collection/{collection_id}', response_model=CollectionOut)
def delete_collection(collection_id: int, db: Session = Depends(get_db)) -> CollectionOut:
    item = db.get(CollectionItem, collection_id)
    if not item:
        raise HTTPException(status_code=404, detail='Collection item not found')

    deleted = CollectionOut.model_validate(item)
    db.delete(item)
    db.commit()
    return deleted


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


def apply_collection_payload(item: CollectionItem, values: dict) -> None:
    for key, value in values.items():
        setattr(item, key, value)