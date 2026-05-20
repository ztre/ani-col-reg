import asyncio
import hashlib
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api import create_collection, delete_collection, get_anime, list_anime, search_anime, update_collection
from app.database import Base
from app.models import AnimeMaster
from app.schemas import AnimeSearchRequest, CollectionCreate, CollectionUpdate
from app.services.scraper import AnimeSourceRecord, normalize_title


def make_session() -> Session:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return Session(engine)


def make_store(*, anime_source: str = "youranimes", sync_strategy: str = "incremental"):
    return SimpleNamespace(load=lambda: SimpleNamespace(anime_source=anime_source, sync_strategy=sync_strategy))


def test_collection_flow() -> None:
    db = make_session()
    anime = AnimeMaster(
        source="youranimes",
        source_id="alpha",
        source_url="https://youranimes.tw/anime/alpha",
        title_cn="春日测试番",
        normalized_title=normalize_title("春日测试番"),
        year=2026,
        season=2,
    )
    db.add(anime)
    db.commit()
    db.refresh(anime)

    created = create_collection(
        CollectionCreate(anime_id=anime.id),
        db,
    )
    assert created.organize_status == "pending"

    updated = update_collection(
        created.id,
        CollectionUpdate(note="手工备注", release_tags="BDRip, 1080p", group_tags="LoliHouse", organize_status="emby"),
        db,
    )
    assert updated.note == "手工备注"
    assert updated.release_tags == ["BDRip", "1080p"]
    assert updated.group_tags == ["LoliHouse"]
    assert updated.organize_status == "emby"

    page = list_anime(season=None, collected=True, release_tag="BDRip", page=1, page_size=20, db=db)
    assert page.total == 1

    deleted = delete_collection(created.id, db)
    assert deleted.anime_id == anime.id

    page = list_anime(season=None, collected=True, page=1, page_size=20, db=db)
    assert page.total == 0


def test_list_anime_supports_multiple_collection_tag_filters() -> None:
    db = make_session()
    anime_alpha = AnimeMaster(
        source="youranimes",
        source_id="alpha",
        source_url="https://youranimes.tw/anime/alpha",
        title_cn="标签测试番 A",
        normalized_title=normalize_title("标签测试番 A"),
        year=2026,
        season=2,
    )
    anime_beta = AnimeMaster(
        source="youranimes",
        source_id="beta",
        source_url="https://youranimes.tw/anime/beta",
        title_cn="标签测试番 B",
        normalized_title=normalize_title("标签测试番 B"),
        year=2026,
        season=2,
    )
    db.add_all([anime_alpha, anime_beta])
    db.commit()
    db.refresh(anime_alpha)
    db.refresh(anime_beta)

    create_collection(CollectionCreate(anime_id=anime_alpha.id, release_tags="BDRip, 1080p", group_tags="ANi"), db)
    create_collection(CollectionCreate(anime_id=anime_beta.id, release_tags="WEB-DL", group_tags="LoliHouse"), db)

    page = list_anime(
        season=None,
        collected=True,
        release_tag=["BDRip", "WEB-DL"],
        group_tag=["ANi", "LoliHouse"],
        page=1,
        page_size=20,
        db=db,
    )

    assert page.total == 2


def test_list_anime_clears_missing_local_cover_urls(monkeypatch, tmp_path) -> None:
    db = make_session()
    anime = AnimeMaster(
        source="mikan",
        source_id="missing-cover",
        source_url="https://mikanani.me/Home/Bangumi/999",
        title_cn="失效封面测试番",
        normalized_title=normalize_title("失效封面测试番"),
        year=2026,
        season=2,
        cover_url="/api/covers/missing-cover.jpg",
    )
    db.add(anime)
    db.commit()
    db.refresh(anime)

    cache_dir = tmp_path / "covers"
    cache_dir.mkdir()
    monkeypatch.setattr(
        "app.routes.common.get_settings",
        lambda: SimpleNamespace(cover_cache_dir=cache_dir, cover_cache_public_path="/api/covers"),
    )

    page = list_anime(year=2026, season=2, page=1, page_size=20, db=db)

    assert page.total == 1
    assert page.items[0].cover_url is None

    stored = db.get(AnimeMaster, anime.id)
    assert stored is not None
    assert stored.cover_url is None


def test_list_anime_repairs_local_cover_extension(monkeypatch, tmp_path) -> None:
    db = make_session()
    anime = AnimeMaster(
        source="mikan",
        source_id="webp-cover",
        source_url="https://mikanani.me/Home/Bangumi/1000",
        title_cn="扩展名修复测试番",
        normalized_title=normalize_title("扩展名修复测试番"),
        year=2026,
        season=2,
        cover_url="/api/covers/webp-cover.jpg",
    )
    db.add(anime)
    db.commit()
    db.refresh(anime)

    cache_dir = tmp_path / "covers"
    cache_dir.mkdir()
    (cache_dir / "webp-cover.jpg").write_bytes(b"RIFF\x10\x00\x00\x00WEBPVP8 " + b"0" * 16)
    monkeypatch.setattr(
        "app.routes.common.get_settings",
        lambda: SimpleNamespace(cover_cache_dir=cache_dir, cover_cache_public_path="/api/covers"),
    )

    page = list_anime(year=2026, season=2, page=1, page_size=20, db=db)

    assert page.total == 1
    assert page.items[0].cover_url == "/api/covers/webp-cover.webp"
    assert not (cache_dir / "webp-cover.jpg").exists()
    assert (cache_dir / "webp-cover.webp").exists()

    stored = db.get(AnimeMaster, anime.id)
    assert stored is not None
    assert stored.cover_url == "/api/covers/webp-cover.webp"


def test_search_anime_upserts_and_caches_source_cover(monkeypatch, tmp_path) -> None:
    db = make_session()
    cache_dir = tmp_path / "covers"
    cache_dir.mkdir()
    (cache_dir / "cached-alpha.webp").write_bytes(b"cover")

    class FakeScraper:
        def __init__(self, base_url: str) -> None:
            self.base_url = base_url

        async def fetch_season(self, year: int, season: int) -> list[AnimeSourceRecord]:
            return [
                AnimeSourceRecord(
                    title_cn="春日测试番",
                    source_id="alpha",
                    source_url="https://youranimes.tw/animes/alpha",
                    year=year,
                    season=season,
                    cover_url="https://cdn.example.test/alpha.webp",
                )
            ]

    class FakeCoverCache:
        def __init__(self, cache_dir, *, public_prefix: str = "/api/covers", concurrency: int = 8) -> None:
            self.cache_dir = cache_dir
            self.public_prefix = public_prefix

        async def cache_records(self, records) -> None:
            for record in records:
                if record.cover_url:
                    record.cover_url = f"{self.public_prefix}/cached-alpha.webp"

    monkeypatch.setattr("app.routes.sync.get_source_client", lambda source_name, settings: FakeScraper(settings.youranimes_base_url))
    monkeypatch.setattr("app.routes.sync.CoverCacheService", FakeCoverCache)
    monkeypatch.setattr("app.routes.sync.get_app_settings_store", lambda: make_store())
    monkeypatch.setattr(
        "app.routes.sync.get_settings",
        lambda: SimpleNamespace(
            youranimes_base_url="https://youranimes.tw",
            mikan_base_url="https://mikanani.me",
            cover_cache_dir=cache_dir,
            cover_cache_public_path="/api/covers",
        ),
    )
    monkeypatch.setattr(
        "app.routes.common.get_settings",
        lambda: SimpleNamespace(
            youranimes_base_url="https://youranimes.tw",
            mikan_base_url="https://mikanani.me",
            cover_cache_dir=cache_dir,
            cover_cache_public_path="/api/covers",
        ),
    )

    page = asyncio.run(search_anime(AnimeSearchRequest(year=2026, season=2, keyword="春日"), db))

    assert page.total == 1
    assert page.items[0].cover_url == "/api/covers/cached-alpha.webp"


def test_search_anime_handles_duplicate_source_records(monkeypatch) -> None:
    db = make_session()

    class FakeScraper:
        def __init__(self, base_url: str) -> None:
            self.base_url = base_url

        async def fetch_season(self, year: int, season: int) -> list[AnimeSourceRecord]:
            return [
                AnimeSourceRecord(
                    title_cn="重复测试番",
                    source_id="dup-alpha",
                    source_url="https://youranimes.tw/animes/dup-alpha",
                    year=year,
                    season=season,
                    platforms="巴哈姆特动画疯",
                ),
                AnimeSourceRecord(
                    title_cn="重复测试番",
                    source_id="dup-alpha",
                    source_url="https://youranimes.tw/animes/dup-alpha",
                    year=year,
                    season=season,
                    platforms="Netflix",
                ),
            ]

    class FakeCoverCache:
        def __init__(self, cache_dir, *, public_prefix: str = "/api/covers", concurrency: int = 8) -> None:
            self.public_prefix = public_prefix

        async def cache_records(self, records) -> None:
            for record in records:
                record.cover_url = f"{self.public_prefix}/dup-alpha.webp"

    monkeypatch.setattr("app.routes.sync.get_source_client", lambda source_name, settings: FakeScraper(settings.youranimes_base_url))
    monkeypatch.setattr("app.routes.sync.CoverCacheService", FakeCoverCache)
    monkeypatch.setattr("app.routes.sync.get_app_settings_store", lambda: make_store())

    page = asyncio.run(search_anime(AnimeSearchRequest(year=2026, season=4), db))

    assert page.total == 1
    assert page.items[0].platforms == "Netflix"


def test_search_anime_uses_selected_mikan_source(monkeypatch, tmp_path) -> None:
    db = make_session()
    cache_dir = tmp_path / "covers"
    cache_dir.mkdir()
    (cache_dir / "mikan-681.jpg").write_bytes(b"cover")

    class FakeMikanScraper:
        def __init__(self, base_url: str) -> None:
            self.base_url = base_url

        async def fetch_season(self, year: int, season: int) -> list[AnimeSourceRecord]:
            return [
                AnimeSourceRecord(
                    title_cn="Mikan 测试番",
                    source_id="681",
                    source_url="https://mikanani.me/Home/Bangumi/681",
                    year=year,
                    season=season,
                    cover_url="https://mikanani.me/images/Bangumi/681.jpg",
                )
            ]

    class FakeCoverCache:
        def __init__(self, cache_dir, *, public_prefix: str = "/api/covers", concurrency: int = 8) -> None:
            self.public_prefix = public_prefix

        async def cache_records(self, records) -> None:
            for record in records:
                record.cover_url = f"{self.public_prefix}/mikan-681.jpg"

    monkeypatch.setattr("app.routes.sync.get_source_client", lambda source_name, settings: FakeMikanScraper(settings.mikan_base_url))
    monkeypatch.setattr("app.routes.sync.CoverCacheService", FakeCoverCache)
    monkeypatch.setattr("app.routes.sync.get_app_settings_store", lambda: make_store(anime_source="mikan"))
    monkeypatch.setattr(
        "app.routes.sync.get_settings",
        lambda: SimpleNamespace(
            youranimes_base_url="https://youranimes.tw",
            mikan_base_url="https://mikanani.me",
            cover_cache_dir=cache_dir,
            cover_cache_public_path="/api/covers",
        ),
    )
    monkeypatch.setattr(
        "app.routes.common.get_settings",
        lambda: SimpleNamespace(
            youranimes_base_url="https://youranimes.tw",
            mikan_base_url="https://mikanani.me",
            cover_cache_dir=cache_dir,
            cover_cache_public_path="/api/covers",
        ),
    )

    page = asyncio.run(search_anime(AnimeSearchRequest(year=2026, season=2), db))

    assert page.total == 1
    assert page.items[0].source == "mikan"
    assert page.items[0].cover_url == "/api/covers/mikan-681.jpg"


def test_search_anime_uses_incremental_sync_for_full_year(monkeypatch) -> None:
    db = make_session()
    captured: dict[str, object] = {}

    class FakeScraper:
        def __init__(self, base_url: str) -> None:
            self.base_url = base_url

        async def fetch_season(self, year: int, season: int) -> list[AnimeSourceRecord]:
            return []

    class FakeCoverCache:
        def __init__(self, cache_dir, *, public_prefix: str = "/api/covers", concurrency: int = 8) -> None:
            self.public_prefix = public_prefix

        async def cache_records(self, records) -> None:
            return None

    def fake_upsert_records(db, records, mode="incremental", sync_scopes=None, source="youranimes"):
        captured["mode"] = mode
        captured["sync_scopes"] = sync_scopes
        captured["source"] = source
        return 0, 0

    monkeypatch.setattr("app.routes.sync.get_source_client", lambda source_name, settings: FakeScraper(settings.youranimes_base_url))
    monkeypatch.setattr("app.routes.sync.CoverCacheService", FakeCoverCache)
    monkeypatch.setattr("app.routes.sync.upsert_records", fake_upsert_records)
    monkeypatch.setattr("app.routes.sync.get_app_settings_store", lambda: make_store(sync_strategy="replace-season"))

    page = asyncio.run(search_anime(AnimeSearchRequest(year=2026, season=None), db))

    assert page.total == 0
    assert captured["mode"] == "incremental"
    assert captured["sync_scopes"] is None


def test_search_anime_uses_incremental_sync_for_single_season(monkeypatch) -> None:
    db = make_session()
    captured: dict[str, object] = {}

    class FakeScraper:
        def __init__(self, base_url: str) -> None:
            self.base_url = base_url

        async def fetch_season(self, year: int, season: int) -> list[AnimeSourceRecord]:
            return []

    class FakeCoverCache:
        def __init__(self, cache_dir, *, public_prefix: str = "/api/covers", concurrency: int = 8) -> None:
            self.public_prefix = public_prefix

        async def cache_records(self, records) -> None:
            return None

    def fake_upsert_records(db, records, mode="incremental", sync_scopes=None, source="youranimes"):
        captured["mode"] = mode
        captured["sync_scopes"] = sync_scopes
        captured["source"] = source
        return 0, 0

    monkeypatch.setattr("app.routes.sync.get_source_client", lambda source_name, settings: FakeScraper(settings.youranimes_base_url))
    monkeypatch.setattr("app.routes.sync.CoverCacheService", FakeCoverCache)
    monkeypatch.setattr("app.routes.sync.upsert_records", fake_upsert_records)
    monkeypatch.setattr("app.routes.sync.get_app_settings_store", lambda: make_store(sync_strategy="replace-season"))

    page = asyncio.run(search_anime(AnimeSearchRequest(year=2026, season=2), db))

    assert page.total == 0
    assert captured["mode"] == "incremental"
    assert captured["sync_scopes"] is None


def test_get_anime_hydrates_missing_detail_fields(monkeypatch) -> None:
    db = make_session()
    anime = AnimeMaster(
        source="youranimes",
        source_id="alpha",
        source_url="https://youranimes.tw/animes/alpha",
        title_cn="春日测试番",
        normalized_title=normalize_title("春日测试番"),
        year=2026,
        season=2,
        cover_url="https://cdn.example.test/alpha.webp",
    )
    db.add(anime)
    db.commit()
    db.refresh(anime)

    class FakeSourceClient:
        async def fetch_detail(self, source_url: str, *, fallback: AnimeSourceRecord) -> AnimeSourceRecord:
            assert source_url == "https://youranimes.tw/animes/alpha"
            return AnimeSourceRecord(
                title_cn=fallback.title_cn,
                source_id=fallback.source_id,
                source_url=source_url,
                year=fallback.year,
                season=fallback.season,
                synopsis="这是补抓的详情简介。",
                staff="Example Studio",
                cast="声优 A, 声优 B",
                tags="奇幻, 动作",
                pv_url="https://www.youtube.com/watch?v=alpha",
                cover_url="https://cdn.example.test/detail.webp",
            )

    class FakeCoverCache:
        def __init__(self, cache_dir, *, public_prefix: str = "/api/covers", concurrency: int = 8) -> None:
            self.public_prefix = public_prefix

        async def cache_records(self, records) -> None:
            for record in records:
                record.cover_url = f"{self.public_prefix}/detail-alpha.webp"

    monkeypatch.setattr("app.routes.common.get_source_client", lambda source_name, settings: FakeSourceClient())
    monkeypatch.setattr("app.routes.common.CoverCacheService", FakeCoverCache)

    detail = asyncio.run(get_anime(anime.id, db))

    assert detail.synopsis == "这是补抓的详情简介。"
    assert detail.staff == "Example Studio"
    assert detail.cover_url == "/api/covers/detail-alpha.webp"

    stored = db.get(AnimeMaster, anime.id)
    assert stored is not None
    assert stored.cast == "声优 A, 声优 B"
    assert stored.tags == "奇幻, 动作"


def test_get_anime_refreshes_known_placeholder_cover(monkeypatch, tmp_path) -> None:
    db = make_session()
    placeholder_digest = hashlib.sha256("https://mikanani.me/images/mikan-pic.png".encode("utf-8")).hexdigest()
    anime = AnimeMaster(
        source="mikan",
        source_id="3288",
        source_url="https://mikanani.me/Home/Bangumi/3288",
        title_cn="吉伊卡哇",
        normalized_title=normalize_title("吉伊卡哇"),
        year=2026,
        season=2,
        synopsis="已有简介",
        staff="已有 staff",
        cast="已有 cast",
        tags="已有 tags",
        cover_url=f"/api/covers/{placeholder_digest}.png",
    )
    db.add(anime)
    db.commit()
    db.refresh(anime)

    class FakeSourceClient:
        async def fetch_detail(self, source_url: str, *, fallback: AnimeSourceRecord) -> AnimeSourceRecord:
            assert source_url == "https://mikanani.me/Home/Bangumi/3288"
            return AnimeSourceRecord(
                title_cn=fallback.title_cn,
                source_id=fallback.source_id,
                source_url=source_url,
                year=fallback.year,
                season=fallback.season,
                synopsis=fallback.synopsis,
                staff=fallback.staff,
                cast=fallback.cast,
                tags=fallback.tags,
                cover_url="https://mikanani.me/images/Bangumi/202204/d8ef46c0.jpg?width=400&height=560&format=webp",
            )

    class FakeCoverCache:
        def __init__(self, cache_dir, *, public_prefix: str = "/api/covers", concurrency: int = 8) -> None:
            self.public_prefix = public_prefix

        async def cache_records(self, records) -> None:
            for record in records:
                record.cover_url = f"{self.public_prefix}/chiikawa-fixed.webp"

    monkeypatch.setattr("app.routes.common.get_source_client", lambda source_name, settings: FakeSourceClient())
    monkeypatch.setattr("app.routes.common.CoverCacheService", FakeCoverCache)
    monkeypatch.setattr(
        "app.routes.common.get_settings",
        lambda: SimpleNamespace(
            cover_cache_dir=tmp_path / "covers",
            cover_cache_public_path="/api/covers",
        ),
    )

    detail = asyncio.run(get_anime(anime.id, db))

    assert detail.cover_url == "/api/covers/chiikawa-fixed.webp"

    stored = db.get(AnimeMaster, anime.id)
    assert stored is not None
    assert stored.cover_url == "/api/covers/chiikawa-fixed.webp"
