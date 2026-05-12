import asyncio
import hashlib

import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.services.cover_cache import CoverCacheService, CoverStaticFiles, DEFAULT_COVER_CACHE_MAX_AGE_SECONDS


def test_cover_cache_reuses_existing_file(tmp_path) -> None:
    requests: list[str] = []
    source_url = "https://cdn.example.test/posters/alpha"

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        return httpx.Response(200, content=b"cached-image", headers={"content-type": "image/webp"})

    service = CoverCacheService(tmp_path)

    async def run() -> tuple[str | None, str | None]:
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            first = await service.cache_cover(source_url, client=client)
            second = await service.cache_cover(source_url, client=client)
        return first, second

    first, second = asyncio.run(run())
    digest = hashlib.sha256(source_url.encode("utf-8")).hexdigest()
    expected_path = tmp_path / f"{digest}.webp"

    assert first == f"/api/covers/{expected_path.name}"
    assert second == first
    assert expected_path.read_bytes() == b"cached-image"
    assert requests == [source_url]


def test_cover_static_files_add_cache_control_to_200_and_304(tmp_path) -> None:
    cover_file = tmp_path / "alpha.webp"
    cover_file.write_bytes(b"cover-bytes")

    app = FastAPI()
    app.mount("/api/covers", CoverStaticFiles(directory=tmp_path), name="cover-cache")
    client = TestClient(app)

    response = client.get("/api/covers/alpha.webp")

    assert response.status_code == 200
    assert response.headers["cache-control"] == f"public, max-age={DEFAULT_COVER_CACHE_MAX_AGE_SECONDS}"

    cached = client.get(
        "/api/covers/alpha.webp",
        headers={"if-none-match": response.headers["etag"]},
    )

    assert cached.status_code == 304
    assert cached.headers["cache-control"] == f"public, max-age={DEFAULT_COVER_CACHE_MAX_AGE_SECONDS}"