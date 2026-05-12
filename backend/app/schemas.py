from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class CollectionOut(BaseModel):
    id: int
    user_id: str
    anime_id: int
    organize_status: Literal["pending", "emby"]
    note: str | None
    release_tags: str | None
    group_tags: str | None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class AnimeOut(BaseModel):
    id: int
    source: str
    source_id: str | None
    source_url: str | None
    title_cn: str
    title_jp: str | None
    title_en: str | None
    aliases: str | None
    synopsis: str | None
    year: int
    season: int
    premiere_date: str | None
    platforms: str | None
    staff: str | None
    cast: str | None
    tags: str | None
    pv_url: str | None
    cover_url: str | None
    collection_item: CollectionOut | None = None

    model_config = {"from_attributes": True}


class PaginatedAnime(BaseModel):
    items: list[AnimeOut]
    total: int
    page: int
    page_size: int


class AuthUserOut(BaseModel):
    username: str


class AuthStatusOut(BaseModel):
    authenticated: bool
    user: AuthUserOut | None = None
    app_name: str
    library_subcopy: str
    default_search_year: int
    default_search_season: int | None = None
    default_page_size: int
    default_filter_collected: bool = False
    default_filter_release_tag: str | None = None
    default_filter_group_tag: str | None = None
    requires_password_change: bool = False


class LoginRequest(BaseModel):
    username: str
    password: str

    @field_validator("username", "password")
    @classmethod
    def fields_must_not_be_empty(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("field cannot be empty")
        return stripped


class LoginResponse(BaseModel):
    token: str
    user: AuthUserOut
    status: AuthStatusOut


class AppSettingsOut(BaseModel):
    app_name: str
    library_subcopy: str
    anime_source: Literal["youranimes", "mikan"]
    default_search_year: int
    default_search_season: int | None = None
    default_page_size: int
    default_filter_collected: bool = False
    default_filter_release_tag: str | None = None
    default_filter_group_tag: str | None = None
    sync_strategy: Literal["incremental", "replace-season"]
    admin_username: str
    youranimes_base_url: str
    mikan_base_url: str
    cover_cache_file_count: int = 0
    cover_cache_total_bytes: int = 0
    updated_at: datetime
    requires_password_change: bool = False


class MaintenanceActionOut(BaseModel):
    deleted_files: int
    deleted_bytes: int
    reset_cover_urls: int = 0
    remaining_files: int
    remaining_bytes: int


class AppSettingsUpdate(BaseModel):
    app_name: str | None = None
    library_subcopy: str | None = None
    anime_source: Literal["youranimes", "mikan"] | None = None
    default_search_year: int | None = Field(default=None, ge=1968, le=2100)
    default_search_season: int | None = Field(default=None, ge=1, le=4)
    default_page_size: int | None = Field(default=None, ge=12, le=96)
    default_filter_collected: bool | None = None
    default_filter_release_tag: str | None = None
    default_filter_group_tag: str | None = None
    sync_strategy: Literal["incremental", "replace-season"] | None = None
    admin_username: str | None = None
    current_password: str | None = None
    new_password: str | None = Field(default=None, min_length=6)

    @field_validator("app_name", "library_subcopy", "admin_username")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("field cannot be empty")
        return stripped

    @field_validator("default_filter_release_tag", "default_filter_group_tag")
    @classmethod
    def normalize_optional_filter_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class CollectionCreate(BaseModel):
    anime_id: int
    organize_status: Literal["pending", "emby"] = "pending"
    note: str | None = None
    release_tags: str | None = None
    group_tags: str | None = None


class CollectionUpdate(BaseModel):
    organize_status: Literal["pending", "emby"] | None = None
    note: str | None = None
    release_tags: str | None = None
    group_tags: str | None = None


class AnimeSearchRequest(BaseModel):
    year: int = Field(ge=1968, le=2100)
    season: int | None = Field(default=None, ge=1, le=4, description="1=Jan, 2=Apr, 3=Jul, 4=Oct")
    keyword: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class MappingCreate(BaseModel):
    anime_id: int
    mgr_item_id: str
    match_method: str = "manual"
    confidence: int = Field(default=100, ge=0, le=100)

    @field_validator("mgr_item_id")
    @classmethod
    def mgr_item_id_not_empty(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("mgr_item_id cannot be empty")
        return stripped


class MappingOut(BaseModel):
    id: int
    anime_id: int
    mgr_item_id: str
    match_method: str
    confidence: int
    created_at: datetime

    model_config = {"from_attributes": True}
