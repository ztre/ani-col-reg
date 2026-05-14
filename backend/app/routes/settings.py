from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.routes.common import clear_collection_state, clear_cover_cache_state, clear_library_state, get_app_settings_store, require_auth, settings_out
from app.schemas import AppSettingsOut, AppSettingsUpdate, CollectionResetActionOut, MaintenanceActionOut


router = APIRouter(prefix='/api', dependencies=[Depends(require_auth)])


@router.get('/settings', response_model=AppSettingsOut)
def get_app_settings(store=Depends(get_app_settings_store), db: Session = Depends(get_db)) -> AppSettingsOut:
    return settings_out(store.load(), store, db)


@router.put('/settings', response_model=AppSettingsOut)
def update_app_settings(
    payload: AppSettingsUpdate,
    store=Depends(get_app_settings_store),
    db: Session = Depends(get_db),
) -> AppSettingsOut:
    previous = store.load()
    try:
        stored = store.update(payload.model_dump(exclude_unset=True))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if payload.anime_source is not None and payload.anime_source != previous.anime_source:
        clear_library_state(db)
        clear_cover_cache_state(db)
    return settings_out(stored, store, db)


@router.post('/settings/maintenance/clear-cover-cache', response_model=MaintenanceActionOut)
def clear_cover_cache_maintenance(db: Session = Depends(get_db)) -> MaintenanceActionOut:
    return clear_cover_cache_state(db)


@router.post('/settings/maintenance/reset-collection-data', response_model=CollectionResetActionOut)
def reset_collection_maintenance(db: Session = Depends(get_db)) -> CollectionResetActionOut:
    return clear_collection_state(db)