"""Application settings — single source of truth for all HP configuration.

All values are driven by environment variables (prefix HP_) or a .env file.
Constructor kwargs override both, which keeps test fixtures clean.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="HP_",
        case_sensitive=False,
        extra="ignore",
    )

    # Core
    app_name: str = "HP"
    debug: bool = False

    # Voice
    wake_phrase: str = "Hey HP"
    follow_up_timeout_s: int = Field(default=10, gt=0)
    audio_sample_rate: int = Field(default=16000, gt=0)
    audio_device_index: int | None = None

    # Logging
    log_level: str = "INFO"
    log_dir: str = "logs"

    # Persistence
    db_path: str = "data/hp.db"
