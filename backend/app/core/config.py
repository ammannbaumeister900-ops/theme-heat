from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "A-Share Theme Heat API"
    app_env: str = "development"
    api_prefix: str = "/api"
    database_url: str = "postgresql+psycopg2://postgres:postgres@postgres:5432/theme_heat"
    cors_origins: str = "http://localhost,http://127.0.0.1"
    scheduler_enabled: bool = True
    scheduler_timezone: str = "Asia/Shanghai"
    scheduler_cron_day_of_week: str = "*"
    scheduler_cron_hour: int = 20
    scheduler_cron_minute: int = 30
    scheduler_skip_non_trading_days: bool = True
    full_sync_enabled: bool = True
    full_sync_cron_day_of_week: str = "fri"
    full_sync_cron_hour: int = 21
    full_sync_cron_minute: int = 30
    default_theme_types: str = "industry,concept"
    ranking_limit: int = 20
    strong_score_threshold: float = 65.0
    compute_batch_size: int = 10
    compute_batch_pause_seconds: float = 0.3

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def theme_type_list(self) -> list[str]:
        return [item.strip() for item in self.default_theme_types.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
