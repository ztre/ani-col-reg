from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.database import Base
from app.models import AnimeMaster, CollectionItem
from app.services.scraper import AnimeSourceRecord
from app.services.sync import upsert_records


def make_session() -> Session:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return Session(engine)


def test_upsert_records_deduplicates_and_preserves_collection() -> None:
    db = make_session()
    records = [
        AnimeSourceRecord(
            title_cn="春日测试番",
            source_id="alpha",
            source_url="https://youranimes.tw/anime/alpha",
            year=2026,
            season=2,
            platforms="巴哈姆特动画疯",
        )
    ]

    created, updated = upsert_records(db, records)
    assert (created, updated) == (1, 0)

    anime = db.scalar(select(AnimeMaster).where(AnimeMaster.source_id == "alpha"))
    assert anime is not None
    collection = CollectionItem(anime_id=anime.id, note="手工备注", release_tags="BDRip", group_tags="ANi")
    db.add(collection)
    db.commit()

    records[0].platforms = "Netflix"
    created, updated = upsert_records(db, records)

    assert (created, updated) == (0, 1)
    anime = db.scalar(select(AnimeMaster).where(AnimeMaster.source_id == "alpha"))
    collection = db.scalar(select(CollectionItem).where(CollectionItem.anime_id == anime.id))
    assert anime.platforms == "Netflix"
    assert collection.note == "手工备注"
    assert collection.release_tags == "BDRip"
    assert collection.group_tags == "ANi"


def test_upsert_records_handles_duplicate_source_ids_in_same_batch() -> None:
    db = make_session()
    records = [
        AnimeSourceRecord(
            title_cn="重复番剧",
            source_id="dup-alpha",
            source_url="https://youranimes.tw/anime/dup-alpha",
            year=2026,
            season=4,
            platforms="巴哈姆特动画疯",
        ),
        AnimeSourceRecord(
            title_cn="重复番剧",
            source_id="dup-alpha",
            source_url="https://youranimes.tw/anime/dup-alpha",
            year=2026,
            season=4,
            platforms="Netflix",
        ),
    ]

    created, updated = upsert_records(db, records)

    assert (created, updated) == (1, 1)
    anime = db.scalar(select(AnimeMaster).where(AnimeMaster.source_id == "dup-alpha"))
    assert anime is not None
    assert anime.platforms == "Netflix"


def test_replace_season_prunes_stale_uncollected_rows_and_keeps_collected() -> None:
    db = make_session()
    stale = AnimeMaster(
        source="youranimes",
        source_id="stale-1",
        title_cn="旧条目",
        normalized_title="旧条目",
        year=2027,
        season=1,
    )
    kept = AnimeMaster(
        source="youranimes",
        source_id="keep-1",
        title_cn="收藏条目",
        normalized_title="收藏条目",
        year=2027,
        season=1,
    )
    db.add_all([stale, kept])
    db.flush()
    db.add(CollectionItem(anime_id=kept.id, note="保留"))
    db.commit()

    records = [
        AnimeSourceRecord(
            title_cn="新条目",
            source_id="fresh-1",
            source_url="https://youranimes.tw/anime/fresh-1",
            year=2027,
            season=1,
            platforms="Netflix",
        )
    ]

    created, updated = upsert_records(db, records, mode="replace-season", sync_scopes=[(2027, 1)])

    assert (created, updated) == (1, 0)
    assert db.scalar(select(AnimeMaster).where(AnimeMaster.source_id == "stale-1")) is None
    assert db.scalar(select(AnimeMaster).where(AnimeMaster.source_id == "keep-1")) is not None
    assert db.scalar(select(AnimeMaster).where(AnimeMaster.source_id == "fresh-1")) is not None


def test_replace_season_can_clear_scope_when_source_returns_empty() -> None:
    db = make_session()
    db.add(
        AnimeMaster(
            source="youranimes",
            source_id="gone-1",
            title_cn="将被清理",
            normalized_title="将被清理",
            year=2027,
            season=2,
        )
    )
    db.commit()

    created, updated = upsert_records(db, [], mode="replace-season", sync_scopes=[(2027, 2)])

    assert (created, updated) == (0, 0)
    assert db.scalar(select(AnimeMaster).where(AnimeMaster.source_id == "gone-1")) is None


def test_upsert_records_merges_old_source_id_row_into_target_scope_row() -> None:
    db = make_session()
    stale_source_row = AnimeMaster(
        source="mikan",
        source_id="same-id",
        source_url="https://mikanani.me/Home/Bangumi/legacy",
        title_cn="测试番",
        normalized_title="测试番",
        year=2026,
        season=1,
    )
    target_scope_row = AnimeMaster(
        source="youranimes",
        source_id="ya-1",
        source_url="https://youranimes.tw/animes/ya-1",
        title_cn="测试番",
        normalized_title="测试番",
        year=2026,
        season=2,
    )
    db.add_all([stale_source_row, target_scope_row])
    db.commit()

    created, updated = upsert_records(
        db,
        [
            AnimeSourceRecord(
                title_cn="测试番",
                source_id="same-id",
                source_url="https://mikanani.me/Home/Bangumi/1",
                year=2026,
                season=2,
            )
        ],
        source="mikan",
    )

    assert (created, updated) == (0, 1)
    rows = db.scalars(select(AnimeMaster).where(AnimeMaster.normalized_title == "测试番")).all()
    assert len(rows) == 1
    assert rows[0].season == 2
    assert rows[0].source == "mikan"
    assert rows[0].source_id == "same-id"


def test_replace_season_only_prunes_active_source_rows() -> None:
    db = make_session()
    db.add_all(
        [
            AnimeMaster(
                source="mikan",
                source_id="mikan-old",
                title_cn="Mikan 旧条目",
                normalized_title="mikan旧条目",
                year=2027,
                season=2,
            ),
            AnimeMaster(
                source="youranimes",
                source_id="ya-old",
                title_cn="YA 旧条目",
                normalized_title="ya旧条目",
                year=2027,
                season=2,
            ),
        ]
    )
    db.commit()

    upsert_records(db, [], mode="replace-season", sync_scopes=[(2027, 2)], source="mikan")

    assert db.scalar(select(AnimeMaster).where(AnimeMaster.source_id == "mikan-old")) is None
    assert db.scalar(select(AnimeMaster).where(AnimeMaster.source_id == "ya-old")) is not None
