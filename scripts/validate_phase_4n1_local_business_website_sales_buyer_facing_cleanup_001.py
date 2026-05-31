#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PHASE-4N1-LOCAL-BUSINESS-WEBSITE-SALES-BUYER-FACING-CLEANUP-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

REQUIRED_FILENAMES = [
    "result.json",
    "report.md",
    "00_dashboard_upload_checklist.md",
    "01_agent_system_prompt.md",
    "02_website_offer_and_packages.md",
    "03_vertical_playbooks.md",
    "04_objection_handling_playbook.md",
    "05_discovery_and_qualification.md",
    "06_close_paths.md",
    "07_compliance_and_calling_boundaries.md",
    "08_manual_eval_script.md",
    "09_upload_manifest.json",
    "10_tests_to_create_in_elevenlabs.md",
]

BUYER_FACING_UPLOAD_FILES = [
    "01_agent_system_prompt.md",
    "02_website_offer_and_packages.md",
    "03_vertical_playbooks.md",
    "04_objection_handling_playbook.md",
    "05_discovery_and_qualification.md",
    "06_close_paths.md",
    "07_compliance_and_calling_boundaries.md",
]

KB_UPLOAD_FILES = [
    "02_website_offer_and_packages.md",
    "03_vertical_playbooks.md",
    "04_objection_handling_playbook.md",
    "05_discovery_and_qualification.md",
    "06_close_paths.md",
    "07_compliance_and_calling_boundaries.md",
]

EXPECTED_UPLOAD_MODES = {
    "result.json": "do_not_upload",
    "report.md": "do_not_upload",
    "00_dashboard_upload_checklist.md": "reference_only",
    "01_agent_system_prompt.md": "upload_to_system_prompt",
    "02_website_offer_and_packages.md": "upload_to_knowledge_base",
    "03_vertical_playbooks.md": "upload_to_knowledge_base",
    "04_objection_handling_playbook.md": "upload_to_knowledge_base",
    "05_discovery_and_qualification.md": "upload_to_knowledge_base",
    "06_close_paths.md": "upload_to_knowledge_base",
    "07_compliance_and_calling_boundaries.md": "upload_to_knowledge_base",
    "08_manual_eval_script.md": "do_not_upload",
    "09_upload_manifest.json": "do_not_upload",
    "10_tests_to_create_in_elevenlabs.md": "do_not_upload",
}

VERTICALS = [
    "restaurants",
    "cafes",
    "jewellers",
    "real estate agents",
    "mechanics",
    "plumbers",
    "electricians",
    "beauty salons",
    "barbers",
    "medical/dental clinics",
    "law offices",
    "cleaning companies",
    "gyms / personal trainers",
    "local home services",
]

REQUIRED_OBJECTION_MARKERS = [
    "we already have a website",
    "we do not need a website",
    "instagram/facebook",
    "too expensive",
    "send me info",
    "i'm busy",
    "who are you",
    "is this spam",
    "guarantee leads",
    "rank us #1 on google",
    "bad agency experience",
    "ask my partner",
    "call me later",
    "already have someone",
    "wrong person",
    "stop calling",
]

FORBIDDEN_BUYER_PHRASES = [
    "internal test",
    "internal testing",
    "test script",
    "simulator",
    "dashboard",
    "evaluator",
    "validation",
    "phase",
    "checkpoint",
    "package",
    "mock environment",
    "in this test script",
    "in this phase",
    "no real side effects are available",
    "tool is enabled",
    "tools are enabled",
    "no calendar tool",
    "no calling tool",
]

FALSE_RESULT_FLAGS = [
    "real_outbound_calls_enabled",
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

BAD_CLAIM_PATTERNS = [
    r"\bwe guarantee (?:leads|sales|revenue|rankings|seo)\b",
    r"\bguaranteed (?:leads|sales|revenue|rankings|seo)\b",
    r"\brank (?:you|your business|your site) #?1\b",
    r"\bwe are (?:google|meta|facebook|yelp|openai)\b",
    r"\bcalling from (?:google|meta|facebook|yelp|openai)\b",
    r"\bofficial (?:google|meta|facebook|yelp|openai) partner\b",
    r"\bproduction ready\b",
    r"\bready for live outbound\b",
    r"\blive calls enabled\b",
]


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(read_text(path))
    return payload if isinstance(payload, dict) else {}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def compliance_buyer_section(text: str) -> str:
    match = re.search(
        r"## A\. Buyer-facing boundaries(?P<section>.*?)## B\. Internal deployment restrictions",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    require(match is not None, "07_compliance_and_calling_boundaries.md must separate buyer-facing and internal sections")
    return match.group("section")


def buyer_facing_text(filename: str) -> str:
    text = read_text(OUT_DIR / filename)
    if filename == "07_compliance_and_calling_boundaries.md":
        return compliance_buyer_section(text)
    return text


def all_buyer_facing_text() -> str:
    return "\n".join(buyer_facing_text(filename) for filename in BUYER_FACING_UPLOAD_FILES)


def count_forbidden_phrases(text: str) -> int:
    normalized = normalize(text)
    return sum(normalized.count(phrase) for phrase in FORBIDDEN_BUYER_PHRASES)


def validate_required_files() -> None:
    missing = [filename for filename in REQUIRED_FILENAMES if not (OUT_DIR / filename).is_file()]
    require(not missing, f"missing required files: {', '.join(missing)}")


def validate_result_json(buyer_text: str, eval_case_count: int) -> dict[str, Any]:
    result = read_json(OUT_DIR / "result.json")
    require(result.get("checkpoint_id") == CHECKPOINT_ID, "result.json checkpoint_id mismatch")
    require(result.get("status") == "pass", "result.json status must be pass")

    forbidden_count = count_forbidden_phrases(buyer_text)
    placeholder_count = buyer_text.count("[AGENCY_NAME]")
    require(result.get("buyer_facing_internal_test_phrase_count") == forbidden_count, "internal-test phrase count mismatch")
    require(forbidden_count == 0, "buyer-facing upload text contains forbidden internal/test wording")
    require(
        result.get("buyer_facing_placeholder_agency_name_count") == placeholder_count,
        "buyer-facing [AGENCY_NAME] placeholder count mismatch",
    )
    require(placeholder_count > 0, "buyer-facing files should retain [AGENCY_NAME] setup placeholders before manual replacement")
    require(result.get("upload_ready_after_agency_name_replacement") is True, "upload readiness flag must be true")

    buyer_files = result.get("buyer_facing_files_created")
    require(isinstance(buyer_files, list), "buyer_facing_files_created must be a list")
    missing_buyer_files = [filename for filename in BUYER_FACING_UPLOAD_FILES if filename not in buyer_files]
    require(not missing_buyer_files, f"result missing buyer-facing file entries: {', '.join(missing_buyer_files)}")

    require(result.get("kb_upload_file_count") == len(KB_UPLOAD_FILES), "kb_upload_file_count mismatch")
    require(result.get("eval_case_count") == eval_case_count, "eval_case_count mismatch")
    require(result.get("objection_count") == len(REQUIRED_OBJECTION_MARKERS), "objection_count mismatch")
    require(result.get("vertical_count") >= len(VERTICALS), "vertical_count must be at least 14")

    enabled = [flag for flag in FALSE_RESULT_FLAGS if result.get(flag) is not False]
    require(not enabled, f"unsafe result flags must be false: {', '.join(enabled)}")
    return result


def validate_buyer_facing_cleanup(buyer_text: str) -> None:
    normalized = normalize(buyer_text)
    found = [phrase for phrase in FORBIDDEN_BUYER_PHRASES if phrase in normalized]
    require(not found, f"forbidden buyer-facing phrases present: {', '.join(found)}")
    require("routesignal" not in normalized and "northstar" not in normalized, "buyer-facing upload text must not mention RouteSignal or Northstar")

    for pattern in BAD_CLAIM_PATTERNS:
        require(re.search(pattern, normalized) is None, f"unsafe claim pattern present: {pattern}")


def validate_system_prompt() -> None:
    prompt = normalize(read_text(OUT_DIR / "01_agent_system_prompt.md"))
    required_markers = [
        "you are the official sales agent for [agency_name]",
        "sell local business websites",
        "free mockup/demo",
        "you are not a passive assistant",
        "do not over-explain",
        "diagnose quickly",
        "calls, bookings, quote requests, walk-ins, trust, and credibility",
        "low-risk",
        "micro-commitment",
        "disqualify politely",
        "stop immediately",
        "never use bracketed emotion/internal labels",
        "hi, this is [name] from [agency_name]",
    ]
    missing = [marker for marker in required_markers if marker not in prompt]
    require(not missing, f"system prompt missing markers: {', '.join(missing)}")
    require("[emotion" not in prompt and "[internal" not in prompt, "system prompt must not include bracketed emotion/internal labels")


def validate_verticals(buyer_text: str) -> None:
    text = normalize(buyer_text)
    missing = [vertical for vertical in VERTICALS if normalize(vertical) not in text]
    require(not missing, f"missing vertical coverage: {', '.join(missing)}")


def validate_objections() -> None:
    objection_text = normalize(read_text(OUT_DIR / "04_objection_handling_playbook.md"))
    missing = [marker for marker in REQUIRED_OBJECTION_MARKERS if normalize(marker) not in objection_text]
    require(not missing, f"missing objection coverage: {', '.join(missing)}")


def validate_close_paths() -> None:
    close_text = normalize(read_text(OUT_DIR / "06_close_paths.md"))
    for marker in ["free mockup yes", "review call yes", "qualified follow-up", "send info / send mockup", "wrong person / referral to decision maker", "disqualified", "stop respected"]:
        require(marker in close_text, f"close paths missing marker: {marker}")


def validate_compliance_file() -> None:
    compliance = read_text(OUT_DIR / "07_compliance_and_calling_boundaries.md")
    buyer_section = normalize(compliance_buyer_section(compliance))
    internal_section = normalize(compliance.split("## B. Internal deployment restrictions", 1)[1])

    buyer_markers = [
        "truthful identity",
        "no third-party impersonation",
        "no guarantees",
        "no payment collection",
        "honor stop requests",
        "no fake urgency",
        "no legal advice",
    ]
    missing_buyer = [marker for marker in buyer_markers if marker not in buyer_section]
    require(not missing_buyer, f"compliance buyer-facing section missing: {', '.join(missing_buyer)}")

    internal_markers = [
        "internal testing only for now",
        "no real outbound calls",
        "no autodialing",
        "no scraping",
        "no crm/email/calendar/payment/account integrations",
        "compliance review required before real calls",
    ]
    missing_internal = [marker for marker in internal_markers if marker not in internal_section]
    require(not missing_internal, f"compliance internal section missing: {', '.join(missing_internal)}")


def validate_manifest() -> None:
    manifest = json.loads(read_text(OUT_DIR / "09_upload_manifest.json"))
    require(isinstance(manifest, list), "09_upload_manifest.json must be a list")
    by_filename = {entry.get("filename"): entry for entry in manifest if isinstance(entry, dict)}
    missing = [filename for filename in REQUIRED_FILENAMES if filename not in by_filename]
    require(not missing, f"upload manifest missing files: {', '.join(missing)}")

    bad_modes = [
        f"{filename}={by_filename[filename].get('upload_mode')}"
        for filename, expected_mode in EXPECTED_UPLOAD_MODES.items()
        if by_filename[filename].get("upload_mode") != expected_mode
    ]
    require(not bad_modes, f"manifest upload modes mismatch: {', '.join(bad_modes)}")

    side_effect_entries = [
        entry.get("filename")
        for entry in by_filename.values()
        if entry.get("side_effects_enabled") is not False
    ]
    require(not side_effect_entries, f"manifest entries must disable side effects: {', '.join(map(str, side_effect_entries))}")

    kb_entries = [entry for entry in by_filename.values() if entry.get("upload_mode") == "upload_to_knowledge_base"]
    require(len(kb_entries) == len(KB_UPLOAD_FILES), "manifest KB upload count mismatch")


def validate_checklist() -> None:
    checklist = read_text(OUT_DIR / "00_dashboard_upload_checklist.md")
    require(
        "Before uploading to ElevenLabs, replace every [AGENCY_NAME] placeholder with the real agency name. Do not upload with the placeholder still present."
        in checklist,
        "checklist must warn that [AGENCY_NAME] must be replaced before upload",
    )


def validate_eval_script() -> int:
    eval_text = read_text(OUT_DIR / "08_manual_eval_script.md")
    case_ids = re.findall(r"^case_id:\s*(4N1-EVAL-\d{2})\s*$", eval_text, flags=re.MULTILINE)
    require(len(set(case_ids)) >= 20, "manual eval script must include at least 20 unique 4N1 eval cases")

    normalized = normalize(eval_text)
    required_success_checks = [
        "no internal-test wording in buyer-facing answer",
        "no fake third-party identity",
        "no fake guarantee",
        "clear micro-close",
        "stop request honored",
        "no bracketed labels",
    ]
    missing_checks = [marker for marker in required_success_checks if marker not in normalized]
    require(not missing_checks, f"manual eval script missing success checks: {', '.join(missing_checks)}")

    required_case_markers = [
        "restaurant no website",
        "restaurant already uses instagram",
        "plumber emergency calls",
        "mechanic outdated website",
        "jeweller premium trust",
        "real estate agent listings",
        "beauty salon booking",
        "medical clinic trust and appointment info",
        "law office consultation request",
        "gym/personal trainer",
        "business already has website",
        "too expensive",
        "send me info",
        "busy owner",
        "who are you / is this spam",
        "guarantee leads objection",
        "seo ranking objection",
        "partner approval",
        "wrong person",
        "stop request",
    ]
    missing_cases = [marker for marker in required_case_markers if marker not in normalized]
    require(not missing_cases, f"manual eval script missing source cases: {', '.join(missing_cases)}")

    required_fields = ["buyer_persona:", "buyer_turns:", "expected_behavior:", "pass_fail_criteria:", "success_target:"]
    for field in required_fields:
        require(normalized.count(field) >= 20, f"manual eval script missing repeated field: {field}")
    return len(set(case_ids))


def validate_git_diff_check() -> None:
    result = subprocess.run(["git", "diff", "--check"], cwd=ROOT, capture_output=True, text=True, check=False)
    details = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
    require(result.returncode == 0, f"git diff --check failed: {details}")


def main() -> int:
    validate_required_files()
    buyer_text = all_buyer_facing_text()
    validate_buyer_facing_cleanup(buyer_text)
    validate_system_prompt()
    validate_verticals(buyer_text)
    validate_objections()
    validate_close_paths()
    validate_compliance_file()
    validate_manifest()
    validate_checklist()
    eval_case_count = validate_eval_script()
    result = validate_result_json(buyer_text, eval_case_count)
    validate_git_diff_check()

    print(
        f"PASS {CHECKPOINT_ID}: {result['kb_upload_file_count']} KB files, "
        f"{eval_case_count} eval cases, "
        f"{result['buyer_facing_placeholder_agency_name_count']} [AGENCY_NAME] placeholders"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
