import asyncio
import hashlib
from datetime import datetime
from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api import (
    create_collection,
    delete_collection,
    get_anime,
    global_search,
    import_anime,
    list_anime,
    list_collection_series,
    list_seasons,
    search_anime,
    search_source,
    set_emby_organized,
)
from app.database import Base
from app.models import AnimeMaster
from app.schemas import AnimeSearchRequest, CollectionCreate, EmbyOrganizedUpdate, ImportRequest
from app.services.scraper import AnimeSourceRecord, normalize_title
from app.services.series import extract_series_info


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


def make_anime(title: str, year: int, season: int, *, source_id: str, cover_url: str | None = None) -> AnimeMaster:
    info = extract_series_info(title)
    return AnimeMaster(
        source="youranimes",
        source_id=source_id,
        source_url=f"https://youranimes.tw/animes/{source_id}",
        title_cn=title,
        normalized_title=normalize_title(title),
        series_key=info.series_key,
        series_title=info.series_title,
        season_label=info.season_label,
        year=year,
        season=season,
        cover_url=cover_url,
    )


def test_collection_flow() -> None:
    db = make_session()
    anime = make_anime("春日测试番", 2026, 2, source_id="alpha")
    db.add(anime)
    db.commit()
    db.refresh(anime)

    # 收藏：幂等，重复 POST 也成功
    created = create_collection(CollectionCreate(anime_id=anime.id), db)
    assert created.anime_id == anime.id
    assert created.user_id == "default"
    again = create_collection(CollectionCreate(anime_id=anime.id), db)
    assert again.anime_id == anime.id

    # is_collected 派生自收藏行存在与否
    page = list_anime(season=None, collected=True, page=1, page_size=20, db=db)
    assert page.total == 1
    assert page.items[0].is_collected is True
    assert page.items[0].series_key == anime.series_key

    # 取消收藏：按 anime_id，幂等 204
    delete_collection(anime.id, db)
    delete_collection(anime.id, db)

    page = list_anime(season=None, collected=True, page=1, page_size=20, db=db)
    assert page.total == 0
    page_all = list_anime(season=None, page=1, page_size=20, db=db)
    assert page_all.total == 1
    assert page_all.items[0].is_collected is False


def test_emby_organized_toggle_flow() -> None:
    db = make_session()
    first = make_anime("鬼灭之刃", 2019, 2, source_id="km-1")
    second = make_anime("鬼灭之刃 游郭篇", 2021, 3, source_id="km-2")
    db.add_all([first, second])
    db.commit()
    db.refresh(first)
    db.refresh(second)
    create_collection(CollectionCreate(anime_id=first.id), db)
    create_collection(CollectionCreate(anime_id=second.id), db)

    # 默认未整理
    groups = list_collection_series(db)
    assert all(item.emby_organized is False for item in groups[0].entries)

    # 标记其中一部
    updated = set_emby_organized(first.id, EmbyOrganizedUpdate(emby_organized=True), db)
    assert updated.emby_organized is True

    groups = list_collection_series(db)
    by_id = {item.id: item for item in groups[0].entries}
    assert by_id[first.id].emby_organized is True
    assert by_id[second.id].emby_organized is False

    # 再取消
    updated = set_emby_organized(first.id, EmbyOrganizedUpdate(emby_organized=False), db)
    assert updated.emby_organized is False
    groups = list_collection_series(db)
    assert all(item.emby_organized is False for item in groups[0].entries)


def test_emby_organized_requires_collected() -> None:
    db = make_session()
    anime = make_anime("未收藏番", 2026, 2, source_id="uncollected")
    db.add(anime)
    db.commit()
    db.refresh(anime)

    with pytest.raises(HTTPException) as exc_info:
        set_emby_organized(anime.id, EmbyOrganizedUpdate(emby_organized=True), db)

    assert exc_info.value.status_code == 404


def test_list_anime_filters_by_series_key() -> None:
    db = make_session()
    first = make_anime("鬼灭之刃", 2019, 2, source_id="km-1")
    second = make_anime("鬼灭之刃 游郭篇", 2021, 3, source_id="km-2")
    other = make_anime("紫罗兰永恒花园", 2018, 1, source_id="vi-1")
    db.add_all([first, second, other])
    db.commit()

    page = list_anime(series_key=first.series_key, page=1, page_size=20, db=db)
    assert page.total == 2
    assert {item.title_cn for item in page.items} == {"鬼灭之刃", "鬼灭之刃 游郭篇"}


def test_list_seasons_returns_descending_summary() -> None:
    db = make_session()
    db.add_all(
        [
            make_anime("冬番 A", 2025, 1, source_id="w-a"),
            make_anime("秋番 A", 2025, 4, source_id="f-a"),
            make_anime("春番 A", 2026, 2, source_id="sp-a"),
            make_anime("春番 B", 2026, 2, source_id="sp-b"),
            make_anime("夏番 A", 2026, 3, source_id="su-a"),
        ]
    )
    db.commit()

    seasons = list_seasons(db)
    assert [(s.year, s.season, s.count) for s in seasons] == [
        (2026, 3, 1),
        (2026, 2, 2),
        (2025, 4, 1),
        (2025, 1, 1),
    ]


def test_collection_series_groups_by_series_key() -> None:
    db = make_session()
    first = make_anime("鬼灭之刃", 2019, 2, source_id="km-1", cover_url="/api/covers/km-1.webp")
    second = make_anime("鬼灭之刃 游郭篇", 2021, 3, source_id="km-2", cover_url="/api/covers/km-2.webp")
    other = make_anime("紫罗兰永恒花园", 2018, 1, source_id="vi-1")
    db.add_all([first, second, other])
    db.commit()
    db.refresh(first)
    db.refresh(second)
    db.refresh(other)

    # 仅收藏同系列两部
    create_collection(CollectionCreate(anime_id=first.id), db)
    create_collection(CollectionCreate(anime_id=second.id), db)

    groups = list_collection_series(db)
    assert len(groups) == 1
    group = groups[0]
    assert group.series_key == first.series_key
    assert group.series_title == "鬼灭之刃"
    assert group.entry_count == 2
    assert group.latest_year == 2021
    assert group.latest_season == 3
    # 封面取最新收录条目
    assert group.cover_url == "/api/covers/km-2.webp"
    # entries 按年份/季度升序
    assert [item.year for item in group.entries] == [2019, 2021]
    assert all(item.is_collected for item in group.entries)


def test_global_search_matches_title_and_expands_series() -> None:
    db = make_session()
    first = make_anime("鬼灭之刃", 2019, 2, source_id="km-1")
    second = make_anime("鬼灭之刃 游郭篇", 2021, 3, source_id="km-2")
    other = make_anime("紫罗兰永恒花园", 2018, 1, source_id="vi-1")
    db.add_all([first, second, other])
    db.commit()

    # 标题命中：只返回命中条目所在分组
    results = global_search(q="游郭", db=db)
    assert len(results) == 1
    assert results[0].series_title == "鬼灭之刃"
    assert results[0].entry_count == 1
    assert results[0].entries[0].title_cn == "鬼灭之刃 游郭篇"

    # 系列名命中：展开该系列全部条目
    results = global_search(q="鬼灭", db=db)
    assert len(results) == 1
    assert results[0].entry_count == 2
    assert {item.title_cn for item in results[0].entries} == {"鬼灭之刃", "鬼灭之刃 游郭篇"}

    # 无结果 / 空关键词
    assert global_search(q="不存在的番", db=db) == []
    assert global_search(q="", db=db) == []
    assert global_search(q=None, db=db) == []
    assert global_search(q="   ", db=db) == []


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
    # 同步链路写入的系列字段随 AnimeOut 返回
    assert page.items[0].series_title == "春日测试番"
    assert page.items[0].is_collected is False


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
    anime = make_anime("春日测试番", 2026, 2, source_id="alpha", cover_url="https://cdn.example.test/alpha.webp")
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
    assert detail.series_key == anime.series_key
    assert detail.is_collected is False

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


def _source_status_error(url: str, status_code: int) -> httpx.HTTPStatusError:
    request = httpx.Request("GET", url)
    response = httpx.Response(status_code, request=request)
    return httpx.HTTPStatusError("source error", request=request, response=response)


def _patch_source_settings(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.routes.search.get_settings",
        lambda: SimpleNamespace(youranimes_base_url="https://youranimes.tw"),
    )


def test_source_search_returns_empty_items_for_blank_query() -> None:
    for query in ("", "   "):
        result = asyncio.run(search_source(query=query))

        assert result.items == []
        assert result.total == 0
        assert result.page == 1
        assert result.page_size == 20


def test_source_search_normalizes_and_clamps_params(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeScraper:
        def __init__(self, base_url: str) -> None:
            self.base_url = base_url
            captured["base_url"] = base_url

        async def search_source(self, tk: str, *, page: int = 1, size: int = 20):
            captured["tk"] = tk
            captured["page"] = page
            captured["size"] = size
            return {
                "items": [
                    {
                        "source_id": "249",
                        "title": "鬼滅之刃",
                        "title_jp": "鬼滅の刃",
                        "cover_url": "https://cdn.example.test/kimetsu.webp",
                        "source_url": "https://youranimes.tw/animes/249",
                    }
                ],
                "total": 13,
            }

    _patch_source_settings(monkeypatch)
    monkeypatch.setattr("app.routes.search.YourAnimesScraper", FakeScraper)

    result = asyncio.run(search_source(query=" 鬼滅 ", page=0, page_size=100))

    assert captured == {"base_url": "https://youranimes.tw", "tk": "鬼滅", "page": 1, "size": 50}
    assert result.total == 13
    assert result.page == 1
    assert result.page_size == 50
    assert result.items[0].source_id == "249"
    assert result.items[0].title == "鬼滅之刃"
    assert result.items[0].title_jp == "鬼滅の刃"
    assert result.items[0].cover_url == "https://cdn.example.test/kimetsu.webp"
    assert result.items[0].source_url == "https://youranimes.tw/animes/249"


def test_source_search_maps_source_errors_to_502(monkeypatch) -> None:
    request = httpx.Request("GET", "https://youranimes.tw/api/v1/animes")
    errors: list[Exception] = [
        _source_status_error("https://youranimes.tw/api/v1/animes", 503),
        httpx.ConnectError("unreachable", request=request),
    ]

    for error in errors:
        class FakeScraper:
            def __init__(self, base_url: str) -> None:
                self.base_url = base_url

            async def search_source(self, tk: str, *, page: int = 1, size: int = 20):
                raise error

        _patch_source_settings(monkeypatch)
        monkeypatch.setattr("app.routes.search.YourAnimesScraper", FakeScraper)

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(search_source(query="鬼滅"))

        assert exc_info.value.status_code == 502
        assert exc_info.value.detail == "数据源搜索暂不可用"


def test_import_anime_returns_existing_row_without_refetch(monkeypatch) -> None:
    db = make_session()
    anime = make_anime("鬼灭之刃", 2019, 2, source_id="249")
    db.add(anime)
    db.commit()
    db.refresh(anime)

    class FailingScraper:
        def __init__(self, base_url: str) -> None:
            self.base_url = base_url

        async def fetch_detail(self, source_url: str, *, fallback: AnimeSourceRecord) -> AnimeSourceRecord:
            raise AssertionError("existing source_id should not refetch")

    _patch_source_settings(monkeypatch)
    monkeypatch.setattr("app.routes.search.YourAnimesScraper", FailingScraper)

    result = asyncio.run(import_anime(ImportRequest(source_id="249"), db))

    assert result.anime_id == anime.id
    assert db.scalar(select(func.count()).select_from(AnimeMaster)) == 1


def test_import_anime_creates_row_with_inferred_year_season_and_series(monkeypatch) -> None:
    db = make_session()
    captured: list[str] = []

    class FakeScraper:
        def __init__(self, base_url: str) -> None:
            self.base_url = base_url

        async def fetch_detail(self, source_url: str, *, fallback: AnimeSourceRecord) -> AnimeSourceRecord:
            captured.append(source_url)
            return AnimeSourceRecord(
                title_cn="鬼灭之刃 游郭篇",
                source_id="kimetsu-2",
                source_url=source_url,
                year=fallback.year,
                season=fallback.season,
                title_jp="鬼滅の刃 遊郭編",
                premiere_date="2021-12-05",
                synopsis="游郭篇简介。",
                tags="奇幻, 动作",
                cover_url="https://cdn.example.test/kimetsu-2.webp",
            )

    _patch_source_settings(monkeypatch)
    monkeypatch.setattr("app.routes.search.YourAnimesScraper", FakeScraper)

    result = asyncio.run(import_anime(ImportRequest(source_id="kimetsu-2"), db))

    anime = db.scalar(select(AnimeMaster).where(AnimeMaster.source_id == "kimetsu-2"))
    assert anime is not None
    assert result.anime_id == anime.id
    assert captured == ["https://youranimes.tw/animes/kimetsu-2"]
    assert anime.source == "youranimes"
    assert anime.source_url == "https://youranimes.tw/animes/kimetsu-2"
    # premiere_date（2021-12-05）推断年份与季度
    assert (anime.year, anime.season) == (2021, 4)
    assert anime.premiere_date == "2021-12-05"
    # extract_series_info 生成系列三字段
    assert anime.series_key == "鬼灭之刃"
    assert anime.series_title == "鬼灭之刃"
    assert anime.season_label == "游郭篇"
    assert anime.title_jp == "鬼滅の刃 遊郭編"
    assert anime.tags == "奇幻, 动作"

    # 幂等：再次导入直接返回同一本地 id，不再抓取详情
    again = asyncio.run(import_anime(ImportRequest(source_id="kimetsu-2"), db))
    assert again.anime_id == anime.id
    assert captured == ["https://youranimes.tw/animes/kimetsu-2"]
    assert db.scalar(select(func.count()).select_from(AnimeMaster)) == 1


def test_import_anime_without_premiere_date_uses_current_year_season(monkeypatch) -> None:
    db = make_session()
    now = datetime.now()

    class FakeScraper:
        def __init__(self, base_url: str) -> None:
            self.base_url = base_url

        async def fetch_detail(self, source_url: str, *, fallback: AnimeSourceRecord) -> AnimeSourceRecord:
            return AnimeSourceRecord(
                title_cn="无日期测试番",
                source_id="no-date",
                source_url=source_url,
                year=fallback.year,
                season=fallback.season,
                synopsis="无日期简介。",
            )

    _patch_source_settings(monkeypatch)
    monkeypatch.setattr("app.routes.search.YourAnimesScraper", FakeScraper)

    result = asyncio.run(import_anime(ImportRequest(source_id="no-date"), db))

    anime = db.scalar(select(AnimeMaster).where(AnimeMaster.source_id == "no-date"))
    assert anime is not None
    assert result.anime_id == anime.id
    assert (anime.year, anime.season) == (now.year, (now.month - 1) // 3 + 1)


def test_import_anime_maps_source_404(monkeypatch) -> None:
    db = make_session()

    class FakeScraper:
        def __init__(self, base_url: str) -> None:
            self.base_url = base_url

        async def fetch_detail(self, source_url: str, *, fallback: AnimeSourceRecord) -> AnimeSourceRecord:
            raise _source_status_error(source_url, 404)

    _patch_source_settings(monkeypatch)
    monkeypatch.setattr("app.routes.search.YourAnimesScraper", FakeScraper)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(import_anime(ImportRequest(source_id="missing"), db))

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "数据源中未找到该作品"
    assert db.scalar(select(func.count()).select_from(AnimeMaster)) == 0
