import unittest
from pathlib import Path
from unittest.mock import patch

from odgs_sparse_demo.feasibility import (
    CRITERION_ORDER,
    ZERO_VIOLATION_THRESHOLDS,
    CandidateMeasurement,
    coverage_index,
    evaluate_candidate,
    normalized_constraint_violations,
    write_provenance,
)


def _measurement(**overrides: float) -> CandidateMeasurement:
    violations = {key: 0.0 for key in CRITERION_ORDER}
    violations.update(overrides)
    return CandidateMeasurement(
        candidate_id="round-1-candidate-7",
        round_index=1,
        seed=3,
        checkpoint="sha256:example",
        source_episode="episode-12",
        sampled_state={"hinge_angle_deg": 35.0},
        violations=violations,
        manual_review_passed=True,
    )


class FeasibilityTest(unittest.TestCase):
    def test_raw_operational_bounds_map_to_zero_violation_decision(self) -> None:
        violations = normalized_constraint_violations(
            {
                "collision_penetration_m": 0.0,
                "workspace_outside_distance_m": 0.0,
                "joint_limit_excess_rad": 0.0,
                "visible_target_fraction": 0.75,
                "hinge_boundary_margin_deg": 3.0,
                "structural_translation_residual_m": 0.004,
                "structural_rotation_residual_deg": 2.0,
                "normalized_action_second_difference": 0.12,
            }
        )
        measurement = _measurement(**violations)
        self.assertTrue(evaluate_candidate(measurement, ZERO_VIOLATION_THRESHOLDS).accepted)

    def test_raw_visibility_bound_is_rejected(self) -> None:
        violations = normalized_constraint_violations(
            {
                "collision_penetration_m": 0.0,
                "workspace_outside_distance_m": 0.0,
                "joint_limit_excess_rad": 0.0,
                "visible_target_fraction": 0.35,
                "hinge_boundary_margin_deg": 3.0,
                "structural_translation_residual_m": 0.004,
                "structural_rotation_residual_deg": 2.0,
                "normalized_action_second_difference": 0.12,
            }
        )
        decision = evaluate_candidate(_measurement(**violations), ZERO_VIOLATION_THRESHOLDS)
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.rejection_reason, "visibility")

    def test_accepts_candidate_when_all_violations_are_within_thresholds(self) -> None:
        thresholds = {key: 0.1 for key in CRITERION_ORDER}
        decision = evaluate_candidate(_measurement(), thresholds)
        self.assertTrue(decision.accepted)
        self.assertEqual(decision.rejection_reason, "")

    def test_manual_review_can_reject_an_automatic_pass(self) -> None:
        base = _measurement()
        measurement = CandidateMeasurement(
            candidate_id=base.candidate_id,
            round_index=base.round_index,
            seed=base.seed,
            checkpoint=base.checkpoint,
            source_episode=base.source_episode,
            sampled_state=base.sampled_state,
            violations=base.violations,
            manual_review_passed=False,
            manual_review_reason="incomplete task stage",
        )
        decision = evaluate_candidate(measurement, ZERO_VIOLATION_THRESHOLDS)
        self.assertFalse(decision.accepted)
        self.assertTrue(decision.automatic_checks_passed)
        self.assertEqual(decision.rejection_reason, "manual_review")

    def test_prismatic_structure_is_outside_scope(self) -> None:
        with self.assertRaises(ValueError):
            normalized_constraint_violations({}, structure_type="prismatic")

    def test_records_first_rejection_reason_under_fixed_precedence(self) -> None:
        thresholds = {key: 0.1 for key in CRITERION_ORDER}
        decision = evaluate_candidate(
            _measurement(collision=0.2, action_smoothness=0.4), thresholds
        )
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.rejection_reason, "collision")

    def test_coverage_and_provenance_serialization(self) -> None:
        value = coverage_index(
            {"robot_start": {"a", "b"}, "hinge_state": {"open"}},
            {"robot_start": 4, "hinge_state": 2},
        )
        self.assertEqual(value, 0.5)

        thresholds = {key: 0.1 for key in CRITERION_ORDER}
        output = Path("outputs") / "rollout_provenance.csv"
        with patch("pandas.DataFrame.to_csv") as to_csv:
            write_provenance(output, [evaluate_candidate(_measurement(), thresholds)])
        to_csv.assert_called_once_with(output, index=False)


if __name__ == "__main__":
    unittest.main()
