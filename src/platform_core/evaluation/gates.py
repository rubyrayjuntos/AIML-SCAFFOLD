from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class GateDecision:
    passed: bool
    reasons: tuple[str, ...]


def validate_training_contract(
    *,
    source_row_count: int,
    minimum_rows: int,
    disallowed_row_count: int = 0,
    required_source: str | None = None,
    actual_source: str | None = None,
) -> GateDecision:
    reasons: list[str] = []
    if source_row_count < minimum_rows:
        reasons.append(f"source row count {source_row_count} is below minimum {minimum_rows}")
    if disallowed_row_count:
        reasons.append(f"dataset contains {disallowed_row_count} disallowed rows")
    if required_source and actual_source != required_source:
        reasons.append(f"source dataset {actual_source!r} does not match {required_source!r}")
    return GateDecision(not reasons, tuple(reasons))


def compare_candidate(
    *,
    champion_metric: float,
    candidate_metric: float,
    minimum_improvement: float,
) -> GateDecision:
    improvement = candidate_metric - champion_metric
    if improvement < minimum_improvement and not math.isclose(
        improvement, minimum_improvement, rel_tol=0.0, abs_tol=1e-12
    ):
        return GateDecision(
            False,
            (f"improvement {improvement:.4f} is below {minimum_improvement:.4f}",),
        )
    return GateDecision(True, (f"improvement {improvement:.4f} meets the gate",))
