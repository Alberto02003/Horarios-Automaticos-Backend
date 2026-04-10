from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg://appuser:changeme@localhost:5432/appdb"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    LOG_LEVEL: str = "info"
    FORCE_HTTPS: bool = False
    PORT: int = 8080

    model_config = {"env_file": ".env", "extra": "ignore"}

    def get_database_url(self) -> str:
        """Normalize DATABASE_URL for SQLAlchemy async with psycopg."""
        url = self.DATABASE_URL
        # Railway provides postgresql:// — convert to psycopg async driver
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg://", 1)
        return url


settings = Settings()
