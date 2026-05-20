import json
import secrets
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field

from app.security import hash_password, verify_password


SYNC_STRATEGIES = {"incremental", "replace-season"}
ANIME_SOURCES = {"youranimes", "mikan"}


def current_default_season(now: datetime | None = None) -> int:
    current = now or datetime.now(UTC)
    month = current.month
    if month <= 3:
        return 1
    if month <= 6:
        return 2
    if month <= 9:
        return 3
    return 4


class StoredAppSettings(BaseModel):
    app_name: str
    library_subcopy: str
    anime_source: str = "youranimes"
    default_search_year: int
    default_search_season: int | None = None
    default_page_size: int = 24
    default_filter_collected: bool = False
    default_filter_release_tag: str | None = None
    default_filter_group_tag: str | None = None
    sync_strategy: str = "incremental"
    admin_username: str
    password_salt: str
    password_hash: str
    auth_secret: str
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AppSettingsStore:
    def __init__(
        self,
        path: Path,
        *,
        default_app_name: str,
        default_library_subcopy: str,
        default_search_year: int,
        default_admin_username: str,
        default_admin_password: str,
    ) -> None:
        self.path = path
        self.default_app_name = default_app_name
        self.default_library_subcopy = default_library_subcopy
        self.default_search_year = default_search_year
        self.default_admin_username = default_admin_username
        self.default_admin_password = default_admin_password

    def load(self) -> StoredAppSettings:
        if not self.path.exists():
            stored = self._default_settings()
            self._save(stored)
            return stored

        with self.path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        stored = StoredAppSettings.model_validate(payload)
        if stored.sync_strategy != "incremental":
            stored.sync_strategy = "incremental"
            self._save(stored)
        return stored

    def authenticate(self, username: str, password: str) -> StoredAppSettings | None:
        stored = self.load()
        if username != stored.admin_username:
            return None
        if not verify_password(password, stored.password_salt, stored.password_hash):
            return None
        return stored

    def update(self, values: dict) -> StoredAppSettings:
        stored = self.load()

        for field in [
            "app_name",
            "library_subcopy",
            "default_search_year",
            "default_search_season",
            "default_page_size",
            "default_filter_collected",
        ]:
            if field in values:
                setattr(stored, field, values[field])

        if "anime_source" in values:
            anime_source = values["anime_source"]
            if anime_source not in ANIME_SOURCES:
                raise ValueError("不支持的数据源")
            stored.anime_source = anime_source

        for field in ["default_filter_release_tag", "default_filter_group_tag"]:
            if field in values:
                value = values[field]
                if isinstance(value, str):
                    value = value.strip() or None
                setattr(stored, field, value)

        if "sync_strategy" in values:
            sync_strategy = values["sync_strategy"]
            if sync_strategy is not None and sync_strategy not in SYNC_STRATEGIES:
                raise ValueError("不支持的同步策略")

        stored.sync_strategy = "incremental"

        if "admin_username" in values:
            admin_username = (values.get("admin_username") or "").strip()
            if not admin_username:
                raise ValueError("管理员用户名不能为空")
            stored.admin_username = admin_username

        new_password = values.get("new_password")
        if new_password:
            current_password = values.get("current_password")
            if not current_password or not verify_password(current_password, stored.password_salt, stored.password_hash):
                raise ValueError("当前密码不正确")
            stored.password_salt, stored.password_hash = hash_password(new_password)

        stored.updated_at = datetime.now(UTC)
        self._save(stored)
        return stored

    def uses_default_credentials(self, stored: StoredAppSettings | None = None) -> bool:
        current = stored or self.load()
        return current.admin_username == self.default_admin_username and verify_password(
            self.default_admin_password,
            current.password_salt,
            current.password_hash,
        )

    def _default_settings(self) -> StoredAppSettings:
        password_salt, password_hash = hash_password(self.default_admin_password)
        return StoredAppSettings(
            app_name=self.default_app_name,
            library_subcopy=self.default_library_subcopy,
            anime_source="youranimes",
            default_search_year=self.default_search_year,
            default_search_season=current_default_season(),
            default_page_size=24,
            default_filter_collected=False,
            default_filter_release_tag=None,
            default_filter_group_tag=None,
            sync_strategy="incremental",
            admin_username=self.default_admin_username,
            password_salt=password_salt,
            password_hash=password_hash,
            auth_secret=secrets.token_urlsafe(32),
        )

    def _save(self, stored: StoredAppSettings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = stored.model_dump(mode="json")
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
