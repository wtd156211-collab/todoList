from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    redis_url: str
    jwt_secret: str
    wechat_app_id: str
    wechat_app_secret: str
    oss_endpoint: str
    oss_bucket: str
    oss_access_key_id: str
    oss_access_key_secret: str

    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
