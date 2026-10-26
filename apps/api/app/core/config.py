import os
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="URBANFLOW_",
        env_file=os.environ.get("URBANFLOW_ENV_FILE", ".env"),
        extra="ignore",
    )
    env: str = "development"
    mongodb_uri: str = "mongodb://127.0.0.1:27017"
    mongodb_database: str = "urbanflow"
    data_source: Literal["mongodb", "snapshot"] = "mongodb"
    snapshot_dir: str = "data/serving"
    web_dir: str = "apps/web/dist"


settings = Settings()
