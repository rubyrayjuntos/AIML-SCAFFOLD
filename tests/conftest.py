from __future__ import annotations

from copy import deepcopy

import pytest


@pytest.fixture
def manifest_payload() -> dict:
    return deepcopy(
        {
            "manifest_schema_version": "1.0",
            "platform_version": "1.0.0",
            "product": {
                "name": "example-risk",
                "owner": "ml-platform@example.com",
                "cost_center": "CC-1234",
            },
            "capabilities": {
                "ml": {
                    "provider": "azure_ml",
                    "features": [
                        "training",
                        "evaluation",
                        "registry",
                        "batch_serving",
                        "evidence",
                    ],
                }
            },
            "infrastructure": {"azure": {"provider": "terraform"}},
            "execution": {
                "development": {"provider": "local", "containerized": True},
                "training": {
                    "provider": "local",
                    "cloud_fallback": {"enabled": False},
                },
                "batch": {
                    "provider": "local",
                    "cloud_fallback": {"enabled": False},
                },
            },
            "cost_policy": {
                "cloud_execution_requires_approval": True,
                "default_max_nodes": 1,
                "permit_spot_training": True,
                "retain_idle_clusters": False,
            },
            "policy": {
                "capability_maturity": "allow_preview",
                "data_classification": "internal",
                "allowed_regions": ["eastus"],
                "evidence_retention_days": 90,
                "deployment_approval": "dev_manual",
            },
            "shared_resources": {
                "azure_context": {
                    "tenant_id": "00000000-0000-0000-0000-000000000001",
                    "subscription_id": "00000000-0000-0000-0000-000000000000",
                    "deployment_identity": {
                        "client_id_environment_variable": "AZURE_CLIENT_ID",
                        "object_id_environment_variable": "AZURE_CLIENT_OBJECT_ID",
                        "federated_credential": {
                            "issuer": "https://token.actions.githubusercontent.com",
                            "subject": "repo:example/example-risk:environment:dev",
                            "audience": "api://AzureADTokenExchange",
                        },
                    },
                },
                "terraform_backend": {
                    "resource_group_id": (
                        "/subscriptions/00000000-0000-0000-0000-000000000000/"
                        "resourceGroups/rg-platform-state"
                    ),
                    "storage_account_id": (
                        "/subscriptions/00000000-0000-0000-0000-000000000000/"
                        "resourceGroups/rg-platform-state/providers/"
                        "Microsoft.Storage/storageAccounts/stplatformstate"
                    ),
                    "container_name": "tfstate",
                }
            },
            "environments": ["dev"],
            "provider_extensions": {
                "azure_ml": {
                    "location": "eastus",
                }
            },
        }
    )
