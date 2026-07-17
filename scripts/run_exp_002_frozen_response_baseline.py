#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.exp_002_frozen_response_baseline import (
    build_frozen_baseline_result,
    render_frozen_baseline_report,
)

OUTPUT_DIR = ROOT / "research" / "experiments" / "generated" / "EXP-002-frozen-response-baseline"
RESULT = OUTPUT_DIR / "result.json"
REPORT = OUTPUT_DIR / "report.md"


def main() -> int:
    payload = build_frozen_baseline_result(ROOT)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    REPORT.write_text(render_frozen_baseline_report(payload), encoding="utf-8", newline="\n")
    print(json.dumps(payload["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
