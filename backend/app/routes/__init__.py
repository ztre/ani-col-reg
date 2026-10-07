from app.routes.anime import router as anime_router
from app.routes.auth import router as auth_router
from app.routes.collection import router as collection_router
from app.routes.logs import router as logs_router
from app.routes.search import router as search_router
from app.routes.settings import router as settings_router
from app.routes.sync import router as sync_router

__all__ = [
    'anime_router',
    'auth_router',
    'collection_router',
    'logs_router',
    'search_router',
    'settings_router',
    'sync_router',
]
