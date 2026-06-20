"""
Application configuration loaded from environment variables and .env file.

All required settings are validated at startup via pydantic-settings.
A missing or empty GEMINI_API_KEY raises a ValidationError immediately.
"""

import json
from typing import List, Tuple, Type, Any
from pydantic import field_validator, ValidationError
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    PydanticBaseSettingsSource,
)

class Settings(BaseSettings):
    """
    Pydantic settings model. Reads from .env and environment variables.

    Attributes:
        gemini_api_key       : Google AI Studio key for the default provider.
        groq_api_key         : Groq API key (optional).
        database_url         : Path to the SQLite file or a PostgreSQL DSN.
        allowed_origins      : CORS allow-list; comma-separated in env.
        rate_limit_chat_rpm  : Max chat messages per user per minute.
        rate_limit_analyze_rph: Max agent pipeline runs per user per hour.
        rate_limit_nl_rpm    : Max NL activity parses per user per minute.
        app_env              : "development" or "production".
    """
    gemini_api_key: str
    groq_api_key: str = ""
    database_url: str = "./carbonsense.db"
    allowed_origins: List[str]
    rate_limit_chat_rpm: int = 10
    rate_limit_analyze_rph: int = 300
    rate_limit_nl_rpm: int = 20
    app_env: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("gemini_api_key")
    @classmethod
    def gemini_key_must_not_be_empty(cls, v: str) -> str:
        """Ensure a Gemini API key is provided before the server starts."""
        if not v or not v.strip():
            raise ValueError(
                "GEMINI_API_KEY is required. "
                "Get a free key at https://ai.google.dev"
            )
        return v.strip()

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        def custom_decode(field_name: str, field: Any, value: str) -> Any:
            if field_name == "allowed_origins":
                return [x.strip() for x in value.split(",") if x.strip()]
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value

        if hasattr(env_settings, "decode_complex_value"):
            env_settings.decode_complex_value = custom_decode
        if hasattr(dotenv_settings, "decode_complex_value"):
            dotenv_settings.decode_complex_value = custom_decode

        return init_settings, env_settings, dotenv_settings, file_secret_settings

try:
    settings = Settings()
except ValidationError as e:
    raise e
