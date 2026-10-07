from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AnimeMaster(Base):
    __tablename__ = "anime_master"
    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uq_anime_source_id"),
        UniqueConstraint("year", "season", "normalized_title", name="uq_anime_year_season_title"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source: Mapped[str] = mapped_column(String(50), default="youranimes", index=True)
    source_id: Mapped[str | None] = mapped_column(String(255), index=True)
    source_url: Mapped[str | None] = mapped_column(String(1000))
    title_cn: Mapped[str] = mapped_column(String(255), index=True)
    title_jp: Mapped[str | None] = mapped_column(String(255))
    title_en: Mapped[str | None] = mapped_column(String(255))
    normalized_title: Mapped[str] = mapped_column(String(255), index=True)
    aliases: Mapped[str | None] = mapped_column(Text)
    synopsis: Mapped[str | None] = mapped_column(Text)
    year: Mapped[int] = mapped_column(Integer, index=True)
    season: Mapped[int] = mapped_column(Integer, index=True)
    premiere_date: Mapped[str | None] = mapped_column(String(50))
    platforms: Mapped[str | None] = mapped_column(Text)
    staff: Mapped[str | None] = mapped_column(Text)
    cast: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[str | None] = mapped_column(Text)
    pv_url: Mapped[str | None] = mapped_column(String(1000))
    cover_url: Mapped[str | None] = mapped_column(String(1000))
    series_key: Mapped[str] = mapped_column(String(255), index=True, default="")
    series_title: Mapped[str] = mapped_column(String(255), default="")
    season_label: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    collection_item: Mapped["CollectionItem | None"] = relationship(back_populates="anime", uselist=False)
    mappings: Mapped[list["AnimeMapping"]] = relationship(back_populates="anime", cascade="all, delete-orphan")
    progress: Mapped["EpisodeProgress | None"] = relationship(back_populates="anime", uselist=False)


class CollectionItem(Base):
    __tablename__ = "collection_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(64), default="default", index=True)
    anime_id: Mapped[int] = mapped_column(ForeignKey("anime_master.id"), unique=True, index=True)
    # 该季度是否已在 Emby 中整理（媒体库归档标记）
    emby_organized: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    anime: Mapped[AnimeMaster] = relationship(back_populates="collection_item")


class AnimeMapping(Base):
    __tablename__ = "anime_mapping"
    __table_args__ = (UniqueConstraint("anime_id", "mgr_item_id", name="uq_anime_mgr_mapping"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    anime_id: Mapped[int] = mapped_column(ForeignKey("anime_master.id"), index=True)
    mgr_item_id: Mapped[str] = mapped_column(String(255), index=True)
    match_method: Mapped[str] = mapped_column(String(50), default="manual")
    confidence: Mapped[int] = mapped_column(Integer, default=100)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    anime: Mapped[AnimeMaster] = relationship(back_populates="mappings")


class EpisodeProgress(Base):
    __tablename__ = "episode_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    anime_id: Mapped[int] = mapped_column(ForeignKey("anime_master.id"), unique=True, index=True)
    watched_eps: Mapped[int] = mapped_column(Integer, default=0)
    total_eps: Mapped[int | None] = mapped_column(Integer)
    last_watched_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    anime: Mapped[AnimeMaster] = relationship(back_populates="progress")


class AppLog(Base):
    __tablename__ = "app_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    level: Mapped[str] = mapped_column(String(16), index=True)
    source: Mapped[str] = mapped_column(String(64), index=True)
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
