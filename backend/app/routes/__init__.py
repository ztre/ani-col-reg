from app.routes.anime import router as anime_router
from app.routes.auth import router as auth_router
from app.routes.collection import router as collection_router
from app.routes.settings import router as settings_router
from app.routes.sync import router as sync_router
from app.routes.tags import router as tags_router

__all__ = [
    'anime_router',
    'auth_router',
    'collection_router',
    'settings_router',
    'sync_router',
    'tags_router',
]