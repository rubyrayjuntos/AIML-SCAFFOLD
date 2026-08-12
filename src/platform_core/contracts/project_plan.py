from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from platform_core.contracts.product_manifest import CapabilityMaturity


class ResourceCostClass(StrEnum):
    ALWAYS_ON = "always_on"
    SCALE_TO_ZERO = "scale_to_zero"
    JOB_SCOPED = "job_scoped"


class CapabilityDescriptor(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: str
    capability: str
    operations: tuple[str, ...]
    maturity: CapabilityMaturity
    required_capabilities: tuple[str, ...] = ()
    incompatible_capabilities: tuple[str, ...] = ()


class PlannedResource(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: str
    owner: str
    cost_class: ResourceCostClass
    notes: str = ""


class ResolvedAzureContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    expected_tenant_id: str
    deployment_subscription_id: str
    backend_subscription_id: str
    cross_subscription_backend: bool
    cross_subscription_backend_allowed: bool
    deployment_identity_client_id_environment_variable: str
    deployment_identity_object_id_environment_variable: str
    oidc_issuer: str
    oidc_subject: str
    oidc_audience: str


class ResolvedProjectPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    manifest_schema_version: str
    platform_version: str
    project: str
    environment: str
    environment_topology: dict[str, dict[str, str]]
    azure_context: ResolvedAzureContext
    providers: dict[str, str]
    capabilities: list[CapabilityDescriptor]
    applied_defaults: dict[str, Any]
    shared_resources: dict[str, Any]
    provider_extensions: dict[str, Any]
    generated_components: list[str]
    resources: list[PlannedResource]
    preconditions: list[str]
    warnings: list[str]
    approval_required: bool
    approval_policy: str
    maturity_report: dict[str, Any]
    unsupported_requests: list[str] = Field(default_factory=list)

    def canonical_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)
