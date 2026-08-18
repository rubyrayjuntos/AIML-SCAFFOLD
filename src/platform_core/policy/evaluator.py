from __future__ import annotations

from platform_core.contracts.product_manifest import (
    CapabilityMaturity,
    CapabilityMaturityPolicy,
    ProductManifest,
)
from platform_core.providers.catalog import R1_PROVIDER_CATALOG, ProviderCatalog

_MATURITY_ORDER = {
    CapabilityMaturity.STABLE: 0,
    CapabilityMaturity.PREVIEW: 1,
    CapabilityMaturity.EXPERIMENTAL: 2,
    CapabilityMaturity.PLANNED: 3,
}

_POLICY_LIMIT = {
    CapabilityMaturityPolicy.STABLE_ONLY: 0,
    CapabilityMaturityPolicy.ALLOW_PREVIEW: 1,
    CapabilityMaturityPolicy.ALLOW_EXPERIMENTAL: 2,
}


def requested_descriptors(
    manifest: ProductManifest,
    catalog: ProviderCatalog = R1_PROVIDER_CATALOG,
) -> list:
    descriptors = [
        catalog.resolve(manifest.infrastructure.azure.provider, "infrastructure", "plan")
    ]
    if manifest.capabilities.ml:
        for feature in manifest.capabilities.ml.features:
            if feature in {"training", "evaluation"}:
                capability = "ml"
                provider = manifest.capabilities.ml.provider
            elif feature == "registry":
                capability = "registry"
                provider = manifest.capabilities.ml.provider
            elif feature == "batch_serving":
                capability = "serving"
                provider = (
                    "azure_ml_batch"
                    if manifest.capabilities.ml.provider == "azure_ml"
                    else manifest.capabilities.ml.provider
                )
            elif feature == "evidence":
                capability = "evidence"
                provider = "azure_blob"
            else:
                raise ValueError(f"unsupported R1 ML feature {feature!r}")
            descriptors.append(catalog.resolve(provider, capability, feature))
    for unsupported_name in ("data", "retrieval", "agent"):
        if getattr(manifest.capabilities, unsupported_name) is not None:
            raise ValueError(f"{unsupported_name} is planned and unavailable in R1")
    unique: dict[str, object] = {}
    for descriptor in descriptors:
        unique.setdefault(descriptor.model_dump_json(), descriptor)
    return list(unique.values())


def evaluate_policy(
    manifest: ProductManifest,
    *,
    allow_experimental: bool = False,
    catalog: ProviderCatalog = R1_PROVIDER_CATALOG,
) -> list:
    if manifest.infrastructure.azure.provider != "terraform":
        raise ValueError("Terraform is the only supported R1 Azure infrastructure provider")
    descriptors = requested_descriptors(manifest, catalog)
    requested_keys = {
        f"{descriptor.capability}:{operation}"
        for descriptor in descriptors
        for operation in descriptor.operations
    }
    for descriptor in descriptors:
        if descriptor.maturity == CapabilityMaturity.PLANNED:
            raise ValueError(f"planned capability {descriptor.capability!r} cannot be generated")
        exceeds_policy = _MATURITY_ORDER[descriptor.maturity] > _POLICY_LIMIT[
            manifest.policy.capability_maturity
        ]
        if exceeds_policy:
            raise ValueError(
                f"capability {descriptor.capability!r} is {descriptor.maturity.value}, "
                "which exceeds "
                f"policy {manifest.policy.capability_maturity.value!r}"
            )
        if descriptor.maturity != CapabilityMaturity.STABLE and not allow_experimental:
            raise ValueError(
                f"capability {descriptor.capability!r} is not stable; pass --allow-experimental "
                "after explicitly allowing its maturity in the manifest"
            )
        missing = set(descriptor.required_capabilities) - requested_keys
        if missing:
            raise ValueError(
                f"capability {descriptor.capability!r} requires {sorted(missing)}"
            )
    return descriptors
