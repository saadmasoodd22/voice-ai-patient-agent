from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Voice AI Patient Registration"
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    public_base_url: str = "http://localhost:8000"

    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "voice_ai"
    database_url: str = ""

    groq_api_key: str = ""
    vapi_api_key: str = ""
    vapi_phone_number: str = ""
    vapi_assistant_id: str = ""
    vapi_server_secret: str = ""

    @property
    def sqlalchemy_url(self) -> str:
        import os
        from urllib.parse import quote_plus

        # PythonAnywhere free accounts have no MySQL. Never try localhost MySQL there
        # or the web worker hangs until the browser times out (error log stays empty).
        on_pythonanywhere = bool(
            os.getenv("PYTHONANYWHERE_DOMAIN")
            or os.getenv("PYTHONANYWHERE_SITE")
            or os.path.isdir("/home/saadmasoodd22")
        )
        pa_sqlite = "sqlite:////home/saadmasoodd22/voice-ai-patient-agent/voice_ai.db"
        if on_pythonanywhere:
            explicit = (os.getenv("DATABASE_URL") or self.database_url or "").strip()
            if explicit.startswith("sqlite"):
                return explicit
            return pa_sqlite

        if self.database_url:
            url = self.database_url.strip()
            if url.startswith("postgres://"):
                url = "postgresql+psycopg2://" + url[len("postgres://") :]
            elif url.startswith("postgresql://") and "+psycopg2" not in url:
                url = "postgresql+psycopg2://" + url[len("postgresql://") :]
            return url

        if (self.app_env or "").lower() == "pythonanywhere":
            return pa_sqlite

        password = quote_plus(self.mysql_password)
        return (
            f"mysql+pymysql://{self.mysql_user}:{password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            "?charset=utf8mb4&connect_timeout=5"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
