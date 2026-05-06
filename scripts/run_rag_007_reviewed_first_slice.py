#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from rag_reviewed_first_slice import build_reviewed_first_slice, render_reviewed_first_slice_report


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAG006_PACKET = ROOT / "research" / "experiments" / "generated" / "RAG-006-chunk-review-packet" / "result.json"
DEFAULT_RAG005_RESULT = ROOT / "research" / "experiments" / "generated" / "RAG-005-chunk-normalization" / "result.json"
DEFAULT_SOURCE_MANIFEST = ROOT / "research" / "experiments" / "generated" / "RAG-004-source-manifest-normalization" / "result.json"
DEFAULT_OUTPUT_DIR = ROOT / "research" / "experiments" / "generated" / "RAG-007-reviewed-first-slice"
DEFAULT_RESULT = DEFAULT_OUTPUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUTPUT_DIR / "report.md"
PRIVATE_PATH_PARTS = (("data", "private"), ("data", "private-restricted"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the reviewed first RAG knowledge slice.")
    parser.add_argument("--rag006-packet", default=str(DEFAULT_RAG006_PACKET), help="RAG-006 chunk review packet JSON path.")
    parser.add_argument("--rag005-result", default=str(DEFAULT_RAG005_RESULT), help="RAG-005 chunk normalization result JSON path.")
    parser.add_argument("--source-manifest", default=str(DEFAULT_SOURCE_MANIFEST), help="RAG-004 source manifest JSON path.")
    parser.add_argument("--out", default=str(DEFAULT_RESULT), help="Output JSON reviewed first slice path.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT), help="Output Markdown reviewed first slice report path.")
    return parser.parse_args()


def _contains_private_path_parts(path: Path) -> bool:
    parts = tuple(part.lower() for part in path.parts)
    for private_parts in PRIVATE_PATH_PARTS:
        for index in range(0, len(parts) - len(private_parts) + 1):
            if parts[index : index + len(private_parts)] == private_parts:
                return True
    return False


def resolve_path(path_value: str) -> Path:
    path = Path(path_value)
    candidate = path if path.is_absolute() else ROOT / path
    resolved = candidate.resolve(strict=False)
    root = ROOT.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"RAG-007 path must stay inside project root: {path_value}") from exc
    if _contains_private_path_parts(resolved):
        raise ValueError(f"RAG-007 path is restricted: {path_value}")
    return resolved


def main() -> None:
    args = parse_args()
    rag006_packet = resolve_path(args.rag006_packet)
    rag005_result = resolve_path(args.rag005_result)
    source_manifest = resolve_path(args.source_manifest)
    out_path = resolve_path(args.out)
    report_path = resolve_path(args.report_out)
    payload = build_reviewed_first_slice(rag006_packet, rag005_result, source_manifest, root=ROOT)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(render_reviewed_first_slice_report(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
