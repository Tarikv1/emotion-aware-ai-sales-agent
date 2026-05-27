#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.llm_brain.compact_planner_contract import (  # noqa: E402
    COMPACT_VALUE_CONTRACT_VERSION,
    compact_label_quality_issues,
    is_case_id_like_label,
    validate_compact_value_contract,
)
from runtime.llm_brain.conversation_brain_schema import (  # noqa: E402
    REQUIRED_COMPACT_PLANNER_FIELDS,
    expand_compact_planner_output,
    validate_compact_conversation_brain_output,
)
from runtime.llm_brain.conversation_brain_verifier import verify_conversation_brain_output  # noqa: E402


EXPERIMENT_ID = "LOCAL-QWEN-SFT-DATASET-001"
SOURCE_EXPERIMENT_ID = "LOCAL-LLM-CONVERSATION-BRAIN-FEASIBILITY-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
SPLIT_PATHS = {
    "train": OUT_DIR / "train.jsonl",
    "validation": OUT_DIR / "validation.jsonl",
    "test": OUT_DIR / "test.jsonl",
}
GOLD_CASES_PATH = (
    ROOT
    / "research"
    / "experiments"
    / "generated"
    / SOURCE_EXPERIMENT_ID
    / "gold_cases.jsonl"
)
EXPECTED_SPLIT_COUNTS = {"train": 60, "validation": 10, "test": 10}

BLOCKED_PROVIDER_PATTERNS = {
    "openai_import": "from " + "openai",
    "openai_client": "openai" + ".OpenAI",
    "openai_api_key": "OPENAI" + "_API_KEY",
    "requests_post": "requests" + ".post",
    "httpx_post": "httpx" + ".post",
}
SIDE_EFFECT_RE = re.compile(
    r"\b(sent|emailed|created|booked|scheduled|updated|logged)\b.{0,48}\b(email|calendar|invite|crm|ticket|record)\b",
    re.I,
)
INTERNAL_POLICY_RE = re.compile(r"internal policy|source-grounded|guardrail|approved qualified reviewer", re.I)
WEIGHT_SUFFIXES = (".safetensors", ".bin", ".gguf", ".pt", ".pth")
REQUIRED_ROW_FIELDS = {
    "case_id",
    "source_type",
    "campaign_id",
    "prompt",
    "target_compact_json",
    "target_full_json",
    "approved_campaign_fact_summaries",
    "prior_state",
    "expected_safety_constraints",
    "failure_tags",
    "privacy_level",
    "raw_private_transcript_included",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


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
            raise ValueError(f"{rel(path)} line {line_number} must contain a JSON object")
        rows.append(payload)
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def listify(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def string_list(value: Any) -> list[str]:
    return [str(item) for item in listify(value) if isinstance(item, str)]


def build_gold_lookup() -> dict[str, dict[str, Any]]:
    return {str(row.get("case_id")): row for row in read_jsonl(GOLD_CASES_PATH)}


def verifier_case(gold: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    return {
        **gold,
        "approved_campaign_fact_summaries": row.get("approved_campaign_fact_summaries") or {},
    }


def contains_key(payload: Any, key_name: str) -> bool:
    if isinstance(payload, dict):
        if key_name in payload:
            return True
        return any(contains_key(value, key_name) for value in payload.values())
    if isinstance(payload, list):
        return any(contains_key(item, key_name) for item in payload)
    return False


def git_model_weights_committed() -> bool:
    try:
        completed = subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except Exception:
        return False
    if completed.returncode != 0:
        return False
    return any(line.strip().lower().endswith(WEIGHT_SUFFIXES) for line in completed.stdout.splitlines())


def validate_no_provider_calls(failures: list[str]) -> None:
    for relative in (
        "scripts/audit_local_qwen_goldset_failures_001.py",
        "scripts/audit_local_qwen_compact_contract_001.py",
        "scripts/build_local_qwen_sft_dataset_001.py",
        "scripts/validate_local_qwen_sft_dataset_001.py",
    ):
        path = ROOT / relative
        if not path.is_file():
            failures.append(f"missing expected script: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        for label, pattern in BLOCKED_PROVIDER_PATTERNS.items():
            if pattern in text:
                failures.append(f"{relative} contains blocked provider/API pattern: {label}")


def validate_row(row: dict[str, Any], split_name: str, index: int, gold_lookup: dict[str, dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    row_label = f"{split_name}[{index}]"
    case_id = str(row.get("case_id") or "")
    missing = sorted(REQUIRED_ROW_FIELDS - set(row))
    if missing:
        failures.append(f"{row_label} missing required field(s): {missing}")
    if "input_messages" not in row and "prompt" not in row:
        failures.append(f"{row_label} must include prompt or input_messages")
    if row.get("privacy_level") != "sanitized_only":
        failures.append(f"{row_label}.privacy_level must be sanitized_only")
    if row.get("raw_private_transcript_included") is not False:
        failures.append(f"{row_label}.raw_private_transcript_included must be false")
    if contains_key(row, "raw_buyer_text"):
        failures.append(f"{row_label} includes raw_buyer_text")
    if "raw private transcript" in json.dumps(row, ensure_ascii=False).lower():
        failures.append(f"{row_label} mentions raw private transcript")

    target = row.get("target_compact_json")
    if not isinstance(target, dict):
        failures.append(f"{row_label}.target_compact_json must be an object")
        return failures
    if tuple(target.keys()) != REQUIRED_COMPACT_PLANNER_FIELDS:
        failures.append(f"{row_label}.target_compact_json fields/order must match compact schema")
    failures.extend(f"{row_label}: {error}" for error in validate_compact_conversation_brain_output(target))
    contract_errors = validate_compact_value_contract(target)
    failures.extend(f"{row_label}: {error}" for error in contract_errors)
    quality_issues = compact_label_quality_issues(target)
    for issue in quality_issues:
        failures.append(
            f"{row_label}.target_compact_json.{issue['field']} violates compact value contract "
            f"({issue['issue']}): {issue['value']!r}"
        )
    for field_name in ("act", "sub", "action", "strategy"):
        value = target.get(field_name)
        if is_case_id_like_label(value):
            failures.append(f"{row_label}.target_compact_json.{field_name} contains case-ID-like value: {value!r}")
        if isinstance(value, str) and case_id and (value == case_id or case_id in value):
            failures.append(f"{row_label}.target_compact_json.{field_name} contains case_id: {case_id}")
        if value == "generalized_sales_move":
            failures.append(f"{row_label}.target_compact_json.{field_name} uses generalized_sales_move")

    approved_ids = set((row.get("approved_campaign_fact_summaries") or {}).keys())
    fact_ids = set(string_list(target.get("facts")))
    if fact_ids - approved_ids:
        failures.append(f"{row_label}.target_compact_json.facts contains unapproved fact id(s): {sorted(fact_ids - approved_ids)}")

    say = str(target.get("say") or "")
    if SIDE_EFFECT_RE.search(say):
        failures.append(f"{row_label}.target_compact_json.say contains fake side effect language")
    if INTERNAL_POLICY_RE.search(say):
        failures.append(f"{row_label}.target_compact_json.say contains internal policy language")

    expanded, adapter_errors = expand_compact_planner_output(target)
    if adapter_errors:
        failures.extend(f"{row_label}: compact-to-full adapter error: {error}" for error in adapter_errors)
        return failures
    if row.get("target_full_json") != expanded:
        failures.append(f"{row_label}.target_full_json must equal compact adapter expansion")

    gold = gold_lookup.get(case_id)
    if not isinstance(gold, dict):
        failures.append(f"{row_label} case_id not found in gold set: {case_id}")
        return failures
    verifier_errors = verify_conversation_brain_output(expanded, verifier_case(gold, row))
    if verifier_errors:
        failures.append(f"{row_label} expanded target failed verifier: {verifier_errors}")
    if not verifier_errors and (contract_errors or quality_issues):
        failures.append(f"{row_label} target passes verifier but violates compact value contract")
    return failures


def build_report(validation: dict[str, Any]) -> str:
    lines = [
        f"# {EXPERIMENT_ID} Dataset Validation",
        "",
        f"- Status: {validation['status']}",
        f"- Train: {validation['split_counts'].get('train', 0)}",
        f"- Validation: {validation['split_counts'].get('validation', 0)}",
        f"- Test: {validation['split_counts'].get('test', 0)}",
        f"- Compact contract: `{COMPACT_VALUE_CONTRACT_VERSION}`",
        f"- Local model calls made: false",
        f"- Provider/API/TTS calls made: false",
        "",
        "## Checks",
        "",
    ]
    for check_name, passed in validation["checks"].items():
        lines.append(f"- {check_name}: {'pass' if passed else 'fail'}")
    if validation["failures"]:
        lines.extend(["", "## Failures", ""])
        for failure in validation["failures"]:
            lines.append(f"- {failure}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    failures: list[str] = []
    split_rows: dict[str, list[dict[str, Any]]] = {}
    for split_name, path in SPLIT_PATHS.items():
        if not path.is_file():
            failures.append(f"missing split file: {rel(path)}")
            split_rows[split_name] = []
            continue
        split_rows[split_name] = read_jsonl(path)
    if not RESULT_PATH.is_file():
        failures.append(f"missing dataset result: {rel(RESULT_PATH)}")
        dataset_result: dict[str, Any] = {}
    else:
        dataset_result = read_json(RESULT_PATH)

    validate_no_provider_calls(failures)
    gold_lookup = build_gold_lookup()
    row_counter = Counter({name: len(rows) for name, rows in split_rows.items()})
    for split_name, expected_count in EXPECTED_SPLIT_COUNTS.items():
        if row_counter[split_name] != expected_count:
            failures.append(
                f"{split_name} split count expected {expected_count}, got {row_counter[split_name]}"
            )
    seen_case_ids: set[str] = set()
    for split_name, rows in split_rows.items():
        for index, row in enumerate(rows, start=1):
            case_id = str(row.get("case_id") or "")
            if case_id in seen_case_ids:
                failures.append(f"duplicate case_id across splits: {case_id}")
            seen_case_ids.add(case_id)
            failures.extend(validate_row(row, split_name, index, gold_lookup))

    if dataset_result:
        side_effects = dataset_result.get("side_effects") if isinstance(dataset_result.get("side_effects"), dict) else {}
        for key in (
            "local_model_calls_made",
            "provider_calls_made",
            "openai_api_calls_made",
            "live_tts_calls_made",
            "provider_side_effects_made",
            "model_download_attempted",
            "model_redownloaded",
            "model_weights_committed",
            "runtime_behavior_changed",
            "response_text_changed",
        ):
            if side_effects.get(key) is not False:
                failures.append(f"result.side_effects.{key} must be false")
        if dataset_result.get("raw_private_transcript_included") is not False:
            failures.append("result.raw_private_transcript_included must be false")
        if dataset_result.get("failed_qwen_outputs_used_as_targets") is not False:
            failures.append("failed_qwen_outputs_used_as_targets must be false")

    if git_model_weights_committed():
        failures.append("model weights are tracked by git")

    checks = {
        "split_files_exist": all(path.is_file() for path in SPLIT_PATHS.values()),
        "result_exists": RESULT_PATH.is_file(),
        "expected_split_counts": all(row_counter[name] == count for name, count in EXPECTED_SPLIT_COUNTS.items()),
        "all_required_fields_present": not any("missing required field" in failure for failure in failures),
        "compact_json_valid": not any("compact." in failure or "compact-to-full" in failure for failure in failures),
        "expanded_targets_pass_verifier": not any("failed verifier" in failure for failure in failures),
        "allowed_enum_values_respected": not any("value not allowed" in failure for failure in failures),
        "no_deprecated_compact_labels": not any("deprecated_label" in failure for failure in failures),
        "no_case_id_label_leaks": not any("case-ID-like" in failure or "contains case_id" in failure for failure in failures),
        "no_generic_compact_labels": not any("generic_" in failure or "generalized_sales_move" in failure for failure in failures),
        "no_raw_private_transcripts": not any("raw" in failure.lower() and "transcript" in failure.lower() for failure in failures),
        "no_provider_api_calls": not any("provider/API pattern" in failure for failure in failures),
        "no_model_weights_committed": not any("model weights" in failure for failure in failures),
        "no_fake_side_effects": not any("fake side effect" in failure for failure in failures),
        "no_internal_policy_language": not any("internal policy language" in failure for failure in failures),
        "no_unsupported_product_facts": not any("unapproved fact" in failure or "unsupported_product" in failure for failure in failures),
    }
    validation = {
        "experiment_id": EXPERIMENT_ID,
        "validated_at": utc_now(),
        "status": "pass" if not failures else "fail",
        "split_counts": dict(row_counter),
        "expected_split_counts": EXPECTED_SPLIT_COUNTS,
        "row_count": sum(row_counter.values()),
        "compact_value_contract_version": COMPACT_VALUE_CONTRACT_VERSION,
        "checks": checks,
        "failures": failures,
        "side_effects": {
            "local_model_calls_made": False,
            "provider_calls_made": False,
            "openai_api_calls_made": False,
            "live_tts_calls_made": False,
            "provider_side_effects_made": False,
        },
    }
    print(json.dumps({"status": validation["status"], "split_counts": validation["split_counts"]}, indent=2))
    if failures:
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
