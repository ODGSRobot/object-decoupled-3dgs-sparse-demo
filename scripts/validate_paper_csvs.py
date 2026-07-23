from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from odgs_sparse_demo.schemas import validate_directory  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate paper-facing CSV schemas, denominators, and task scope."
    )
    parser.add_argument("--data", type=Path, default=Path("examples/real_data"))
    args = parser.parse_args()

    report = validate_directory(args.data)
    if report:
        for filename, errors in report.items():
            for error in errors:
                print(f"[ERROR] {filename}: {error}")
        raise SystemExit(1)
    print(f"OK: schemas, rollout denominators, and task scope are valid in {args.data}")


if __name__ == "__main__":
    main()
