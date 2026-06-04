#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ID = "ELEVENLABS-001-universal-sales-core"
BASE = ROOT / "runtime" / "providers" / "elevenlabs_agents"
README = BASE / "README.md"
KB = BASE / "knowledge_base" / "universal_sales_core.md"
TESTS = BASE / "tests" / "universal_sales_core_baseline_tests.json"
MANIFEST = BASE / "manifests" / "universal_sales_core.package.json"
DOC = ROOT / "docs" / "product" / "ELEVENLABS_001_UNIVERSAL_SALES_CORE.md"
RUNTIME_MANIFEST = ROOT / "runtime" / "runtime_manifest.json"


REQUIRED_KB_SECTIONS = (
    "Operating Boundary",
    "Conversation Frame",
    "Customer State Reading",
    "Objection Handling",
    "Ethical Persuasion",
    "Meeting Setting",
    "Campaign Override Rules",
    "Hard Stops",
)

REQUIRED_KB_MARKERS = (
    "Campaign facts override universal sales advice.",
    "Do not invent urgency, scarcity, guarantees, discounts, legal claims, or results.",
    "Use observable empathy; do not claim hidden emotional certainty.",
    "Ask one clear question at a time.",
    "Respect do-not-call, clear refusal, repeated silence, and human-transfer requests.",
    "This knowledge base is advisory, not a script.",
)

REQUIRED_TEST_IDS = (
    "permission_based_opener",
    "not_interested_low_pressure_relevance_check",
    "send_info_specificity_request",
    "price_objection_diagnose_before_answer",
    "trust_objection_truthful_proof_only",
    "emotion_boundary_observable_empathy",
    "fake_urgency_blocked",
    "meeting_setting_low_friction_next_step",
    "campaign_facts_override_generic_advice",
    "do_not_call_stop_rule",
)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def fail(message: str) -> None:
    raise AssertionError(message)


def read_text(path: Path) -> str:
    if not path.is_file():
        fail(f"Missing required file: {rel(path)}")
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    text = read_text(path)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        fail(f"{rel(path)} is not valid JSON: {exc}")
    if not isinstance(payload, dict):
        fail(f"{rel(path)} must be a JSON object.")
    return payload


def assert_no_private_or_secret_text(path: Path, text: str) -> None:
    normalized = text.lower().replace("\\", "/")
    blocked = (
        "elevenlabs_api_key",
        "xi-api-key",
        "api key value",
        "data/private/",
        "data/private-restricted/",
        "customer email:",
        "raw customer email",
        "private transcript",
    )
    found = [item for item in blocked if item in normalized]
    if found:
        fail(f"{rel(path)} contains blocked private/secret marker(s): {found}")


def assert_kb() -> None:
    text = read_text(KB)
    assert_no_private_or_secret_text(KB, text)
    if len(text.encode("utf-8")) > 120_000:
        fail("Universal sales core KB must stay curated and compact, not a bulk dump.")
    for section in REQUIRED_KB_SECTIONS:
        if f"## {section}" not in text:
            fail(f"Universal sales core KB missing section: {section}")
    for marker in REQUIRED_KB_MARKERS:
        if marker not in text:
            fail(f"Universal sales core KB missing marker: {marker}")


def assert_tests() -> None:
    payload = load_json(TESTS)
    if payload.get("package_id") != PACKAGE_ID:
        fail("Baseline tests package_id mismatch.")
    tests = payload.get("tests")
    if not isinstance(tests, list) or len(tests) < len(REQUIRED_TEST_IDS):
        fail("Baseline tests must include at least the required scenario set.")
    by_id = {str(item.get("test_id")): item for item in tests if isinstance(item, dict)}
    missing = [test_id for test_id in REQUIRED_TEST_IDS if test_id not in by_id]
    if missing:
        fail(f"Baseline tests missing scenario(s): {missing}")
    for test_id, item in by_id.items():
        for field in ("customer_utterance", "expected_behavior", "forbidden_behavior"):
            value = item.get(field)
            if not isinstance(value, str) or len(value.strip()) < 20:
                fail(f"{test_id} needs a specific {field}.")


def assert_manifest() -> None:
    payload = load_json(MANIFEST)
    if payload.get("package_id") != PACKAGE_ID:
        fail("Package manifest package_id mismatch.")
    expected_false = (
        "live_provider_calls_made",
        "private_customer_data_used",
        "api_key_required_for_generation",
        "dashboard_manual_changes_source_of_truth",
    )
    for key in expected_false:
        if payload.get(key) is not False:
            fail(f"Package manifest must keep {key}=false.")
    if payload.get("provider") != "elevenlabs":
        fail("Package manifest provider must be elevenlabs.")
    if payload.get("source_of_truth") != "repo":
        fail("Package manifest must record repo as source_of_truth.")
    if payload.get("dashboard_role") != "managed runtime and manual upload surface":
        fail("Package manifest must keep ElevenLabs dashboard as runtime/upload surface.")
    for field, path in (
        ("knowledge_base_docs", KB),
        ("baseline_tests", TESTS),
    ):
        values = payload.get(field)
        if not isinstance(values, list) or rel(path) not in values:
            fail(f"Package manifest must list {rel(path)} in {field}.")


def assert_runtime_manifest() -> None:
    payload = load_json(RUNTIME_MANIFEST)
    entries = payload.get("runtime_entries", [])
    paths = {entry.get("path") for entry in entries if isinstance(entry, dict)}
    if "runtime/providers/elevenlabs_agents" not in paths:
        fail("Runtime manifest must list runtime/providers/elevenlabs_agents.")
    flags = payload.get("boundary_flags", {})
    if flags.get("provider_calls_made") is not False:
        fail("ELEVENLABS-001 must not unblock provider calls.")
    if flags.get("production_runtime_promotion_allowed") is not False:
        fail("ELEVENLABS-001 must not promote production runtime.")


def assert_doc() -> None:
    text = read_text(DOC)
    assert_no_private_or_secret_text(DOC, text)
    required = (
        PACKAGE_ID,
        "Repo remains the source of truth.",
        "ElevenLabs dashboard is the managed runtime and manual upload surface.",
        "Universal sales advice must stay subordinate to campaign facts.",
        "No live provider call is made by this checkpoint.",
    )
    for marker in required:
        if marker not in text:
            fail(f"Product doc missing marker: {marker}")


def main() -> None:
    read_text(README)
    assert_kb()
    assert_tests()
    assert_manifest()
    assert_runtime_manifest()
    assert_doc()
    print(
        json.dumps(
            {
                "status": "pass",
                "package_id": PACKAGE_ID,
                "knowledge_base": rel(KB),
                "tests": rel(TESTS),
                "manifest": rel(MANIFEST),
                "live_provider_calls_made": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
