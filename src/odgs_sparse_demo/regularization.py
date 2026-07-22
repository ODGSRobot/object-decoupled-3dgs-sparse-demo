from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class SequenceLosses:
    temporal_consistency: Any
    velocity_smoothness: Any


def _validate_shapes(
    pred_velocity: Any,
    noisy_trajectory: Any,
    action_mask: Any,
) -> None:
    if pred_velocity.ndim != 3:
        raise ValueError("pred_velocity must have shape [batch, horizon, action_dim]")
    if noisy_trajectory.shape != pred_velocity.shape:
        raise ValueError("noisy_trajectory must match pred_velocity")
    if action_mask.shape != pred_velocity.shape:
        raise ValueError("action_mask must match pred_velocity")


def sequence_regularization_numpy(
    pred_velocity: np.ndarray,
    noisy_trajectory: np.ndarray,
    time: np.ndarray,
    action_mask: np.ndarray,
) -> SequenceLosses:
    """Reference implementation of the two training-only sequence losses."""
    pred_velocity = np.asarray(pred_velocity, dtype=float)
    noisy_trajectory = np.asarray(noisy_trajectory, dtype=float)
    action_mask = np.asarray(action_mask, dtype=float)
    _validate_shapes(pred_velocity, noisy_trajectory, action_mask)

    time = np.asarray(time, dtype=float)
    if time.ndim == 1:
        time = time[:, None, None]
    if time.shape not in {(pred_velocity.shape[0], 1, 1), (1, 1, 1)}:
        raise ValueError("time must have shape [batch], [batch, 1, 1], or [1, 1, 1]")

    velocity_loss = 0.0
    if pred_velocity.shape[1] > 1:
        delta = pred_velocity[:, 1:] - pred_velocity[:, :-1]
        mask = action_mask[:, 1:] * action_mask[:, :-1]
        velocity_loss = _masked_mean_square_numpy(delta, mask)

    temporal_loss = 0.0
    if pred_velocity.shape[1] > 2:
        clean_estimate = noisy_trajectory + (1.0 - time) * pred_velocity
        curvature = clean_estimate[:, 2:] - 2.0 * clean_estimate[:, 1:-1] + clean_estimate[:, :-2]
        mask = action_mask[:, 2:] * action_mask[:, 1:-1] * action_mask[:, :-2]
        temporal_loss = _masked_mean_square_numpy(curvature, mask)

    return SequenceLosses(temporal_loss, velocity_loss)


def _masked_mean_square_numpy(values: np.ndarray, mask: np.ndarray) -> float:
    denominator = float(mask.sum())
    if denominator <= 0.0:
        return 0.0
    return float((values * values * mask).sum() / denominator)


def sequence_regularization_torch(
    pred_velocity: Any,
    noisy_trajectory: Any,
    time: Any,
    action_mask: Any,
) -> SequenceLosses:
    """PyTorch implementation used by the GR00T N1.7 integration hook.

    Torch is imported lazily so the geometry, screening, and analysis modules
    remain usable in a lightweight CPU-only environment.
    """
    try:
        import torch
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError("install the 'policy' extra to use the Torch hook") from exc

    _validate_shapes(pred_velocity, noisy_trajectory, action_mask)
    if time.ndim == 1:
        time = time[:, None, None]
    if time.shape not in {(pred_velocity.shape[0], 1, 1), (1, 1, 1)}:
        raise ValueError("time must have shape [batch], [batch, 1, 1], or [1, 1, 1]")

    zero = pred_velocity.new_zeros(())
    velocity_loss = zero
    if pred_velocity.shape[1] > 1:
        delta = pred_velocity[:, 1:] - pred_velocity[:, :-1]
        mask = action_mask[:, 1:] * action_mask[:, :-1]
        velocity_loss = (delta.square() * mask).sum() / (mask.sum() + 1e-6)

    temporal_loss = zero
    if pred_velocity.shape[1] > 2:
        clean_estimate = noisy_trajectory + (1.0 - time) * pred_velocity
        curvature = clean_estimate[:, 2:] - 2.0 * clean_estimate[:, 1:-1] + clean_estimate[:, :-2]
        mask = action_mask[:, 2:] * action_mask[:, 1:-1] * action_mask[:, :-2]
        temporal_loss = (curvature.square() * mask).sum() / (mask.sum() + 1e-6)

    if not torch.isfinite(temporal_loss) or not torch.isfinite(velocity_loss):
        raise FloatingPointError("sequence regularization produced a non-finite loss")
    return SequenceLosses(temporal_loss, velocity_loss)


def compose_training_loss(
    flow_matching_loss: Any,
    sequence_losses: SequenceLosses,
    temporal_weight: float,
    velocity_weight: float,
) -> Any:
    """Compose the training objective without changing model inference."""
    if temporal_weight < 0.0 or velocity_weight < 0.0:
        raise ValueError("regularization weights must be nonnegative")
    return (
        flow_matching_loss
        + temporal_weight * sequence_losses.temporal_consistency
        + velocity_weight * sequence_losses.velocity_smoothness
    )
