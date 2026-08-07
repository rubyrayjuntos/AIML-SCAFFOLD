from __future__ import annotations

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "enterprise-ml-workflow"
    app_env: Literal["dev", "test", "prod"] = "dev"
    model_serving_endpoint: str = "churn-classifier"
    foundry_endpoint: str | None = None
    foundry_deployment: str | None = None


settings = Settings()
