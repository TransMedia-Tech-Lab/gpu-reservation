from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = BASE_DIR / "data"


class Settings(BaseSettings):
    """アプリ全体の設定値。環境変数や`.env`からも読み込む。"""

    api_prefix: str = "/api"
    app_name: str = "GPU Reservation Backend"
    timezone: str = "UTC"
    cors_origins: list[str] = ["*"]

    data_dir: Path = DEFAULT_DATA_DIR
    database_url: str = (
        f"sqlite:///{(DEFAULT_DATA_DIR / 'gpu_reservations.db').as_posix()}"
    )
    echo_sql: bool = False

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()

    # Render/Supabase provides DATABASE_URL, but SQLAlchemy needs postgresql://
    # Supabase/Render often gives postgres://
    if settings.database_url and settings.database_url.startswith("postgres://"):
        settings.database_url = settings.database_url.replace(
            "postgres://", "postgresql://", 1
        )

    return settings
