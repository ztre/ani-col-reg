from fastapi import APIRouter

from app.config import get_settings
from app.routes import anime_router, auth_router, collection_router, settings_router, sync_router, tags_router
from app.routes.anime import get_anime, list_anime
from app.routes.auth import auth_status, login
from app.routes.collection import create_collection, create_mapping, delete_collection, update_collection
from app.routes.common import get_app_settings_store
from app.routes.settings import clear_cover_cache_maintenance, get_app_settings, reset_collection_maintenance, update_app_settings
from app.routes.sync import search_anime


router = APIRouter()
router.include_router(auth_router)
router.include_router(settings_router)
router.include_router(anime_router)
router.include_router(sync_router)
router.include_router(collection_router)
router.include_router(tags_router)

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
    'list_anime',
    'login',
    'reset_collection_maintenance',
    'router',
    'search_anime',
    'update_app_settings',
    'update_collection',
]
