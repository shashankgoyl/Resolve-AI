from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Resolve AI"
    ENVIRONMENT: str = "development"
    DEMO_MODE: bool = True
    CORS_ORIGINS: str = "http://localhost:5173"

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # Swytchcode
    SWYTCHCODE_API_KEY: str = ""
    SWYTCHCODE_BIN: str = "swytchcode"
    SWYTCHCODE_MODE: str = "sandbox"
    SWYTCHCODE_TIMEOUT_SECONDS: int = 20

    # Resend
    RESEND_FROM_EMAIL: str = "support@yourcompany.com"
    SUPPORT_INBOX_EMAIL: str = "support@yourcompany.com"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def supabase_configured(self) -> bool:
        return bool(self.SUPABASE_URL and self.SUPABASE_SERVICE_ROLE_KEY)

    @property
    def gemini_configured(self) -> bool:
        return bool(self.GEMINI_API_KEY)

    @property
    def swytchcode_configured(self) -> bool:
        return bool(self.SWYTCHCODE_API_KEY)


@lru_cache
def get_settings() -> Settings:
    return Settings()
