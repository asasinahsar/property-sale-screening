from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Property Sale Screening API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    DATABASE_URL: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/property_db"
    )

    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    # JWT + HttpOnly Cookie
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    COOKIE_NAME: str = "access_token"
    COOKIE_SECURE: bool = False  # True in production (HTTPS only)
    COOKIE_SAMESITE: str = "lax"
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_MINUTES: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
