from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class CsvSchema:
    name: str
    required_columns: tuple[str, ...]

    def validate(self, path: Path) -> list[str]:
        if not path.exists():
            return [f"missing file {path}"]
        frame = pd.read_csv(path)
        errors: list[str] = []
        columns = {str(column).strip() for column in frame.columns}
        missing = [column for column in self.required_columns if column not in columns]
        if missing:
            errors.append(f"missing columns {missing}")
        if frame.empty:
            errors.append("file is empty")
        return errors


SCHEMAS = (
    CsvSchema(
        "iteration_results_long.csv",
        (
            "task",
            "method",
            "round",
            "seed",
            "candidate_rollouts",
            "accepted_rollouts",
            "rejected_rollouts",
            "acceptance_rate",
            "total_reject_rate",
            "success_trials",
            "total_trials",
            "action_smoothness",
        ),
    ),
    CsvSchema(
        "iteration_results_summary.csv",
        (
            "task",
            "method",
            "round",
            "seed_count",
            "candidate_rollouts",
            "accepted_rollouts",
            "rejected_rollouts",
            "acceptance_rate_pct",
            "total_rejection_rate_pct",
            "success_trials",
            "total_trials",
            "incremental_success_rate_pct",
        ),
    ),
    CsvSchema(
        "rollout_rejection_diagnostics.csv",
        (
            "task",
            "method",
            "round",
            "candidate_rollouts",
            "accepted_rollouts",
            "rejected_rollouts",
            "acceptance_rate_pct",
            "total_rejection_rate_pct",
        ),
    ),
    CsvSchema(
        "real_robot_trials.csv",
        ("task", "method", "demo_count", "seed", "trial_id", "success", "failure_type"),
    ),
    CsvSchema(
        "table2_3dgs_scene_metrics.csv",
        ("scene", "seed_count", "holdout_views", "psnr_mean", "ssim_mean", "lpips_mean"),
    ),
    CsvSchema(
        "table3_structure_parameter_metrics.csv",
        ("object_part", "axis_error_deg_mean", "center_error_m_mean", "angle_error_deg_mean"),
    ),
    CsvSchema(
        "table4_feasibility_projection_alpha.csv",
        (
            "candidate_rollouts",
            "seed_count",
            "accepted_rollouts",
            "rejected_rollouts",
            "acceptance_rate_mean_pct",
            "total_rejection_rate_mean_pct",
            "coverage_index_mean",
            "success_trials",
            "total_trials",
            "incremental_success_rate_pct",
        ),
    ),
    CsvSchema(
        "table5_real_robot_trial_summary.csv",
        ("task", "method", "seed_count", "trial_count", "success_count", "success_rate_pct"),
    ),
    CsvSchema(
        "table6_ablation_statistics.csv",
        (
            "ablation_config",
            "success_rate_macro_pct",
            "success_delta",
            "smoothness_delta",
            "task_count",
            "seed_count",
            "task_seed_units",
            "ci95",
            "p_value",
            "test",
            "drawer_excluded",
            "aggregation",
        ),
    ),
)


def validate_directory(data_dir: Path) -> dict[str, list[str]]:
    report: dict[str, list[str]] = {}
    for schema in SCHEMAS:
        errors = schema.validate(data_dir / schema.name)
        if errors:
            report[schema.name] = errors

    long_path = data_dir / "iteration_results_long.csv"
    if long_path.exists():
        frame = pd.read_csv(long_path)
        _validate_rollout_counts(
            frame,
            long_path.name,
            report,
            acceptance_column="acceptance_rate",
            rejection_column="total_reject_rate",
            scale=1.0,
            tolerance=1e-6,
        )

    for filename in (
        "iteration_results_summary.csv",
        "rollout_rejection_diagnostics.csv",
    ):
        path = data_dir / filename
        if path.exists():
            _validate_rollout_counts(
                pd.read_csv(path),
                filename,
                report,
                acceptance_column="acceptance_rate_pct",
                rejection_column="total_rejection_rate_pct",
                scale=100.0,
                tolerance=0.051,
            )

    intensity_path = data_dir / "table4_feasibility_projection_alpha.csv"
    if intensity_path.exists():
        _validate_rollout_counts(
            pd.read_csv(intensity_path),
            intensity_path.name,
            report,
            acceptance_column="acceptance_rate_mean_pct",
            rejection_column="total_rejection_rate_mean_pct",
            scale=100.0,
            tolerance=0.051,
        )

    for filename in ("real_robot_trials.csv", "table5_real_robot_trial_summary.csv"):
        path = data_dir / filename
        if path.exists():
            frame = pd.read_csv(path)
            if "task" in frame:
                forbidden = (
                    frame["task"].astype(str).str.contains("drawer|抽屉", case=False, regex=True)
                )
                if bool(forbidden.any()):
                    report.setdefault(filename, []).append(
                        "drawer task is outside the current manuscript evaluation scope"
                    )
    return report


def _validate_rollout_counts(
    frame: pd.DataFrame,
    filename: str,
    report: dict[str, list[str]],
    acceptance_column: str,
    rejection_column: str,
    scale: float,
    tolerance: float,
) -> None:
    required = {
        "candidate_rollouts",
        "accepted_rollouts",
        "rejected_rollouts",
        acceptance_column,
        rejection_column,
    }
    if not required.issubset(frame.columns):
        return
    candidates = pd.to_numeric(frame["candidate_rollouts"], errors="coerce")
    accepted = pd.to_numeric(frame["accepted_rollouts"], errors="coerce")
    rejected = pd.to_numeric(frame["rejected_rollouts"], errors="coerce")
    acceptance = pd.to_numeric(frame[acceptance_column], errors="coerce")
    rejection = pd.to_numeric(frame[rejection_column], errors="coerce")
    invalid_counts = (
        candidates.isna()
        | accepted.isna()
        | rejected.isna()
        | (candidates < 0)
        | (accepted < 0)
        | (accepted > candidates)
        | (rejected != candidates - accepted)
    )
    positive = candidates > 0
    invalid_rates = positive & (
        ((acceptance - scale * accepted / candidates).abs() > tolerance)
        | ((rejection - scale * rejected / candidates).abs() > tolerance)
        | ((acceptance + rejection - scale).abs() > tolerance)
    )
    if bool(invalid_counts.any()):
        report.setdefault(filename, []).append("rollout counts are internally inconsistent")
    if bool(invalid_rates.any()):
        report.setdefault(filename, []).append("rollout rates do not match integer counts")
