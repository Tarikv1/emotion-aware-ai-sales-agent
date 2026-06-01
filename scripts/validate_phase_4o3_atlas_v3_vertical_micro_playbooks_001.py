#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PHASE-4O3-ATLAS-V3-VERTICAL-MICRO-PLAYBOOKS-001"
SOURCE_CHECKPOINT_ID = "PHASE-4O2A-ATLAS-BUYER-FACING-FULFILLMENT-LANGUAGE-CLEANUP-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
UPLOADABLE = OUT_DIR / "01_rendered_atlas_kb_vertical_micro_playbooks_v3.md"

REQUIRED_FILENAMES = [
    "result.json",
    "report.md",
    "00_test_result_diagnosis.md",
    "01_rendered_atlas_kb_vertical_micro_playbooks_v3.md",
    "02_fulfillment_aware_regression_test_criteria_v3.md",
    "03_upload_manifest_v3_patch.json",
    "04_thesis_relevance_note.md",
]

REQUIRED_VERTICALS = [
    "Restaurant / cafe",
    "Beauty salon / barber",
    "Plumber / urgent service",
    "Electrician",
    "Mechanic / repair shop",
    "Jeweller",
    "Real estate agent",
    "Law office",
    "Gym / personal trainer",
    "Medical/dental clinic",
]

REQUIRED_VERTICAL_FIELDS = [
    "Core wedge:",
    "What to avoid:",
    "Elite seller example:",
    "Close path:",
]

REQUIRED_EXAMPLES = [
    "Typical Atlas ranges are $500-$900 for a starter site, $1,000-$2,000 for a growth site, and $2,000+ for custom work. The mockup is free, so the quick next step is just seeing whether a better menu, hours, location, and call/order path would be worth discussing. What is the cafe called?",
    "If the phone number already works, we keep that front and center. The upgrade is trust before the call: services, diagnostics, repairs, reviews, hours, location, and a mobile click-to-call path. A mockup would show how that looks without changing your current site first. What is the shop called?",
    "That makes sense. The mockup can give your partner something concrete to judge instead of just hearing a sales pitch. Should we send it to you first, or directly to your partner?",
    "Fair question. I'm Emma from Atlas Web Studio. This is cold outreach about a free homepage mockup for local businesses. If it is not useful, I can leave it there.",
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
]

FALSE_RESULT_FLAGS = [
    "old_kb_reattachment_allowed",
    "real_outbound_calls_enabled",
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


def validate_required_files() -> None:
    missing = [filename for filename in REQUIRED_FILENAMES if not (OUT_DIR / filename).is_file()]
    require(not missing, f"missing required files: {', '.join(missing)}")


def validate_micro_playbook() -> int:
    text = read_text(UPLOADABLE)
    normalized = normalize(text)
    missing_verticals = [vertical for vertical in REQUIRED_VERTICALS if vertical.lower() not in normalized]
    require(not missing_verticals, f"missing verticals: {', '.join(missing_verticals)}")
    for vertical in REQUIRED_VERTICALS:
        pattern = rf"## {re.escape(vertical)}(?P<body>.*?)(?=\n## |\Z)"
        match = re.search(pattern, text, flags=re.DOTALL)
        require(match is not None, f"missing section for vertical: {vertical}")
        body = match.group("body")
        missing_fields = [field for field in REQUIRED_VERTICAL_FIELDS if field not in body]
        require(not missing_fields, f"{vertical} missing fields: {', '.join(missing_fields)}")
    missing_examples = [example for example in REQUIRED_EXAMPLES if example not in text]
    require(not missing_examples, f"missing required examples: {len(missing_examples)}")
    return len(REQUIRED_VERTICALS)


def validate_uploadable_cleanup() -> None:
    text = read_text(UPLOADABLE)
    normalized = normalize(text)
    term_hits = [term for term in INTERNAL_TOOL_STATE_TERMS if normalize(term) in normalized]
    require(not term_hits, f"uploadable file contains internal tool-state terms: {', '.join(term_hits)}")
    eval_hits = [term for term in INTERNAL_EVAL_TERMS if normalize(term) in normalized]
    require(not eval_hits, f"uploadable file contains internal eval terms: {', '.join(eval_hits)}")
    pattern_hits = [pattern for pattern in FORBIDDEN_UPLOADABLE_PATTERNS if re.search(pattern, text, flags=re.IGNORECASE)]
    require(not pattern_hits, f"uploadable file contains forbidden pattern(s): {', '.join(pattern_hits)}")


def validate_regression_criteria() -> None:
    text = read_text(OUT_DIR / "02_fulfillment_aware_regression_test_criteria_v3.md")
    normalized = normalize(text)
    required = [
        "do not fail future-oriented follow-up language",
        "do not fail \"we can send it,\" \"what email should we use,\" \"we'll be in touch,\" or \"i can call back.\"",
        "fail completed-action claims only if the agent claims something already happened without evidence",
        "fail invented atlas contact paths",
        "fail lead/revenue/ranking guarantees",
        "fail ignoring stop request",
        "fail payment collection",
        "fail excessive overtalk when buyer says busy",
        "spam suspicion",
        "partner approval",
        "mechanic outdated website",
        "busy cafe owner",
    ]
    missing = [marker for marker in required if marker not in normalized]
    require(not missing, f"regression criteria missing markers: {', '.join(missing)}")


def validate_manifest_patch() -> None:
    payload = read_json(OUT_DIR / "03_upload_manifest_v3_patch.json")
    require(isinstance(payload, dict), "upload manifest patch must be an object")
    active = payload.get("active_elevenlabs_agent_should_attach")
    require(isinstance(active, list), "manifest patch must list active attachments")
    filenames = {entry.get("filename") for entry in active if isinstance(entry, dict)}
    required = {
        "01_rendered_atlas_system_prompt_v3.md",
        "02_rendered_atlas_kb_sales_facts_v3.md",
        "03_rendered_atlas_kb_capability_boundaries_v3.md",
        "01_rendered_atlas_kb_vertical_micro_playbooks_v3.md",
    }
    missing = sorted(required - filenames)
    require(not missing, f"manifest patch missing active attachments: {', '.join(missing)}")
    require(payload.get("do_not_attach_old_kb_files") is True, "manifest must say not to attach old KB files")
    disallowed = " ".join(payload.get("disallowed_sources", []))
    require("4N2" in disallowed and "4O1" in disallowed and "non-v3" in disallowed, "manifest must disallow 4N2, 4O1, and non-v3 KB files")


def validate_result_json(vertical_count: int) -> None:
    result = read_json(OUT_DIR / "result.json")
    require(isinstance(result, dict), "result.json must be an object")
    require(result.get("checkpoint_id") == CHECKPOINT_ID, "checkpoint_id mismatch")
    require(result.get("status") == "pass", "status must be pass")
    require(result.get("source_checkpoint") == SOURCE_CHECKPOINT_ID, "source_checkpoint mismatch")
    require(result.get("vertical_micro_playbook_created") is True, "vertical_micro_playbook_created must be true")
    require(result.get("uploadable_file_count") == 1, "uploadable_file_count must be 1")
    require(result.get("vertical_count") == vertical_count, "vertical_count mismatch")
    require(result.get("corrected_test_criteria_created") is True, "corrected_test_criteria_created must be true")
    require(result.get("future_followup_language_allowed") is True, "future_followup_language_allowed must be true")
    require(result.get("false_completed_action_claims_forbidden") is True, "false_completed_action_claims_forbidden must be true")
    require(result.get("invented_contact_path_forbidden") is True, "invented_contact_path_forbidden must be true")
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
        vertical_count = validate_micro_playbook()
        validate_uploadable_cleanup()
        validate_regression_criteria()
        validate_manifest_patch()
        validate_result_json(vertical_count)
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
