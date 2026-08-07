from pathlib import Path

import yaml


def test_churn_scenario_has_one_canonical_corpus() -> None:
    config = yaml.safe_load(Path("src/scenarios/churn/config.yaml").read_text())
    manifest = yaml.safe_load(Path("src/scenarios/churn/scenario.yaml").read_text())
    assert config["expected_customer_count"] == 7043
    assert config["source_dataset"] == "telco_customer_churn_v1"
    assert manifest["task"] == "classification"
    assert manifest["features"]["version"] == config["feature_schema_version"]
    assert "C123" not in config["source_url"]
