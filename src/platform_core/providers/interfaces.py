from __future__ import annotations

from typing import Protocol

from platform_core.contracts.product_manifest import ProductManifest
from platform_core.contracts.project_plan import CapabilityDescriptor, ResolvedProjectPlan


class CapabilityProvider(Protocol):
    def capabilities(self) -> tuple[CapabilityDescriptor, ...]: ...


class InfrastructureProvider(CapabilityProvider, Protocol):
    def resolve(self, manifest: ProductManifest, environment: str) -> ResolvedProjectPlan: ...


class DataProvider(CapabilityProvider, Protocol):
    pass


class TrainingProvider(CapabilityProvider, Protocol):
    pass


class ModelRegistryProvider(CapabilityProvider, Protocol):
    pass


class ServingProvider(CapabilityProvider, Protocol):
    pass


class RetrievalProvider(CapabilityProvider, Protocol):
    pass


class AgentRuntimeProvider(CapabilityProvider, Protocol):
    pass


class EvidenceSink(CapabilityProvider, Protocol):
    pass


class PolicyEvaluator(Protocol):
    def evaluate(self, manifest: ProductManifest, *, allow_experimental: bool) -> None: ...
