from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    app_name: str = "Secret Management Service"
    app_env: str = "dev"
    app_debug: bool = True

    api_v1_prefix: str = "/api/v1"

    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "secret_manager"
    postgres_user: str = "secret_manager"
    postgres_password: str = "change_me"

    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        return URL.create(
                drivername="postgresql+psycopg", # какую СУБД мы используем (PostgreSQL) и через какой драйвер/библиотеку к ней подключаться
                username=self.postgres_user,
                password=self.postgres_password,
                host=self.postgres_host,
                port=self.postgres_port,
                database=self.postgres_db,
        ).render_as_string(hide_password=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
