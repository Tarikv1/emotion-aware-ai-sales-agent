#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from rag_runtime_knowledge_registry import (
    DEFAULT_INCLUDED_ARTIFACT_KEYS,
    build_runtime_knowledge_registry,
    render_runtime_knowledge_registry_report,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "research" / "experiments" / "generated" / "RAG-017-runtime-knowledge-registry"
DEFAULT_RESULT = DEFAULT_OUTPUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUTPUT_DIR / "report.md"
DEFAULT_ARTIFACT_PATHS = {
    "RAG-007-reviewed-first-slice": ROOT / "research" / "experiments" / "generated" / "RAG-007-reviewed-first-slice" / "result.json",
    "RAG-010-reviewed-expansion-slice": ROOT / "research" / "experiments" / "generated" / "RAG-010-reviewed-expansion-slice" / "result.json",
    "RAG-012-accepted-cleanup": ROOT / "research" / "experiments" / "generated" / "RAG-012-accepted-cleanup" / "result.json",
    "RAG-014-source-mapped-quote-followup": ROOT / "research" / "experiments" / "generated" / "RAG-014-source-mapped-quote-followup" / "result.json",
    "RAG-016A-quote-clearance-decision-slice": ROOT / "research" / "experiments" / "generated" / "RAG-016A-quote-clearance-decision-slice" / "result.json",
    "RAG-016B-voice-delivery-quote-clearance-decision-slice": ROOT / "research" / "experiments" / "generated" / "RAG-016B-voice-delivery-decision-slice" / "result.json",
    "RAG-019-sales-communication-source-expansion": ROOT / "research" / "experiments" / "generated" / "RAG-019-sales-communication-source-expansion" / "result.json",
}
PRIVATE_PATH_PARTS = (("data", "private"), ("data", "private-restricted"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the RAG-017 runtime knowledge registry.")
    for artifact_id in DEFAULT_INCLUDED_ARTIFACT_KEYS:
        arg_name = "--" + artifact_id.lower().replace("_", "-").replace("rag-", "rag").replace("-", "", 1)
        parser.add_argument(arg_name, dest=artifact_id, default=str(DEFAULT_ARTIFACT_PATHS[artifact_id]))
    parser.add_argument("--out", default=str(DEFAULT_RESULT), help="Output JSON registry path.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT), help="Output Markdown report path.")
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
        raise ValueError(f"RAG-017 path must stay inside project root: {path_value}") from exc
    if _contains_private_path_parts(resolved):
        raise ValueError(f"RAG-017 path is restricted: {path_value}")
    return resolved


def main() -> None:
    args = parse_args()
    artifact_paths = {
        artifact_id: resolve_path(getattr(args, artifact_id))
        for artifact_id in DEFAULT_INCLUDED_ARTIFACT_KEYS
    }
    out_path = resolve_path(args.out)
    report_path = resolve_path(args.report_out)
    payload = build_runtime_knowledge_registry(artifact_paths, root=ROOT)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(render_runtime_knowledge_registry_report(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
