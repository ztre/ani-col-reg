from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.api import router
from app.config import get_settings
from app.database import SessionLocal, init_db
from app.logging_filters import configure_uvicorn_access_log_filters
from app.services.cover_cache import CoverStaticFiles, clear_missing_cached_cover_references


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    settings = get_settings()
    with SessionLocal() as db:
        clear_missing_cached_cover_references(
            db,
            settings.cover_cache_dir,
            public_prefix=settings.cover_cache_public_path,
        )
    yield


settings = get_settings()
configure_uvicorn_access_log_filters(cover_public_path=settings.cover_cache_public_path)
settings.cover_cache_dir.mkdir(parents=True, exist_ok=True)
frontend_dist_dir = Path(__file__).resolve().parents[1] / "frontend_dist"
frontend_index_file = frontend_dist_dir / "index.html"
app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount(settings.cover_cache_public_path, CoverStaticFiles(directory=settings.cover_cache_dir), name="cover-cache")
app.include_router(router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _frontend_target(path: str | None = None) -> Path | None:
    if not frontend_index_file.is_file():
        return None

    if not path:
        return frontend_index_file

    requested = (frontend_dist_dir / path).resolve()
    try:
        requested.relative_to(frontend_dist_dir.resolve())
    except ValueError:
        return None

    if requested.is_file():
        return requested

    if Path(path).suffix:
        return None

    return frontend_index_file


def _frontend_response(path: str | None = None) -> FileResponse:
    target = _frontend_target(path)
    if target is None:
        raise HTTPException(status_code=404, detail="Frontend not found")
    return FileResponse(target)


@app.get("/", include_in_schema=False)
def serve_frontend_index() -> FileResponse:
    return _frontend_response()


@app.get("/{full_path:path}", include_in_schema=False)
def serve_frontend_path(full_path: str) -> FileResponse:
    if full_path == "api" or full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    if full_path in {"health", "docs", "redoc", "openapi.json"}:
        raise HTTPException(status_code=404, detail="Not found")
    return _frontend_response(full_path)
