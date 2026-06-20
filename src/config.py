from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "MusicAgent Studio")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY") or None
    max_iterations: int = int(os.getenv("MAX_ITERATIONS", "2"))
    music_generator_backend: str = os.getenv("MUSIC_GENERATOR_BACKEND", "mock")
    musicgen_model: str = os.getenv("MUSICGEN_MODEL", "facebook/musicgen-small")
    musicgen_duration: int = int(os.getenv("MUSICGEN_DURATION", "8"))
    musicgen_fallback_to_mock: bool = (
        os.getenv("MUSICGEN_FALLBACK_TO_MOCK", "true").lower()
        in {"1", "true", "yes"}
    )


def get_settings() -> Settings:
    return Settings()
