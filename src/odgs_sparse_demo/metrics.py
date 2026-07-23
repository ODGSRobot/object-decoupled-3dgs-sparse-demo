from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

import numpy as np


def success_rate(successes: int, trials: int) -> float:
    """Return success rate in percent."""
    if trials <= 0:
        raise ValueError("trials must be positive")
    if successes < 0 or successes > trials:
        raise ValueError("successes must be in [0, trials]")
    return 100.0 * successes / trials


def wilson_ci(successes: int, trials: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score confidence interval for a binomial proportion, returned in percent."""
    if trials <= 0:
        raise ValueError("trials must be positive")
    if successes < 0 or successes > trials:
        raise ValueError("successes must be in [0, trials]")
    p = successes / trials
    denom = 1.0 + z * z / trials
    center = (p + z * z / (2 * trials)) / denom
    half = z * math.sqrt((p * (1.0 - p) + z * z / (4 * trials)) / trials) / denom
    return 100.0 * max(0.0, center - half), 100.0 * min(1.0, center + half)


def action_smoothness(actions: Sequence[Sequence[float]] | np.ndarray) -> float:
    """Temporal mean squared Euclidean norm of second-order action differences."""
    arr = np.asarray(actions, dtype=float)
    if arr.ndim != 2:
        raise ValueError("actions must have shape [time, action_dim]")
    if arr.shape[0] < 3:
        return 0.0
    second_diff = arr[2:] - 2.0 * arr[1:-1] + arr[:-2]
    return float(np.mean(np.sum(second_diff * second_diff, axis=1)))


def mean_std(values: Iterable[float]) -> tuple[float, float]:
    arr = np.asarray(list(values), dtype=float)
    if arr.size == 0:
        raise ValueError("values must be non-empty")
    if arr.size == 1:
        return float(arr[0]), 0.0
    return float(np.mean(arr)), float(np.std(arr, ddof=1))


def rollout_rates(accepted: int, candidates: int) -> tuple[float, float]:
    """Return acceptance and total rejection rates as percentages."""
    if candidates <= 0:
        raise ValueError("candidates must be positive")
    if accepted < 0 or accepted > candidates:
        raise ValueError("accepted must be in [0, candidates]")
    acceptance = 100.0 * accepted / candidates
    return acceptance, 100.0 - acceptance
