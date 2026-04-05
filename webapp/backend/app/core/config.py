from __future__ import annotations

import json
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENV: str = Field(default="dev")
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)

    MODEL_DIR: Path = Field(default=Path("models"))
    DATA_DIR: Path = Field(default=Path("data"))

    CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"]
    )
    EXOG_FUTURE_MODE: str = Field(default="known")  # known | last_known

    APP_NAME: str = Field(default="scale-ai-backend")
    VERSION: str = Field(default="0.1.0")

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        case_sensitive=False,
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _parse_cors_origins(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            raw = v.strip()
            if raw.startswith("[") and raw.endswith("]"):
                try:
                    parsed = json.loads(raw)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except json.JSONDecodeError:
                    # fall back to comma-split if JSON parsing fails
                    pass
            return [s.strip() for s in raw.split(",") if s.strip()]
        return v

    @field_validator("MODEL_DIR", "DATA_DIR", mode="before")
    @classmethod
    def _to_path(cls, v):
        if v is None:
            return v
        return Path(v)


def get_settings() -> Settings:
    return Settings()
