#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CURRENT_VALIDATOR = ROOT / "scripts" / "validate_elevenlabs_037_confident_capability_control.py"


def main() -> None:
    completed = subprocess.run(
        [sys.executable, str(CURRENT_VALIDATOR)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)
    print(
        json.dumps(
            {
                "status": "deprecated-wrapper",
                "deprecated_checkpoint_id": "ELEVENLABS-037-custom-capability-scope-confidence",
                "current_checkpoint_id": "ELEVENLABS-037-confident-capability-control",
                "message": "This validator is deprecated; the current 037 contract is validate_elevenlabs_037_confident_capability_control.py.",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
