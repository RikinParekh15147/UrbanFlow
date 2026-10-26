from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="URBANFLOW_", env_file=".env", extra="ignore")
    env: str = "development"
    mongodb_uri: str = ""
    mongodb_database: str = "urbanflow"


settings = Settings()
