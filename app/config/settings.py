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

    # Voice — base
    wake_phrase: str = "Hey HP"
    follow_up_timeout_s: int = Field(default=10, gt=0)
    audio_sample_rate: int = Field(default=16000, gt=0)
    audio_device_index: int | None = None

    # Wake-word
    wakeword_model: str = "hey_jarvis"
    wakeword_sensitivity: float = Field(default=0.5, ge=0.0, le=1.0)

    # STT
    stt_model_size: str = "small"
    stt_device: str = "cpu"

    # TTS
    tts_rate: int = Field(default=175, gt=0)
    tts_volume: float = Field(default=1.0, ge=0.0, le=1.0)

    # VAD
    vad_silence_threshold: float = Field(default=500.0, gt=0.0)
    vad_silence_duration_s: float = Field(default=0.8, gt=0.0)

    # Logging
    log_level: str = "INFO"
    log_dir: str = "logs"

    # Persistence
    db_path: str = "data/hp.db"
