from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

from platform_core.contracts.product_manifest import discover_scenario_dir


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "enterprise-ml-workflow"
    app_env: Literal["dev", "test", "prod"] = "dev"
    model_serving_endpoint: str = ""
    databricks_catalog: str = ""
    databricks_sql_warehouse_id: str | None = None
    feature_schema_version: str = "unconfigured"
    feature_contract: str = "unconfigured"
    foundry_endpoint: str | None = None
    foundry_deployment: str | None = None

    @classmethod
    def from_scenario(cls, scenario_dir: Path | None = None, **overrides) -> Settings:
        root = scenario_dir or discover_scenario_dir()
        scenario = yaml.safe_load((root / "scenario.yaml").read_text(encoding="utf-8"))
        config = yaml.safe_load((root / "config.yaml").read_text(encoding="utf-8"))
        environment = overrides.get("app_env", "dev")
        values = {
            "model_serving_endpoint": scenario["serving"]["endpoint"],
            "databricks_catalog": config["catalogs"][environment],
            "feature_schema_version": scenario["features"]["version"],
            "feature_contract": scenario["features"]["contract"],
        }
        values.update(overrides)
        return cls(**values)


settings = Settings.from_scenario()
