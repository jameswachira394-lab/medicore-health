"""
Shared base settings for all MediCore microservices.
Each service extends BaseServiceSettings with its own DATABASE_URL / SERVICE_NAME.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SERVICE_NAME: str = "medicore-service"
    ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # Auth / JWT (shared secret in dev; in prod each service validates via JWKS from auth-service)
    JWT_SECRET: str = "CHANGE_ME_IN_PRODUCTION_USE_SECRETS_MANAGER"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: str = "postgresql+psycopg://medicore:medicore@localhost:5432/medicore"
    REDIS_URL: str = "redis://localhost:6379/0"

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Observability
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://otel-collector:4317"
