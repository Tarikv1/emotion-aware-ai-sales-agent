from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PHASE-4K10A-SELECTOR-RUNTIME-RECONCILIATION-001"
GENERATED = ROOT / "research" / "experiments" / "generated"
RESULT_PATH = GENERATED / CHECKPOINT_ID / "result.json"
REPORT_PATH = GENERATED / CHECKPOINT_ID / "report.md"
REVIEW_SCRIPT = ROOT / "scripts" / "review_phase_4k10a_selector_runtime_reconciliation_001.py"
VALIDATOR_SCRIPT = ROOT / "scripts" / "validate_phase_4k10a_selector_runtime_reconciliation_001.py"
TARGET_CASE_ID = "phase_4k8_b2b_saas_003"

FORBIDDEN_IMPORT_ROOTS = {"elevenlabs", "httpx", "openai", "requests", "ultravox", "urllib"}


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def validate(result: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if result.get("checkpoint_id") != CHECKPOINT_ID:
        failures.append("checkpoint_id mismatch")
    if result.get("status") != "pass":
        failures.append(f"status must be pass: {result.get('status')}")
    if not REPORT_PATH.is_file():
        failures.append("report.md missing")
    for script in [REVIEW_SCRIPT, VALIDATOR_SCRIPT]:
        imports = sorted(imported_roots(script) & FORBIDDEN_IMPORT_ROOTS)
        if imports:
            failures.append(f"{script.relative_to(ROOT)} imports forbidden provider/network modules: {imports}")
    after = result.get("after") if isinstance(result.get("after"), dict) else {}
    if after.get("false_asr_mapping_count") != 0:
        failures.append(f"false_asr_mapping_count must remain 0: {after.get('false_asr_mapping_count')}")
    if int(after.get("naturalness_issue_count") or 999) > 14:
        failures.append(f"4K10 naturalness issue count rose above 14: {after.get('naturalness_issue_count')}")
    target = result.get("target_case") if isinstance(result.get("target_case"), dict) else {}
    if target.get("case_id") != TARGET_CASE_ID:
        failures.append("target case missing")
    if target.get("resolution_status") != "resolved_same_action":
        failures.append(f"target case must be resolved_same_action: {target.get('resolution_status')}")
    if target.get("runtime_action_id") != "respect_boundary":
        failures.append(f"target runtime action must be respect_boundary: {target.get('runtime_action_id')}")
    if target.get("selector_action_id") != "respect_boundary":
        failures.append(f"target selector action must be respect_boundary: {target.get('selector_action_id')}")
    if target.get("disagreement_review_classification") != "same_action":
        failures.append(f"target review classification must be same_action: {target.get('disagreement_review_classification')}")
    if after.get("genuine_selector_runtime_disagreement_count") != 0:
        failures.append(
            f"genuine selector/runtime disagreement count must be 0 before any readiness claim: {after.get('genuine_selector_runtime_disagreement_count')}"
        )
    acceptance = result.get("acceptance") if isinstance(result.get("acceptance"), dict) else {}
    for key, value in sorted(acceptance.items()):
        if value is not True:
            failures.append(f"acceptance.{key} must be true")
    if result.get("live_selector_control_recommended") is not False:
        failures.append("live selector control must remain false")
    if result.get("selector_control_allowed") is not False:
        failures.append("selector_control_allowed must remain false")
    if result.get("response_replacement_performed") is not False:
        failures.append("response replacement must remain false")
    if result.get("no_provider_model_tts_crm_email_calendar_side_effect_path_enabled") is not True:
        failures.append("provider/model/TTS/CRM/email/calendar side-effect path must remain disabled")
    if result.get("no_private_raw_transcript_or_audio_added_to_public_evidence") is not True:
        failures.append("private raw transcript/audio must not be added to public evidence")
    return failures


def main() -> int:
    result = read_json(RESULT_PATH)
    failures = validate(result)
    print(
        json.dumps(
            {
                "status": "pass" if not failures else "fail",
                "failure_count": len(failures),
                "failures": failures,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
