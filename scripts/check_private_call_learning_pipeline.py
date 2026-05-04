#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASE = ROOT / "research" / "experiments" / "cases" / "private-call-learning-001.json"
DEFAULT_OUT = ROOT / "research" / "experiments" / "generated" / "PRIVATE-CALL-LEARNING-001.json"
DEFAULT_REPORT_OUT = ROOT / "research" / "experiments" / "generated" / "PRIVATE-CALL-LEARNING-001-report.md"
POLICY_DOC = ROOT / "docs" / "data" / "PRIVATE_CALL_LEARNING_PIPELINE.md"
PRIVATE_ROOT = ROOT / "data" / "private"
ROOT_GITIGNORE = ROOT / ".gitignore"
PRIVATE_GITIGNORE = PRIVATE_ROOT / ".gitignore"


REQUIRED_STAGE_IDS = [
    "ingest_raw_audio_local_only",
    "local_transcription",
    "speaker_segmentation",
    "pii_sensitive_redaction",
    "outcome_labeling",
    "pattern_mining",
    "human_review",
    "safe_learning_export",
    "retention_or_deletion",
]

REQUIRED_POLICY_PHRASES = [
    "Pattern-mining first, fine-tuning later",
    "Raw private audio never leaves `data/private/`",
    "Private identifiers are not training signal",
    "Bad calls are useful as negative constraints",
    "No safe export before redaction and human review",
]


def build_check(check_id: str, status: str, message: str, path: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": check_id,
        "status": status,
        "message": message,
    }
    if path:
        payload["path"] = path
    return payload


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_text_if_exists(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def root_gitignore_allows_only_private_gitignore() -> bool:
    text = read_text_if_exists(ROOT_GITIGNORE)
    return "data/private/*" in text and "!data/private/.gitignore" in text


def private_gitignore_ignores_private_contents() -> bool:
    lines = read_text_if_exists(PRIVATE_GITIGNORE).splitlines()
    return "*" in lines and "!.gitignore" in lines


def validate_case_file(case: dict[str, Any]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    checks.append(
        build_check(
            "case_file.safe",
            "pass" if case.get("pipeline_id") == "PRIVATE-CALL-LEARNING-001" else "fail",
            "Pipeline case file is present and uses the expected id.",
            "research/experiments/cases/private-call-learning-001.json",
        )
    )
    stage_ids = [stage.get("stage_id") for stage in case.get("stages", [])]
    checks.append(
        build_check(
            "pipeline.stage_order",
            "pass" if stage_ids == REQUIRED_STAGE_IDS else "fail",
            "Pipeline preserves local ingest, redaction, review, export, and deletion order.",
            "research/experiments/cases/private-call-learning-001.json",
        )
    )
    learning_outputs = set(case.get("learning_outputs", []))
    required_outputs = {
        "positive_sales_pattern",
        "negative_sales_pattern",
        "customer_objection_pattern",
        "human_agent_success_pattern",
        "human_agent_failure_pattern",
        "safety_or_compliance_constraint",
    }
    checks.append(
        build_check(
            "pipeline.good_and_bad_patterns",
            "pass" if required_outputs.issubset(learning_outputs) else "fail",
            "Pipeline includes successful, unsuccessful, customer, human-agent, and safety pattern outputs.",
            "research/experiments/cases/private-call-learning-001.json",
        )
    )
    return checks


def validate_policy_doc() -> list[dict[str, Any]]:
    text = read_text_if_exists(POLICY_DOC)
    checks = [
        build_check(
            "policy_doc.exists",
            "pass" if POLICY_DOC.is_file() else "fail",
            "Private call learning policy document exists.",
            "docs/data/PRIVATE_CALL_LEARNING_PIPELINE.md",
        )
    ]
    missing = [phrase for phrase in REQUIRED_POLICY_PHRASES if phrase not in text]
    checks.append(
        build_check(
            "policy_doc.boundary",
            "pass" if not missing else "fail",
            "Policy document records pattern-first learning, private audio boundary, identifier exclusion, negative examples, and export gates.",
            "docs/data/PRIVATE_CALL_LEARNING_PIPELINE.md",
        )
    )
    return checks


def validate_boundary(case: dict[str, Any]) -> list[dict[str, Any]]:
    boundary = case.get("boundary", {})
    return [
        build_check(
            "private_root.exists",
            "pass" if PRIVATE_ROOT.is_dir() else "fail",
            "Local-only private data root exists.",
            "data/private",
        ),
        build_check(
            "private_root.gitignored",
            "pass" if root_gitignore_allows_only_private_gitignore() and private_gitignore_ignores_private_contents() else "fail",
            "Root and private .gitignore rules keep private contents out of Git.",
            "data/private/.gitignore",
        ),
        build_check(
            "pipeline.no_provider_upload",
            "pass" if boundary.get("raw_audio_provider_upload_allowed") is False else "fail",
            "Raw private audio upload to providers is disabled by default.",
            "research/experiments/cases/private-call-learning-001.json",
        ),
        build_check(
            "pipeline.no_identifier_learning",
            "pass" if boundary.get("customer_identifier_learning_allowed") is False else "fail",
            "Customer identifiers are excluded from learning signal.",
            "research/experiments/cases/private-call-learning-001.json",
        ),
        build_check(
            "pipeline.redaction_before_export",
            "pass" if boundary.get("safe_export_requires_redaction") is True else "fail",
            "Safe export requires redaction first.",
            "research/experiments/cases/private-call-learning-001.json",
        ),
        build_check(
            "pipeline.human_review_before_export",
            "pass" if boundary.get("safe_export_requires_human_review") is True else "fail",
            "Safe export requires human review first.",
            "research/experiments/cases/private-call-learning-001.json",
        ),
        build_check(
            "pipeline.retention_or_deletion",
            "pass" if boundary.get("deletion_manifest_required_after_source_removal") is True else "fail",
            "Retention/deletion handling records deletion manifests without private content.",
            "research/experiments/cases/private-call-learning-001.json",
        ),
    ]


def summarize(checks: list[dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    failures = [check for check in checks if check["status"] == "fail"]
    return ("fail" if failures else "pass"), {
        "check_count": len(checks),
        "failure_count": len(failures),
        "private_files_scanned": 0,
        "auto_fixes_applied": False,
    }


def build_payload(case_path: Path) -> dict[str, Any]:
    case = read_json(case_path)
    checks: list[dict[str, Any]] = []
    checks.extend(validate_case_file(case))
    checks.extend(validate_policy_doc())
    checks.extend(validate_boundary(case))
    status, summary = summarize(checks)
    boundary = case["boundary"]
    return {
        "pipeline_id": case["pipeline_id"],
        "title": case["title"],
        "source_label": case["source_label"],
        "status": status,
        "summary": summary,
        "network_calls_made": False,
        "raw_private_content_read": False,
        "secret_values_logged": False,
        "private_root": case["private_root"],
        "required_private_subdirs": case["required_private_subdirs"],
        "boundary": boundary,
        "stages": case["stages"],
        "learning_outputs": case["learning_outputs"],
        "disallowed_learning_outputs": case["disallowed_learning_outputs"],
        "rag_policy": case["rag_policy"],
        "fine_tuning_policy": case["fine_tuning_policy"],
        "checks": checks,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# PRIVATE-CALL-LEARNING-001 Report",
        "",
        f"- Status: `{payload['status']}`",
        "- Network calls made: false",
        "- Raw private content read: false",
        "- Secret values logged: false",
        f"- Private root: `{payload['private_root']}`",
        f"- Required private workspace folders: {len(payload['required_private_subdirs'])}",
        f"- Checks: {payload['summary']['check_count']}",
        f"- Failures: {payload['summary']['failure_count']}",
        "",
        "## Boundary",
        "",
        "- Raw private audio stays local and is not provider-uploaded by default.",
        "- Customer identifiers and sensitive personal facts are not learning signal.",
        "- Fine-tuning remains disabled until a separate reviewed checkpoint.",
        "- Safe export requires redaction plus human review.",
        "",
        "## Pipeline Stages",
        "",
    ]
    for index, stage in enumerate(payload["stages"], start=1):
        lines.append(f"{index}. `{stage['stage_id']}` -> `{stage['output_location']}`")
    lines.extend(["", "## Learning Outputs", ""])
    for output in payload["learning_outputs"]:
        lines.append(f"- `{output}`")
    lines.extend(["", "## Checks", ""])
    for check in payload["checks"]:
        lines.append(f"- `{check['status']}` `{check['id']}`: {check['message']}")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check the local-only private call-center learning pipeline scaffold.")
    parser.add_argument("--case", default=str(DEFAULT_CASE), help="Pipeline case/config JSON.")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="JSON output path.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT_OUT), help="Markdown report output path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    case_path = Path(args.case)
    if not case_path.is_absolute():
        case_path = ROOT / case_path
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = ROOT / out_path
    report_path = Path(args.report_out)
    if not report_path.is_absolute():
        report_path = ROOT / report_path

    payload = build_payload(case_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps({"pipeline_id": payload["pipeline_id"], "status": payload["status"]}, indent=2))
    raise SystemExit(0 if payload["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
