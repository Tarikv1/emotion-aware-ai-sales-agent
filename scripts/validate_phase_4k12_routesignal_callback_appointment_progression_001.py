from __future__ import annotations

import ast
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


CHECKPOINT_ID = "PHASE-4K12-ROUTESIGNAL-CALLBACK-APPOINTMENT-PROGRESSION-001"
GENERATED = ROOT / "research" / "experiments" / "generated"
OUT_DIR = GENERATED / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
REVIEW_SCRIPT = ROOT / "scripts" / "review_phase_4k12_routesignal_callback_appointment_progression_001.py"
VALIDATOR_SCRIPT = ROOT / "scripts" / "validate_phase_4k12_routesignal_callback_appointment_progression_001.py"
SHADOW_EXPANSION_ID = "NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-EXPANSION-001"
SHADOW_EXPANSION_JSONL = GENERATED / SHADOW_EXPANSION_ID / "shadow_expansion_records.jsonl"

FORBIDDEN_IMPORT_ROOTS = {"elevenlabs", "httpx", "openai", "requests", "ultravox", "urllib"}
FORBIDDEN_PUBLIC_SHADOW_KEYS = {
    "candidate_response",
    "response_text",
    "agent_response",
    "final_response",
    "audio",
    "audio_path",
    "audio_file",
    "wav_path",
    "mp3_path",
    "raw_url",
}


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
            raise ValueError(f"{path}:{line_number} is not a JSON object")
        rows.append(payload)
    return rows


def imported_roots(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def nested_key_hits(value: Any, forbidden: set[str]) -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) in forbidden:
                hits.append(str(key))
            hits.extend(nested_key_hits(child, forbidden))
    elif isinstance(value, list):
        for child in value:
            hits.extend(nested_key_hits(child, forbidden))
    return hits


def validate_result(failures: list[str], result: dict[str, Any]) -> None:
    if result.get("checkpoint_id") != CHECKPOINT_ID:
        failures.append("checkpoint_id mismatch")
    if result.get("status") != "pass":
        failures.append(f"status must be pass: {result.get('status')}")
    if not REPORT_PATH.is_file():
        failures.append("report.md missing")
    acceptance = result.get("acceptance") if isinstance(result.get("acceptance"), dict) else {}
    for key, value in acceptance.items():
        if value is not True:
            failures.append(f"acceptance {key} must be true: {value}")
    statuses = result.get("live_demo_statuses") if isinstance(result.get("live_demo_statuses"), dict) else {}
    for short_id in ["LIVE-DEMO-002", "LIVE-DEMO-009", "LIVE-DEMO-014"]:
        payload = statuses.get(short_id) if isinstance(statuses.get(short_id), dict) else {}
        if payload.get("passed") is not True or payload.get("failure_count") != 0:
            failures.append(f"{short_id} must pass with zero failures: {payload}")
        if payload.get("provider_calls_made") is not False:
            failures.append(f"{short_id} provider_calls_made must be false")
    prior = result.get("prior_evidence") if isinstance(result.get("prior_evidence"), dict) else {}
    if int(prior.get("phase_4k10_after_naturalness_issue_count") or 999) > 14:
        failures.append(f"4K10 naturalness issue count must stay <=14: {prior.get('phase_4k10_after_naturalness_issue_count')}")
    if prior.get("false_asr_mapping_count") != 0:
        failures.append(f"false_asr_mapping_count must remain 0: {prior.get('false_asr_mapping_count')}")
    if prior.get("genuine_selector_runtime_disagreement_count") != 0:
        failures.append(
            "genuine_selector_runtime_disagreement_count must remain 0: "
            f"{prior.get('genuine_selector_runtime_disagreement_count')}"
        )
    if result.get("public_openai_plan_dialogue_modified") is not False:
        failures.append("public OpenAI plan dialogue must remain unmodified")
    for key in [
        "provider_calls_made",
        "model_calls_made",
        "openai_api_calls_made",
        "ultravox_calls_made",
        "elevenlabs_calls_made",
        "local_llm_calls_made",
        "ollama_calls_made",
        "tts_calls_made",
        "crm_calls_made",
        "email_calls_made",
        "calendar_calls_made",
        "payment_calls_made",
        "account_side_effects_made",
        "selector_control_allowed",
        "live_selector_control_recommended",
        "response_replacement_performed",
        "side_effects_allowed",
        "raw_private_data",
        "raw_transcript_or_audio_public",
    ]:
        if result.get(key) is not False:
            failures.append(f"{key} must be false: {result.get(key)}")


def validate_shadow_records(failures: list[str]) -> None:
    rows = read_jsonl(SHADOW_EXPANSION_JSONL)
    for index, row in enumerate(rows, start=1):
        hits = nested_key_hits(row, FORBIDDEN_PUBLIC_SHADOW_KEYS)
        if hits:
            failures.append(f"public shadow row {index} contains forbidden raw response/audio keys: {sorted(set(hits))}")


def validate_script_imports(failures: list[str]) -> None:
    for path in [REVIEW_SCRIPT, VALIDATOR_SCRIPT]:
        roots = imported_roots(path)
        forbidden = sorted(roots & FORBIDDEN_IMPORT_ROOTS)
        if forbidden:
            failures.append(f"{path.name} imports forbidden provider/network roots: {forbidden}")


def main() -> int:
    failures: list[str] = []
    result = read_json(RESULT_PATH)
    validate_result(failures, result)
    validate_shadow_records(failures)
    validate_script_imports(failures)
    if failures:
        print(json.dumps({"status": "fail", "failures": failures}, indent=2, sort_keys=True))
        raise AssertionError(f"{CHECKPOINT_ID} failed with {len(failures)} issue(s). See {RESULT_PATH}.")
    print(json.dumps({"status": "pass", "checkpoint_id": CHECKPOINT_ID}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
