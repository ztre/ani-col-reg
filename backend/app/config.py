from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


CURRENT_FILE = Path(__file__).resolve()
ENV_FILE_CANDIDATES = [CURRENT_FILE.parents[2] / ".env", CURRENT_FILE.parents[1] / ".env"]
ENV_FILE = next((path for path in ENV_FILE_CANDIDATES if path.exists()), ENV_FILE_CANDIDATES[-1])


class Settings(BaseSettings):
    app_name: str = "番剧收藏登记系统"
    database_url: str = "sqlite:///./data/ani_col_reg.sqlite3"
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            origin
            for host in ("localhost", "127.0.0.1")
            for origin in [f"http://{host}:{port}" for port in (5173, 5174, 5175)]
        ]
    )
    youranimes_base_url: str = "https://youranimes.tw"
    mikan_base_url: str = "https://mikanani.me"
    cover_cache_public_path: str = "/api/covers"
    auth_token_ttl_hours: int = 168
    auth_default_username: str = "admin"
    auth_default_password: str = "ani-col-reg"

    model_config = SettingsConfigDict(env_file=str(ENV_FILE), env_prefix="ANI_COL_")

    @property
    def sqlite_path(self) -> Path | None:
        if not self.database_url.startswith("sqlite:///"):
            return None
        return Path(self.database_url.removeprefix("sqlite:///"))

    @property
    def data_dir(self) -> Path:
        if self.sqlite_path is not None:
            return self.sqlite_path.parent
        return Path("./data")

    @property
    def cover_cache_dir(self) -> Path:
        return self.data_dir / "covers"

    @property
    def app_settings_path(self) -> Path:
        return self.data_dir / "app_settings.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()
