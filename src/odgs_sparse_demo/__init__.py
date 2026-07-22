"""Paper-facing implementation of structure-constrained data expansion."""

from .feasibility import (
    CRITERION_ORDER,
    CandidateMeasurement,
    FeasibilityDecision,
    coverage_index,
    evaluate_candidate,
    normalized_constraint_violations,
    write_provenance,
)
from .metrics import action_smoothness, success_rate, wilson_ci
from .pipeline import ClosedLoopResult, RolloutCandidate, run_closed_loop_expansion
from .regularization import (
    SequenceLosses,
    compose_training_loss,
    sequence_regularization_numpy,
    sequence_regularization_torch,
)
from .scene import HingeModel, RandomizationRanges, hinge_transform, sample_scene_state

__all__ = [
    "CRITERION_ORDER",
    "CandidateMeasurement",
    "ClosedLoopResult",
    "FeasibilityDecision",
    "HingeModel",
    "RandomizationRanges",
    "RolloutCandidate",
    "SequenceLosses",
    "action_smoothness",
    "compose_training_loss",
    "coverage_index",
    "evaluate_candidate",
    "hinge_transform",
    "normalized_constraint_violations",
    "run_closed_loop_expansion",
    "sample_scene_state",
    "sequence_regularization_numpy",
    "sequence_regularization_torch",
    "success_rate",
    "wilson_ci",
    "write_provenance",
]
