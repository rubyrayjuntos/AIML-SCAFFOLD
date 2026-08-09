# Product Manifest Schema Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `ProductManifest` schema in `platform_core`, apply it to churn's own config files (fixing two real, non-duplicate fields a draft of the spec nearly dropped), and retire the pre-existing hardcoded churn defaults in `Settings`.

**Architecture:** One new module, `platform_core/contracts/product_manifest.py`, holds section-file Pydantic models, the composite `ProductManifest` model with four cross-field validators, and two generic (non-domain) directory-discovery helpers. Churn's `scenario.yaml`/`config.yaml` get corrected/narrowed and two new files (`product.yaml`, `routing.yaml`) are added. `Settings` becomes a thin wrapper that loads a `ProductManifest` once (cached) and exposes the same attribute names it already exposes today, so no other file has to change.

**Tech Stack:** Python 3.12, pydantic v2, pydantic-settings, PyYAML, pytest.

## Global Constraints

- `platform_core` code and its own tests must never reference "churn" or any other scenario name (see `docs/template/architecture.md`: "No scenario data, model, customer, or endpoint names are hardcoded in `platform_core`"). All fixtures in `tests/contracts/test_product_manifest.py` use a synthetic `widgets` example.
- Churn's own validation lives in `tests/data_quality/test_churn_config.py`, as an ordinary consumer of `ProductManifest` — same as any future product's manifest test would look.
- `manifest_version` is fixed at `"1.0"` for now; no migration tooling.
- `prod` can never validate with `agent_data_access: direct` — this is enforced in code, not configurable.
- Pydantic models use `model_config = ConfigDict(extra="forbid")`, matching the existing convention in `src/platform_core/contracts/models.py`.
- Ruff: line-length 100, target py312. Run `ruff check .` and `pytest` before every commit (per `AGENTS.md`).
- Ran from repo root; all relative paths in code (`Path("src/scenarios")`, `Path("foundry")`) assume CWD is the repo root, matching the existing pattern in `tests/data_quality/test_churn_config.py`.
- `ScenarioFeatures`' Python attribute is `schema_name`, aliased to the YAML key `schema` (`Field(min_length=1, alias="schema")`) — the bare name `schema` collides with a deprecated `BaseModel` attribute and warns on every use. Construction and YAML loading both use the alias (`schema=...` as a kwarg, or the `schema` dict key), so no other code changes; only the field declaration differs from a plain `schema: str` (found and corrected during Task 1's review, 2026-08-08).

---

## File structure

```
src/platform_core/contracts/product_manifest.py   # new — all models, validators, loader, discovery helpers
src/scenarios/churn/product.yaml                  # new
src/scenarios/churn/routing.yaml                  # new
src/scenarios/churn/scenario.yaml                 # modified — add `model` block, enrich `retrieval`
src/scenarios/churn/config.yaml                   # modified — narrowed, dedup removed
src/platform_core/settings/config.py              # modified — derive fields from ProductManifest
tests/contracts/test_product_manifest.py          # new — synthetic-fixture unit tests
tests/data_quality/test_churn_config.py           # modified — fix broken assertions, add golden-fixture test
tests/unit/test_settings.py                       # new
```

---

### Task 1: Section-file models and discovery helpers

**Files:**
- Create: `src/platform_core/contracts/product_manifest.py`
- Test: `tests/contracts/test_product_manifest.py`

**Interfaces:**
- Produces: `SUPPORTED_MANIFEST_VERSION: str`, `Environment` (type alias for `Literal["dev", "test", "prod"]`), `ProductIdentity`, `SecurityPosture`, `ScenarioFeatures`, `ScenarioModel`, `ScenarioEvaluation`, `ScenarioPromotionPolicy`, `ScenarioServing`, `VectorIndex`, `ScenarioRetrieval`, `ScenarioYaml`, `ConfigYaml`, `RoutingEntry`, `ToolEntry`, `ToolsContract`, `AgentYaml` (all `pydantic.BaseModel`), plus `discover_single_subdir(base: Path) -> Path` and `discover_single_file(base: Path, pattern: str) -> Path`.

- [ ] **Step 1: Write the failing test**

Create `tests/contracts/test_product_manifest.py`:

```python
from pathlib import Path

import pytest
from pydantic import ValidationError

from platform_core.contracts.product_manifest import (
    AgentYaml,
    ConfigYaml,
    ProductIdentity,
    RoutingEntry,
    ScenarioEvaluation,
    ScenarioFeatures,
    ScenarioModel,
    ScenarioPromotionPolicy,
    ScenarioRetrieval,
    ScenarioServing,
    ScenarioYaml,
    SecurityPosture,
    ToolEntry,
    ToolsContract,
    VectorIndex,
    discover_single_file,
    discover_single_subdir,
)


def test_product_identity_requires_all_fields() -> None:
    identity = ProductIdentity(name="widgets", display_name="Widgets", manifest_version="1.0")
    assert identity.manifest_version == "1.0"
    with pytest.raises(ValidationError):
        ProductIdentity(name="widgets", display_name="Widgets")


def test_security_posture_rejects_unknown_access_mode() -> None:
    with pytest.raises(ValidationError):
        SecurityPosture(agent_data_access="raw")


def test_vector_index_requires_at_least_one_consumer() -> None:
    with pytest.raises(ValidationError):
        VectorIndex(name="notes_vs", source_table="gold.notes", used_by=[])


def test_scenario_yaml_parses_a_complete_synthetic_scenario() -> None:
    scenario = ScenarioYaml(
        name="widgets",
        task="classification",
        source_datasets=["orders"],
        features=ScenarioFeatures(
            builder="widgets_feature_builder",
            schema="widgets_feature_schema_v1",
            version="widgets.features.v1",
            contract="widgets_feature_contract_v1",
        ),
        model=ScenarioModel(
            name="widgets_classifier",
            candidate_models=["logistic_regression"],
            minimum_rows=100,
        ),
        evaluation=ScenarioEvaluation(metrics=["auc"]),
        promotion_policy=ScenarioPromotionPolicy(metric="auc", threshold=0.01),
        serving=ScenarioServing(endpoint="widgets-model-endpoint"),
        retrieval=ScenarioRetrieval(
            vector_indexes=[
                VectorIndex(name="notes_vs", source_table="gold.notes", used_by=["retrieve_notes"])
            ]
        ),
    )
    assert scenario.model.minimum_rows == 100


def test_scenario_retrieval_defaults_to_no_indexes() -> None:
    assert ScenarioRetrieval().vector_indexes == []


def test_config_yaml_requires_catalog_keys_to_be_known_environments() -> None:
    valid = dict(
        scenario="widgets",
        source_dataset="widgets_v1",
        source_url="https://example.com/widgets.csv",
        expected_customer_count=100,
        schemas=["bronze", "silver", "gold"],
        playbooks_table="gold.recommended_actions",
    )
    config = ConfigYaml(catalogs={"dev": "widgets_dev", "prod": "widgets_prod"}, **valid)
    assert config.catalogs["prod"] == "widgets_prod"
    with pytest.raises(ValidationError):
        ConfigYaml(catalogs={"staging": "widgets_staging"}, **valid)


def test_routing_entry_defaults_fallback_to_empty_list() -> None:
    routing = RoutingEntry(primary="gpt-4o-mini")
    assert routing.fallback == []


def test_tools_contract_requires_at_least_one_tool() -> None:
    with pytest.raises(ValidationError):
        ToolsContract(tools=[])


def test_agent_yaml_parses_guardrails() -> None:
    agent = AgentYaml(
        name="widgets-grounded-agent",
        description="Explain a widgets score",
        tools=["get_widget_score"],
        output_schema="foundry/agents/assistant_response.schema.json",
        guardrails={"require_citations": True},
    )
    assert agent.guardrails["require_citations"] is True


def test_discover_single_subdir_requires_exactly_one(tmp_path: Path) -> None:
    (tmp_path / "only").mkdir()
    assert discover_single_subdir(tmp_path).name == "only"

    (tmp_path / "second").mkdir()
    with pytest.raises(ValueError, match="expected exactly one subdirectory"):
        discover_single_subdir(tmp_path)


def test_discover_single_file_requires_exactly_one(tmp_path: Path) -> None:
    (tmp_path / "agent.yaml").write_text("name: x")
    assert discover_single_file(tmp_path, "*.yaml").name == "agent.yaml"

    (tmp_path / "other.yaml").write_text("name: y")
    with pytest.raises(ValueError, match="expected exactly one file"):
        discover_single_file(tmp_path, "*.yaml")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/contracts/test_product_manifest.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'platform_core.contracts.product_manifest'`

- [ ] **Step 3: Write the implementation**

Create `src/platform_core/contracts/product_manifest.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/contracts/test_product_manifest.py -v`
Expected: PASS (12 tests)

- [ ] **Step 5: Lint and commit**

```bash
ruff check src/platform_core/contracts/product_manifest.py tests/contracts/test_product_manifest.py
git add src/platform_core/contracts/product_manifest.py tests/contracts/test_product_manifest.py
git commit -m "feat: add product manifest section-file models and discovery helpers"
```

---

### Task 2: `ProductManifest` composite model, loader, and cross-field validators

**Files:**
- Modify: `src/platform_core/contracts/product_manifest.py` (append)
- Modify: `tests/contracts/test_product_manifest.py` (append)

**Interfaces:**
- Consumes: every model from Task 1 (`ProductIdentity`, `SecurityPosture`, `ScenarioYaml`, `ConfigYaml`, `RoutingEntry`, `ToolsContract`, `AgentYaml`, `Environment`, `SUPPORTED_MANIFEST_VERSION`, `discover_single_subdir`, `discover_single_file`).
- Produces: `ProductManifest` (BaseModel with fields `product: ProductIdentity`, `environments: list[Environment]`, `security: dict[Environment, SecurityPosture]`, `scenario: ScenarioYaml`, `config: ConfigYaml`, `routing: dict[Environment, RoutingEntry]`, `tools: ToolsContract`, `agent: AgentYaml`) with classmethod `ProductManifest.load(scenario_dir: Path, foundry_dir: Path = Path("foundry")) -> ProductManifest`, and `discover_scenario_dir(base: Path = Path("src/scenarios")) -> Path`.

- [ ] **Step 1: Write the failing test**

Append to `tests/contracts/test_product_manifest.py`:

```python
import json

import yaml

from platform_core.contracts.product_manifest import ProductManifest, discover_scenario_dir


def _write_synthetic_manifest(tmp_path: Path) -> tuple[Path, Path]:
    scenario_dir = tmp_path / "src" / "scenarios" / "widgets"
    scenario_dir.mkdir(parents=True)
    foundry_dir = tmp_path / "foundry"
    (foundry_dir / "agents").mkdir(parents=True)
    (foundry_dir / "tools").mkdir(parents=True)

    (scenario_dir / "product.yaml").write_text(
        yaml.dump(
            {
                "product": {
                    "name": "widgets",
                    "display_name": "Widgets",
                    "manifest_version": "1.0",
                },
                "environments": ["dev", "prod"],
                "security": {
                    "dev": {"agent_data_access": "mediated"},
                    "prod": {"agent_data_access": "mediated"},
                },
            }
        )
    )
    (scenario_dir / "scenario.yaml").write_text(
        yaml.dump(
            {
                "name": "widgets",
                "task": "classification",
                "source_datasets": ["orders"],
                "features": {
                    "builder": "widgets_feature_builder",
                    "schema": "widgets_feature_schema_v1",
                    "version": "widgets.features.v1",
                    "contract": "widgets_feature_contract_v1",
                },
                "model": {
                    "name": "widgets_classifier",
                    "candidate_models": ["logistic_regression"],
                    "minimum_rows": 100,
                },
                "evaluation": {"metrics": ["auc"]},
                "promotion_policy": {"metric": "auc", "threshold": 0.01},
                "serving": {"endpoint": "widgets-model-endpoint"},
                "retrieval": {
                    "vector_indexes": [
                        {
                            "name": "notes_vs",
                            "source_table": "gold.notes",
                            "used_by": ["retrieve_notes"],
                        }
                    ]
                },
            }
        )
    )
    (scenario_dir / "config.yaml").write_text(
        yaml.dump(
            {
                "scenario": "widgets",
                "source_dataset": "widgets_v1",
                "source_url": "https://example.com/widgets.csv",
                "expected_customer_count": 100,
                "catalogs": {"dev": "widgets_dev", "prod": "widgets_prod"},
                "schemas": ["bronze", "silver", "gold"],
                "playbooks_table": "gold.recommended_actions",
            }
        )
    )
    (scenario_dir / "routing.yaml").write_text(
        yaml.dump(
            {
                "dev": {"primary": "gpt-4o-mini", "fallback": []},
                "prod": {"primary": "gpt-4o", "fallback": ["gpt-4o-mini"]},
            }
        )
    )
    (foundry_dir / "agents" / "widgets-grounded-agent.yaml").write_text(
        yaml.dump(
            {
                "name": "widgets-grounded-agent",
                "description": "Explain a widgets score",
                "tools": ["retrieve_notes"],
                "output_schema": "foundry/agents/assistant_response.schema.json",
                "guardrails": {"require_citations": True},
            }
        )
    )
    (foundry_dir / "tools" / "tools.contract.json").write_text(
        json.dumps(
            {
                "tools": [
                    {
                        "name": "retrieve_notes",
                        "mutates_data": False,
                        "authorization": "read-approved-gold-context",
                    }
                ]
            }
        )
    )
    return scenario_dir, foundry_dir


def test_product_manifest_loads_a_valid_synthetic_product(tmp_path: Path) -> None:
    scenario_dir, foundry_dir = _write_synthetic_manifest(tmp_path)

    manifest = ProductManifest.load(scenario_dir, foundry_dir=foundry_dir)

    assert manifest.product.name == "widgets"
    assert manifest.routing["prod"].primary == "gpt-4o"
    assert manifest.scenario.model.minimum_rows == 100


def test_product_manifest_rejects_unsupported_version(tmp_path: Path) -> None:
    scenario_dir, foundry_dir = _write_synthetic_manifest(tmp_path)
    product_yaml = scenario_dir / "product.yaml"
    data = yaml.safe_load(product_yaml.read_text())
    data["product"]["manifest_version"] = "2.0"
    product_yaml.write_text(yaml.dump(data))

    with pytest.raises(ValidationError, match="manifest_version"):
        ProductManifest.load(scenario_dir, foundry_dir=foundry_dir)


def test_product_manifest_requires_security_for_every_declared_environment(tmp_path: Path) -> None:
    scenario_dir, foundry_dir = _write_synthetic_manifest(tmp_path)
    product_yaml = scenario_dir / "product.yaml"
    data = yaml.safe_load(product_yaml.read_text())
    del data["security"]["prod"]
    product_yaml.write_text(yaml.dump(data))

    with pytest.raises(ValidationError, match="security"):
        ProductManifest.load(scenario_dir, foundry_dir=foundry_dir)


def test_product_manifest_rejects_direct_agent_data_access_in_prod(tmp_path: Path) -> None:
    scenario_dir, foundry_dir = _write_synthetic_manifest(tmp_path)
    product_yaml = scenario_dir / "product.yaml"
    data = yaml.safe_load(product_yaml.read_text())
    data["security"]["prod"]["agent_data_access"] = "direct"
    product_yaml.write_text(yaml.dump(data))

    with pytest.raises(ValidationError, match="agent_data_access"):
        ProductManifest.load(scenario_dir, foundry_dir=foundry_dir)


def test_product_manifest_allows_direct_agent_data_access_in_dev(tmp_path: Path) -> None:
    scenario_dir, foundry_dir = _write_synthetic_manifest(tmp_path)
    product_yaml = scenario_dir / "product.yaml"
    data = yaml.safe_load(product_yaml.read_text())
    data["security"]["dev"]["agent_data_access"] = "direct"
    product_yaml.write_text(yaml.dump(data))

    manifest = ProductManifest.load(scenario_dir, foundry_dir=foundry_dir)
    assert manifest.security["dev"].agent_data_access == "direct"


def test_product_manifest_rejects_orphaned_vector_index(tmp_path: Path) -> None:
    scenario_dir, foundry_dir = _write_synthetic_manifest(tmp_path)
    scenario_yaml = scenario_dir / "scenario.yaml"
    data = yaml.safe_load(scenario_yaml.read_text())
    data["retrieval"]["vector_indexes"][0]["used_by"] = ["unknown_tool"]
    scenario_yaml.write_text(yaml.dump(data))

    with pytest.raises(ValidationError, match="unknown tool"):
        ProductManifest.load(scenario_dir, foundry_dir=foundry_dir)


def test_product_manifest_rejects_retrieval_tool_with_no_backing_index(tmp_path: Path) -> None:
    scenario_dir, foundry_dir = _write_synthetic_manifest(tmp_path)
    tools_path = foundry_dir / "tools" / "tools.contract.json"
    data = json.loads(tools_path.read_text())
    data["tools"].append(
        {
            "name": "retrieve_playbooks",
            "mutates_data": False,
            "authorization": "read-approved-gold-playbooks",
        }
    )
    tools_path.write_text(json.dumps(data))

    with pytest.raises(ValidationError, match="not referenced by any vector index"):
        ProductManifest.load(scenario_dir, foundry_dir=foundry_dir)


def test_discover_scenario_dir_finds_the_single_scenario(tmp_path: Path) -> None:
    scenario_dir, _ = _write_synthetic_manifest(tmp_path)
    assert discover_scenario_dir(scenario_dir.parent) == scenario_dir
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/contracts/test_product_manifest.py -v`
Expected: FAIL with `ImportError: cannot import name 'ProductManifest'`

- [ ] **Step 3: Write the implementation**

Append to `src/platform_core/contracts/product_manifest.py` (add `json` and `yaml` to the existing imports, add `model_validator` to the pydantic import line):

```python
import json

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator
```

Then append the composite model and loader:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/contracts/test_product_manifest.py -v`
Expected: PASS (19 tests)

- [ ] **Step 5: Lint and commit**

```bash
ruff check src/platform_core/contracts/product_manifest.py tests/contracts/test_product_manifest.py
git add src/platform_core/contracts/product_manifest.py tests/contracts/test_product_manifest.py
git commit -m "feat: add ProductManifest composite model, loader, and validators"
```

---

### Task 3: Churn's manifest files, corrected `config.yaml`/`scenario.yaml`, and the golden-fixture test

**Files:**
- Create: `src/scenarios/churn/product.yaml`
- Create: `src/scenarios/churn/routing.yaml`
- Modify: `src/scenarios/churn/scenario.yaml` (all 31 lines — full rewrite)
- Modify: `src/scenarios/churn/config.yaml` (all 19 lines — full rewrite)
- Modify: `tests/data_quality/test_churn_config.py:1-25`

**Interfaces:**
- Consumes: `ProductManifest.load` from Task 2.
- Produces: churn's manifest files as the golden fixture every later sub-project (#2–#5) and product repo can point to as a working example.

- [ ] **Step 1: Write the failing test**

Replace `tests/data_quality/test_churn_config.py` in full:

```python
from pathlib import Path

import yaml

from platform_core.contracts.product_manifest import ProductManifest
from platform_core.settings.config import Settings


def test_churn_scenario_has_one_canonical_corpus() -> None:
    config = yaml.safe_load(Path("src/scenarios/churn/config.yaml").read_text())
    manifest = yaml.safe_load(Path("src/scenarios/churn/scenario.yaml").read_text())
    assert config["expected_customer_count"] == 7043
    assert config["source_dataset"] == "telco_customer_churn_v1"
    assert manifest["task"] == "classification"
    assert manifest["features"]["version"] == "churn.features.v1"
    assert "C123" not in config["source_url"]


def test_endpoint_and_promotion_policy_are_canonical() -> None:
    manifest = yaml.safe_load(Path("src/scenarios/churn/scenario.yaml").read_text())
    assert manifest["promotion_policy"] == {"metric": "auc", "threshold": 0.02}
    assert manifest["serving"]["endpoint"] == "churn-model-endpoint"
    assert manifest["model"]["name"] == "churn_classifier"
    assert manifest["model"]["candidate_models"] == ["logistic_regression", "random_forest"]
    assert manifest["model"]["minimum_rows"] == 7043
    assert Settings().model_serving_endpoint == "churn-model-endpoint"


def test_churn_product_manifest_is_valid() -> None:
    manifest = ProductManifest.load(Path("src/scenarios/churn"))

    assert manifest.product.name == "churn"
    assert manifest.environments == ["dev", "test", "prod"]
    assert manifest.security["prod"].agent_data_access == "mediated"
    assert manifest.routing["prod"].primary == "gpt-4o"
    assert manifest.routing["dev"].primary == "gpt-4o-mini"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/data_quality/test_churn_config.py -v`
Expected: FAIL — `test_endpoint_and_promotion_policy_are_canonical` raises `KeyError: 'model'` (scenario.yaml doesn't have a `model` key yet), and `test_churn_product_manifest_is_valid` raises `FileNotFoundError` for `product.yaml`.

- [ ] **Step 3: Write the implementation**

Create `src/scenarios/churn/product.yaml`:

```yaml
product:
  name: churn
  display_name: "Telco Churn Reference"
  manifest_version: "1.0"
environments: [dev, test, prod]
security:
  dev:
    agent_data_access: mediated
  test:
    agent_data_access: mediated
  prod:
    agent_data_access: mediated
```

Create `src/scenarios/churn/routing.yaml`:

```yaml
dev:
  primary: gpt-4o-mini
  fallback: []
test:
  primary: gpt-4o-mini
  fallback: []
prod:
  primary: gpt-4o
  fallback: [gpt-4o-mini]
```

Replace `src/scenarios/churn/scenario.yaml` in full:

```yaml
name: churn
task: classification
source_datasets:
  - customers
  - usage_events
  - support_tickets
features:
  builder: churn_feature_builder
  schema: churn_feature_schema_v1
  version: churn.features.v1
  contract: churn_feature_contract_v1
model:
  name: churn_classifier
  candidate_models: [logistic_regression, random_forest]
  minimum_rows: 7043
evaluation:
  metrics:
    - auc
    - f1
    - accuracy
promotion_policy:
  metric: auc
  threshold: 0.02
serving:
  endpoint: churn-model-endpoint
retrieval:
  vector_indexes:
    - name: notes_vs
      source_table: gold.customer_notes
      used_by: [retrieve_customer_evidence]
    - name: tickets_vs
      source_table: gold.support_tickets
      used_by: [retrieve_customer_evidence]
    - name: playbooks_vs
      source_table: gold.recommended_actions
      used_by: [retrieve_playbooks]
```

Replace `src/scenarios/churn/config.yaml` in full:

```yaml
scenario: churn
source_dataset: telco_customer_churn_v1
source_url: https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv
expected_customer_count: 7043
catalogs:
  dev: mlworkflow_dev
  test: mlworkflow_test
  prod: mlworkflow_prod
schemas: [bronze, silver, gold, ml, ops]
playbooks_table: gold.recommended_actions
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/data_quality/test_churn_config.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Lint and commit**

```bash
ruff check src/scenarios/churn tests/data_quality/test_churn_config.py
git add src/scenarios/churn/product.yaml src/scenarios/churn/routing.yaml \
        src/scenarios/churn/scenario.yaml src/scenarios/churn/config.yaml \
        tests/data_quality/test_churn_config.py
git commit -m "feat: add churn product.yaml/routing.yaml, dedupe config.yaml/scenario.yaml"
```

---

### Task 4: Migrate `Settings` off hardcoded churn defaults

**Files:**
- Modify: `src/platform_core/settings/config.py:1-23` (full rewrite)
- Test: `tests/unit/test_settings.py`

**Interfaces:**
- Consumes: `ProductManifest.load`, `discover_scenario_dir` from Task 2; churn's real manifest files from Task 3.
- Produces: `Settings` keeps its existing public attribute names (`model_serving_endpoint`, `databricks_catalog`, `feature_schema_version`, `feature_contract`, `foundry_deployment`) as computed properties instead of hardcoded fields — `src/api/app.py` and `src/platform_core/integrations/databricks_serving.py` need no changes, since both only ever read `settings.<attr>` by name.

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_settings.py`:

```python
from platform_core.settings.config import Settings


def test_settings_derives_model_serving_endpoint_from_manifest() -> None:
    assert Settings().model_serving_endpoint == "churn-model-endpoint"


def test_settings_resolves_catalog_for_configured_environment() -> None:
    assert Settings(app_env="prod").databricks_catalog == "mlworkflow_prod"
    assert Settings(app_env="dev").databricks_catalog == "mlworkflow_dev"


def test_settings_derives_feature_schema_version_and_contract() -> None:
    settings = Settings()
    assert settings.feature_schema_version == "churn.features.v1"
    assert settings.feature_contract == "churn_feature_contract_v1"


def test_settings_derives_foundry_deployment_from_routing() -> None:
    assert Settings(app_env="prod").foundry_deployment == "gpt-4o"
    assert Settings(app_env="dev").foundry_deployment == "gpt-4o-mini"


def test_settings_manifest_is_cached_across_property_access() -> None:
    settings = Settings()
    assert settings.manifest is settings.manifest
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_settings.py -v`
Expected: FAIL — `Settings(app_env="prod")` works today (field exists) but `.databricks_catalog` returns the hardcoded `"mlworkflow_dev"` regardless of `app_env`, so the `prod` assertion fails.

- [ ] **Step 3: Write the implementation**

Replace `src/platform_core/settings/config.py` in full:

```python
from __future__ import annotations

from functools import cached_property
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

from platform_core.contracts.product_manifest import ProductManifest, discover_scenario_dir


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "enterprise-ml-workflow"
    app_env: Literal["dev", "test", "prod"] = "dev"
    databricks_sql_warehouse_id: str | None = None
    foundry_endpoint: str | None = None

    @cached_property
    def manifest(self) -> ProductManifest:
        return ProductManifest.load(discover_scenario_dir())

    @property
    def model_serving_endpoint(self) -> str:
        return self.manifest.scenario.serving.endpoint

    @property
    def databricks_catalog(self) -> str:
        return self.manifest.config.catalogs[self.app_env]

    @property
    def feature_schema_version(self) -> str:
        return self.manifest.scenario.features.version

    @property
    def feature_contract(self) -> str:
        return self.manifest.scenario.features.contract

    @property
    def foundry_deployment(self) -> str:
        return self.manifest.routing[self.app_env].primary


settings = Settings()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_settings.py -v`
Expected: PASS (5 tests)

Then run the full suite to confirm nothing else broke:

Run: `pytest`
Expected: PASS — in particular `tests/smoke/test_api.py` and `tests/integrations/test_databricks_serving.py`, which read `settings.model_serving_endpoint`/`settings.databricks_catalog`/etc. by attribute name and require no code changes.

- [ ] **Step 5: Lint and commit**

```bash
ruff check .
pytest
git add src/platform_core/settings/config.py tests/unit/test_settings.py
git commit -m "feat: derive Settings' scenario fields from ProductManifest instead of hardcoding churn"
```

---

## Self-review notes

- **Spec coverage:** every non-goal-excluded item in the spec (section models, composite validation, manifest_version check, prod hard-block, retrieval/tools reciprocity, copy-on-generate churn defaults as golden fixture, Settings migration) maps to a task above. Retrieval infrastructure, the factory generator, AKS, packaging, and portfolio reporting are out of scope per the spec's non-goals and are not tasked here.
- **Type consistency:** `ProductManifest.routing`/`security` keyed by `Environment` throughout; `RoutingEntry.primary`/`fallback` and `SecurityPosture.agent_data_access` names match between Task 1, Task 2's synthetic fixtures, and Task 3's real churn files.
- **No placeholders:** every step has full, runnable code; no "add error handling" or "similar to Task N" steps.
