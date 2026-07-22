from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from odgs_sparse_demo.figures import PLOT_SPECS, plot_all_iteration_results, plot_iteration_result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Draw separate success, rollout-acceptance, and action-curvature figures."
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("examples/real_data/iteration_results_long.csv"),
    )
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/iteration_figures"))
    parser.add_argument("--metric", choices=["all", *PLOT_SPECS], default="all")
    parser.add_argument("--format", choices=["pdf", "svg", "png"], default="pdf")
    args = parser.parse_args()

    if args.metric == "all" and args.format in {"pdf", "svg"}:
        outputs = plot_all_iteration_results(args.data, args.output_dir)
    elif args.metric == "all":
        outputs = tuple(
            plot_iteration_result(
                args.data,
                metric,
                args.output_dir / f"{spec.output_stem}.{args.format}",
            )
            for metric, spec in PLOT_SPECS.items()
        )
    else:
        spec = PLOT_SPECS[args.metric]
        outputs = (
            plot_iteration_result(
                args.data,
                args.metric,
                args.output_dir / f"{spec.output_stem}.{args.format}",
            ),
        )
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
