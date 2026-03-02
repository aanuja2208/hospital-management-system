from pydantic_settings import BaseSettings
from functools import lru_cache
class Settings(BaseSettings):
    APP_NAME: str = "Hospital Management Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/hospital_db"
    DATABASE_ECHO: bool = False
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_SECRET_KEY: str = "super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@hospital.com"
    model_config = {"env_file": ".env", "extra": "ignore"}
@lru_cache()
def get_settings() -> Settings:
    return Settings()