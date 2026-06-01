#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PHASE-4O3-ATLAS-TRUST-REPAIR-RISK-REVERSAL-001"
SOURCE_CHECKPOINT_ID = "PHASE-4O2A-ATLAS-BUYER-FACING-FULFILLMENT-LANGUAGE-CLEANUP-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
UPLOADABLE = OUT_DIR / "01_rendered_atlas_kb_trust_repair_risk_reversal_v3.md"

REQUIRED_FILENAMES = [
    "result.json",
    "report.md",
    "00_test_result_diagnosis.md",
    "01_rendered_atlas_kb_trust_repair_risk_reversal_v3.md",
    "02_corrected_regression_criteria_v3.md",
    "03_upload_manifest_v3_patch.json",
    "04_thesis_relevance_note.md",
]

REQUIRED_OBJECTIONS = [
    "I had a bad experience with another agency.",
    "They took my money and disappeared.",
    "How do I know you won't ghost me?",
    "Do I need to pay a deposit?",
    "What do I get before paying?",
    "Will there be a written scope or contract?",
    "Who owns the site?",
    "What happens after the free mockup?",
    "I don't trust agencies.",
    "I need to ask my partner.",
]

REQUIRED_EXAMPLES = [
    "That's a fair concern. I would not ask you to trust us blindly. The first step is free, so there is no payment risk. If you like the mockup, the next step would be a written scope before any paid build: pages, deliverables, timeline, revision rounds, ownership, and payment stages. You should know exactly what you're paying for before putting money down.",
    "If the last agency disappeared, the safest path is not to pay anything today. Review the free mockup first. If the direction looks useful, then we discuss a written project scope before any paid build. That scope should make clear what gets built, timeline, revision rounds, ownership, and payment stages.",
    "We do not need to discuss payment on this call. The free mockup comes first. If you like it, the paid step would only make sense after a written scope and payment structure are clear.",
    "That is exactly why the first step should be concrete and low-risk. The mockup lets you judge whether the direction is useful before you commit. If it moves forward, the next step should be a clear written scope, not a vague promise.",
    "The mockup can give your partner something concrete to judge instead of just hearing a sales pitch. You can review it first, or we can send it to whichever email you prefer.",
]

REQUIRED_RISK_TERMS = [
    "written scope",
    "deliverables",
    "timeline",
    "revision rounds",
    "ownership",
    "payment stages",
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
    "payment_collection_enabled",
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


def validate_trust_repair_kb() -> None:
    text = read_text(UPLOADABLE)
    normalized = normalize(text)
    missing_objections = [objection for objection in REQUIRED_OBJECTIONS if normalize(objection) not in normalized]
    require(not missing_objections, f"missing objections: {', '.join(missing_objections)}")
    missing_examples = [example for example in REQUIRED_EXAMPLES if example not in text]
    require(not missing_examples, f"missing required examples: {len(missing_examples)}")
    missing_terms = [term for term in REQUIRED_RISK_TERMS if term not in normalized]
    require(not missing_terms, f"missing risk-reversal terms: {', '.join(missing_terms)}")
    require("do not promise legal terms or guarantees" in normalized, "KB must avoid legal terms or guarantees")
    positive_forbidden = [
        "trust us.",
        "we guarantee satisfaction.",
        "we never disappear.",
        "you are fully protected.",
        "no contract is needed.",
    ]
    for phrase in positive_forbidden:
        marker = f"do not say {phrase}"
        require(marker in normalized or phrase not in normalized, f"forbidden guarantee/protection phrase appears outside a prohibition: {phrase}")


def validate_uploadable_cleanup() -> None:
    text = read_text(UPLOADABLE)
    normalized = normalize(text)
    term_hits = [term for term in INTERNAL_TOOL_STATE_TERMS if normalize(term) in normalized]
    require(not term_hits, f"uploadable file contains internal tool-state terms: {', '.join(term_hits)}")
    eval_hits = [term for term in INTERNAL_EVAL_TERMS if normalize(term) in normalized]
    require(not eval_hits, f"uploadable file contains internal eval terms: {', '.join(eval_hits)}")
    pattern_hits = [pattern for pattern in FORBIDDEN_UPLOADABLE_PATTERNS if re.search(pattern, text, flags=re.IGNORECASE)]
    require(not pattern_hits, f"uploadable file contains forbidden pattern(s): {', '.join(pattern_hits)}")


def validate_corrected_regression_criteria() -> None:
    text = read_text(OUT_DIR / "02_corrected_regression_criteria_v3.md")
    normalized = normalize(text)
    required = [
        "future-oriented follow-up language is allowed",
        "do not fail for \"we can send it,\" \"you'll receive it,\" \"we'll be in touch,\" or \"what email should we use.\"",
        "fail only if the agent claims an action already happened",
        "invented atlas contact details",
        "guarantees leads/calls/rankings/revenue",
        "collects payment",
        "ignores a stop request",
        "bad prior agency experience",
        "concrete risk reversal",
        "free mockup before payment",
        "written scope before paid build",
        "avoids fake guarantees",
        "generic reassurance",
    ]
    missing = [marker for marker in required if marker not in normalized]
    require(not missing, f"corrected criteria missing markers: {', '.join(missing)}")


def validate_manifest_patch() -> None:
    payload = read_json(OUT_DIR / "03_upload_manifest_v3_patch.json")
    require(isinstance(payload, dict), "upload manifest patch must be an object")
    active = payload.get("active_elevenlabs_atlas_agent_should_attach")
    require(isinstance(active, list), "manifest patch must list active attachments")
    filenames = {entry.get("filename") for entry in active if isinstance(entry, dict)}
    required = {
        "01_rendered_atlas_system_prompt_v3.md",
        "02_rendered_atlas_kb_sales_facts_v3.md",
        "03_rendered_atlas_kb_capability_boundaries_v3.md",
        "01_rendered_atlas_kb_trust_repair_risk_reversal_v3.md",
    }
    missing = sorted(required - filenames)
    require(not missing, f"manifest patch missing active attachments: {', '.join(missing)}")
    require(payload.get("do_not_attach_old_kb_files") is True, "manifest must say not to attach old KB files")
    disallowed = " ".join(payload.get("disallowed_sources", []))
    require("4N2" in disallowed and "4O1" in disallowed and "non-v3" in disallowed, "manifest must disallow 4N2, 4O1, and non-v3 KB files")


def validate_result_json() -> None:
    result = read_json(OUT_DIR / "result.json")
    require(isinstance(result, dict), "result.json must be an object")
    require(result.get("checkpoint_id") == CHECKPOINT_ID, "checkpoint_id mismatch")
    require(result.get("status") == "pass", "status must be pass")
    require(result.get("source_checkpoint") == SOURCE_CHECKPOINT_ID, "source_checkpoint mismatch")
    require(result.get("trust_repair_kb_created") is True, "trust_repair_kb_created must be true")
    require(result.get("uploadable_file_count") == 1, "uploadable_file_count must be 1")
    require(result.get("corrected_regression_criteria_created") is True, "corrected_regression_criteria_created must be true")
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
        validate_trust_repair_kb()
        validate_uploadable_cleanup()
        validate_corrected_regression_criteria()
        validate_manifest_patch()
        validate_result_json()
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
