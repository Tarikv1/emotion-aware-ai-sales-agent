#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "voice-029-local-speech-profile-learning.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create the ignored local personal speech-learning workspace without reading private content."
    )
    parser.add_argument("--case", default=str(CASE_PATH), help="VOICE-029 case/config JSON.")
    parser.add_argument("--dry-run", action="store_true", help="Preview folders without creating them.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    case_path = Path(args.case)
    if not case_path.is_absolute():
        case_path = ROOT / case_path
    case = json.loads(case_path.read_text(encoding="utf-8"))
    workspace = case["private_workspace"]
    private_root = ROOT / workspace["private_root"]
    subdirs = [private_root / relative for relative in workspace["required_private_subdirs"]]

    print("Personal speech learning workspace")
    print(f"Root: {private_root}")
    print(f"Dry run: {str(args.dry_run).lower()}")
    print("Raw/private contents read: false")
    print()
    for path in subdirs:
        if args.dry_run:
            print(f"would create: {path}")
        else:
            path.mkdir(parents=True, exist_ok=True)
            print(f"exists: {path}")


if __name__ == "__main__":
    main()
