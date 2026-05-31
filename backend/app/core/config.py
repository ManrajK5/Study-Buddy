from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Study Buddy API"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    backend_cors_origins: str = "http://localhost:5173,http://localhost:3000"

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_storage_bucket: str = "course-documents"

    supabase_embedding_function: str = "embed"
    embedding_dimensions: int = 384
    embedding_batch_size: int = Field(default=1, ge=1, le=8)

    google_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    max_upload_mb: int = Field(default=25, ge=1, le=100)
    rag_chunk_size: int = Field(default=1200, ge=200)
    rag_chunk_overlap: int = Field(default=180, ge=0)

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def supabase_functions_url(self) -> str:
        return f"{self.supabase_url.rstrip('/')}/functions/v1"

    @property
    def is_supabase_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_role_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
