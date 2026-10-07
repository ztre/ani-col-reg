from collections.abc import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


settings = get_settings()
sqlite_path = settings.sqlite_path
if sqlite_path is not None:
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
if settings.database_url.startswith("sqlite"):
    connect_args["timeout"] = 30

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=3600,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)


@event.listens_for(engine, "connect")
def configure_sqlite_connection(dbapi_connection, connection_record) -> None:
    del connection_record
    if not settings.database_url.startswith("sqlite"):
        return

    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


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
        if anime_columns and "series_key" not in anime_columns:
            conn.execute(text("ALTER TABLE anime_master ADD COLUMN series_key VARCHAR(255) NOT NULL DEFAULT ''"))
        if anime_columns and "series_title" not in anime_columns:
            conn.execute(text("ALTER TABLE anime_master ADD COLUMN series_title VARCHAR(255) NOT NULL DEFAULT ''"))
        if anime_columns and "season_label" not in anime_columns:
            conn.execute(text("ALTER TABLE anime_master ADD COLUMN season_label VARCHAR(255)"))
        if anime_columns:
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS ix_anime_master_series_key ON anime_master (series_key)")
            )
            _backfill_series_columns(conn)

        collection_columns = _table_columns(conn, "collection_item")
        if collection_columns and _collection_table_needs_rebuild(collection_columns):
            _rebuild_collection_table(conn, collection_columns)
            collection_columns = _table_columns(conn, "collection_item")
        if collection_columns and "emby_organized" not in collection_columns:
            conn.execute(
                text("ALTER TABLE collection_item ADD COLUMN emby_organized BOOLEAN NOT NULL DEFAULT 0")
            )

        if _table_columns(conn, "sync_job"):
            conn.execute(text("DROP TABLE sync_job"))

        _migrate_series_algorithm(conn)


def _migrate_series_algorithm(conn) -> None:
    """系列归一化算法升级时，用 user_version 标记并对存量行全量重算。"""
    from app.services.series import SERIES_ALGORITHM_VERSION

    current_version = conn.execute(text("PRAGMA user_version")).scalar() or 0
    if current_version >= SERIES_ALGORITHM_VERSION:
        return

    from app.services.series import extract_series_info

    rows = conn.execute(text("SELECT id, title_cn FROM anime_master")).mappings().all()
    for row in rows:
        info = extract_series_info(row["title_cn"] or "")
        conn.execute(
            text(
                """
                UPDATE anime_master
                SET series_key = :series_key,
                    series_title = :series_title,
                    season_label = :season_label
                WHERE id = :id
                """
            ),
            {
                "series_key": info.series_key,
                "series_title": info.series_title,
                "season_label": info.season_label,
                "id": row["id"],
            },
        )
    conn.execute(text(f"PRAGMA user_version = {SERIES_ALGORITHM_VERSION}"))


def _backfill_series_columns(conn) -> None:
    from app.services.series import extract_series_info

    rows = conn.execute(
        text("SELECT id, title_cn FROM anime_master WHERE series_key IS NULL OR series_key = ''")
    ).mappings().all()
    for row in rows:
        info = extract_series_info(row["title_cn"] or "")
        conn.execute(
            text(
                """
                UPDATE anime_master
                SET series_key = :series_key,
                    series_title = :series_title,
                    season_label = :season_label
                WHERE id = :id
                """
            ),
            {
                "id": row["id"],
                "series_key": info.series_key,
                "series_title": info.series_title,
                "season_label": info.season_label,
            },
        )


def _table_columns(conn, table_name: str) -> set[str]:
    rows = conn.execute(text(f"PRAGMA table_info({table_name})")).mappings().all()
    return {row["name"] for row in rows}


def _collection_table_needs_rebuild(columns: set[str]) -> bool:
    required = {"id", "user_id", "anime_id", "created_at"}
    # TODO(后续任务重写): organize_status/note/release_tags/group_tags 等列已从模型删除，仅在迁移期需要识别。
    removed = {
        "organize_status",
        "note",
        "release_tags",
        "group_tags",
        "updated_at",
        "status",
        "score",
        "favorite_reason",
        "favorite_level",
        "tags",
    }
    return bool(required - columns) or bool(removed & columns)


def _rebuild_collection_table(conn, columns: set[str]) -> None:
    user_expr = "COALESCE(user_id, 'default')" if "user_id" in columns else "'default'"
    created_expr = "created_at" if "created_at" in columns else "CURRENT_TIMESTAMP"

    conn.execute(text("PRAGMA foreign_keys=OFF"))
    conn.execute(
        text(
            """
            CREATE TABLE collection_item_new (
                id INTEGER NOT NULL PRIMARY KEY,
                user_id VARCHAR(64) NOT NULL DEFAULT 'default',
                anime_id INTEGER NOT NULL UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(anime_id) REFERENCES anime_master (id)
            )
            """
        )
    )
    conn.execute(
        text(
            f"""
            INSERT INTO collection_item_new (id, user_id, anime_id, created_at)
            SELECT id, {user_expr}, anime_id, {created_expr}
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
