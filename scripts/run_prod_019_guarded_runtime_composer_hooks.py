#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from prod_019_guarded_runtime_composer_hooks import (
    DEFAULT_CAMPAIGN_CASE_SOURCE,
    DEFAULT_PROD_015_RESULT,
    DEFAULT_PROD_018_RESULT,
    DEFAULT_REPORT,
    DEFAULT_RESULT,
    DEFAULT_RETRIEVAL_REGISTRY,
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
        raise ValueError(f"PROD-019 path must stay inside project root: {path_text}") from exc
    if _contains_private_path_parts(resolved):
        raise ValueError(f"PROD-019 path is restricted: {path_text}")
    if not allow_missing and not resolved.exists():
        raise FileNotFoundError(resolved)
    return resolved


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the PROD-019 opt-in guarded runtime composer-hook checkpoint.")
    parser.add_argument("--prod-015-result", default=str(DEFAULT_PROD_015_RESULT), help="PROD-015 result JSON path.")
    parser.add_argument("--prod-018-result", default=str(DEFAULT_PROD_018_RESULT), help="PROD-018 result JSON path.")
    parser.add_argument("--retrieval-registry", default=str(DEFAULT_RETRIEVAL_REGISTRY), help="RAG-017 runtime registry JSON path.")
    parser.add_argument("--campaign-case-source", default=str(DEFAULT_CAMPAIGN_CASE_SOURCE), help="Campaign case source path.")
    parser.add_argument("--out", default=str(DEFAULT_RESULT), help="Output JSON path.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT), help="Output Markdown report path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    prod_015_result = resolve_path(args.prod_015_result, DEFAULT_PROD_015_RESULT, allow_missing=False)
    prod_018_result = resolve_path(args.prod_018_result, DEFAULT_PROD_018_RESULT)
    retrieval_registry = resolve_path(args.retrieval_registry, DEFAULT_RETRIEVAL_REGISTRY, allow_missing=False)
    campaign_case_source = resolve_path(args.campaign_case_source, DEFAULT_CAMPAIGN_CASE_SOURCE, allow_missing=False)
    out_path = resolve_path(args.out, DEFAULT_RESULT)
    report_path = resolve_path(args.report_out, DEFAULT_REPORT)

    payload = build_payload(
        prod_015_result,
        prod_018_result_path=prod_018_result,
        registry_path=retrieval_registry,
        campaign_case_source=campaign_case_source,
    )
    write_json(out_path, payload)
    write_text(report_path, render_report(payload))
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
