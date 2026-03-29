from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    app_api_key: str | None = None
    app_port: int = 8080
    database_host: str | None = None
    database_port: int | None = None
    database_user: str | None = None
    database_pass: str | None = None
    database_name: str | None = None

    model_config = SettingsConfigDict(env_file=".env")

@lru_cache
def get_setting():
    return Settings()
