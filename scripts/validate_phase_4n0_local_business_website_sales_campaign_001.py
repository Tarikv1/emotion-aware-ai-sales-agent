#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PHASE-4N0-LOCAL-BUSINESS-WEBSITE-SALES-CAMPAIGN-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

REQUIRED_FILENAMES = [
    "result.json",
    "report.md",
    "00_campaign_summary.md",
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
    "already have a website",
    "do not need a website",
    "instagram/facebook",
    "too expensive",
    "send me info",
    "i'm busy",
    "who are you",
    "is this spam",
    "guarantee leads",
    "rank us #1 on google",
    "bad experience",
    "ask my partner",
    "call me later",
    "already have someone",
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


def load_package_text() -> str:
    parts: list[str] = []
    for filename in REQUIRED_FILENAMES:
        path = OUT_DIR / filename
        if path.suffix.lower() in {".md", ".json"} and path.is_file():
            parts.append(read_text(path))
    return "\n".join(parts)


def validate_required_files() -> None:
    missing = [filename for filename in REQUIRED_FILENAMES if not (OUT_DIR / filename).is_file()]
    require(not missing, f"missing required files: {', '.join(missing)}")


def validate_result_json() -> dict[str, Any]:
    result = read_json(OUT_DIR / "result.json")
    require(result.get("checkpoint_id") == CHECKPOINT_ID, "result.json checkpoint_id mismatch")
    require(result.get("status") == "pass", "result.json status must be pass")
    require(result.get("campaign_name") == "Local Business Website Sales Campaign", "campaign_name mismatch")
    require("free homepage/mockup" in normalize(result.get("primary_offer", "")), "primary_offer must mention free homepage/mockup")
    require(result.get("vertical_count") == len(VERTICALS), "vertical_count mismatch")
    require(isinstance(result.get("eval_case_count"), int) and result["eval_case_count"] >= 20, "eval_case_count must be at least 20")
    require(result.get("ready_for_manual_elevenlabs_upload") is True, "manual upload readiness flag must be true")

    package_files = result.get("package_files_created")
    require(isinstance(package_files, list), "package_files_created must be a list")
    missing_from_result = [filename for filename in REQUIRED_FILENAMES if filename not in package_files]
    require(not missing_from_result, f"result.json missing package file entries: {', '.join(missing_from_result)}")

    enabled = [flag for flag in FALSE_RESULT_FLAGS if result.get(flag) is not False]
    require(not enabled, f"unsafe result flags must be false: {', '.join(enabled)}")
    return result


def validate_system_prompt() -> None:
    prompt = normalize(read_text(OUT_DIR / "01_agent_system_prompt.md"))
    require("official sales agent for [agency_name]" in prompt, "system prompt must include official seller role for [AGENCY_NAME]")
    require("first conversion goal" in prompt and "free homepage mockup" in prompt, "system prompt must include first conversion goal")
    require("no real side effects" in prompt, "system prompt must include no real side effects")
    require("do not claim to be google, meta, yelp, openai" in prompt, "system prompt must block third-party impersonation")
    require("do not collect payment" in prompt, "system prompt must block payment collection")
    require("concise spoken style" in prompt, "system prompt must require concise spoken style")
    require("[emotion" not in prompt and "[internal" not in prompt, "system prompt must not include bracketed emotion/internal labels")


def validate_verticals(package_text: str) -> None:
    text = normalize(package_text)
    missing = [vertical for vertical in VERTICALS if normalize(vertical) not in text]
    require(not missing, f"missing vertical coverage: {', '.join(missing)}")


def validate_offer(package_text: str) -> None:
    text = normalize(package_text)
    require("would it be useful if we sent over a free homepage mockup" in text, "preferred free mockup close missing")
    require("internal testing placeholder - replace before real use" in text, "test pricing disclaimer missing")
    for package_name in ["starter website", "growth website", "premium website", "monthly care plan"]:
        require(package_name in text, f"missing package: {package_name}")


def validate_objections() -> None:
    objection_text = normalize(read_text(OUT_DIR / "04_objection_handling_playbook.md"))
    missing = [marker for marker in REQUIRED_OBJECTION_MARKERS if normalize(marker) not in objection_text]
    require(not missing, f"missing objection coverage: {', '.join(missing)}")


def validate_eval_script() -> int:
    eval_text = read_text(OUT_DIR / "08_manual_eval_script.md")
    case_ids = re.findall(r"^case_id:\s*(4N0-EVAL-\d{2})\s*$", eval_text, flags=re.MULTILINE)
    require(len(set(case_ids)) >= 20, "manual eval script must include at least 20 unique eval cases")

    normalized = normalize(eval_text)
    required_eval_markers = [
        "restaurant no website",
        "restaurant already uses instagram",
        "plumber emergency calls",
        "mechanic outdated website",
        "jeweller premium trust",
        "real estate agent listings",
        "beauty salon booking",
        "medical clinic trust",
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
    missing = [marker for marker in required_eval_markers if marker not in normalized]
    require(not missing, f"manual eval script missing required cases: {', '.join(missing)}")

    success_targets = {"free_mockup_yes", "review_call_yes", "qualified_followup", "disqualified", "stop_respected"}
    for target in success_targets:
        require(f"success_target: {target}" in normalized, f"missing success target: {target}")

    required_fields = ["buyer_persona:", "buyer_turns:", "expected_behavior:", "pass_fail_criteria:", "success_target:"]
    for field in required_fields:
        require(normalized.count(field) >= 20, f"manual eval script missing repeated field: {field}")
    return len(set(case_ids))


def validate_manifest() -> None:
    manifest = json.loads(read_text(OUT_DIR / "09_upload_manifest.json"))
    require(isinstance(manifest, list), "09_upload_manifest.json must be a list")
    filenames = {entry.get("filename") for entry in manifest if isinstance(entry, dict)}
    missing = [filename for filename in REQUIRED_FILENAMES if filename not in filenames]
    require(not missing, f"upload manifest missing files: {', '.join(missing)}")
    side_effect_entries = [
        entry.get("filename")
        for entry in manifest
        if isinstance(entry, dict) and entry.get("side_effects_enabled") is not False
    ]
    require(not side_effect_entries, f"manifest entries must disable side effects: {', '.join(map(str, side_effect_entries))}")


def validate_safety_text(package_text: str) -> None:
    text = normalize(package_text)
    for pattern in BAD_CLAIM_PATTERNS:
        require(re.search(pattern, text) is None, f"unsafe claim pattern present: {pattern}")

    required_boundary_markers = [
        "internal testing only",
        "no real outbound calling",
        "no autodialing",
        "no scraping",
        "before real calls, jurisdiction-specific telemarketing/ai voice compliance review is required",
        "must honor stop requests",
        "must not guarantee sales, leads, seo rankings, revenue, or conversion results",
        "must not claim live readiness",
    ]
    missing = [marker for marker in required_boundary_markers if marker not in text]
    require(not missing, f"missing safety boundary markers: {', '.join(missing)}")


def main() -> int:
    validate_required_files()
    result = validate_result_json()
    package_text = load_package_text()
    validate_system_prompt()
    validate_verticals(package_text)
    validate_offer(package_text)
    validate_objections()
    eval_case_count = validate_eval_script()
    validate_manifest()
    validate_safety_text(package_text)

    require(result.get("eval_case_count") == eval_case_count, "result eval_case_count must match manual eval script")
    print(f"PASS {CHECKPOINT_ID}: {len(VERTICALS)} verticals, {eval_case_count} eval cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
