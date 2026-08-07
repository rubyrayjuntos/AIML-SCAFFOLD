from platform_core.contracts.models import FeatureRegistryEntry


def test_feature_registry_entry_is_versioned_and_bound_to_sources() -> None:
    entry = FeatureRegistryEntry(
        feature_version="churn.features.v1",
        feature_contract="churn_feature_contract_v1",
        feature_schema={"health_score": "double", "open_tickets_30d": "int"},
        builder="churn_feature_builder",
        source_datasets=["customers", "usage_events"],
    )
    assert entry.feature_version == "churn.features.v1"
    assert entry.feature_contract == "churn_feature_contract_v1"
