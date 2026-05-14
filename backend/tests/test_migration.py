import json

from sqlalchemy import create_engine, text

from app.database import _rebuild_collection_table


def test_collection_table_rebuild_removes_rating_fields_and_keeps_notes_tags() -> None:
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
                    note TEXT,
                    favorite_reason TEXT,
                    favorite_level INTEGER,
                    tags TEXT,
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
                    id, user_id, anime_id, status, score, note, favorite_reason, favorite_level, tags
                )
                VALUES (7, 'default', 1, '在看', 8, '手工备注', '旧理由', 4, 'BDRip, 1080p')
                """
            )
        )

        columns = {row["name"] for row in conn.execute(text("PRAGMA table_info(collection_item)")).mappings()}
        _rebuild_collection_table(conn, columns)

        rebuilt = {row["name"] for row in conn.execute(text("PRAGMA table_info(collection_item)")).mappings()}
        assert {"status", "score", "favorite_reason", "favorite_level", "tags"}.isdisjoint(rebuilt)
        assert {"organize_status", "release_tags", "group_tags", "note"}.issubset(rebuilt)

        row = conn.execute(text("SELECT organize_status, note, release_tags, group_tags FROM collection_item WHERE id = 7")).mappings().one()
        assert row["organize_status"] == "pending"
        assert row["note"] == "手工备注"
        assert json.loads(row["release_tags"]) == ["BDRip", "1080p"]
        assert json.loads(row["group_tags"]) == []
