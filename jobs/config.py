"""Worker-only settings (scheduler). Everything else — DATABASE_URL, API keys, phone keys — is read by the
backend's settings (`app.core.config`) from this repo's `.env`."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    scheduler_enabled: bool = False
    timezone: str = "Asia/Kolkata"
    pipeline_cron: str = "0 6 * * *"  # daily pipeline (PRD §11.1)
    rapid_check_cron: str = "0 */3 * * *"  # sudden-impact check (PRD §11.9)
    officer_summary_cron: str = "15 7 * * *"  # officer daily summary (PRD §14.7)


@lru_cache
def get_worker_settings() -> WorkerSettings:
    return WorkerSettings()
