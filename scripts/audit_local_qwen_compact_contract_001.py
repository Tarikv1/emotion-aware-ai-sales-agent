#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.llm_brain.compact_planner_contract import (  # noqa: E402
    ALLOWED_COMPACT_VALUES,
    COMPACT_VALUE_CONTRACT_VERSION,
    OVERLY_GENERIC_ACT_VALUES,
    compact_label_quality_issues,
    is_case_id_like_label,
)


EXPERIMENT_ID = "LOCAL-QWEN-COMPACT-CONTRACT-AUDIT-001"
SFT_EXPERIMENT_ID = "LOCAL-QWEN-SFT-DATASET-001"
EVAL_EXPERIMENT_ID = "LOCAL-QWEN-LORA-EVAL-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
SFT_DIR = ROOT / "research" / "experiments" / "generated" / SFT_EXPERIMENT_ID
EVAL_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / EVAL_EXPERIMENT_ID / "result.json"
SPLIT_PATHS = {
    "train": SFT_DIR / "train.jsonl",
    "validation": SFT_DIR / "validation.jsonl",
    "test": SFT_DIR / "test.jsonl",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        payload = json.loads(stripped)
        if not isinstance(payload, dict):
            raise ValueError(f"{rel(path)} line {line_number} must be an object")
        rows.append(payload)
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def issue_summary(payloads: list[dict[str, Any]], *, source: str) -> dict[str, Any]:
    issue_counts: Counter[str] = Counter()
    field_value_counts: Counter[str] = Counter()
    label_occurrences: Counter[str] = Counter()
    flagged_items: list[dict[str, Any]] = []
    for item in payloads:
        compact = item.get("compact") if isinstance(item.get("compact"), dict) else {}
        if not compact:
            continue
        for field_name in ("act", "sub", "action", "strategy"):
            value = compact.get(field_name)
            if isinstance(value, str) and value:
                label_occurrences[f"{field_name}={value}"] += 1
        issues = compact_label_quality_issues(compact)
        for issue in issues:
            issue_counts[issue["issue"]] += 1
            field_value_counts[f"{issue['field']}={issue['value']}"] += 1
        if issues:
            flagged_items.append(
                {
                    "source": source,
                    "case_id": item.get("case_id"),
                    "split": item.get("split"),
                    "issues": issues,
                    "labels": {
                        "act": compact.get("act"),
                        "sub": compact.get("sub"),
                        "action": compact.get("action"),
                        "strategy": compact.get("strategy"),
                    },
                }
            )
    return {
        "payload_count": len(payloads),
        "issue_counts": dict(sorted(issue_counts.items())),
        "flagged_payload_count": len(flagged_items),
        "top_flagged_labels": dict(field_value_counts.most_common(30)),
        "label_occurrences": dict(label_occurrences),
        "flagged_items": flagged_items[:80],
    }


def audit_contract() -> dict[str, Any]:
    payloads: list[dict[str, Any]] = []
    deprecated_allowed: list[dict[str, str]] = []
    case_id_like_allowed: list[dict[str, str]] = []
    generic_allowed: list[dict[str, str]] = []
    for field_name, values in ALLOWED_COMPACT_VALUES.items():
        for value in values:
            compact = {"act": "", "sub": "", "action": "", "strategy": ""}
            if field_name in compact:
                compact[field_name] = value
                payloads.append({"case_id": f"contract:{field_name}:{value}", "compact": compact})
            if is_case_id_like_label(value):
                case_id_like_allowed.append({"field": field_name, "value": value})
            if field_name == "act" and value in OVERLY_GENERIC_ACT_VALUES:
                generic_allowed.append({"field": field_name, "value": value})
    summary = issue_summary(payloads, source="contract")
    for item in summary["flagged_items"]:
        for issue in item["issues"]:
            if issue["issue"] == "deprecated_label":
                deprecated_allowed.append({"field": issue["field"], "value": issue["value"]})
            if issue["issue"].startswith("generic"):
                generic_allowed.append({"field": issue["field"], "value": issue["value"]})
    return {
        "contract_version": COMPACT_VALUE_CONTRACT_VERSION,
        "deprecated_allowed_count": len(deprecated_allowed),
        "case_id_like_allowed_count": len(case_id_like_allowed),
        "generic_allowed_count": len(generic_allowed),
        "deprecated_allowed": deprecated_allowed,
        "case_id_like_allowed": case_id_like_allowed,
        "generic_allowed": generic_allowed,
    }


def audit_dataset() -> dict[str, Any]:
    payloads: list[dict[str, Any]] = []
    split_counts: dict[str, int] = {}
    target_contains_case_id_count = 0
    for split_name, path in SPLIT_PATHS.items():
        rows = read_jsonl(path)
        split_counts[split_name] = len(rows)
        for row in rows:
            compact = row.get("target_compact_json") if isinstance(row.get("target_compact_json"), dict) else {}
            case_id = str(row.get("case_id") or "")
            if case_id:
                for field_name in ("act", "sub", "action", "strategy"):
                    if compact.get(field_name) == case_id or case_id in str(compact.get(field_name) or ""):
                        target_contains_case_id_count += 1
            payloads.append({"case_id": case_id, "split": split_name, "compact": compact})
    summary = issue_summary(payloads, source="dataset_target")
    summary["split_counts"] = split_counts
    summary["target_contains_case_id_count"] = target_contains_case_id_count
    return summary


def audit_eval() -> dict[str, Any]:
    result = read_json(EVAL_RESULT_PATH)
    cases = result.get("cases") if isinstance(result.get("cases"), list) else []
    payloads: list[dict[str, Any]] = []
    verifier_pass_gold_fail: list[dict[str, Any]] = []
    for case in cases:
        if not isinstance(case, dict):
            continue
        payloads.append(
            {
                "case_id": case.get("case_id"),
                "split": case.get("split"),
                "compact": case.get("compact_planner_output") if isinstance(case.get("compact_planner_output"), dict) else {},
            }
        )
        if case.get("verifier_pass") is True and case.get("gold_section_semantic_match") is not True:
            verifier_pass_gold_fail.append(
                {
                    "case_id": case.get("case_id"),
                    "split": case.get("split"),
                    "semantic_mismatches": case.get("semantic_mismatches") or [],
                    "labels": {
                        "act": (case.get("compact_planner_output") or {}).get("act"),
                        "sub": (case.get("compact_planner_output") or {}).get("sub"),
                        "action": (case.get("compact_planner_output") or {}).get("action"),
                        "strategy": (case.get("compact_planner_output") or {}).get("strategy"),
                    },
                }
            )
    summary = issue_summary(payloads, source="eval_output")
    summary["status"] = result.get("status")
    summary["adapter_path"] = result.get("adapter_path")
    summary["verifier_pass_gold_section_fail_count"] = len(verifier_pass_gold_fail)
    summary["verifier_pass_gold_section_failures"] = verifier_pass_gold_fail
    summary["latency_metrics"] = result.get("latency_metrics") or {}
    return summary


def count_issue(summary: dict[str, Any], issue: str) -> int:
    return int((summary.get("issue_counts") or {}).get(issue) or 0)


def current_summary() -> dict[str, Any]:
    contract = audit_contract()
    dataset = audit_dataset()
    eval_summary = audit_eval()
    deprecated = (
        contract["deprecated_allowed_count"]
        + count_issue(dataset, "deprecated_label")
        + count_issue(eval_summary, "deprecated_label")
    )
    case_id_like = (
        contract["case_id_like_allowed_count"]
        + count_issue(dataset, "case_id_label_leak")
        + count_issue(eval_summary, "case_id_label_leak")
    )
    generic = (
        contract["generic_allowed_count"]
        + count_issue(dataset, "generic_act")
        + count_issue(dataset, "generic_action")
        + count_issue(dataset, "generic_sub_intent")
        + count_issue(eval_summary, "generic_act")
        + count_issue(eval_summary, "generic_action")
        + count_issue(eval_summary, "generic_sub_intent")
    )
    generalized_sales_move_count = 0
    for bucket in (dataset, eval_summary):
        labels = bucket.get("label_occurrences") or {}
        generalized_sales_move_count += int(labels.get("act=generalized_sales_move") or 0)
    return {
        "contract": contract,
        "dataset": dataset,
        "eval": eval_summary,
        "summary_counts": {
            "deprecated_label_count": deprecated,
            "case_id_label_leak_count": case_id_like,
            "generic_label_count": generic,
            "generalized_sales_move_count": generalized_sales_move_count,
            "verifier_pass_gold_section_fail_count": eval_summary["verifier_pass_gold_section_fail_count"],
        },
    }


def previous_audit_state() -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    previous = read_json(RESULT_PATH)
    current = previous.get("current") if isinstance(previous.get("current"), dict) else None
    baseline = previous.get("baseline_current") if isinstance(previous.get("baseline_current"), dict) else None
    if baseline is None and isinstance(previous.get("previous_current"), dict):
        baseline = previous["previous_current"]
    if baseline is None:
        baseline = current
    return baseline, current


def build_report(result: dict[str, Any]) -> str:
    current = result["current"]
    previous = result.get("baseline_current") or {}
    current_counts = current["summary_counts"]
    previous_counts = previous.get("summary_counts") or {}
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- Status: {result['status']}",
        f"- Contract: `{COMPACT_VALUE_CONTRACT_VERSION}`",
        f"- Provider calls made: {str(result['side_effects']['provider_calls_made']).lower()}",
        f"- OpenAI API calls made: {str(result['side_effects']['openai_api_calls_made']).lower()}",
        f"- Live TTS calls made: {str(result['side_effects']['live_tts_calls_made']).lower()}",
        f"- Runtime behavior changed: {str(result['side_effects']['runtime_behavior_changed']).lower()}",
        f"- Response text changed: {str(result['side_effects']['response_text_changed']).lower()}",
        "",
        "## Before / Current",
        "",
        "| Metric | Previous audit | Current audit |",
        "| --- | ---: | ---: |",
    ]
    for key in (
        "deprecated_label_count",
        "case_id_label_leak_count",
        "generic_label_count",
        "generalized_sales_move_count",
        "verifier_pass_gold_section_fail_count",
    ):
        lines.append(f"| {key} | {previous_counts.get(key, 'n/a')} | {current_counts.get(key, 0)} |")
    lines.extend(
        [
            "",
            "## Dataset",
            "",
            f"- Rows: {current['dataset']['payload_count']}",
            f"- Flagged targets: {current['dataset']['flagged_payload_count']}",
            f"- Split counts: `{json.dumps(current['dataset']['split_counts'], sort_keys=True)}`",
            "",
            "## Eval",
            "",
            f"- Status: {current['eval'].get('status')}",
            f"- Adapter path: `{current['eval'].get('adapter_path')}`",
            f"- Flagged outputs: {current['eval']['flagged_payload_count']}",
            f"- Verifier-pass but gold-section-fail: {current['eval']['verifier_pass_gold_section_fail_count']}",
            "",
            "## Top Flagged Dataset Labels",
            "",
        ]
    )
    for label, count in (current["dataset"].get("top_flagged_labels") or {}).items():
        lines.append(f"- `{label}`: {count}")
    lines.extend(["", "## Top Flagged Eval Labels", ""])
    for label, count in (current["eval"].get("top_flagged_labels") or {}).items():
        lines.append(f"- `{label}`: {count}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    baseline, prior = previous_audit_state()
    current = current_summary()
    issue_total = sum(int(value or 0) for value in current["summary_counts"].values())
    result = {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "issues_found" if issue_total else "pass",
        "current": current,
        "baseline_current": baseline,
        "previous_current": prior,
        "side_effects": {
            "provider_calls_made": False,
            "openai_api_calls_made": False,
            "live_tts_calls_made": False,
            "runtime_behavior_changed": False,
            "response_text_changed": False,
            "raw_private_transcript_included": False,
        },
    }
    write_json(RESULT_PATH, result)
    REPORT_PATH.write_text(build_report(result), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": result["status"],
                "summary_counts": current["summary_counts"],
                "dataset_flagged": current["dataset"]["flagged_payload_count"],
                "eval_flagged": current["eval"]["flagged_payload_count"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
