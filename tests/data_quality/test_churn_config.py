from pathlib import Path

import yaml

from platform_core.settings.config import Settings


def test_churn_scenario_has_one_canonical_corpus() -> None:
    config = yaml.safe_load(Path("src/scenarios/churn/config.yaml").read_text())
    manifest = yaml.safe_load(Path("src/scenarios/churn/scenario.yaml").read_text())
    assert config["expected_customer_count"] == 7043
    assert config["source_dataset"] == "telco_customer_churn_v1"
    assert manifest["task"] == "classification"
    assert manifest["features"]["version"] == config["feature_schema_version"]
    assert "C123" not in config["source_url"]


def test_endpoint_and_promotion_policy_are_canonical() -> None:
    config = yaml.safe_load(Path("src/scenarios/churn/config.yaml").read_text())
    manifest = yaml.safe_load(Path("src/scenarios/churn/scenario.yaml").read_text())
    assert manifest["promotion_policy"] == {"metric": "auc", "threshold": 0.02}
    assert manifest["serving"]["endpoint"] == "churn-model-endpoint"
    assert config["model"]["primary_metric"] == "auc"
    assert config["model"]["minimum_improvement"] == 0.02
    assert Settings.from_scenario(Path("src/scenarios/churn")).model_serving_endpoint == (
        "churn-model-endpoint"
    )
