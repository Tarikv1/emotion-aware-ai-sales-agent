#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PHASE-4O1-ATLAS-CAMPAIGN-INTAKE-ADAPTER-RENDER-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

REQUIRED_FILENAMES = [
    "result.json",
    "report.md",
    "00_atlas_campaign_intake.md",
    "01_atlas_campaign_intake.json",
    "02_intake_validation_report.md",
    "03_atlas_campaign_adapter.md",
    "04_atlas_campaign_adapter.json",
    "05_rendered_atlas_system_prompt.md",
    "06_rendered_atlas_kb_sales_facts.md",
    "07_rendered_atlas_kb_vertical_playbooks.md",
    "08_rendered_atlas_kb_objection_handling.md",
    "09_rendered_atlas_kb_capability_boundaries.md",
    "10_rendered_atlas_upload_manifest.json",
    "11_atlas_regression_tests.md",
    "12_dashboard_failure_analysis.md",
    "13_thesis_relevance_note.md",
]

KB_FILENAMES = [
    "06_rendered_atlas_kb_sales_facts.md",
    "07_rendered_atlas_kb_vertical_playbooks.md",
    "08_rendered_atlas_kb_objection_handling.md",
    "09_rendered_atlas_kb_capability_boundaries.md",
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

REQUIRED_DASHBOARD_CASES = [
    "restaurant_no_website",
    "beauty_salon_instagram_booking",
    "plumber_emergency_call",
    "already_has_strong_website",
]

REQUIRED_PRICING_MARKERS = [
    "These are internal test ranges, not final public pricing. Replace before real commercial use.",
    "Starter Website: $500-$900",
    "Growth Website: $1,000-$2,000",
    "Premium/custom: $2,000+",
    "Monthly Care Plan: optional, $50-$150/month",
    "replace-before-real-use",
]

FORBIDDEN_SIDE_EFFECT_CLAIMS = [
    "I sent the email",
    "I booked the meeting",
    "I scheduled the callback",
    "I updated the CRM",
    "I created the mockup",
    "I submitted anything",
]

SAFER_WORDING = [
    "The next step would be",
    "Who would normally review that?",
    "What information would be useful for preparing the mockup?",
    "The agency could follow up",
    "If you want to proceed, the next step is",
]

PROMPT_FORBIDDEN_PATTERNS = [
    r"\bOpenAI\b",
    r"\bRouteSignal\b",
    r"\[[^\]\n]+\]",
    r"\binternal test\b",
    r"\bevaluation\b",
    r"\breplace-before-real-use\b",
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


def validate_intake_and_adapter() -> None:
    intake = read_json(OUT_DIR / "01_atlas_campaign_intake.json")
    adapter = read_json(OUT_DIR / "04_atlas_campaign_adapter.json")
    require(isinstance(intake, dict), "Atlas intake must be a JSON object")
    require(isinstance(adapter, dict), "Atlas adapter must be a JSON object")
    require(intake.get("company_name") == "Atlas Web Studio", "intake company_name mismatch")
    require(intake.get("agent_name") == "Emma", "intake agent_name mismatch")
    require(intake.get("product_category") == "local business websites", "intake product_category mismatch")
    require(adapter.get("campaign_id") == intake.get("campaign_id"), "adapter campaign_id must match intake")
    require(adapter.get("tool_capability_boundaries", {}).get("side_effects_allowed") is False, "adapter side effects must be false")


def validate_pricing_policy() -> None:
    combined = "\n".join(
        read_text(OUT_DIR / filename)
        for filename in [
            "00_atlas_campaign_intake.md",
            "01_atlas_campaign_intake.json",
            "02_intake_validation_report.md",
            "03_atlas_campaign_adapter.md",
            "04_atlas_campaign_adapter.json",
            "06_rendered_atlas_kb_sales_facts.md",
        ]
    )
    missing = [marker for marker in REQUIRED_PRICING_MARKERS if marker not in combined]
    require(not missing, f"pricing policy missing markers: {', '.join(missing)}")


def validate_capability_boundaries() -> None:
    combined = "\n".join(read_text(OUT_DIR / filename) for filename in ["05_rendered_atlas_system_prompt.md", "09_rendered_atlas_kb_capability_boundaries.md"])
    missing_forbidden = [claim for claim in FORBIDDEN_SIDE_EFFECT_CLAIMS if claim not in combined]
    require(not missing_forbidden, f"capability boundary missing forbidden claims: {', '.join(missing_forbidden)}")
    missing_safer = [phrase for phrase in SAFER_WORDING if phrase not in combined]
    require(not missing_safer, f"capability boundary missing safer wording: {', '.join(missing_safer)}")


def validate_rendered_prompt() -> None:
    prompt = read_text(OUT_DIR / "05_rendered_atlas_system_prompt.md")
    require("Atlas Web Studio" in prompt, "rendered prompt must contain Atlas Web Studio")
    require("Emma" in prompt, "rendered prompt must contain Emma")
    hits = [pattern for pattern in PROMPT_FORBIDDEN_PATTERNS if re.search(pattern, prompt, flags=re.IGNORECASE)]
    require(not hits, f"rendered prompt contains forbidden pattern(s): {', '.join(hits)}")
    require("free homepage mockup" in prompt.lower(), "rendered prompt must include free homepage mockup close")
    require("no fake guarantees" in prompt.lower(), "rendered prompt must include no fake guarantees")
    require("stop" in prompt.lower(), "rendered prompt must include stop handling")


def validate_kb_and_manifest() -> None:
    for filename in KB_FILENAMES:
        require((OUT_DIR / filename).is_file(), f"missing KB file: {filename}")
    manifest = read_json(OUT_DIR / "10_rendered_atlas_upload_manifest.json")
    require(isinstance(manifest, list), "upload manifest must be a list")
    by_filename = {entry.get("filename"): entry for entry in manifest if isinstance(entry, dict)}
    expected = ["05_rendered_atlas_system_prompt.md", *KB_FILENAMES]
    missing = [filename for filename in expected if filename not in by_filename]
    require(not missing, f"manifest missing uploadable files: {', '.join(missing)}")
    side_effects = [filename for filename in expected if by_filename[filename].get("side_effects_enabled") is not False]
    require(not side_effects, f"manifest side effects must be false: {', '.join(side_effects)}")


def validate_regression_tests() -> int:
    text = read_text(OUT_DIR / "11_atlas_regression_tests.md")
    test_ids = set(re.findall(r"\btest_id:\s*(4O1-ATLAS-\d{2})\b", text))
    require(len(test_ids) >= 12, f"regression tests must include at least 12 tests, found {len(test_ids)}")
    missing_cases = [case for case in REQUIRED_DASHBOARD_CASES if case not in text]
    require(not missing_cases, f"regression tests missing dashboard cases: {', '.join(missing_cases)}")
    required_markers = [
        "source_failure_if_any:",
        "universal_or_campaign_failure:",
        "scenario:",
        "expected behavior:",
        "pass/fail criteria:",
        "target outcome:",
        "relevant EASID fields:",
    ]
    missing_markers = [marker for marker in required_markers if marker not in text]
    require(not missing_markers, f"regression tests missing markers: {', '.join(missing_markers)}")
    return len(test_ids)


def validate_validation_report() -> tuple[int, int]:
    text = read_text(OUT_DIR / "02_intake_validation_report.md")
    required_markers = [
        "blocker_count:",
        "warning_count:",
        "optional_count:",
        "missing_fields:",
        "pricing_policy_status:",
        "proof_point_status:",
        "side_effect_risk_status:",
        "fake_guarantee_risk_status:",
        "upload_ready_status:",
    ]
    missing = [marker for marker in required_markers if marker not in text]
    require(not missing, f"validation report missing markers: {', '.join(missing)}")
    blocker_match = re.search(r"blocker_count:\s*(\d+)", text)
    warning_match = re.search(r"warning_count:\s*(\d+)", text)
    require(blocker_match is not None, "validation report missing blocker count value")
    require(warning_match is not None, "validation report missing warning count value")
    return int(blocker_match.group(1)), int(warning_match.group(1))


def validate_result_json(regression_test_count: int, blocker_count: int, warning_count: int) -> None:
    result = read_json(OUT_DIR / "result.json")
    require(isinstance(result, dict), "result.json must be an object")
    require(result.get("checkpoint_id") == CHECKPOINT_ID, "checkpoint_id mismatch")
    require(result.get("status") == "pass", "status must be pass")
    require(result.get("atlas_intake_created") is True, "atlas_intake_created must be true")
    require(result.get("atlas_adapter_created") is True, "atlas_adapter_created must be true")
    require(result.get("rendered_prompt_created") is True, "rendered_prompt_created must be true")
    require(result.get("rendered_kb_file_count") == len(KB_FILENAMES), "rendered_kb_file_count mismatch")
    require(result.get("regression_test_count") == regression_test_count, "regression_test_count mismatch")
    require(result.get("intake_blocker_count") == blocker_count, "intake_blocker_count mismatch")
    require(result.get("intake_warning_count") == warning_count, "intake_warning_count mismatch")
    require(result.get("pricing_policy_defined") is True, "pricing_policy_defined must be true")
    require(result.get("capability_boundary_defined") is True, "capability_boundary_defined must be true")
    require(result.get("side_effect_boundary_defined") is True, "side_effect_boundary_defined must be true")
    require(isinstance(result.get("upload_ready_status"), str), "upload_ready_status must be a string")
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
        validate_intake_and_adapter()
        validate_pricing_policy()
        validate_capability_boundaries()
        validate_rendered_prompt()
        validate_kb_and_manifest()
        blocker_count, warning_count = validate_validation_report()
        regression_test_count = validate_regression_tests()
        validate_result_json(regression_test_count, blocker_count, warning_count)
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
