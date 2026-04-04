from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = "postgresql+psycopg://competition:competition@localhost:5432/competition"
    redis_url: str = "redis://localhost:6379/0"
    session_secret: str = "change-me"
    session_cookie_name: str = "competition_session"
    session_max_age_seconds: int = 28800
    web_origin: str = "http://localhost:3000"
    web_origins: str | None = None
    local_storage_root: str = "./data/storage"
    default_admin_email: str = "admin@example.com"
    default_admin_password: str = "admin1234"
    default_admin_name: str = "Phase Zero Admin"
    default_competition_slug: str = "phase-0-smoke-test"
    default_competition_title: str = "Phase 0 Smoke Test"
    default_competition_description: str = (
        "Baseline competition used to verify auth, queue, and worker wiring."
    )
    worker_id: str = "worker-local"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_allowed_origins(self) -> list[str]:
        raw = self.web_origins or self.web_origin
        return [
            origin.rstrip("/")
            for origin in (item.strip() for item in raw.split(","))
            if origin
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
