from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SUPPORTED_MANIFEST_VERSION = "1.0"
Environment = Literal["dev", "test", "prod"]


class ProductIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    manifest_version: str = Field(min_length=1)


class SecurityPosture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent_data_access: Literal["mediated", "direct"]


class ScenarioFeatures(BaseModel):
    model_config = ConfigDict(extra="forbid")

    builder: str = Field(min_length=1)
    schema_name: str = Field(min_length=1, alias="schema")
    version: str = Field(min_length=1)
    contract: str = Field(min_length=1)


class ScenarioModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    candidate_models: list[str] = Field(min_length=1)
    minimum_rows: int = Field(ge=1)


class ScenarioEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metrics: list[str] = Field(min_length=1)


class ScenarioPromotionPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric: str = Field(min_length=1)
    threshold: float = Field(ge=0)


class ScenarioServing(BaseModel):
    model_config = ConfigDict(extra="forbid")

    endpoint: str = Field(min_length=1)


class VectorIndex(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    source_table: str = Field(min_length=1)
    used_by: list[str] = Field(min_length=1)


class ScenarioRetrieval(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vector_indexes: list[VectorIndex] = Field(default_factory=list)


class ScenarioYaml(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    task: str = Field(min_length=1)
    source_datasets: list[str] = Field(min_length=1)
    features: ScenarioFeatures
    model: ScenarioModel
    evaluation: ScenarioEvaluation
    promotion_policy: ScenarioPromotionPolicy
    serving: ScenarioServing
    retrieval: ScenarioRetrieval = Field(default_factory=ScenarioRetrieval)


class ConfigYaml(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario: str = Field(min_length=1)
    source_dataset: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    expected_customer_count: int = Field(ge=1)
    catalogs: dict[Environment, str] = Field(min_length=1)
    schemas: list[str] = Field(min_length=1)
    playbooks_table: str = Field(min_length=1)


class RoutingEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    primary: str = Field(min_length=1)
    fallback: list[str] = Field(default_factory=list)


class ToolEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    mutates_data: bool
    authorization: str = Field(min_length=1)


class ToolsContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tools: list[ToolEntry] = Field(min_length=1)


class AgentYaml(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    tools: list[str] = Field(min_length=1)
    output_schema: str = Field(min_length=1)
    guardrails: dict[str, bool]


def discover_single_subdir(base: Path) -> Path:
    candidates = sorted(p for p in base.iterdir() if p.is_dir())
    if len(candidates) != 1:
        raise ValueError(
            f"expected exactly one subdirectory under {base}, found {len(candidates)}: "
            f"{[p.name for p in candidates]}"
        )
    return candidates[0]


def discover_single_file(base: Path, pattern: str) -> Path:
    candidates = sorted(base.glob(pattern))
    if len(candidates) != 1:
        raise ValueError(
            f"expected exactly one file matching {pattern!r} under {base}, found "
            f"{len(candidates)}: {[p.name for p in candidates]}"
        )
    return candidates[0]
