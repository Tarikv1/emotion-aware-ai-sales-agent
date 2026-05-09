#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from prod_022_prod_021_review_gap_packet import (
    DEFAULT_REPORT,
    DEFAULT_RESULT,
    DEFAULT_SOURCE_RESULT,
    ROOT,
    build_payload,
    render_report,
    write_json,
    write_text,
)


PRIVATE_PATH_PARTS = (("data", "private"), ("data", "private-restricted"))


def _contains_private_path_parts(path: Path) -> bool:
    parts = tuple(part.lower() for part in path.parts)
    for private_parts in PRIVATE_PATH_PARTS:
        for index in range(0, len(parts) - len(private_parts) + 1):
            if parts[index : index + len(private_parts)] == private_parts:
                return True
    return False


def resolve_path(path_text: str | None, default: Path, *, allow_missing: bool = True) -> Path:
    path = Path(path_text) if path_text else default
    candidate = path if path.is_absolute() else ROOT / path
    resolved = candidate.resolve(strict=False)
    root = ROOT.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"PROD-022 path must stay inside project root: {path_text}") from exc
    if _contains_private_path_parts(resolved):
        raise ValueError(f"PROD-022 path is restricted: {path_text}")
    if not allow_missing and not resolved.exists():
        raise FileNotFoundError(resolved)
    return resolved


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the PROD-022 PROD-021 review gap packet checkpoint.")
    parser.add_argument("--source-result", default=str(DEFAULT_SOURCE_RESULT), help="PROD-021 result JSON path.")
    parser.add_argument("--out", default=str(DEFAULT_RESULT), help="Output JSON packet path.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT), help="Output Markdown packet path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_result = resolve_path(args.source_result, DEFAULT_SOURCE_RESULT, allow_missing=False)
    out_path = resolve_path(args.out, DEFAULT_RESULT)
    report_path = resolve_path(args.report_out, DEFAULT_REPORT)

    payload = build_payload(source_result)
    write_json(out_path, payload)
    write_text(report_path, render_report(payload))
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
