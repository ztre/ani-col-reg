from types import SimpleNamespace

from fastapi import HTTPException
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api import auth_status, clear_cover_cache_maintenance, get_app_settings, login, reset_collection_maintenance, update_app_settings
from app.database import Base
from app.models import AnimeMapping, AnimeMaster, CollectionItem, EpisodeProgress
from app.schemas import AppSettingsUpdate, LoginRequest
from app.services.app_settings import AppSettingsStore, current_default_season
from app.services.scraper import normalize_title


def make_store(tmp_path) -> AppSettingsStore:
    return AppSettingsStore(
        tmp_path / "app_settings.json",
        default_app_name="番剧收藏登记系统",
        default_library_subcopy="默认说明文案",
        default_search_year=2026,
        default_admin_username="admin",
        default_admin_password="ani-col-reg",
    )


def make_session() -> Session:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return Session(engine)


def test_login_status_and_password_rotation(tmp_path) -> None:
    store = make_store(tmp_path)
    db = make_session()

    initial_status = auth_status(store=store)
    assert initial_status.authenticated is False
    assert initial_status.requires_password_change is True
    assert initial_status.default_search_season == current_default_season()

    response = login(LoginRequest(username="admin", password="ani-col-reg"), store=store)
    assert response.user.username == "admin"
    assert response.status.authenticated is True

    status = auth_status(authorization=f"Bearer {response.token}", store=store)
    assert status.authenticated is True

    updated = update_app_settings(
        AppSettingsUpdate(app_name="新的番剧库", current_password="ani-col-reg", new_password="safe-pass"),
        store=store,
        db=db,
    )
    assert updated.app_name == "新的番剧库"
    assert updated.requires_password_change is False

    try:
        login(LoginRequest(username="admin", password="ani-col-reg"), store=store)
    except HTTPException as exc:
        assert exc.status_code == 401
    else:
        raise AssertionError("old password should be rejected")

    rotated = login(LoginRequest(username="admin", password="safe-pass"), store=store)
    assert rotated.status.authenticated is True


def test_settings_include_sync_defaults_and_cover_cache_actions(tmp_path, monkeypatch) -> None:
    store = make_store(tmp_path)
    db = make_session()
    cache_dir = tmp_path / "covers"
    cache_dir.mkdir()
    (cache_dir / "alpha.webp").write_bytes(b"cover-a")
    (cache_dir / "beta.webp").write_bytes(b"cover-b")

    anime = AnimeMaster(
        source="youranimes",
        source_id="alpha",
        source_url="https://youranimes.tw/animes/alpha",
        title_cn="缓存测试番",
        normalized_title=normalize_title("缓存测试番"),
        year=2026,
        season=2,
        cover_url="/api/covers/alpha.webp",
    )
    db.add(anime)
    db.commit()
    db.refresh(anime)

    db.add_all(
        [
            CollectionItem(anime_id=anime.id, note="保留测试"),
            AnimeMapping(anime_id=anime.id, mgr_item_id="mgr-alpha"),
            EpisodeProgress(anime_id=anime.id, watched_eps=3),
        ]
    )
    db.commit()

    monkeypatch.setattr(
        "app.routes.common.get_settings",
        lambda: SimpleNamespace(
            cover_cache_dir=cache_dir,
            cover_cache_public_path="/api/covers",
            youranimes_base_url="https://youranimes.tw",
            mikan_base_url="https://mikanani.me",
        ),
    )

    updated = update_app_settings(
        AppSettingsUpdate(
            anime_source="mikan",
            sync_strategy="replace-season",
            default_filter_collected=True,
            default_filter_release_tag="BDRip",
            default_filter_group_tag="ANi",
        ),
        store=store,
        db=db,
    )
    assert updated.anime_source == "mikan"
    assert updated.sync_strategy == "replace-season"
    assert updated.default_filter_collected is True
    assert updated.default_filter_release_tag == "BDRip"
    assert updated.cover_cache_file_count == 0
    assert db.scalar(select(func.count()).select_from(AnimeMaster)) == 0
    assert db.scalar(select(func.count()).select_from(CollectionItem)) == 0
    assert db.scalar(select(func.count()).select_from(AnimeMapping)) == 0
    assert db.scalar(select(func.count()).select_from(EpisodeProgress)) == 0

    current = get_app_settings(store=store, db=db)
    assert current.default_filter_group_tag == "ANi"
    assert current.collection_count == 0
    assert current.cover_cache_total_bytes == 0

    (cache_dir / "gamma.webp").write_bytes(b"cover-c")
    anime = AnimeMaster(
        source="mikan",
        source_id="beta",
        source_url="https://mikanani.me/Home/Bangumi/777",
        title_cn="维护测试番",
        normalized_title=normalize_title("维护测试番"),
        year=2026,
        season=2,
        cover_url="/api/covers/gamma.webp",
    )
    db.add(anime)
    db.commit()
    db.refresh(anime)

    cleared = clear_cover_cache_maintenance(db=db)
    assert cleared.deleted_files == 1
    assert cleared.reset_cover_urls == 1
    assert cleared.remaining_files == 0

    refreshed_anime = db.get(AnimeMaster, anime.id)
    assert refreshed_anime is not None
    assert refreshed_anime.cover_url is None


def test_reset_collection_maintenance_only_clears_collection_items(tmp_path) -> None:
    store = make_store(tmp_path)
    db = make_session()

    anime = AnimeMaster(
        source="youranimes",
        source_id="collection-reset-alpha",
        source_url="https://youranimes.tw/animes/collection-reset-alpha",
        title_cn="收藏重置测试番",
        normalized_title=normalize_title("收藏重置测试番"),
        year=2026,
        season=2,
    )
    db.add(anime)
    db.commit()
    db.refresh(anime)

    db.add_all(
        [
            CollectionItem(anime_id=anime.id, note="待清理"),
            AnimeMapping(anime_id=anime.id, mgr_item_id="mgr-reset-alpha"),
            EpisodeProgress(anime_id=anime.id, watched_eps=4),
        ]
    )
    db.commit()

    before_reset = get_app_settings(store=store, db=db)
    assert before_reset.collection_count == 1

    reset = reset_collection_maintenance(db=db)

    assert reset.deleted_collections == 1
    assert reset.remaining_collections == 0

    after_reset = get_app_settings(store=store, db=db)
    assert after_reset.collection_count == 0
    assert db.scalar(select(func.count()).select_from(AnimeMaster)) == 1
    assert db.scalar(select(func.count()).select_from(CollectionItem)) == 0
    assert db.scalar(select(func.count()).select_from(AnimeMapping)) == 1
    assert db.scalar(select(func.count()).select_from(EpisodeProgress)) == 1
