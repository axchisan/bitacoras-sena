from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from datetime import date


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://bitacoras:bitacoras_pass@localhost:5432/bitacoras_db"

    # Azure DevOps
    azure_devops_org: str = "linktic"
    azure_devops_project: str = "397 - COLFONDOS CORE"
    azure_devops_pat: str = ""

    # Anthropic
    anthropic_api_key: str = ""

    # IA — Proveedor activo y claves de API alternativas
    # Opciones: "anthropic" | "gemini" | "groq"
    ai_provider: str = "anthropic"
    gemini_api_key: str = ""   # Google Gemini — gratis: 15 RPM, 1M tokens/día
    groq_api_key: str = ""     # Groq Llama 3.3 70B — gratis: 500K tokens/día

    # OneDrive / Microsoft Graph
    onedrive_client_id: str = ""
    onedrive_client_secret: str = ""
    onedrive_tenant_id: str = ""
    onedrive_folder_path: str = "/Bitacoras SENA"
    onedrive_refresh_token: str = ""  # Obtenido con scripts/get_onedrive_token.py (una sola vez)

    # App
    secret_key: str = "change_this_secret"
    environment: str = "development"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Bitácoras configuration
    bitacoras_start_date: date = date(2026, 1, 26)
    bitacoras_total: int = 12
    bitacoras_period_days: int = 15

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
