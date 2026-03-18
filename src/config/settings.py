from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    app_api_key: str

    database_host: str
    database_port: int
    database_user: str
    database_pass: str
    database_name: str

    model_config = SettingsConfigDict(env_file=".env")

@lru_cache
def get_setting():
    return Settings()
