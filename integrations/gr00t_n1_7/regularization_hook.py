"""Minimal GR00T N1.7 action-head hook for the training-only objective."""

from __future__ import annotations

from typing import Any

from odgs_sparse_demo.regularization import compose_training_loss, sequence_regularization_torch


def apply_training_regularization(
    flow_matching_loss: Any,
    pred_velocity: Any,
    noisy_trajectory: Any,
    time: Any,
    action_mask: Any,
    temporal_weight: float = 0.05,
    velocity_weight: float = 0.02,
) -> tuple[Any, dict[str, Any]]:
    """Return the combined loss and separately loggable training terms."""
    terms = sequence_regularization_torch(
        pred_velocity=pred_velocity,
        noisy_trajectory=noisy_trajectory,
        time=time,
        action_mask=action_mask,
    )
    total = compose_training_loss(
        flow_matching_loss=flow_matching_loss,
        sequence_losses=terms,
        temporal_weight=temporal_weight,
        velocity_weight=velocity_weight,
    )
    return total, {
        "flow_matching_loss": flow_matching_loss,
        "temporal_consistency_loss": terms.temporal_consistency,
        "velocity_smoothness_loss": terms.velocity_smoothness,
        "loss": total,
    }
