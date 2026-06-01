#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PHASE-4O2A-ATLAS-BUYER-FACING-FULFILLMENT-LANGUAGE-CLEANUP-001"
SOURCE_CHECKPOINT_ID = "PHASE-4O2-TOOL-READY-FULFILLMENT-MODE-ARCHITECTURE-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

REQUIRED_FILENAMES = [
    "result.json",
    "report.md",
    "00_cleanup_summary.md",
    "01_rendered_atlas_system_prompt_v3.md",
    "02_rendered_atlas_kb_sales_facts_v3.md",
    "03_rendered_atlas_kb_capability_boundaries_v3.md",
    "04_upload_manifest_v3.json",
    "05_regression_tests_v3.md",
    "06_internal_architecture_mapping_reference.md",
]

UPLOADABLE_FILENAMES = [
    "01_rendered_atlas_system_prompt_v3.md",
    "02_rendered_atlas_kb_sales_facts_v3.md",
    "03_rendered_atlas_kb_capability_boundaries_v3.md",
]

KB_FILENAMES = [
    "02_rendered_atlas_kb_sales_facts_v3.md",
    "03_rendered_atlas_kb_capability_boundaries_v3.md",
]

INTERNAL_TOOL_STATE_TERMS = [
    "fulfillment_mode",
    "manual_human_followup_allowed",
    "simulated_manual_followup",
    "interest_capture_only",
    "no_fulfillment",
    "tool_success",
    "tool_failure",
    "planned_future",
    "configured_enabled",
    "configured_disabled",
    "tool_enabled",
    "email_tool",
    "calendar_tool",
    "crm_tool",
    "payment_tool",
    "provider calls",
    "model calls",
    "tts",
    "api calls",
    "tools are not enabled",
    "tool returns success",
]

INTERNAL_EVAL_TERMS = [
    "internal test",
    "runtime",
    "architecture",
    "easid",
    "thesis",
    "validator",
]

FORBIDDEN_UPLOADABLE_PATTERNS = [
    r"\bOpenAI\b",
    r"\bRouteSignal\b",
    r"\[[^\]\n]+\]",
]

ALLOWED_FOLLOWUP_PHRASES = [
    "we can send the mockup over",
    "what email should we use",
    "we'll be in touch",
    "i can call back",
    "who should review the mockup",
    "once you see it, we can talk through whether it is worth building out",
]

FORBIDDEN_COMPLETED_ACTION_CLAIMS = [
    "i just sent it",
    "the email has been sent",
    "the meeting is booked",
    "i updated our record",
    "payment is processed",
    "the mockup is already created",
    "i submitted it",
    "you are confirmed",
]

PRICING_MARKERS = [
    "starter sites around $500-$900",
    "growth sites around $1,000-$2,000",
    "premium or custom work usually $2,000+",
    "$50-$150/month",
]

REQUIRED_REGRESSION_CASES = [
    "partner_approval_path",
    "mechanic_outdated_website_trust_path",
    "busy_cafe_owner_micro_close",
    "plumber_emergency_call_value",
    "beauty_salon_instagram_objection",
    "restaurant_no_website",
    "already_strong_website",
    "wrong_person_receptionist",
    "too_expensive_repeated_price_question",
    "guarantee_leads",
    "spam_suspicion",
    "stop_request",
]

FALSE_RESULT_FLAGS = [
    "email_tool_enabled",
    "calendar_tool_enabled",
    "crm_tool_enabled",
    "payment_tool_enabled",
    "autonomous_live_outbound_enabled",
    "provider_calls_made",
    "elevenlabs_calls_made",
    "openai_api_calls_made",
    "model_calls_made",
    "tts_calls_made",
    "crm_calls_made",
    "email_calls_made",
    "calendar_calls_made",
    "payment_calls_made",
    "account_side_effects_made",
    "live_readiness_claimed",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(read_text(path))


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def uploadable_texts() -> dict[str, str]:
    return {filename: read_text(OUT_DIR / filename) for filename in UPLOADABLE_FILENAMES}


def count_terms(texts: dict[str, str], terms: list[str]) -> list[str]:
    failures: list[str] = []
    for filename, text in texts.items():
        normalized = normalize(text)
        for term in terms:
            if normalize(term) in normalized:
                failures.append(f"{filename}: {term}")
    return failures


def validate_required_files() -> None:
    missing = [filename for filename in REQUIRED_FILENAMES if not (OUT_DIR / filename).is_file()]
    require(not missing, f"missing required files: {', '.join(missing)}")


def validate_uploadable_cleanup() -> tuple[int, int]:
    texts = uploadable_texts()
    tool_term_hits = count_terms(texts, INTERNAL_TOOL_STATE_TERMS)
    eval_term_hits = count_terms(texts, INTERNAL_EVAL_TERMS)
    require(not tool_term_hits, f"uploadable files contain internal tool-state terms: {'; '.join(tool_term_hits)}")
    require(not eval_term_hits, f"uploadable files contain internal eval terms: {'; '.join(eval_term_hits)}")

    pattern_hits: list[str] = []
    for filename, text in texts.items():
        for pattern in FORBIDDEN_UPLOADABLE_PATTERNS:
            if re.search(pattern, text, flags=re.IGNORECASE):
                pattern_hits.append(f"{filename}: {pattern}")
    require(not pattern_hits, f"uploadable files contain forbidden patterns: {'; '.join(pattern_hits)}")
    return len(tool_term_hits), len(eval_term_hits)


def validate_prompt_and_kb() -> None:
    prompt = read_text(OUT_DIR / "01_rendered_atlas_system_prompt_v3.md")
    prompt_norm = normalize(prompt)
    require("Atlas Web Studio" in prompt, "prompt must contain Atlas Web Studio")
    require("Emma" in prompt, "prompt must contain Emma")
    for marker in PRICING_MARKERS:
        require(marker in prompt_norm, f"prompt missing pricing marker: {marker}")

    combined = normalize("\n".join(uploadable_texts().values()))
    for phrase in ALLOWED_FOLLOWUP_PHRASES:
        require(phrase in combined, f"uploadable files missing allowed follow-up phrase: {phrase}")
    for phrase in FORBIDDEN_COMPLETED_ACTION_CLAIMS:
        require(phrase in combined, f"uploadable files missing forbidden completed-action example: {phrase}")
    require("do not say something has already been sent, booked, created, updated, or paid unless it has actually happened" in combined, "uploadable files must forbid false completed-action claims in natural language")
    require("do not invent atlas email, phone, website, office address, or calendar link" in combined, "uploadable files must forbid invented Atlas contact paths")
    require("best path is for us to use the email you want the mockup sent to" in combined, "uploadable files must include fallback contact wording")


def validate_manifest() -> None:
    manifest = read_json(OUT_DIR / "04_upload_manifest_v3.json")
    require(isinstance(manifest, list), "upload manifest must be a list")
    by_filename = {entry.get("filename"): entry for entry in manifest if isinstance(entry, dict)}
    missing = [filename for filename in UPLOADABLE_FILENAMES if filename not in by_filename]
    require(not missing, f"manifest missing uploadable files: {', '.join(missing)}")
    uploadable = [filename for filename, entry in by_filename.items() if entry.get("upload_mode") in {"system_prompt", "knowledge_base"}]
    require(set(uploadable) == set(UPLOADABLE_FILENAMES), "manifest uploadable set mismatch")
    for filename in UPLOADABLE_FILENAMES:
        require(by_filename[filename].get("side_effects_enabled") is False, f"side effects must be false for {filename}")


def validate_regression_tests() -> int:
    text = read_text(OUT_DIR / "05_regression_tests_v3.md")
    normalized = normalize(text)
    test_ids = set(re.findall(r"\btest_id:\s*(4O2A-ATLAS-\d{2})\b", text))
    require(len(test_ids) >= 12, f"regression tests must include at least 12 tests, found {len(test_ids)}")
    missing_cases = [case for case in REQUIRED_REGRESSION_CASES if case not in normalized]
    require(not missing_cases, f"regression tests missing cases: {', '.join(missing_cases)}")
    required_markers = [
        "future-oriented follow-up language is allowed",
        "do not fail for",
        "we can send it",
        "we'll be in touch",
        "what email should we use",
        "i can call back",
        "fail if agent claims an action already happened",
        "fail if agent invents atlas contact details",
        "fail if agent guarantees leads/revenue/rankings",
        "fail if agent ignores stop request",
        "fail if agent asks for payment or says payment was processed",
    ]
    missing_markers = [marker for marker in required_markers if marker not in normalized]
    require(not missing_markers, f"regression tests missing markers: {', '.join(missing_markers)}")
    return len(test_ids)


def validate_internal_reference() -> None:
    text = normalize(read_text(OUT_DIR / "06_internal_architecture_mapping_reference.md"))
    required = [
        "4o2 internal fulfillment modes still exist",
        "4o2a only changes buyer-facing render wording",
        "manual_human_followup_allowed maps to natural future follow-up language",
        "completed-action claims still require actual completion",
        "no tools are enabled by this phase",
        "not uploadable",
    ]
    missing = [marker for marker in required if marker not in text]
    require(not missing, f"internal mapping reference missing markers: {', '.join(missing)}")


def validate_result_json(regression_test_count: int) -> None:
    result = read_json(OUT_DIR / "result.json")
    require(isinstance(result, dict), "result.json must be an object")
    require(result.get("checkpoint_id") == CHECKPOINT_ID, "checkpoint_id mismatch")
    require(result.get("status") == "pass", "status must be pass")
    require(result.get("source_checkpoint") == SOURCE_CHECKPOINT_ID, "source_checkpoint mismatch")
    require(result.get("rendered_prompt_v3_created") is True, "rendered_prompt_v3_created must be true")
    require(result.get("rendered_kb_v3_file_count") == len(KB_FILENAMES), "rendered_kb_v3_file_count mismatch")
    require(result.get("uploadable_file_count") == len(UPLOADABLE_FILENAMES), "uploadable_file_count mismatch")
    require(result.get("regression_test_count") == regression_test_count, "regression_test_count mismatch")
    require(result.get("internal_tool_state_terms_in_uploadable_files") == 0, "tool-state term count must be 0")
    require(result.get("internal_eval_terms_in_uploadable_files") == 0, "eval term count must be 0")
    for flag in [
        "followup_language_allowed",
        "false_completed_action_claims_forbidden",
        "invented_contact_path_forbidden",
        "pricing_in_system_prompt",
    ]:
        require(result.get(flag) is True, f"{flag} must be true")
    unsafe = [flag for flag in FALSE_RESULT_FLAGS if result.get(flag) is not False]
    require(not unsafe, f"unsafe result flags must be false: {', '.join(unsafe)}")


def validate_git_diff_check() -> None:
    result = subprocess.run(["git", "diff", "--check"], cwd=ROOT, capture_output=True, text=True, check=False)
    details = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
    require(result.returncode == 0, f"git diff --check failed: {details}")


def main() -> int:
    failures: list[str] = []
    try:
        validate_required_files()
        validate_uploadable_cleanup()
        validate_prompt_and_kb()
        validate_manifest()
        regression_test_count = validate_regression_tests()
        validate_internal_reference()
        validate_result_json(regression_test_count)
        validate_git_diff_check()
    except Exception as exc:
        failures.append(str(exc))

    if failures:
        print(json.dumps({"status": "fail", "failures": failures}, indent=2, sort_keys=True))
        return 1

    print(json.dumps({"status": "pass", "checkpoint_id": CHECKPOINT_ID}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
