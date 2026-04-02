from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "NFC Exercise Tracker"
    database_url: str = "postgresql+psycopg://exercise:exercise@postgres:5432/exercise"
    auto_seed: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
