import json
from typing import List, Tuple, Type, Any
from pydantic import field_validator, ValidationError
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    PydanticBaseSettingsSource,
)

class Settings(BaseSettings):
    gemini_api_key: str = ""
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
