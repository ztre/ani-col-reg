from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


settings = get_settings()
sqlite_path = settings.sqlite_path
if sqlite_path is not None:
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _migrate_sqlite_schema()


def _migrate_sqlite_schema() -> None:
    if not settings.database_url.startswith("sqlite"):
        return

    with engine.begin() as conn:
        anime_columns = _table_columns(conn, "anime_master")
        if anime_columns and "cover_url" not in anime_columns:
            conn.execute(text("ALTER TABLE anime_master ADD COLUMN cover_url VARCHAR(1000)"))

        collection_columns = _table_columns(conn, "collection_item")
        if collection_columns and _collection_table_needs_rebuild(collection_columns):
            _rebuild_collection_table(conn, collection_columns)

        if _table_columns(conn, "sync_job"):
            conn.execute(text("DROP TABLE sync_job"))


def _table_columns(conn, table_name: str) -> set[str]:
    rows = conn.execute(text(f"PRAGMA table_info({table_name})")).mappings().all()
    return {row["name"] for row in rows}


def _collection_table_needs_rebuild(columns: set[str]) -> bool:
    required = {"id", "user_id", "anime_id", "organize_status", "note", "release_tags", "group_tags", "created_at", "updated_at"}
    removed = {"status", "score", "favorite_reason", "favorite_level", "tags"}
    return bool(required - columns) or bool(removed & columns)


def _rebuild_collection_table(conn, columns: set[str]) -> None:
    release_expr = "release_tags" if "release_tags" in columns else "NULL"
    if "tags" in columns:
        release_expr = f"COALESCE({release_expr}, tags)"

    user_expr = "COALESCE(user_id, 'default')" if "user_id" in columns else "'default'"
    organize_expr = "organize_status" if "organize_status" in columns else "'pending'"
    note_expr = "note" if "note" in columns else "NULL"
    group_expr = "group_tags" if "group_tags" in columns else "NULL"
    created_expr = "created_at" if "created_at" in columns else "CURRENT_TIMESTAMP"
    updated_expr = "updated_at" if "updated_at" in columns else "CURRENT_TIMESTAMP"

    conn.execute(text("PRAGMA foreign_keys=OFF"))
    conn.execute(
        text(
            """
            CREATE TABLE collection_item_new (
                id INTEGER NOT NULL PRIMARY KEY,
                user_id VARCHAR(64) NOT NULL DEFAULT 'default',
                anime_id INTEGER NOT NULL UNIQUE,
                organize_status VARCHAR(32) NOT NULL DEFAULT 'pending',
                note TEXT,
                release_tags TEXT,
                group_tags TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(anime_id) REFERENCES anime_master (id)
            )
            """
        )
    )
    conn.execute(
        text(
            f"""
            INSERT INTO collection_item_new (
                id, user_id, anime_id, organize_status, note, release_tags, group_tags, created_at, updated_at
            )
            SELECT id, {user_expr}, anime_id, {organize_expr}, {note_expr}, {release_expr}, {group_expr}, {created_expr}, {updated_expr}
            FROM collection_item
            """
        )
    )
    conn.execute(text("DROP TABLE collection_item"))
    conn.execute(text("ALTER TABLE collection_item_new RENAME TO collection_item"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_collection_item_id ON collection_item (id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_collection_item_user_id ON collection_item (user_id)"))
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_collection_item_anime_id ON collection_item (anime_id)"))
    conn.execute(text("PRAGMA foreign_keys=ON"))
