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
