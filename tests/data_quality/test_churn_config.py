from pathlib import Path

import yaml


def test_churn_scenario_has_one_canonical_corpus() -> None:
    config = yaml.safe_load(Path("src/scenarios/churn/config.yaml").read_text())
    assert config["expected_customer_count"] == 7043
    assert config["source_dataset"] == "telco_customer_churn_v1"
    assert config["task_type"] == "classification"
    assert "C123" not in config["source_url"]
