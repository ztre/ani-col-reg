from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AnimeMaster, AnimeMapping, CollectionItem, EpisodeProgress
from app.services.scraper import AnimeSourceRecord, normalize_title


DEFAULT_SOURCE = "youranimes"


def upsert_records(
    db: Session,
    records: list[AnimeSourceRecord],
    mode: str = "incremental",
    sync_scopes: list[tuple[int, int]] | None = None,
    source: str = DEFAULT_SOURCE,
) -> tuple[int, int]:
    created = 0
    updated = 0

    for record in records:
        normalized = normalize_title(record.title_cn)
        existing = _find_existing(db, record, normalized, source=source)
        if existing is None:
            anime = AnimeMaster(
                source=source,
                source_id=record.source_id,
                source_url=record.source_url,
                title_cn=record.title_cn,
                title_jp=record.title_jp,
                title_en=record.title_en,
                normalized_title=normalized,
                aliases=record.aliases,
                synopsis=record.synopsis,
                year=record.year,
                season=record.season,
                premiere_date=record.premiere_date,
                platforms=record.platforms,
                staff=record.staff,
                cast=record.cast,
                tags=record.tags,
                pv_url=record.pv_url,
                cover_url=record.cover_url,
            )
            db.add(anime)
            db.flush()
            created += 1
            continue

        _update_source_fields(existing, record, normalized, source=source)
        updated += 1

    if mode == "replace-season":
        _prune_missing_records(db, records, sync_scopes=sync_scopes, source=source)

    db.commit()
    return created, updated


def _find_existing(db: Session, record: AnimeSourceRecord, normalized: str, source: str = DEFAULT_SOURCE) -> AnimeMaster | None:
    by_source: AnimeMaster | None = None
    if record.source_id:
        by_source = db.scalar(
            select(AnimeMaster).where(
                AnimeMaster.source == source,
                AnimeMaster.source_id == record.source_id,
            )
        )
    by_scope = db.scalar(
        select(AnimeMaster).where(
            AnimeMaster.year == record.year,
            AnimeMaster.season == record.season,
            AnimeMaster.normalized_title == normalized,
        )
    )

    if by_source and by_scope and by_source.id != by_scope.id:
        _merge_anime_rows(db, source_row=by_source, target_row=by_scope)
        return by_scope

    return by_scope or by_source


def _update_source_fields(anime: AnimeMaster, record: AnimeSourceRecord, normalized: str, *, source: str) -> None:
    anime.source = source
    anime.source_id = record.source_id or anime.source_id
    anime.source_url = record.source_url or anime.source_url
    anime.title_cn = record.title_cn
    anime.title_jp = record.title_jp
    anime.title_en = record.title_en
    anime.normalized_title = normalized
    anime.aliases = record.aliases
    anime.synopsis = record.synopsis
    anime.year = record.year
    anime.season = record.season
    anime.premiere_date = record.premiere_date
    anime.platforms = record.platforms
    anime.staff = record.staff
    anime.cast = record.cast
    anime.tags = record.tags
    anime.pv_url = record.pv_url
    anime.cover_url = record.cover_url or anime.cover_url


def _prune_missing_records(
    db: Session,
    records: list[AnimeSourceRecord],
    sync_scopes: list[tuple[int, int]] | None = None,
    source: str = DEFAULT_SOURCE,
) -> None:
    source_ids_by_scope: dict[tuple[int, int], set[str]] = defaultdict(set)
    for record in records:
        if record.source_id:
            source_ids_by_scope[(record.year, record.season)].add(record.source_id)

    scopes = set(sync_scopes or source_ids_by_scope.keys())
    for scope in scopes:
        source_ids = source_ids_by_scope.get(scope, set())
        year, season = scope

        stale_rows = db.scalars(
            select(AnimeMaster)
            .outerjoin(CollectionItem, CollectionItem.anime_id == AnimeMaster.id)
            .where(
                AnimeMaster.source == source,
                AnimeMaster.year == year,
                AnimeMaster.season == season,
                AnimeMaster.source_id.is_not(None),
                CollectionItem.id.is_(None),
            )
        ).all()

        for anime in stale_rows:
            if anime.source_id not in source_ids:
                db.delete(anime)


def _merge_anime_rows(db: Session, *, source_row: AnimeMaster, target_row: AnimeMaster) -> None:
    if source_row.collection_item is not None:
        if target_row.collection_item is None:
            source_row.collection_item.anime_id = target_row.id
        else:
            _merge_collection(source_row.collection_item, target_row.collection_item)
            db.delete(source_row.collection_item)

    if source_row.progress is not None:
        if target_row.progress is None:
            source_row.progress.anime_id = target_row.id
        else:
            _merge_progress(source_row.progress, target_row.progress)
            db.delete(source_row.progress)

    existing_mapping_ids = {mapping.mgr_item_id for mapping in target_row.mappings}
    for mapping in list(source_row.mappings):
        if mapping.mgr_item_id in existing_mapping_ids:
            db.delete(mapping)
            continue
        mapping.anime_id = target_row.id

    source_row.source_id = None
    db.flush()
    db.delete(source_row)


def _merge_collection(source: CollectionItem, target: CollectionItem) -> None:
    if not target.note and source.note:
        target.note = source.note
    if not target.release_tags and source.release_tags:
        target.release_tags = source.release_tags
    if not target.group_tags and source.group_tags:
        target.group_tags = source.group_tags


def _merge_progress(source: EpisodeProgress, target: EpisodeProgress) -> None:
    target.watched_eps = max(target.watched_eps or 0, source.watched_eps or 0)
    if target.total_eps is None and source.total_eps is not None:
        target.total_eps = source.total_eps
    if target.last_watched_at is None and source.last_watched_at is not None:
        target.last_watched_at = source.last_watched_at
