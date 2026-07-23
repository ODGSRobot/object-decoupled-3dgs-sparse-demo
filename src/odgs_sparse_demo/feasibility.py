from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

CRITERION_ORDER = (
    "collision",
    "workspace",
    "joint_limit",
    "visibility",
    "boundary",
    "structural_consistency",
    "action_smoothness",
)

DEFAULT_OPERATIONAL_BOUNDS = {
    "visible_target_fraction_min": 0.50,
    "hinge_boundary_margin_deg_min": 2.0,
    "structural_translation_residual_m_max": 0.010,
    "structural_rotation_residual_deg_max": 5.0,
    "normalized_action_second_difference_max": 0.20,
}

ZERO_VIOLATION_THRESHOLDS = {key: 0.0 for key in CRITERION_ORDER}


@dataclass(frozen=True)
class CandidateMeasurement:
    candidate_id: str
    round_index: int
    seed: int
    checkpoint: str
    source_episode: str
    sampled_state: Mapping[str, float | int | str | None]
    violations: Mapping[str, float]
    manual_review_passed: bool
    manual_review_reason: str = ""


@dataclass(frozen=True)
class FeasibilityDecision:
    candidate_id: str
    round_index: int
    seed: int
    checkpoint: str
    source_episode: str
    accepted: bool
    rejection_reason: str
    automatic_checks_passed: bool
    manual_review_passed: bool
    manual_review_reason: str
    sampled_state_json: str
    violations_json: str
    thresholds_json: str


def normalized_constraint_violations(
    measurements: Mapping[str, float],
    structure_type: str = "hinge",
    bounds: Mapping[str, float] | None = None,
) -> dict[str, float]:
    """Map raw kinematic and geometric checks to nonnegative violations.

    Zero means the operational bound is satisfied. Positive values measure
    only the amount by which a bound is exceeded. The implemented scope is
    intentionally limited to rigid and hinged objects; force, friction, and
    dynamic stability are not evaluated here.
    """
    if structure_type not in {"hinge", "rigid"}:
        raise ValueError("structure_type must be 'hinge' or 'rigid'")
    if bounds is None:
        bounds = DEFAULT_OPERATIONAL_BOUNDS

    required = {
        "collision_penetration_m",
        "workspace_outside_distance_m",
        "joint_limit_excess_rad",
        "visible_target_fraction",
        "structural_translation_residual_m",
        "structural_rotation_residual_deg",
        "normalized_action_second_difference",
    }
    if structure_type == "hinge":
        required.add("hinge_boundary_margin_deg")
    missing = sorted(required - set(measurements))
    if missing:
        raise ValueError(f"missing raw constraint measurements={missing}")

    boundary = 0.0
    if structure_type == "hinge":
        boundary = max(
            0.0,
            bounds["hinge_boundary_margin_deg_min"]
            - float(measurements["hinge_boundary_margin_deg"]),
        )

    structural = max(
        0.0,
        float(measurements["structural_translation_residual_m"])
        / bounds["structural_translation_residual_m_max"]
        - 1.0,
        float(measurements["structural_rotation_residual_deg"])
        / bounds["structural_rotation_residual_deg_max"]
        - 1.0,
    )
    return {
        "collision": max(0.0, float(measurements["collision_penetration_m"])),
        "workspace": max(0.0, float(measurements["workspace_outside_distance_m"])),
        "joint_limit": max(0.0, float(measurements["joint_limit_excess_rad"])),
        "visibility": max(
            0.0,
            bounds["visible_target_fraction_min"]
            - float(measurements["visible_target_fraction"]),
        ),
        "boundary": boundary,
        "structural_consistency": structural,
        "action_smoothness": max(
            0.0,
            float(measurements["normalized_action_second_difference"])
            / bounds["normalized_action_second_difference_max"]
            - 1.0,
        ),
    }


def evaluate_candidate(
    measurement: CandidateMeasurement,
    thresholds: Mapping[str, float] | None = None,
    criterion_order: Sequence[str] = CRITERION_ORDER,
) -> FeasibilityDecision:
    """Apply automatic checks followed by the recorded manual review."""
    if thresholds is None:
        thresholds = ZERO_VIOLATION_THRESHOLDS
    missing_measurements = [key for key in criterion_order if key not in measurement.violations]
    missing_thresholds = [key for key in criterion_order if key not in thresholds]
    if missing_measurements or missing_thresholds:
        raise ValueError(
            f"missing measurements={missing_measurements}; missing thresholds={missing_thresholds}"
        )

    rejection_reason = ""
    for key in criterion_order:
        value = float(measurement.violations[key])
        threshold = float(thresholds[key])
        if value < 0:
            raise ValueError(f"violation '{key}' must be nonnegative, got {value}")
        if value > threshold:
            rejection_reason = key
            break

    automatic_checks_passed = not rejection_reason
    if automatic_checks_passed and not measurement.manual_review_passed:
        rejection_reason = "manual_review"

    return FeasibilityDecision(
        candidate_id=measurement.candidate_id,
        round_index=measurement.round_index,
        seed=measurement.seed,
        checkpoint=measurement.checkpoint,
        source_episode=measurement.source_episode,
        accepted=not rejection_reason,
        rejection_reason=rejection_reason,
        automatic_checks_passed=automatic_checks_passed,
        manual_review_passed=measurement.manual_review_passed,
        manual_review_reason=measurement.manual_review_reason,
        sampled_state_json=json.dumps(measurement.sampled_state, sort_keys=True),
        violations_json=json.dumps(measurement.violations, sort_keys=True),
        thresholds_json=json.dumps(dict(thresholds), sort_keys=True),
    )


def coverage_index(visited_bins: Mapping[str, set[str]], total_bins: Mapping[str, int]) -> float:
    """Compute mean visited-bin fraction across randomized dimensions."""
    if not total_bins:
        raise ValueError("total_bins must contain at least one randomized dimension")
    values: list[float] = []
    for dimension, denominator in total_bins.items():
        if denominator <= 0:
            raise ValueError(f"total bin count for '{dimension}' must be positive")
        visited = len(visited_bins.get(dimension, set()))
        if visited > denominator:
            raise ValueError(f"visited bins exceed total bins for '{dimension}'")
        values.append(visited / denominator)
    return sum(values) / len(values)


def write_provenance(path: Path, decisions: Sequence[FeasibilityDecision]) -> None:
    """Write one immutable provenance row per candidate rollout."""
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(asdict(item) for item in decisions).to_csv(path, index=False)
