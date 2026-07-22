from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .metrics import wilson_ci


METHOD_ORDER = (
    "Sparse-only",
    "Random-Aug",
    "Scene-Aug w/o structure",
    "Ours",
)
METHOD_LABELS = {
    "Sparse-only": "Sparse only",
    "Random-Aug": "Random augmentation",
    "Scene-Aug w/o structure": "Scene augmentation without structure",
    "Ours": "Complete framework",
}
METHOD_COLORS = {
    "Sparse-only": "#6b7280",
    "Random-Aug": "#d97706",
    "Scene-Aug w/o structure": "#2563eb",
    "Ours": "#047857",
}
TASK_ORDER = ("Pick-place", "Microwave door", "Multi-step retrieval")


@dataclass(frozen=True)
class PlotSpec:
    metric: str
    ylabel: str
    direction: str
    output_stem: str


PLOT_SPECS = {
    "success": PlotSpec("success", "Task success (%)", "higher", "task_success_iterations"),
    "acceptance": PlotSpec(
        "acceptance", "Accepted rollouts (%)", "higher", "rollout_acceptance_iterations"
    ),
    "smoothness": PlotSpec(
        "smoothness", "Second-order action curvature", "lower", "action_curvature_iterations"
    ),
}


def plot_iteration_result(data_csv: Path, metric: str, output: Path) -> Path:
    """Draw one three-task figure for a single closed-loop result metric."""
    if metric not in PLOT_SPECS:
        raise ValueError(f"metric must be one of {sorted(PLOT_SPECS)}")
    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError("install the 'figures' extra to draw manuscript plots") from exc

    frame = pd.read_csv(data_csv)
    prepared = _aggregate(frame, metric)
    spec = PLOT_SPECS[metric]

    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "font.size": 9.5,
            "axes.linewidth": 0.8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    fig, axes = plt.subplots(1, 3, figsize=(10.6, 3.15), sharey=True)
    handles = []
    labels = []
    for axis, task in zip(axes, TASK_ORDER, strict=True):
        task_rows = prepared[prepared["task"] == task]
        for method in METHOD_ORDER:
            rows = task_rows[task_rows["method"] == method].sort_values("round")
            if rows.empty:
                continue
            handle = axis.plot(
                rows["round"],
                rows["value"],
                color=METHOD_COLORS[method],
                marker="o",
                markersize=3.4,
                linewidth=1.75,
                label=METHOD_LABELS[method],
            )[0]
            axis.fill_between(
                rows["round"].to_numpy(dtype=float),
                rows["lower"].to_numpy(dtype=float),
                rows["upper"].to_numpy(dtype=float),
                color=METHOD_COLORS[method],
                alpha=0.12,
                linewidth=0,
            )
            if method not in labels:
                handles.append(handle)
                labels.append(method)
        axis.set_title(task, fontsize=10.2, pad=7)
        axis.set_xlabel("Iteration round")
        axis.set_xticks(sorted(task_rows["round"].dropna().unique()))
        axis.grid(axis="y", color="#d1d5db", linewidth=0.65, alpha=0.8)
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
    axes[0].set_ylabel(spec.ylabel)
    if handles:
        ordered_handles = [
            handles[labels.index(method)] for method in METHOD_ORDER if method in labels
        ]
        ordered_labels = [METHOD_LABELS[method] for method in METHOD_ORDER if method in labels]
        fig.legend(
            ordered_handles,
            ordered_labels,
            loc="upper center",
            ncol=len(ordered_labels),
            frameon=False,
            bbox_to_anchor=(0.5, 1.02),
            fontsize=8.3,
        )
    fig.tight_layout(rect=(0.02, 0.0, 1.0, 0.89), w_pad=1.25)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)
    return output


def plot_all_iteration_results(data_csv: Path, output_dir: Path) -> tuple[Path, ...]:
    outputs: list[Path] = []
    for metric, spec in PLOT_SPECS.items():
        for suffix in (".pdf", ".svg"):
            outputs.append(
                plot_iteration_result(data_csv, metric, output_dir / f"{spec.output_stem}{suffix}")
            )
    return tuple(outputs)


def _aggregate(frame: pd.DataFrame, metric: str) -> pd.DataFrame:
    required = {"task", "method", "round", "seed"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"iteration data are missing columns {missing}")
    rows: list[dict[str, float | int | str]] = []
    for (task, method, round_index), group in frame.groupby(["task", "method", "round"]):
        if metric == "success":
            successes = int(pd.to_numeric(group["success_trials"]).sum())
            trials = int(pd.to_numeric(group["total_trials"]).sum())
            if trials <= 0:
                continue
            lower, upper = wilson_ci(successes, trials)
            value = 100.0 * successes / trials
        elif metric == "acceptance":
            candidates = int(pd.to_numeric(group["candidate_rollouts"]).sum())
            accepted = int(pd.to_numeric(group["accepted_rollouts"]).sum())
            if candidates <= 0:
                continue
            lower, upper = wilson_ci(accepted, candidates)
            value = 100.0 * accepted / candidates
        else:
            values = pd.to_numeric(group["action_smoothness"], errors="coerce").dropna().to_numpy()
            if not len(values):
                continue
            value = float(np.mean(values))
            if len(values) == 1:
                lower = upper = value
            else:
                critical = _t_critical_95(len(values) - 1)
                half = critical * float(np.std(values, ddof=1)) / math.sqrt(len(values))
                lower, upper = value - half, value + half
        rows.append(
            {
                "task": str(task),
                "method": str(method),
                "round": int(round_index),
                "value": value,
                "lower": lower,
                "upper": upper,
            }
        )
    return pd.DataFrame(rows)


def _t_critical_95(degrees_of_freedom: int) -> float:
    values = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447}
    return values.get(degrees_of_freedom, 1.96 if degrees_of_freedom >= 30 else 2.262)
