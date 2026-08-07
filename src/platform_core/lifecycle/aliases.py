from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class AliasClient(Protocol):
    def set_alias(self, model_name: str, alias: str, version: str) -> None: ...

    def get_alias(self, model_name: str, alias: str) -> str | None: ...


@dataclass(frozen=True)
class LifecycleState:
    model_name: str
    champion_version: str | None
    challenger_version: str | None
    served_version: str | None


def promote_after_approval(
    client: AliasClient,
    *,
    model_name: str,
    candidate_version: str,
    validation_passed: bool,
    production_approved: bool,
) -> str:
    if not validation_passed:
        raise ValueError("candidate failed automated validation gates")
    if not production_approved:
        raise PermissionError("production approval is required before promotion")
    client.set_alias(model_name, "champion", candidate_version)
    return candidate_version
