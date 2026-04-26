"""Application settings loaded from environment / .env file."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="HP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General
    app_name: str = "HP"
    log_level: str = "INFO"
    log_dir: str = "logs"
    debug: bool = False
    db_path: str = "data/hp.db"

    # Wake word
    wake_phrase: str = "Hey HP"
    wake_word_model: str = "hey_jarvis"
    wake_word_threshold: float = Field(default=0.5, ge=0.0, le=1.0)

    # Audio
    audio_sample_rate: int = Field(default=16000, gt=0)
    audio_device_index: int | None = None

    # VAD
    vad_energy_threshold: float = Field(default=300.0, ge=0.0)
    silence_timeout_s: float = Field(default=1.5, ge=0.1)

    # STT
    whisper_model: str = "tiny.en"
    stt_device: str = "cpu"

    # TTS
    tts_rate: int = Field(default=175, ge=50, le=400)
    tts_volume: float = Field(default=1.0, ge=0.0, le=1.0)

    # Follow-up
    follow_up_timeout_s: float = Field(default=10.0, gt=0)

    # LLM
    llm_provider: str = "stub"
    llm_max_history: int = Field(default=10, ge=1)
