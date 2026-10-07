from fastapi import APIRouter

from app.config import get_settings
from app.routes import anime_router, auth_router, collection_router, logs_router, search_router, settings_router, sync_router
from app.routes.anime import get_anime, list_anime, list_seasons
from app.routes.auth import auth_status, login
from app.routes.collection import (
    create_collection,
    create_mapping,
    delete_collection,
    list_collection_series,
    set_emby_organized,
)
from app.routes.common import get_app_settings_store
from app.routes.search import global_search, import_anime, search_source
from app.routes.settings import clear_cover_cache_maintenance, get_app_settings, reset_collection_maintenance, update_app_settings
from app.routes.sync import search_anime


router = APIRouter()
router.include_router(auth_router)
router.include_router(settings_router)
router.include_router(anime_router)
router.include_router(sync_router)
router.include_router(collection_router)
router.include_router(search_router)
router.include_router(logs_router)

__all__ = [
    'auth_status',
    'clear_cover_cache_maintenance',
    'create_collection',
    'create_mapping',
    'delete_collection',
    'get_anime',
    'get_app_settings',
    'get_app_settings_store',
    'get_settings',
    'global_search',
    'import_anime',
    'list_anime',
    'list_collection_series',
    'list_seasons',
    'login',
    'reset_collection_maintenance',
    'router',
    'search_anime',
    'search_source',
    'set_emby_organized',
    'update_app_settings',
]
