from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

StructureType = Literal["rigid", "hinge"]


@dataclass(frozen=True)
class HingeModel:
    axis: tuple[float, float, float]
    center_m: tuple[float, float, float]
    lower_deg: float
    upper_deg: float

    def __post_init__(self) -> None:
        if self.lower_deg >= self.upper_deg:
            raise ValueError("hinge lower limit must be smaller than upper limit")
        _unit_vector(np.asarray(self.axis, dtype=float))


@dataclass(frozen=True)
class RandomizationRanges:
    robot_xy_m: tuple[float, float] = (-0.03, 0.03)
    object_xy_m: tuple[float, float] = (-0.03, 0.03)
    object_yaw_deg: tuple[float, float] = (-10.0, 10.0)
    target_xy_m: tuple[float, float] = (-0.03, 0.03)
    hinge_boundary_margin_deg: float = 2.0


@dataclass(frozen=True)
class SampledSceneState:
    structure_type: StructureType
    robot_xy_offset_m: tuple[float, float]
    object_xy_offset_m: tuple[float, float]
    object_yaw_offset_deg: float
    target_xy_offset_m: tuple[float, float]
    hinge_angle_deg: float | None

    def as_dict(self) -> dict[str, float | str | None]:
        return {
            "structure_type": self.structure_type,
            "robot_x_offset_m": self.robot_xy_offset_m[0],
            "robot_y_offset_m": self.robot_xy_offset_m[1],
            "object_x_offset_m": self.object_xy_offset_m[0],
            "object_y_offset_m": self.object_xy_offset_m[1],
            "object_yaw_offset_deg": self.object_yaw_offset_deg,
            "target_x_offset_m": self.target_xy_offset_m[0],
            "target_y_offset_m": self.target_xy_offset_m[1],
            "hinge_angle_deg": self.hinge_angle_deg,
        }


def hinge_transform(model: HingeModel, angle_deg: float) -> np.ndarray:
    """Return a 4x4 transform for rotation about an arbitrary hinge axis."""
    if angle_deg < model.lower_deg or angle_deg > model.upper_deg:
        raise ValueError("angle lies outside the annotated hinge range")
    axis = _unit_vector(np.asarray(model.axis, dtype=float))
    center = np.asarray(model.center_m, dtype=float)
    angle = np.deg2rad(float(angle_deg))

    cross = np.array(
        [[0.0, -axis[2], axis[1]], [axis[2], 0.0, -axis[0]], [-axis[1], axis[0], 0.0]]
    )
    rotation = np.eye(3) + np.sin(angle) * cross + (1.0 - np.cos(angle)) * (cross @ cross)
    transform = np.eye(4)
    transform[:3, :3] = rotation
    transform[:3, 3] = center - rotation @ center
    return transform


def sample_scene_state(
    rng: np.random.Generator,
    structure_type: StructureType,
    ranges: RandomizationRanges | None = None,
    hinge: HingeModel | None = None,
) -> SampledSceneState:
    """Sample one rigid or hinged state from the configured low-dimensional domain."""
    if ranges is None:
        ranges = RandomizationRanges()
    if structure_type == "hinge" and hinge is None:
        raise ValueError("hinge metadata is required for a hinged object")
    if structure_type == "rigid" and hinge is not None:
        raise ValueError("rigid objects must not carry hinge metadata")

    def pair(bounds: tuple[float, float]) -> tuple[float, float]:
        return tuple(float(value) for value in rng.uniform(bounds[0], bounds[1], size=2))

    angle = None
    if hinge is not None:
        low = hinge.lower_deg + ranges.hinge_boundary_margin_deg
        high = hinge.upper_deg - ranges.hinge_boundary_margin_deg
        if low >= high:
            raise ValueError("hinge margin leaves no sampleable angle range")
        angle = float(rng.uniform(low, high))

    return SampledSceneState(
        structure_type=structure_type,
        robot_xy_offset_m=pair(ranges.robot_xy_m),
        object_xy_offset_m=pair(ranges.object_xy_m),
        object_yaw_offset_deg=float(rng.uniform(*ranges.object_yaw_deg)),
        target_xy_offset_m=pair(ranges.target_xy_m),
        hinge_angle_deg=angle,
    )


def normalized_bin(value: float, bounds: tuple[float, float], bins: int = 5) -> int:
    """Map a sampled scalar to one of the fixed coverage bins."""
    low, high = bounds
    if bins <= 0 or low >= high:
        raise ValueError("invalid bin configuration")
    if value < low or value > high:
        raise ValueError("value lies outside the configured randomization interval")
    normalized = (value - low) / (high - low)
    return min(int(np.floor(normalized * bins)), bins - 1)


def _unit_vector(vector: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if norm <= 1e-12:
        raise ValueError("axis length must be positive")
    return vector / norm
