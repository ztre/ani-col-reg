from types import SimpleNamespace

from sqlalchemy import create_engine, text

import app.database as database_module
from app.database import _rebuild_collection_table, init_db


def _create_legacy_schema(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE anime_master (
                id INTEGER PRIMARY KEY,
                source VARCHAR(50),
                source_id VARCHAR(255),
                title_cn VARCHAR(255),
                normalized_title VARCHAR(255),
                year INTEGER,
                season INTEGER,
                cover_url VARCHAR(1000),
                created_at DATETIME,
                updated_at DATETIME
            )
            """
        )
    )
    conn.execute(
        text(
            """
            INSERT INTO anime_master (id, source, source_id, title_cn, normalized_title, year, season) VALUES
                (1, 'youranimes', 'kn-1', '鬼灭之刃', '鬼灭之刃', 2019, 2),
                (2, 'youranimes', 'kn-2', '鬼灭之刃 游郭篇', '鬼灭之刃游郭篇', 2021, 4),
                (3, 'youranimes', 'sl-2', '关于我转生变成史莱姆这档事 第二季', '关于我转生变成史莱姆这档事第二季', 2021, 1),
                (4, 'youranimes', 'suffix-only', '第二季', '第二季', 2020, 1)
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE collection_item (
                id INTEGER PRIMARY KEY,
                user_id VARCHAR(64),
                anime_id INTEGER UNIQUE,
                organize_status VARCHAR(32),
                note TEXT,
                release_tags JSON,
                group_tags JSON,
                created_at DATETIME,
                updated_at DATETIME
            )
            """
        )
    )
    conn.execute(
        text(
            """
            INSERT INTO collection_item (
                id, user_id, anime_id, organize_status, note, release_tags, group_tags, created_at
            )
            VALUES (7, 'default', 1, 'emby', '手工备注', '["BDRip"]', '[]', '2025-01-02 03:04:05')
            """
        )
    )


def test_init_db_backfills_series_columns_and_rebuilds_collection_item(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "legacy.sqlite3"
    legacy_engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    with legacy_engine.begin() as conn:
        _create_legacy_schema(conn)
    legacy_engine.dispose()

    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    monkeypatch.setattr(database_module, "engine", engine)
    monkeypatch.setattr(database_module, "settings", SimpleNamespace(database_url=f"sqlite:///{db_path}"))

    init_db()
    init_db()  # 幂等：可重复启动

    with engine.begin() as conn:
        anime_columns = {row["name"] for row in conn.execute(text("PRAGMA table_info(anime_master)")).mappings()}
        assert {"series_key", "series_title", "season_label"}.issubset(anime_columns)

        rows = {
            row["id"]: row
            for row in conn.execute(
                text("SELECT id, title_cn, series_key, series_title, season_label FROM anime_master")
            ).mappings()
        }
        assert rows[1]["series_key"] == "鬼灭之刃"
        assert rows[1]["series_title"] == "鬼灭之刃"
        assert rows[1]["season_label"] is None
        assert rows[2]["series_key"] == "鬼灭之刃"
        assert rows[2]["series_title"] == "鬼灭之刃"
        assert rows[2]["season_label"] == "游郭篇"
        assert rows[3]["series_key"] == "关于我转生变成史莱姆这档事"
        assert rows[3]["series_title"] == "关于我转生变成史莱姆这档事"
        assert rows[3]["season_label"] == "第二季"
        assert rows[4]["series_key"] == "第二季"
        assert rows[4]["series_title"] == "第二季"
        assert rows[4]["season_label"] is None

        collection_columns = {
            row["name"] for row in conn.execute(text("PRAGMA table_info(collection_item)")).mappings()
        }
        # 迁移后新增 emby_organized 列（默认 0，未整理）
        assert collection_columns == {"id", "user_id", "anime_id", "emby_organized", "created_at"}
        emby_default = conn.execute(
            text("SELECT emby_organized FROM collection_item WHERE id = 7")
        ).scalar()
        assert emby_default == 0

        item = conn.execute(
            text("SELECT id, user_id, anime_id, created_at FROM collection_item WHERE id = 7")
        ).mappings().one()
        assert item["user_id"] == "default"
        assert item["anime_id"] == 1
        assert item["created_at"] == "2025-01-02 03:04:05"

    engine.dispose()


def test_collection_table_rebuild_drops_legacy_columns_and_keeps_rows() -> None:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE anime_master (id INTEGER PRIMARY KEY)"))
        conn.execute(text("INSERT INTO anime_master (id) VALUES (1)"))
        conn.execute(
            text(
                """
                CREATE TABLE collection_item (
                    id INTEGER PRIMARY KEY,
                    user_id VARCHAR(64),
                    anime_id INTEGER UNIQUE,
                    status VARCHAR(20),
                    score INTEGER,
                    organize_status VARCHAR(32),
                    note TEXT,
                    release_tags JSON,
                    group_tags JSON,
                    created_at DATETIME,
                    updated_at DATETIME
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO collection_item (
                    id, user_id, anime_id, status, score, organize_status, note, release_tags, group_tags, created_at
                )
                VALUES (7, 'default', 1, '在看', 8, 'emby', '手工备注', '["BDRip"]', '[]', '2025-01-02 03:04:05')
                """
            )
        )

        columns = {row["name"] for row in conn.execute(text("PRAGMA table_info(collection_item)")).mappings()}
        _rebuild_collection_table(conn, columns)

        rebuilt = {row["name"] for row in conn.execute(text("PRAGMA table_info(collection_item)")).mappings()}
        assert rebuilt == {"id", "user_id", "anime_id", "created_at"}

        row = conn.execute(
            text("SELECT id, user_id, anime_id, created_at FROM collection_item WHERE id = 7")
        ).mappings().one()
        assert row["user_id"] == "default"
        assert row["anime_id"] == 1
        assert row["created_at"] == "2025-01-02 03:04:05"
