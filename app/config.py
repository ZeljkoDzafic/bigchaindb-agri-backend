"""Configuration management for the BigchainDB Agri Backend."""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "BigchainDB Agri Backend"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "change-me-in-production"

    # BigchainDB
    bigchaindb_root_url: str = "http://localhost:9984"
    bigchaindb_ws_url: str = "ws://localhost:9985"

    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "bigchain"

    # RabbitMQ
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672"
    rabbitmq_queue: str = "sensor_data"
    rabbitmq_exchange: str = "agri_exchange"

    # Authentication
    jwt_secret_key: str = "your-jwt-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Rate Limiting
    rate_limit_per_minute: int = 100

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
