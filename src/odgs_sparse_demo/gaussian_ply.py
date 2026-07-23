from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

PLY_DTYPE_MAP = {
    "char": "i1",
    "uchar": "u1",
    "short": "<i2",
    "ushort": "<u2",
    "int": "<i4",
    "uint": "<u4",
    "float": "<f4",
    "double": "<f8",
}
PLY_TYPE_BY_DTYPE = {
    "int8": "char",
    "uint8": "uchar",
    "int16": "short",
    "uint16": "ushort",
    "int32": "int",
    "uint32": "uint",
    "float32": "float",
    "float64": "double",
}


@dataclass(frozen=True)
class HingeSplitMetadata:
    source_ply: str
    negative_ply: str
    positive_ply: str
    plane_point: tuple[float, float, float]
    plane_normal: tuple[float, float, float]
    hinge_center: tuple[float, float, float]
    hinge_axis: tuple[float, float, float]
    overlap_width: float
    negative_count: int
    positive_count: int


def read_gaussian_ply(path: Path) -> np.ndarray:
    """Read a binary little-endian vertex-only Gaussian PLY."""
    raw = path.read_bytes()
    marker = b"end_header"
    marker_index = raw.find(marker)
    if marker_index < 0:
        raise ValueError(f"{path} is missing a PLY header")
    header_end = marker_index + len(marker)
    if raw[header_end : header_end + 2] == b"\r\n":
        data_start = header_end + 2
    elif raw[header_end : header_end + 1] == b"\n":
        data_start = header_end + 1
    else:
        data_start = header_end

    lines = raw[:data_start].decode("ascii", errors="strict").splitlines()
    if not lines or lines[0].strip() != "ply":
        raise ValueError(f"{path} is not a PLY file")
    vertex_count: int | None = None
    properties: list[tuple[str, str]] = []
    current_element = ""
    file_format = ""
    for line in lines[1:]:
        parts = line.strip().split()
        if not parts:
            continue
        if parts[0] == "format":
            file_format = parts[1]
        elif parts[0] == "element":
            current_element = parts[1]
            if current_element == "vertex":
                vertex_count = int(parts[2])
        elif parts[0] == "property" and current_element == "vertex":
            if parts[1] == "list":
                raise ValueError("list-valued vertex properties are unsupported")
            if parts[1] not in PLY_DTYPE_MAP:
                raise ValueError(f"unsupported PLY type {parts[1]!r}")
            properties.append((parts[2], PLY_DTYPE_MAP[parts[1]]))

    if file_format != "binary_little_endian":
        raise ValueError("only binary_little_endian Gaussian PLY files are supported")
    if vertex_count is None or not properties:
        raise ValueError("PLY vertex element or properties are missing")
    dtype = np.dtype(properties)
    expected = dtype.itemsize * vertex_count
    payload = raw[data_start : data_start + expected]
    if len(payload) != expected:
        raise ValueError("PLY vertex payload is truncated")
    vertices = np.frombuffer(payload, dtype=dtype, count=vertex_count).copy()
    _require_fields(vertices.dtype.names or (), ("x", "y", "z"))
    return vertices


def write_gaussian_ply(path: Path, vertices: np.ndarray, comment: str = "OD3GS asset") -> None:
    """Write all structured vertex properties without flattening 3DGS attributes."""
    if vertices.dtype.names is None:
        raise ValueError("vertices must be a structured NumPy array")
    lines = [
        "ply",
        "format binary_little_endian 1.0",
        f"comment {comment}",
        f"element vertex {len(vertices)}",
    ]
    for name in vertices.dtype.names:
        dtype_name = np.dtype(vertices.dtype[name]).name
        if dtype_name not in PLY_TYPE_BY_DTYPE:
            raise ValueError(f"unsupported dtype {dtype_name!r} for field {name!r}")
        lines.append(f"property {PLY_TYPE_BY_DTYPE[dtype_name]} {name}")
    lines.append("end_header")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        handle.write(("\n".join(lines) + "\n").encode("ascii"))
        handle.write(np.ascontiguousarray(vertices).tobytes())


def crop_gaussian_ply(
    input_path: Path,
    output_path: Path,
    lower_xyz: tuple[float, float, float] | None = None,
    upper_xyz: tuple[float, float, float] | None = None,
    min_opacity: float | None = None,
) -> int:
    """Crop a Gaussian PLY while preserving every vertex attribute."""
    vertices = read_gaussian_ply(input_path)
    points = _points(vertices)
    keep = np.isfinite(points).all(axis=1)
    if lower_xyz is not None:
        keep &= (points >= np.asarray(lower_xyz, dtype=float)).all(axis=1)
    if upper_xyz is not None:
        keep &= (points <= np.asarray(upper_xyz, dtype=float)).all(axis=1)
    if min_opacity is not None:
        _require_fields(vertices.dtype.names or (), ("opacity",))
        opacity = 1.0 / (1.0 + np.exp(-vertices["opacity"].astype(float)))
        keep &= opacity >= min_opacity
    selected = vertices[keep]
    write_gaussian_ply(output_path, selected, "cropped by odgs_sparse_demo")
    return len(selected)


def split_hinged_gaussian_ply(
    input_path: Path,
    negative_path: Path,
    positive_path: Path,
    plane_point: Iterable[float],
    plane_normal: Iterable[float],
    hinge_center: Iterable[float],
    hinge_axis: Iterable[float],
    overlap_width: float = 0.0,
    metadata_path: Path | None = None,
) -> HingeSplitMetadata:
    """Split one Gaussian asset into two hinge parts in a shared frame."""
    if overlap_width < 0.0:
        raise ValueError("overlap_width must be nonnegative")
    vertices = read_gaussian_ply(input_path)
    point = _vec3(plane_point, "plane_point")
    normal = _unit(_vec3(plane_normal, "plane_normal"))
    center = _vec3(hinge_center, "hinge_center")
    axis = _unit(_vec3(hinge_axis, "hinge_axis"))
    signed_distance = (_points(vertices) - point[None, :]) @ normal
    negative = vertices[signed_distance <= overlap_width]
    positive = vertices[signed_distance >= -overlap_width]
    write_gaussian_ply(negative_path, negative, "negative hinge part")
    write_gaussian_ply(positive_path, positive, "positive hinge part")

    metadata = HingeSplitMetadata(
        source_ply=str(input_path),
        negative_ply=str(negative_path),
        positive_ply=str(positive_path),
        plane_point=tuple(float(value) for value in point),
        plane_normal=tuple(float(value) for value in normal),
        hinge_center=tuple(float(value) for value in center),
        hinge_axis=tuple(float(value) for value in axis),
        overlap_width=float(overlap_width),
        negative_count=len(negative),
        positive_count=len(positive),
    )
    if metadata_path is not None:
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(json.dumps(asdict(metadata), indent=2), encoding="utf-8")
    return metadata


def _points(vertices: np.ndarray) -> np.ndarray:
    return np.column_stack((vertices["x"], vertices["y"], vertices["z"])).astype(float)


def _vec3(values: Iterable[float], name: str) -> np.ndarray:
    vector = np.asarray(tuple(values), dtype=float)
    if vector.shape != (3,) or not np.isfinite(vector).all():
        raise ValueError(f"{name} must contain three finite values")
    return vector


def _unit(vector: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if norm <= 1e-12:
        raise ValueError("vector length must be positive")
    return vector / norm


def _require_fields(names: Iterable[str], required: Iterable[str]) -> None:
    missing = sorted(set(required) - set(names))
    if missing:
        raise ValueError(f"Gaussian PLY is missing fields {missing}")
