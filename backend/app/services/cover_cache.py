import asyncio
import hashlib
import mimetypes
import os
from collections.abc import Sequence
from pathlib import Path
from urllib.parse import urlparse

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

from app.models import AnimeMaster
from app.services.scraper import AnimeSourceRecord


IMAGE_SIGNATURES = (
    (b"\x89PNG\r\n\x1a\n", ".png"),
    (b"\xff\xd8\xff", ".jpg"),
    (b"GIF87a", ".gif"),
    (b"GIF89a", ".gif"),
)
KNOWN_PLACEHOLDER_COVER_URLS = (
    "https://mikanani.me/images/mikan-pic.png",
    "http://mikanani.me/images/mikan-pic.png",
)
KNOWN_PLACEHOLDER_COVER_PATHS = {urlparse(url).path for url in KNOWN_PLACEHOLDER_COVER_URLS}
KNOWN_PLACEHOLDER_CACHE_DIGESTS = {
    hashlib.sha256(url.encode("utf-8")).hexdigest() for url in KNOWN_PLACEHOLDER_COVER_URLS
}
DEFAULT_COVER_CACHE_MAX_AGE_SECONDS = 86400


class CoverStaticFiles(StaticFiles):
    def __init__(self, *args, cache_control: str | None = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.cache_control = cache_control or f"public, max-age={DEFAULT_COVER_CACHE_MAX_AGE_SECONDS}"

    def file_response(
        self,
        full_path: os.PathLike[str] | str,
        stat_result: os.stat_result,
        scope: Scope,
        status_code: int = 200,
    ) -> Response:
        response = super().file_response(full_path, stat_result, scope, status_code)
        response.headers.setdefault("Cache-Control", self.cache_control)
        return response


class CoverCacheService:
    def __init__(self, cache_dir: Path, *, public_prefix: str = "/api/covers", concurrency: int = 8) -> None:
        self.cache_dir = cache_dir
        self.public_prefix = public_prefix.rstrip("/")
        self.concurrency = concurrency
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def cache_records(self, records: Sequence[AnimeSourceRecord]) -> None:
        unique_urls = list(dict.fromkeys(record.cover_url for record in records if record.cover_url))
        if not unique_urls:
            return

        semaphore = asyncio.Semaphore(self.concurrency)
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            async def cache_one(source_url: str) -> tuple[str, str | None]:
                async with semaphore:
                    return source_url, await self.cache_cover(source_url, client=client)

            pairs = await asyncio.gather(*(cache_one(source_url) for source_url in unique_urls))

        cached = {source_url: cached_url for source_url, cached_url in pairs}
        for record in records:
            if record.cover_url:
                record.cover_url = cached.get(record.cover_url) or record.cover_url

    async def cache_cover(self, source_url: str | None, *, client: httpx.AsyncClient | None = None) -> str | None:
        if not source_url:
            return None

        digest = self._digest(source_url)
        existing = self._existing_path(digest)
        if existing is not None:
            return self._public_url(_repair_cached_file_path(existing).name)

        owns_client = client is None
        if owns_client:
            client = httpx.AsyncClient(timeout=20, follow_redirects=True)

        try:
            assert client is not None
            response = await client.get(source_url)
            response.raise_for_status()
            if not response.content:
                return source_url

            extension = self._guess_extension(str(response.url), response.headers.get("content-type"))
            target = self.cache_dir / f"{digest}{extension}"
            temp = target.with_suffix(f"{target.suffix}.tmp")
            temp.write_bytes(response.content)
            temp.replace(target)
            return self._public_url(target.name)
        except Exception:
            return source_url
        finally:
            if owns_client and client is not None:
                await client.aclose()

    def _existing_path(self, digest: str) -> Path | None:
        for path in sorted(self.cache_dir.glob(f"{digest}.*")):
            if path.is_file() and path.stat().st_size > 0:
                return path
        return None

    def _public_url(self, file_name: str) -> str:
        return f"{self.public_prefix}/{file_name}"

    @staticmethod
    def _digest(source_url: str) -> str:
        return hashlib.sha256(source_url.encode("utf-8")).hexdigest()

    @staticmethod
    def _guess_extension(source_url: str, content_type: str | None) -> str:
        if content_type:
            guessed = mimetypes.guess_extension(content_type.split(";", 1)[0].strip()) or ""
            if guessed == ".jpe":
                return ".jpg"
            if guessed:
                return guessed

        path = urlparse(source_url).path
        extension = Path(path).suffix.lower()
        if extension:
            return extension

        return ".jpg"


def cover_cache_stats(cache_dir: Path) -> tuple[int, int]:
    if not cache_dir.exists():
        return 0, 0

    file_count = 0
    total_bytes = 0
    for path in cache_dir.iterdir():
        if path.is_file():
            file_count += 1
            total_bytes += path.stat().st_size
    return file_count, total_bytes


def clear_cover_cache(cache_dir: Path) -> tuple[int, int]:
    if not cache_dir.exists():
        return 0, 0

    deleted_files = 0
    deleted_bytes = 0
    for path in list(cache_dir.iterdir()):
        if path.is_file():
            deleted_bytes += path.stat().st_size
            path.unlink()
            deleted_files += 1
    return deleted_files, deleted_bytes


def clear_missing_cached_cover_references(db: Session, cache_dir: Path, *, public_prefix: str = "/api/covers") -> int:
    prefix = public_prefix.rstrip("/")
    if not prefix:
        return 0

    records = db.scalars(select(AnimeMaster).where(AnimeMaster.cover_url.like(f"{prefix}/%"))).all()
    repaired = 0
    for record in records:
        fixed_url = repair_cached_cover_url(record.cover_url, cache_dir, public_prefix=prefix)
        if fixed_url == record.cover_url:
            continue
        record.cover_url = fixed_url
        repaired += 1

    if repaired:
        db.commit()

    return repaired


def repair_cached_cover_url(cover_url: str | None, cache_dir: Path, *, public_prefix: str = "/api/covers") -> str | None:
    file_path = _local_cover_path(cover_url, cache_dir, public_prefix=public_prefix)
    if file_path is None or not file_path.is_file():
        return None

    repaired_path = _repair_cached_file_path(file_path)
    return _public_url_from_prefix(public_prefix, repaired_path.name)


def is_known_placeholder_cover_url(cover_url: str | None, *, public_prefix: str = "/api/covers") -> bool:
    if not cover_url:
        return False

    parsed = urlparse(cover_url)
    if parsed.path in KNOWN_PLACEHOLDER_COVER_PATHS and (not parsed.netloc or parsed.netloc.endswith("mikanani.me")):
        return True

    prefix = public_prefix.rstrip("/")
    cover_prefix = f"{prefix}/"
    if not cover_url.startswith(cover_prefix):
        return False

    file_name = cover_url.removeprefix(cover_prefix)
    if not file_name or Path(file_name).name != file_name:
        return False

    return Path(file_name).stem in KNOWN_PLACEHOLDER_CACHE_DIGESTS


def _local_cover_path(cover_url: str | None, cache_dir: Path, *, public_prefix: str) -> Path | None:
    if not cover_url:
        return None

    prefix = public_prefix.rstrip("/")
    cover_prefix = f"{prefix}/"
    if not cover_url.startswith(cover_prefix):
        return None

    file_name = cover_url.removeprefix(cover_prefix)
    if not file_name or Path(file_name).name != file_name:
        return None

    return cache_dir / file_name


def _repair_cached_file_path(path: Path) -> Path:
    detected_extension = _detect_image_extension(path)
    if detected_extension is None or path.suffix.lower() == detected_extension:
        return path

    target = path.with_suffix(detected_extension)
    if target.exists():
        target.unlink()
    path.replace(target)
    return target


def _detect_image_extension(path: Path) -> str | None:
    header = path.read_bytes()[:16]
    if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return ".webp"

    for signature, extension in IMAGE_SIGNATURES:
        if header.startswith(signature):
            return extension

    return None


def _public_url_from_prefix(public_prefix: str, file_name: str) -> str:
    return f"{public_prefix.rstrip('/')}/{file_name}"