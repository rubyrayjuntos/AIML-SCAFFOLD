from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any, Literal
from uuid import UUID

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SUPPORTED_MANIFEST_SCHEMA_VERSION = "1.0"
SUPPORTED_PLATFORM_VERSION = "1.0.0"
Environment = Literal["dev", "test", "prod"]


class CapabilityMaturity(StrEnum):
    STABLE = "stable"
    PREVIEW = "preview"
    EXPERIMENTAL = "experimental"
    PLANNED = "planned"


class CapabilityMaturityPolicy(StrEnum):
    STABLE_ONLY = "stable_only"
    ALLOW_PREVIEW = "allow_preview"
    ALLOW_EXPERIMENTAL = "allow_experimental"


class ProductIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(pattern=r"^[a-z][a-z0-9-]{1,38}[a-z0-9]$")
    owner: str = Field(min_length=1)
    cost_center: str = Field(min_length=1)
    display_name: str | None = None


class CapabilityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str = Field(min_length=1)
    features: list[str] = Field(min_length=1)

    @field_validator("features")
    @classmethod
    def unique_features(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("capability features must be unique")
        return value


class CapabilitySelection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ml: CapabilityRequest | None = None
    data: CapabilityRequest | None = None
    retrieval: CapabilityRequest | None = None
    agent: CapabilityRequest | None = None

    @model_validator(mode="after")
    def at_least_one_capability(self) -> CapabilitySelection:
        if not any((self.ml, self.data, self.retrieval, self.agent)):
            raise ValueError("at least one capability must be enabled")
        return self


class AzureInfrastructure(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: Literal["terraform", "bicep"]


class InfrastructureSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    azure: AzureInfrastructure


class LocalDevelopmentExecution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: Literal["local"] = "local"
    containerized: bool = True


class AzureTrainingFallback(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    mode: Literal["azure_ml_serverless", "azure_ml_cluster"] | None = None
    instance_type: str | None = None
    tier: Literal["spot", "dedicated"] = "spot"
    min_instances: Literal[0] = 0
    max_instances: int = Field(default=1, ge=1, le=1, strict=True)
    idle_seconds_before_scaledown: int = Field(default=120, ge=60, le=3600, strict=True)

    @field_validator("instance_type")
    @classmethod
    def normalize_instance_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("instance_type cannot be empty")
        return normalized

    @model_validator(mode="after")
    def require_explicit_cloud_intent(self) -> AzureTrainingFallback:
        if self.enabled and (self.mode is None or self.instance_type is None):
            raise ValueError(
                "enabled Azure training requires explicit mode and instance_type"
            )
        if not self.enabled and (self.mode is not None or self.instance_type is not None):
            raise ValueError(
                "Azure training mode and instance_type require cloud_fallback.enabled=true"
            )
        return self


class TrainingExecution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: Literal["local"] = "local"
    cloud_fallback: AzureTrainingFallback = Field(default_factory=AzureTrainingFallback)


class AzureBatchFallback(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    mode: Literal["azure_ml_cluster"] | None = None
    instance_type: str | None = None
    tier: Literal["spot", "dedicated"] = "dedicated"
    min_instances: Literal[0] = 0
    max_instances: int = Field(default=1, ge=1, le=1, strict=True)
    idle_seconds_before_scaledown: int = Field(default=120, ge=60, le=3600, strict=True)

    @field_validator("instance_type")
    @classmethod
    def normalize_instance_type(cls, value: str | None) -> str | None:
        return AzureTrainingFallback.normalize_instance_type(value)

    @model_validator(mode="after")
    def require_explicit_cloud_intent(self) -> AzureBatchFallback:
        if self.enabled and (self.mode is None or self.instance_type is None):
            raise ValueError(
                "enabled Azure batch requires explicit mode and instance_type"
            )
        if not self.enabled and (self.mode is not None or self.instance_type is not None):
            raise ValueError(
                "Azure batch mode and instance_type require cloud_fallback.enabled=true"
            )
        return self


class BatchExecution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: Literal["local"] = "local"
    cloud_fallback: AzureBatchFallback = Field(default_factory=AzureBatchFallback)


class MonitoringExecution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False


class ExecutionPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    development: LocalDevelopmentExecution = Field(
        default_factory=LocalDevelopmentExecution
    )
    training: TrainingExecution = Field(default_factory=TrainingExecution)
    batch: BatchExecution = Field(default_factory=BatchExecution)
    monitoring: MonitoringExecution = Field(default_factory=MonitoringExecution)


class CostPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cloud_execution_requires_approval: Literal[True] = True
    default_max_nodes: Literal[1] = 1
    permit_spot_training: bool = True
    retain_idle_clusters: Literal[False] = False


class PlatformPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability_maturity: CapabilityMaturityPolicy = CapabilityMaturityPolicy.STABLE_ONLY
    data_classification: Literal["public", "internal", "confidential", "restricted"]
    allowed_regions: list[str] = Field(min_length=1)
    evidence_retention_days: int = Field(default=90, ge=1, le=3650)
    deployment_approval: Literal[
        "dev_manual",
        "environment_manual",
        "manual_dispatch_with_plan_digest",
        "external",
    ] = "dev_manual"
    allow_cross_subscription_backend: bool = False

    @field_validator("allowed_regions")
    @classmethod
    def normalized_regions(cls, value: list[str]) -> list[str]:
        normalized = [region.strip().lower() for region in value]
        if any(not region for region in normalized):
            raise ValueError("allowed regions cannot contain empty values")
        if len(normalized) != len(set(normalized)):
            raise ValueError("allowed regions must be unique")
        return normalized


class TerraformBackendReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resource_group_id: str = Field(min_length=1)
    storage_account_id: str = Field(min_length=1)
    container_name: str = Field(default="tfstate", min_length=3)

    @model_validator(mode="after")
    def validate_arm_ids(self) -> TerraformBackendReference:
        resource_group_marker = "/resourceGroups/"
        storage_marker = "/providers/Microsoft.Storage/storageAccounts/"
        valid_resource_group = (
            self.resource_group_id.startswith("/subscriptions/")
            and resource_group_marker in self.resource_group_id
        )
        if not valid_resource_group:
            raise ValueError(
                "terraform backend resource_group_id must be an Azure resource group ARM ID"
            )
        valid_storage = (
            self.storage_account_id.startswith("/subscriptions/")
            and storage_marker in self.storage_account_id
        )
        if not valid_storage:
            raise ValueError(
                "terraform backend storage_account_id must be a storage account ARM ID"
            )
        resource_group_subscription = self.resource_group_id.split("/", 3)[2]
        storage_subscription = self.storage_account_id.split("/", 3)[2]
        try:
            UUID(resource_group_subscription)
            UUID(storage_subscription)
        except ValueError as exc:
            raise ValueError(
                "terraform backend ARM IDs must contain UUID subscription IDs"
            ) from exc
        return self

    @property
    def subscription_id(self) -> str:
        return self.storage_account_id.split("/", 3)[2].lower()


class FederatedCredentialIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    issuer: str = "https://token.actions.githubusercontent.com"
    subject: str = Field(min_length=1)
    audience: str = "api://AzureADTokenExchange"


class DeploymentIdentityReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_id_environment_variable: str = "AZURE_CLIENT_ID"
    object_id_environment_variable: str = "AZURE_CLIENT_OBJECT_ID"
    federated_credential: FederatedCredentialIntent


class AzureContextReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    subscription_id: UUID
    deployment_identity: DeploymentIdentityReference


class SharedResources(BaseModel):
    model_config = ConfigDict(extra="forbid")

    azure_context: AzureContextReference
    terraform_backend: TerraformBackendReference


class AzureMlProviderExtension(BaseModel):
    model_config = ConfigDict(extra="forbid")

    location: str | None = None

    @field_validator("location")
    @classmethod
    def normalize_location(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("location cannot be empty")
        return normalized

class ProviderExtensions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    azure_ml: AzureMlProviderExtension = Field(default_factory=AzureMlProviderExtension)


class SecurityPosture(BaseModel):
    """Legacy section-file model retained for scenario compatibility."""

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


class ProductManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    manifest_schema_version: str
    platform_version: str
    product: ProductIdentity
    capabilities: CapabilitySelection
    infrastructure: InfrastructureSelection
    execution: ExecutionPolicy = Field(default_factory=ExecutionPolicy)
    cost_policy: CostPolicy = Field(default_factory=CostPolicy)
    policy: PlatformPolicy
    shared_resources: SharedResources
    environments: list[Environment] = Field(default_factory=lambda: ["dev"])
    provider_extensions: ProviderExtensions = Field(default_factory=ProviderExtensions)

    # Optional domain sections. They are inputs to generated scenario hooks, not platform defaults.
    scenario: ScenarioYaml | None = None
    config: ConfigYaml | None = None
    routing: dict[Environment, RoutingEntry] | None = None
    tools: ToolsContract | None = None
    agent: AgentYaml | None = None

    @model_validator(mode="after")
    def validate_versions_and_composition(self) -> ProductManifest:
        if self.manifest_schema_version != SUPPORTED_MANIFEST_SCHEMA_VERSION:
            raise ValueError(
                f"manifest_schema_version {self.manifest_schema_version!r} is not supported; "
                f"expected {SUPPORTED_MANIFEST_SCHEMA_VERSION!r}"
            )
        if self.platform_version != SUPPORTED_PLATFORM_VERSION:
            raise ValueError(
                f"platform_version {self.platform_version!r} is not supported; "
                f"expected {SUPPORTED_PLATFORM_VERSION!r}"
            )
        if len(self.environments) != len(set(self.environments)):
            raise ValueError("environments must be unique")
        if self.capabilities.agent and self.agent is None:
            raise ValueError("agent capability requires an agent definition")
        if self.capabilities.retrieval and not self.scenario:
            raise ValueError("retrieval capability requires a scenario retrieval definition")
        if self.agent and not self.capabilities.agent:
            raise ValueError("agent definition is present but the agent capability is disabled")
        if self.tools and not self.capabilities.agent:
            raise ValueError("tool contract is present but the agent capability is disabled")
        if (
            self.execution.training.cloud_fallback.tier == "spot"
            and self.execution.training.cloud_fallback.enabled
            and not self.cost_policy.permit_spot_training
        ):
            raise ValueError("spot training is prohibited by cost policy")
        backend_resource_group_subscription = (
            self.shared_resources.terraform_backend.resource_group_id.split("/", 3)[2].lower()
        )
        backend_subscription = self.shared_resources.terraform_backend.subscription_id
        if backend_resource_group_subscription != backend_subscription:
            raise ValueError("Terraform backend resource IDs must use the same subscription")
        deployment_subscription = str(
            self.shared_resources.azure_context.subscription_id
        ).lower()
        if (
            backend_subscription != deployment_subscription
            and not self.policy.allow_cross_subscription_backend
        ):
            raise ValueError(
                "cross-subscription Terraform backend requires "
                "policy.allow_cross_subscription_backend=true"
            )
        return self

    @classmethod
    def load(cls, path: Path) -> ProductManifest:
        manifest_path = path / "product.yaml" if path.is_dir() else path
        return cls.model_validate(_load_yaml(manifest_path))

    def canonical_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json", by_alias=True, exclude_none=True)

    def source_dict(self) -> dict[str, Any]:
        """Canonicalized user-supplied intent without model or platform defaults."""

        return self.model_dump(
            mode="json", by_alias=True, exclude_none=True, exclude_unset=True
        )


def discover_single_subdir(base: Path) -> Path:
    candidates = sorted(path for path in base.iterdir() if path.is_dir())
    if len(candidates) != 1:
        raise ValueError(
            f"expected exactly one subdirectory under {base}, found {len(candidates)}: "
            f"{[path.name for path in candidates]}"
        )
    return candidates[0]


def discover_single_file(base: Path, pattern: str) -> Path:
    candidates = sorted(base.glob(pattern))
    if len(candidates) != 1:
        raise ValueError(
            f"expected exactly one file matching {pattern!r} under {base}, found "
            f"{len(candidates)}: {[path.name for path in candidates]}"
        )
    return candidates[0]


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a YAML object")
    return payload


def discover_scenario_dir(base: Path = Path("src/scenarios")) -> Path:
    return discover_single_subdir(base)
