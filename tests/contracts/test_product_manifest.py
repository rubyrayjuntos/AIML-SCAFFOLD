import json
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from platform_core.contracts.product_manifest import (
    AgentYaml,
    ConfigYaml,
    ProductIdentity,
    ProductManifest,
    RoutingEntry,
    ScenarioEvaluation,
    ScenarioFeatures,
    ScenarioModel,
    ScenarioPromotionPolicy,
    ScenarioRetrieval,
    ScenarioServing,
    ScenarioYaml,
    SecurityPosture,
    ToolsContract,
    VectorIndex,
    discover_scenario_dir,
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
