"""Application settings loaded from environment / .env file."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_data_dir() -> Path:
    if getattr(sys, "frozen", False):
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return base / "HP"
    return Path(".")


_DATA_DIR = _default_data_dir()


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
    log_dir: str = Field(default_factory=lambda: str(_DATA_DIR / "logs"))
    debug: bool = False
    db_path: str = Field(default_factory=lambda: str(_DATA_DIR / "data" / "hp.db"))

    # Wake word
    wake_phrase: str = "Hey HP"
    wake_word_model: str = "hey_jarvis"
    wake_word_threshold: float = Field(default=0.3, ge=0.0, le=1.0)

    # Audio
    audio_sample_rate: int = Field(default=16000, gt=0)
    audio_device_index: int | None = None

    # VAD
    vad_energy_threshold: float = Field(default=300.0, ge=0.0)
    silence_timeout_s: float = Field(default=2.5, ge=0.1)

    # STT
    whisper_model: str = "base.en"
    stt_device: str = "cpu"

    # TTS
    tts_rate: int = Field(default=175, ge=50, le=400)
    tts_volume: float = Field(default=1.0, ge=0.0, le=1.0)

    # Follow-up
    follow_up_timeout_s: float = Field(default=30.0, gt=0)

    # LLM
    llm_provider: str = "groq"
    llm_max_history: int = Field(default=10, ge=1)
    llm_model: str = "claude-haiku-4-5-20251001"
    anthropic_api_key: str = ""
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    # Vision
    webcam_index: int = Field(default=0, ge=0)
    vision_max_frames: int = Field(default=30, ge=1)
    vision_confidence: float = Field(default=0.4, ge=0.0, le=1.0)
