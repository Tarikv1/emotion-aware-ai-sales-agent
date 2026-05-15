#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from runtime.policy.core_sales_delivery_playbook import (
    build_core_sales_delivery_pack,
    render_core_sales_delivery_pack_report,
    validate_core_sales_delivery_pack,
)


DEFAULT_OUTPUT_DIR = ROOT / "research" / "experiments" / "generated" / "CORE-sales-delivery-playbook"
DEFAULT_RESULT = DEFAULT_OUTPUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUTPUT_DIR / "report.md"


def resolve_project_path(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else ROOT / path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the core sales and delivery playbook.")
    parser.add_argument("--out", default=str(DEFAULT_RESULT))
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_core_sales_delivery_pack()
    errors = validate_core_sales_delivery_pack(payload)
    if errors:
        raise SystemExit("; ".join(errors))
    out = resolve_project_path(args.out)
    report = resolve_project_path(args.report_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report.write_text(render_core_sales_delivery_pack_report(payload), encoding="utf-8")
    print(json.dumps({"core_pack_id": payload["core_pack_id"], "validation_passed": True}, indent=2))


if __name__ == "__main__":
    main()
