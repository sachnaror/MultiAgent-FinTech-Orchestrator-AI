from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Multi-Agent FinTech Orchestrator AI"
    environment: str = "local"

    azure_document_intelligence_endpoint: str = ""
    azure_document_intelligence_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_deployment: str = "gpt-4o-mini"
    azure_openai_api_version: str = "2024-10-21"

    auto_approve_max_amount: float = Field(default=10000, ge=0)
    min_extraction_confidence: float = Field(default=0.82, ge=0, le=1)
    strict_fail_fast: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()

