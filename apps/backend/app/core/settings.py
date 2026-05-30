from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://medical_user:medical_password@db:5432/medical_data"
    api_cors_origins: str = "http://localhost:3000"
    raw_file_storage: str = "/app/uploads/raw"
    auth_secret: str = "medical-data-dev-secret"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]

    @property
    def raw_file_storage_path(self) -> Path:
        return Path(self.raw_file_storage)


settings = Settings()
