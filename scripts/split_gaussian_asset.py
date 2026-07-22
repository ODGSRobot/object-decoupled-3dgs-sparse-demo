from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from odgs_sparse_demo.gaussian_ply import split_hinged_gaussian_ply


def vec3(text: str) -> tuple[float, float, float]:
    values = tuple(float(value.strip()) for value in text.split(","))
    if len(values) != 3:
        raise argparse.ArgumentTypeError("expected x,y,z")
    return values


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Split a Gaussian PLY into two hinge parts while preserving all 3DGS fields."
    )
    parser.add_argument("input_ply", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--plane-point", type=vec3, required=True)
    parser.add_argument("--plane-normal", type=vec3, required=True)
    parser.add_argument("--hinge-center", type=vec3, required=True)
    parser.add_argument("--hinge-axis", type=vec3, required=True)
    parser.add_argument("--overlap-width", type=float, default=0.0)
    args = parser.parse_args()

    metadata = split_hinged_gaussian_ply(
        input_path=args.input_ply,
        negative_path=args.output_dir / "part_a.ply",
        positive_path=args.output_dir / "part_b.ply",
        plane_point=args.plane_point,
        plane_normal=args.plane_normal,
        hinge_center=args.hinge_center,
        hinge_axis=args.hinge_axis,
        overlap_width=args.overlap_width,
        metadata_path=args.output_dir / "hinge_split.json",
    )
    print(f"part_a={metadata.negative_count}; part_b={metadata.positive_count}")
    print(args.output_dir / "hinge_split.json")


if __name__ == "__main__":
    main()
