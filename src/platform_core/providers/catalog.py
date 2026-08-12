from __future__ import annotations

from platform_core.contracts.product_manifest import CapabilityMaturity
from platform_core.contracts.project_plan import CapabilityDescriptor


class ProviderCatalog:
    def __init__(self, descriptors: tuple[CapabilityDescriptor, ...]) -> None:
        self._descriptors = descriptors

    def capabilities(self) -> tuple[CapabilityDescriptor, ...]:
        return self._descriptors

    def resolve(self, provider: str, capability: str, operation: str) -> CapabilityDescriptor:
        matches = [
            descriptor
            for descriptor in self._descriptors
            if descriptor.provider == provider
            and descriptor.capability == capability
            and operation in descriptor.operations
        ]
        if len(matches) != 1:
            raise ValueError(
                f"no R1 provider capability for provider={provider!r}, "
                f"capability={capability!r}, operation={operation!r}"
            )
        return matches[0]


R1_PROVIDER_CATALOG = ProviderCatalog(
    (
        CapabilityDescriptor(
            provider="terraform",
            capability="infrastructure",
            operations=("plan", "apply"),
            maturity=CapabilityMaturity.PREVIEW,
        ),
        CapabilityDescriptor(
            provider="azure_ml",
            capability="ml",
            operations=("training", "evaluation"),
            maturity=CapabilityMaturity.PREVIEW,
        ),
        CapabilityDescriptor(
            provider="azure_ml",
            capability="registry",
            operations=("registry",),
            maturity=CapabilityMaturity.PREVIEW,
            required_capabilities=("ml:training", "ml:evaluation"),
        ),
        CapabilityDescriptor(
            provider="azure_ml_batch",
            capability="serving",
            operations=("batch_serving",),
            maturity=CapabilityMaturity.PREVIEW,
            required_capabilities=("registry:registry",),
        ),
        CapabilityDescriptor(
            provider="azure_blob",
            capability="evidence",
            operations=("evidence",),
            maturity=CapabilityMaturity.PREVIEW,
        ),
    )
)
