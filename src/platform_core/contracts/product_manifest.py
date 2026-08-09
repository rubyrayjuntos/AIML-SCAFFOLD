from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

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


class ProductManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product: ProductIdentity
    environments: list[Environment] = Field(min_length=1)
    security: dict[Environment, SecurityPosture]
    scenario: ScenarioYaml
    config: ConfigYaml
    routing: dict[Environment, RoutingEntry]
    tools: ToolsContract
    agent: AgentYaml

    @model_validator(mode="after")
    def _check_manifest_version(self) -> ProductManifest:
        if self.product.manifest_version != SUPPORTED_MANIFEST_VERSION:
            raise ValueError(
                f"manifest_version {self.product.manifest_version!r} is not supported by "
                f"this platform_core version (supports {SUPPORTED_MANIFEST_VERSION!r}); "
                "upgrade platform_core or update product.yaml"
            )
        return self

    @model_validator(mode="after")
    def _check_environment_completeness(self) -> ProductManifest:
        declared = set(self.environments)
        for section_name, section in (("security", self.security), ("routing", self.routing)):
            keys = set(section)
            if keys != declared:
                raise ValueError(
                    f"{section_name} environments {sorted(keys)} do not match declared "
                    f"environments {sorted(declared)}"
                )
        return self

    @model_validator(mode="after")
    def _check_prod_agent_data_access(self) -> ProductManifest:
        prod = self.security.get("prod")
        if prod is not None and prod.agent_data_access == "direct":
            raise ValueError(
                "security.prod.agent_data_access cannot be 'direct'; production agent data "
                "access must stay 'mediated' unless platform_core's shared validator is "
                "changed via an ADR and version bump"
            )
        return self

    @model_validator(mode="after")
    def _check_retrieval_tool_reciprocity(self) -> ProductManifest:
        # Convention, not a declared field: a tool is "retrieval-capable" if its name
        # starts with retrieve_ (matches get_customer_score/get_customer_diff not being
        # retrieval tools, and retrieve_customer_evidence/retrieve_playbooks being ones).
        tool_names = {tool.name for tool in self.tools.tools}
        referenced: set[str] = set()
        for index in self.scenario.retrieval.vector_indexes:
            for tool_name in index.used_by:
                referenced.add(tool_name)
                if tool_name not in tool_names:
                    raise ValueError(
                        f"retrieval index {index.name!r} references unknown tool {tool_name!r}"
                    )
        retrieval_tool_names = {name for name in tool_names if name.startswith("retrieve_")}
        orphaned = retrieval_tool_names - referenced
        if orphaned:
            raise ValueError(
                f"retrieval tool(s) {sorted(orphaned)} are not referenced by any vector index"
            )
        return self

    @classmethod
    def load(cls, scenario_dir: Path, foundry_dir: Path = Path("foundry")) -> ProductManifest:
        product_data = _load_yaml(scenario_dir / "product.yaml")
        agent_path = discover_single_file(foundry_dir / "agents", "*.yaml")

        return cls(
            product=product_data["product"],
            environments=product_data["environments"],
            security=product_data["security"],
            scenario=_load_yaml(scenario_dir / "scenario.yaml"),
            config=_load_yaml(scenario_dir / "config.yaml"),
            routing=_load_yaml(scenario_dir / "routing.yaml"),
            tools=json.loads((foundry_dir / "tools" / "tools.contract.json").read_text()),
            agent=_load_yaml(agent_path),
        )


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def discover_scenario_dir(base: Path = Path("src/scenarios")) -> Path:
    return discover_single_subdir(base)
