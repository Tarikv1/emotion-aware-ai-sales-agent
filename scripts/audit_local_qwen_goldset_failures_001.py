#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


EXPERIMENT_ID = "LOCAL-QWEN-GOLDSET-FAILURE-AUDIT-001"
SOURCE_EXPERIMENT_ID = "LOCAL-QWEN-GOLDSET-EVAL-001"
SOURCE_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / SOURCE_EXPERIMENT_ID / "result.json"
SOURCE_GOLD_PATH = (
    ROOT
    / "research"
    / "experiments"
    / "generated"
    / "LOCAL-LLM-CONVERSATION-BRAIN-FEASIBILITY-001"
    / "gold_cases.jsonl"
)
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"

FAILURE_CLASSES = (
    "schema_shape_failure",
    "compact_json_field_type_failure",
    "compact_update_shape_failure",
    "semantic_family_mismatch",
    "speech_act_mismatch",
    "sub_intent_mismatch",
    "object_mentions_mismatch",
    "conjunction_relation_mismatch",
    "negation_scope_mismatch",
    "current_utterance_fidelity_failure",
    "state_update_failure",
    "team_state_failure",
    "recommendation_state_failure",
    "sales_action_failure",
    "response_plan_failure",
    "buyer_word_preservation_failure",
    "internal_policy_or_safety_failure",
    "unsupported_claim_failure",
    "latency_risk",
    "verifier_blocked_correctly",
    "gold_expected_output_maybe_too_strict",
    "needs_human_review",
)

QUALITY_FLAG_TO_CLASS = {
    "current_utterance_fidelity": "current_utterance_fidelity_failure",
    "team_state_poisoning": "team_state_failure",
    "internal_policy_leak": "internal_policy_or_safety_failure",
    "fake_side_effect": "internal_policy_or_safety_failure",
    "unsupported_claim": "unsupported_claim_failure",
    "sales_action": "sales_action_failure",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        payload = json.loads(stripped)
        if not isinstance(payload, dict):
            raise ValueError(f"{path} line {line_number} must contain a JSON object")
        rows.append(payload)
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sanitized_snippet(value: Any, *, limit: int = 140) -> str:
    text = " ".join(str(value or "").split())
    blocked = ("raw transcript", "private transcript", "data/private", "private-restricted")
    lowered = text.lower()
    if any(item in lowered for item in blocked):
        return "[redacted]"
    if len(text) > limit:
        return text[: limit - 3].rstrip() + "..."
    return text


def listify(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def nested(payload: dict[str, Any], *keys: str) -> Any:
    value: Any = payload
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def is_failed_case(case: dict[str, Any]) -> bool:
    comparison = case.get("qwen_gold_comparison")
    return case.get("status") == "fail" or not isinstance(comparison, dict) or comparison.get("semantic_match") is not True


def classify_case(case: dict[str, Any], result: dict[str, Any]) -> tuple[list[str], list[str]]:
    classes: set[str] = set()
    cause_types: set[str] = set()
    schema_errors = [str(item) for item in listify(case.get("schema_errors"))]
    verifier_errors = [str(item) for item in listify(case.get("verifier_errors"))]
    comparison = case.get("qwen_gold_comparison") if isinstance(case.get("qwen_gold_comparison"), dict) else {}
    mismatches = [str(item) for item in listify(comparison.get("semantic_mismatches"))]
    failure_classes = [str(item) for item in listify(comparison.get("failure_classes"))]

    for error in schema_errors:
        classes.add("schema_shape_failure")
        cause_types.update({"prompt/schema issue", "training-data issue"})
        if "must be a list of strings" in error or "must be a string" in error or "must be boolean" in error:
            classes.add("compact_json_field_type_failure")
        if "compact.update" in error:
            classes.add("compact_update_shape_failure")

    for mismatch in mismatches:
        if mismatch == "planner_output_missing":
            classes.add("schema_shape_failure")
            cause_types.update({"prompt/schema issue", "training-data issue"})
        elif mismatch == "semantic_frame.semantic_family":
            classes.add("semantic_family_mismatch")
            cause_types.add("model reasoning issue")
        elif mismatch == "semantic_frame.speech_act":
            classes.add("speech_act_mismatch")
            cause_types.add("model reasoning issue")
        elif mismatch == "semantic_frame.sub_intent":
            classes.add("sub_intent_mismatch")
            cause_types.add("model reasoning issue")
        elif mismatch == "semantic_frame.object_mentions":
            classes.add("object_mentions_mismatch")
            cause_types.add("model reasoning issue")
        elif mismatch == "semantic_frame.conjunction_relation":
            classes.add("conjunction_relation_mismatch")
            cause_types.add("model reasoning issue")
        elif mismatch == "semantic_frame.negation_scope":
            classes.add("negation_scope_mismatch")
            cause_types.add("model reasoning issue")
        elif mismatch == "semantic_frame.current_utterance_fidelity_notes":
            classes.add("current_utterance_fidelity_failure")
            cause_types.add("model reasoning issue")
        elif mismatch.startswith("state_update."):
            classes.add("state_update_failure")
            cause_types.add("model reasoning issue")
            if "team" in mismatch:
                classes.add("team_state_failure")
            if "recommendation" in mismatch:
                classes.add("recommendation_state_failure")
        elif mismatch.startswith("sales_strategy."):
            classes.add("sales_action_failure")
            cause_types.add("model reasoning issue")
        elif mismatch.startswith("response_plan."):
            classes.add("response_plan_failure")
            cause_types.add("model reasoning issue")

    for error in verifier_errors:
        classes.add("verifier_blocked_correctly")
        cause_types.add("model reasoning issue")
        if error.startswith("conjunction_relation_mismatch") or error in {"and_or_drift", "or_and_drift"}:
            classes.add("conjunction_relation_mismatch")
        if error.startswith("buyer_word_not_preserved"):
            classes.add("buyer_word_preservation_failure")
            classes.add("current_utterance_fidelity_failure")
        if "negation" in error or "team" in error:
            classes.add("team_state_failure")
            if "negation" in error:
                classes.add("negation_scope_mismatch")
        if error.startswith("must_not_include_present") or "safety_flag" in error:
            classes.add("internal_policy_or_safety_failure")
        if "unsupported" in error:
            classes.add("unsupported_claim_failure")

    quality_flags = comparison.get("quality_flags") if isinstance(comparison, dict) else {}
    if isinstance(quality_flags, dict):
        for flag_name, failure_class in QUALITY_FLAG_TO_CLASS.items():
            flag = quality_flags.get(flag_name)
            if isinstance(flag, dict) and flag.get("applicable") is True and flag.get("pass") is not True:
                classes.add(failure_class)
                cause_types.add("model reasoning issue")

    if "gold_response_plan_mismatch" in failure_classes:
        classes.add("response_plan_failure")
    if "gold_state_mismatch" in failure_classes:
        classes.add("state_update_failure")
    if "gold_sales_mismatch" in failure_classes:
        classes.add("sales_action_failure")
    if "gold_semantic_mismatch" in failure_classes and not schema_errors:
        cause_types.add("model reasoning issue")

    latency = nested(case, "latency_metrics", "total_generation_latency_ms")
    if isinstance(latency, (int, float)) and latency >= 10000:
        classes.add("latency_risk")

    outcome = nested(case, "qwen_vs_deterministic", "outcome")
    deterministic = case.get("deterministic_gold_comparison")
    deterministic_errors = []
    if isinstance(deterministic, dict):
        deterministic_errors = [str(item) for item in listify(deterministic.get("verifier_errors"))]
    if outcome == "both_fail" or deterministic_errors:
        classes.add("gold_expected_output_maybe_too_strict")
        classes.add("needs_human_review")
        cause_types.add("gold-label issue")
        if deterministic_errors:
            cause_types.add("verifier issue")

    if not classes:
        classes.add("needs_human_review")
        cause_types.add("training-data issue")

    return sorted(classes), sorted(cause_types)


def pattern_for_case(case: dict[str, Any]) -> str:
    parts = []
    parts.extend(str(item) for item in listify(case.get("schema_errors")))
    parts.extend(str(item) for item in listify(case.get("verifier_errors")))
    comparison = case.get("qwen_gold_comparison")
    if isinstance(comparison, dict):
        parts.extend(str(item) for item in listify(comparison.get("failure_classes")))
    if not parts:
        return "semantic/verifier mismatch without explicit error"
    return " | ".join(sorted(set(parts)))[:240]


def build_report(result: dict[str, Any], audit: dict[str, Any]) -> str:
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        "## Summary",
        "",
        f"- Source: `{SOURCE_EXPERIMENT_ID}`",
        f"- Total failed cases: {audit['summary']['total_failed_cases']}",
        f"- Local model calls made in this audit: {str(audit['side_effects']['local_model_calls_made']).lower()}",
        f"- Provider/API/TTS calls made: {str(audit['side_effects']['provider_side_effects_made']).lower()}",
        f"- Runtime behavior changed: {str(audit['side_effects']['runtime_behavior_changed']).lower()}",
        f"- Response text changed: {str(audit['side_effects']['response_text_changed']).lower()}",
        "",
        "## Failure Counts By Class",
        "",
    ]
    for class_name, count in audit["failure_counts_by_class"].items():
        lines.append(f"- `{class_name}`: {count}")
    lines.extend(["", "## Cause Counts", ""])
    for cause_name, count in audit["cause_counts"].items():
        lines.append(f"- {cause_name}: {count}")
    lines.extend(["", "## Top Repeated Failure Patterns", ""])
    for item in audit["top_repeated_failure_patterns"]:
        lines.append(f"- {item['count']}x `{item['pattern']}`")
    lines.extend(["", "## Examples By Class", ""])
    for class_name, examples in audit["examples_by_class"].items():
        lines.append(f"### {class_name}")
        if not examples:
            lines.append("")
            lines.append("- none")
            lines.append("")
            continue
        for example in examples:
            lines.append(
                "- "
                f"`{example['case_id']}` ({', '.join(example['cause_types'])}): "
                f"{example['sanitized_buyer_snippet']} "
                f"[errors: {', '.join(example['error_summary']) or 'none'}]"
            )
        lines.append("")
    lines.extend(
        [
            "## Interpretation",
            "",
            "Qwen is not ready for live dialogue replacement. The useful output of this phase is offline failure taxonomy and compact supervised data for a later fine-tuning review.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    source = read_json(SOURCE_RESULT_PATH)
    gold_by_case = {str(row.get("case_id")): row for row in read_jsonl(SOURCE_GOLD_PATH)}
    failed_cases = [case for case in source.get("cases", []) if isinstance(case, dict) and is_failed_case(case)]
    class_counts: Counter[str] = Counter()
    cause_counts: Counter[str] = Counter()
    pattern_counts: Counter[str] = Counter()
    examples_by_class: dict[str, list[dict[str, Any]]] = {class_name: [] for class_name in FAILURE_CLASSES}
    case_audits: list[dict[str, Any]] = []

    for case in failed_cases:
        case_id = str(case.get("case_id") or "")
        classes, cause_types = classify_case(case, source)
        class_counts.update(classes)
        cause_counts.update(cause_types)
        pattern_counts[pattern_for_case(case)] += 1
        gold = gold_by_case.get(case_id, {})
        error_summary = [
            *[str(item) for item in listify(case.get("schema_errors"))],
            *[str(item) for item in listify(case.get("verifier_errors"))],
        ][:4]
        case_payload = {
            "case_id": case_id,
            "source_type": gold.get("source_type") or case.get("source_type"),
            "failure_classes": classes,
            "cause_types": cause_types,
            "sanitized_buyer_snippet": sanitized_snippet(gold.get("sanitized_buyer_text")),
            "error_summary": error_summary,
            "qwen_vs_deterministic": nested(case, "qwen_vs_deterministic", "outcome"),
            "latency_ms": nested(case, "latency_metrics", "total_generation_latency_ms"),
        }
        case_audits.append(case_payload)
        for class_name in classes:
            if len(examples_by_class[class_name]) < 3:
                examples_by_class[class_name].append(
                    {
                        "case_id": case_id,
                        "cause_types": cause_types,
                        "sanitized_buyer_snippet": case_payload["sanitized_buyer_snippet"],
                        "error_summary": error_summary,
                    }
                )

    for class_name in FAILURE_CLASSES:
        class_counts.setdefault(class_name, 0)
        examples_by_class.setdefault(class_name, [])
    for cause_name in (
        "prompt/schema issue",
        "model reasoning issue",
        "verifier issue",
        "gold-label issue",
        "training-data issue",
    ):
        cause_counts.setdefault(cause_name, 0)

    latency_values = [
        nested(case, "latency_metrics", "total_generation_latency_ms")
        for case in failed_cases
        if isinstance(nested(case, "latency_metrics", "total_generation_latency_ms"), (int, float))
    ]
    audit = {
        "experiment_id": EXPERIMENT_ID,
        "source_experiment_id": SOURCE_EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass",
        "summary": {
            "total_failed_cases": len(failed_cases),
            "source_failed_case_count": source.get("failed_case_count"),
            "source_case_count_attempted": source.get("case_count_attempted"),
            "source_case_count_completed": source.get("case_count_completed"),
            "schema_valid_count": source.get("schema_valid_count"),
            "verifier_pass_count": source.get("verifier_pass_count"),
            "semantic_match_count": source.get("semantic_match_count"),
            "exact_match_count": source.get("exact_match_count"),
        },
        "failure_counts_by_class": dict(sorted(class_counts.items())),
        "cause_counts": dict(sorted(cause_counts.items())),
        "top_repeated_failure_patterns": [
            {"pattern": pattern, "count": count} for pattern, count in pattern_counts.most_common(12)
        ],
        "failed_case_audits": case_audits,
        "examples_by_class": examples_by_class,
        "latency_summary_failed_cases": {
            "count": len(latency_values),
            "average_ms": round(statistics.mean(latency_values), 3) if latency_values else None,
            "max_ms": round(max(latency_values), 3) if latency_values else None,
            "latency_risk_threshold_ms": 10000,
        },
        "side_effects": {
            "local_model_calls_made": False,
            "local_model_call_count": 0,
            "provider_calls_made": False,
            "openai_api_calls_made": False,
            "live_tts_calls_made": False,
            "provider_side_effects_made": False,
            "raw_private_transcript_copied_to_public_evidence": False,
            "runtime_behavior_changed": False,
            "response_text_changed": False,
        },
        "source_side_effects": {
            "local_model_calls_made": source.get("local_model_calls_made"),
            "local_model_call_count": source.get("local_model_call_count"),
            "provider_calls_made": source.get("provider_calls_made"),
            "openai_api_calls_made": source.get("openai_api_calls_made"),
            "live_tts_calls_made": source.get("live_tts_calls_made"),
            "provider_side_effects_made": source.get("provider_side_effects_made"),
            "runtime_behavior_changed": source.get("runtime_behavior_changed"),
            "response_text_changed": source.get("response_text_changed"),
        },
    }
    write_json(RESULT_PATH, audit)
    REPORT_PATH.write_text(build_report(source, audit), encoding="utf-8")
    print(json.dumps({"status": "pass", "result": str(RESULT_PATH), "failed_cases": len(failed_cases)}, indent=2))


if __name__ == "__main__":
    main()
