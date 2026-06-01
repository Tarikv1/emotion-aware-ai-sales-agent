#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PHASE-4N2-FINAL-ATLAS-WEB-STUDIO-ELEVENLABS-UPLOAD-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

AGENCY_NAME = "Atlas Web Studio"
AGENT_NAME = "Emma"

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

UPLOADABLE_FILES = [
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
    "00_dashboard_upload_checklist.md": "do_not_upload",
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
    "brand_legal_clearance_claimed",
]

REQUIRED_FALSE_MANIFEST_FIELD = "side_effects_enabled"

RECOMMENDED_COLD_OPENING = (
    "Hi, this is Emma from Atlas Web Studio. I'll be honest, this is a cold call. "
    "We build websites for local businesses that help turn visitors into calls, bookings, or quote requests. "
    "Would it be useful if we prepared a free homepage mockup so you can see what this could look like for your business?"
)

SOFTER_OPENING = (
    "Hi, this is Emma from Atlas Web Studio. I'll keep it quick. "
    "We build websites for local businesses that help turn visitors into calls, bookings, or quote requests. "
    "Would seeing a free homepage mockup be worth a look?"
)

SPAM_RESPONSE = (
    "Fair question. I'm Emma from Atlas Web Studio. It is a cold outreach call, "
    "and I'm only asking whether a free homepage mockup would be useful. If not, I can leave it there."
)

INTERNAL_DEPLOYMENT_PATTERNS = [
    "internal deployment restrictions",
    "internal testing only",
    "no real outbound calls",
    "no provider, model, tts, or elevenlabs api actions",
    "no crm/email/calendar/payment/account integrations",
    "compliance review required before real calls",
]

BAD_CLAIM_PATTERNS = [
    r"\bwe guarantee (?:leads|sales|revenue|rankings|seo|calls|bookings)\b",
    r"\bguaranteed (?:leads|sales|revenue|rankings|seo|calls|bookings)\b",
    r"\bwe will rank (?:you|your business|your site) #?1\b",
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


def uploadable_text_by_file() -> dict[str, str]:
    return {filename: read_text(OUT_DIR / filename) for filename in UPLOADABLE_FILES}


def count_placeholder_brackets(text: str) -> int:
    return len(re.findall(r"\[[^\]\n]+\]", text))


def count_internal_deployment_restrictions(text: str) -> int:
    normalized = normalize(text)
    return sum(normalized.count(pattern) for pattern in INTERNAL_DEPLOYMENT_PATTERNS)


def validate_required_files() -> None:
    missing = [filename for filename in REQUIRED_FILENAMES if not (OUT_DIR / filename).is_file()]
    require(not missing, f"missing required files: {', '.join(missing)}")


def validate_uploadable_text(uploadable_text: dict[str, str]) -> tuple[str, int, int]:
    combined = "\n".join(uploadable_text.values())
    normalized = normalize(combined)

    require(AGENCY_NAME in combined, "Atlas Web Studio must appear in uploadable files")
    require(AGENT_NAME in combined, "Emma must appear in uploadable files")
    require("[AGENCY_NAME]" not in combined, "uploadable files still contain [AGENCY_NAME]")
    require("[NAME]" not in combined, "uploadable files still contain [NAME]")

    placeholder_count = count_placeholder_brackets(combined)
    require(placeholder_count == 0, f"uploadable files contain bracket placeholders: {placeholder_count}")

    internal_count = count_internal_deployment_restrictions(combined)
    require(internal_count == 0, f"uploadable files contain internal deployment restrictions: {internal_count}")
    require("internal testing only" not in normalized, "uploadable files contain internal testing only")

    for filename, text in uploadable_text.items():
        file_normalized = normalize(text)
        require("routesignal" not in file_normalized, f"{filename} mentions RouteSignal")
        require("northstar" not in file_normalized, f"{filename} mentions Northstar")
        require("internal deployment restrictions" not in file_normalized, f"{filename} has internal deployment section")
        for pattern in BAD_CLAIM_PATTERNS:
            require(re.search(pattern, file_normalized) is None, f"{filename} has unsafe claim pattern: {pattern}")

    return combined, placeholder_count, internal_count


def validate_openings() -> None:
    prompt = read_text(OUT_DIR / "01_agent_system_prompt.md")
    objections = read_text(OUT_DIR / "04_objection_handling_playbook.md")

    require(RECOMMENDED_COLD_OPENING in prompt, "recommended cold-call opening missing from system prompt")
    require(SOFTER_OPENING in prompt, "softer alternate opening missing from system prompt")
    require(SPAM_RESPONSE in objections, "truthful 'Is this spam?' response missing")


def validate_compliance_file() -> None:
    compliance = read_text(OUT_DIR / "07_compliance_and_calling_boundaries.md")
    normalized = normalize(compliance)
    require("## buyer-facing boundaries" in normalized, "compliance file must keep buyer-facing boundaries")
    require("internal deployment restrictions" not in normalized, "compliance file must not include internal deployment restrictions")
    require("internal testing only" not in normalized, "compliance file must not include internal testing only")

    required_markers = [
        "truthful identity",
        "no third-party impersonation",
        "no guarantees",
        "no payment collection",
        "honor stop requests",
        "no fake urgency",
        "no legal advice",
    ]
    missing = [marker for marker in required_markers if marker not in normalized]
    require(not missing, f"compliance file missing buyer-facing markers: {', '.join(missing)}")


def validate_counts() -> tuple[int, int]:
    eval_text = read_text(OUT_DIR / "08_manual_eval_script.md")
    eval_case_ids = re.findall(r"^case_id:\s*(4N2-EVAL-\d{2})\s*$", eval_text, flags=re.MULTILINE)
    eval_case_count = len(set(eval_case_ids))
    require(eval_case_count >= 20, "manual eval script must include at least 20 unique 4N2 cases")

    objection_text = read_text(OUT_DIR / "04_objection_handling_playbook.md")
    objection_count = len(re.findall(r'^## "', objection_text, flags=re.MULTILINE))
    require(objection_count == 16, f"objection count mismatch: {objection_count}")

    vertical_text = read_text(OUT_DIR / "03_vertical_playbooks.md")
    vertical_count = len(re.findall(r"^## .+", vertical_text, flags=re.MULTILINE))
    require(vertical_count >= 14, f"vertical count must be at least 14: {vertical_count}")
    return eval_case_count, vertical_count


def validate_manifest() -> None:
    manifest = json.loads(read_text(OUT_DIR / "09_upload_manifest.json"))
    require(isinstance(manifest, list), "09_upload_manifest.json must be a list")
    by_filename = {entry.get("filename"): entry for entry in manifest if isinstance(entry, dict)}
    missing = [filename for filename in REQUIRED_FILENAMES if filename not in by_filename]
    require(not missing, f"manifest missing files: {', '.join(missing)}")

    bad_modes = [
        f"{filename}={by_filename[filename].get('upload_mode')}"
        for filename, expected in EXPECTED_UPLOAD_MODES.items()
        if by_filename[filename].get("upload_mode") != expected
    ]
    require(not bad_modes, f"manifest upload modes mismatch: {', '.join(bad_modes)}")

    bad_uploadable = [
        filename
        for filename in REQUIRED_FILENAMES
        if bool(by_filename[filename].get("uploadable")) != (filename in UPLOADABLE_FILES)
    ]
    require(not bad_uploadable, f"manifest uploadable flags mismatch: {', '.join(bad_uploadable)}")

    side_effects = [
        filename
        for filename in REQUIRED_FILENAMES
        if by_filename[filename].get(REQUIRED_FALSE_MANIFEST_FIELD) is not False
    ]
    require(not side_effects, f"manifest side effects must be false: {', '.join(side_effects)}")

    kb_entries = [entry for entry in by_filename.values() if entry.get("upload_mode") == "upload_to_knowledge_base"]
    require(len(kb_entries) == len(KB_UPLOAD_FILES), "manifest KB upload count mismatch")


def validate_result_json(placeholder_count: int, internal_count: int, eval_case_count: int, vertical_count: int) -> None:
    result = read_json(OUT_DIR / "result.json")
    require(result.get("checkpoint_id") == CHECKPOINT_ID, "result.json checkpoint_id mismatch")
    require(result.get("status") == "pass", "result.json status must be pass")
    require(result.get("agency_name") == AGENCY_NAME, "result.json agency_name mismatch")
    require(result.get("agent_name") == AGENT_NAME, "result.json agent_name mismatch")
    require(result.get("placeholder_count_in_uploadable_files") == placeholder_count, "placeholder count mismatch")
    require(
        result.get("uploadable_internal_deployment_restriction_count") == internal_count,
        "internal deployment restriction count mismatch",
    )
    require(result.get("uploadable_file_count") == len(UPLOADABLE_FILES), "uploadable_file_count mismatch")
    require(result.get("kb_upload_file_count") == len(KB_UPLOAD_FILES), "kb_upload_file_count mismatch")
    require(result.get("eval_case_count") == eval_case_count, "eval_case_count mismatch")
    require(result.get("objection_count") == 16, "objection_count mismatch")
    require(result.get("vertical_count") == vertical_count, "vertical_count mismatch")
    require(result.get("ready_for_manual_elevenlabs_upload") is True, "ready_for_manual_elevenlabs_upload must be true")

    uploadable_files = result.get("uploadable_files")
    require(isinstance(uploadable_files, list), "result.json uploadable_files must be a list")
    missing_uploadable = [filename for filename in UPLOADABLE_FILES if filename not in uploadable_files]
    require(not missing_uploadable, f"result.json missing uploadable files: {', '.join(missing_uploadable)}")

    enabled = [flag for flag in FALSE_RESULT_FLAGS if result.get(flag) is not False]
    require(not enabled, f"unsafe result flags must be false: {', '.join(enabled)}")


def validate_reference_files() -> None:
    report = normalize(read_text(OUT_DIR / "report.md"))
    checklist = normalize(read_text(OUT_DIR / "00_dashboard_upload_checklist.md"))
    references = report + "\n" + checklist

    required_reference_markers = [
        "atlas web studio is an internal testing brand for now",
        "brand legal or trademark clearance is not claimed",
        "domain or social handle availability is not claimed",
        "no real outbound calls",
        "no scraping",
        "stop requests must be honored",
    ]
    missing = [marker for marker in required_reference_markers if marker not in references]
    require(not missing, f"reference files missing internal restriction markers: {', '.join(missing)}")


def validate_git_diff_check() -> None:
    result = subprocess.run(["git", "diff", "--check"], cwd=ROOT, capture_output=True, text=True, check=False)
    details = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
    require(result.returncode == 0, f"git diff --check failed: {details}")


def main() -> int:
    validate_required_files()
    uploadable_text = uploadable_text_by_file()
    _, placeholder_count, internal_count = validate_uploadable_text(uploadable_text)
    validate_openings()
    validate_compliance_file()
    eval_case_count, vertical_count = validate_counts()
    validate_manifest()
    validate_result_json(placeholder_count, internal_count, eval_case_count, vertical_count)
    validate_reference_files()
    validate_git_diff_check()

    print(
        f"PASS {CHECKPOINT_ID}: {len(UPLOADABLE_FILES)} uploadable files, "
        f"{len(KB_UPLOAD_FILES)} KB files, {eval_case_count} eval cases, "
        f"{placeholder_count} placeholders"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
