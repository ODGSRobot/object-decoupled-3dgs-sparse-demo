from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_path(path: Path) -> str:
    if path.is_file():
        return sha256_file(path)
    if not path.is_dir():
        raise FileNotFoundError(path)
    digest = hashlib.sha256()
    for item in sorted(candidate for candidate in path.rglob("*") if candidate.is_file()):
        digest.update(item.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256_file(item).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def gpu_record() -> dict[str, str]:
    command = [
        "nvidia-smi",
        "--query-gpu=name,memory.total,driver_version",
        "--format=csv,noheader,nounits",
    ]
    try:
        line = subprocess.check_output(
            command, text=True, stderr=subprocess.STDOUT
        ).splitlines()[0]
        name, memory, driver = [part.strip() for part in line.split(",", 2)]
        return {"gpu_name": name, "gpu_memory_mib": memory, "driver_version": driver}
    except (FileNotFoundError, subprocess.CalledProcessError, IndexError, ValueError):
        return {
            "gpu_name": "unavailable",
            "gpu_memory_mib": "unavailable",
            "driver_version": "unavailable",
        }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Record immutable checkpoint, timing, hardware, and source hashes."
    )
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--source-tree", type=Path, required=True)
    parser.add_argument("--started-at", required=True, help="ISO-8601 timestamp")
    parser.add_argument("--finished-at", required=True, help="ISO-8601 timestamp")
    parser.add_argument("--training-command", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    started = parse_time(args.started_at)
    finished = parse_time(args.finished_at)
    if finished < started:
        raise ValueError("finished-at precedes started-at")

    manifest = {
        "resolved_training_command": args.training_command,
        "start_time_utc": started.isoformat().replace("+00:00", "Z"),
        "end_time_utc": finished.isoformat().replace("+00:00", "Z"),
        "wall_clock_seconds": (finished - started).total_seconds(),
        "final_checkpoint_path": str(args.checkpoint.resolve()),
        "final_checkpoint_sha256": sha256_path(args.checkpoint),
        "source_tree_path": str(args.source_tree.resolve()),
        "source_tree_sha256": sha256_path(args.source_tree),
        "host_operating_system": platform.platform(),
        "python_version": platform.python_version(),
        **gpu_record(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
