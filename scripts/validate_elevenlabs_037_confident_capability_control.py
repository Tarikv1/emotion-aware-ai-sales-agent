#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "ELEVENLABS-037-confident-capability-control"

PROMPT = ROOT / "runtime/providers/elevenlabs_agents/prompts/web_design_atlas_sales_prompt.md"
OFFER = ROOT / "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_offer_facts.md"
PRICE = ROOT / "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_price_scope_cost_drivers.md"
OUTPUT = ROOT / "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_output_quality_rules.md"
CLOSE = ROOT / "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_close_and_followup_playbook.md"
OBJECTION = ROOT / "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_objection_playbook.md"
ANALYSIS_CONFIG = ROOT / "runtime/providers/elevenlabs_agents/analysis/atlas_web_studio_analysis_config.json"
ANALYSIS_SETUP = ROOT / "runtime/providers/elevenlabs_agents/analysis/atlas_web_studio_analysis_setup.md"
TESTS = ROOT / "runtime/providers/elevenlabs_agents/tests/web_design_confident_capability_control_tests.json"
ACTIVE_UPLOAD_MANIFEST = ROOT / "runtime/providers/elevenlabs_agents/manifests/web_design_sales_spine_compression.package.json"

EXPECTED_TEST_IDS = {
    "sim_037_custom_portal_capability_confident_no_price",
    "sim_037_custom_work_small_business_direct_answer",
    "sim_037_prior_experience_confident_without_fake_case_study",
    "sim_037_jobber_payment_capability_then_price",
    "sim_037_no_question_echo_preface",
    "sim_037_unresolved_concern_outranks_close",
    "sim_037_terminal_close_once",
    "sim_037_spoken_email_exact_normalization",
}


def fail(message: str) -> None:
    raise AssertionError(message)


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def read(path: Path) -> str:
    assert_condition(path.is_file(), f"Missing file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(read(path))
    assert_condition(isinstance(payload, dict), f"{path.relative_to(ROOT)} must contain a JSON object")
    return payload


def assert_markers(label: str, text: str, markers: tuple[str, ...]) -> None:
    missing = [marker for marker in markers if marker not in text]
    assert_condition(not missing, f"{label} missing markers: {missing}")


def word_count(text: str) -> int:
    return len(re.findall(r"\b\S+\b", text))


def git_diff_names(*paths: str) -> list[str]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", "--", *paths],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def assert_policy() -> None:
    offer = read(OFFER)
    price = read(PRICE)
    output = read(OUTPUT)
    close = read(CLOSE)
    objection = read(OBJECTION)
    prompt = read(PROMPT)
    combined = "\n".join((offer, price, output, close, objection, prompt))

    assert_condition(word_count(prompt) <= 1900, f"prompt no longer compact: {word_count(prompt)} words")
    assert_markers(
        "canonical capability facts",
        offer,
        (
            "## Atlas Website And Custom Development Capabilities",
            "Atlas builds both standard websites and advanced custom web systems.",
            "custom forms and quote workflows",
            "live booking and calendar integrations",
            "Jobber and similar field-service integrations",
            "automation workflows",
            "custom web applications",
            "cloud-connected functionality",
            "service-area pages",
            "multi-location website structures",
            "Technical scoping determines the exact workflow, data, permissions, APIs, security, integrations, and implementation; it does not determine whether Atlas is willing or able to take on the work.",
            "Third-party integrations may depend on the platform's available API, webhooks, account access, or supported integration methods.",
            "Atlas has substantial hands-on website and custom-development experience.",
        ),
    )
    assert_markers(
        "capability variables",
        offer,
        (
            "{{atlas_custom_web_capability}}",
            "{{atlas_broad_experience_claim}}",
            "{{atlas_specific_proof_boundary}}",
        ),
    )
    assert_markers(
        "capability scope price proof process split",
        combined,
        (
            "Capability question examples",
            "Scope question examples",
            "Price question examples",
            "Proof/experience question examples",
            "Process-risk question examples",
            "\"What's the catch?\" is a process-risk question, not automatically a request for the full pricing menu.",
            "Do not introduce price unless the buyer also asks price.",
        ),
    )
    assert_markers(
        "confidence proof boundary",
        combined,
        (
            "Allowed:",
            "confident statement of Atlas's owner-authorized capabilities",
            "broad statement that Atlas has hands-on website and custom-development experience",
            "Not allowed:",
            "invented named clients",
            "invented portfolio links",
            "invented exact project history",
            "Do not make that final proof-boundary response the default.",
        ),
    )
    assert_markers(
        "price timing and band semantics",
        price,
        (
            "Emma must not give paid price information merely because a buyer mentions an advanced feature.",
            "Complexity ranges describe the likely total project band by default, not an automatic add-on on top of the basic site.",
            "Do not add basic-site range and integration-heavy range together unless approved campaign facts explicitly define separate add-on pricing.",
            "For a real Jobber and payment integration, the whole project would usually move toward the {{website_integration_heavy_range}} range.",
            "Say \"likely moves the whole project toward...\" rather than \"that integration costs an extra...\"",
        ),
    )
    assert_markers(
        "custom portal confident scope",
        price,
        (
            "Yes, we can build that. It's custom, so we'd scope the user accounts, database, permissions, security, cloud setup, and integrations before giving you a final quote.",
            "That needs a proper scope before I give you a real number.",
            "Our standard website projects run roughly from {{website_starting_price}} to {{website_premium_price_anchor}}, but a full custom portal is a different category.",
            "Do not volunteer the {{website_starting_price}}-{{website_premium_price_anchor}} range",
        ),
    )
    assert_markers(
        "natural no echo and direct answer",
        output,
        (
            "Do not restate or paraphrase the buyer's question before answering unless clarification is genuinely required.",
            "Things that would make it not a typical scope and cost more include",
            "What makes it more complex is",
            "In terms of what would increase the price",
            "Mostly the data flow, payment rules, and how much needs to sync.",
            "When the buyer repeats a direct factual question because Emma did not answer it, stop reframing and answer the exact question.",
        ),
    )
    assert_markers(
        "terminal and unresolved concern",
        close,
        (
            "A live direct question or unresolved objection outranks `end_call`",
            "I'm still worried about the booking cost.",
            "not an automatic add-on",
            "do not repeat \"Take care\"",
            "Repeated \"Take care\" is a failure, not a pass.",
        ),
    )
    assert_markers(
        "exact email normalization",
        close + "\n" + prompt,
        (
            "literal @ symbol and normal domain periods",
            "hello@cedarridgeglass.com",
            "service@northsideautorepair.com",
            "Repeating \"at\" and \"dot\" wording is not normalized confirmation.",
        ),
    )


def assert_analysis() -> None:
    config = read_json(ANALYSIS_CONFIG)
    criteria = config.get("success_evaluation_criteria")
    assert_condition(isinstance(criteria, list), "analysis criteria missing")
    assert_condition(len(criteria) <= 30, "ElevenLabs Analysis criteria cap exceeded")
    combined = json.dumps(config, ensure_ascii=False) + "\n" + read(ANALYSIS_SETUP)
    assert_markers(
        "analysis contract",
        combined,
        (
            "separates capability, scope, price, proof, and process-risk states",
            "what's the catch?",
            "likely total project band, not an automatic add-on",
            "omits the literal @ symbol or normal domain periods",
            "repeats 'Take care'",
            "live unresolved concern such as booking cost",
            "formal answer-prefaces that add no meaning",
            "Authorized broad capability and broad experience",
            "named clients, portfolio links",
        ),
    )


def assert_tests() -> None:
    payload = read_json(TESTS)
    assert_condition(payload.get("package_id") == CHECKPOINT_ID, "037 package_id mismatch")
    assert_condition(payload.get("test_type") == "simulation", "037 tests must be simulation tests")
    tests = payload.get("tests")
    assert_condition(isinstance(tests, list) and len(tests) == 8, "037 tests must contain eight simulations")
    ids = {str(test.get("test_id")) for test in tests if isinstance(test, dict)}
    assert_condition(ids == EXPECTED_TEST_IDS, f"037 test IDs mismatch: {sorted(ids)}")
    serialized = json.dumps(payload, ensure_ascii=False)
    assert_condition("procedure_under_test" not in serialized, "037 tests contain alpha routing field")
    assert_condition("example.com" not in serialized.lower(), "037 tests contain placeholder example.com address")
    for marker in (
        "sim_037_custom_portal_capability_confident_no_price",
        "sim_037_custom_work_small_business_direct_answer",
        "sim_037_prior_experience_confident_without_fake_case_study",
        "sim_037_jobber_payment_capability_then_price",
        "sim_037_no_question_echo_preface",
        "sim_037_unresolved_concern_outranks_close",
        "sim_037_terminal_close_once",
        "sim_037_spoken_email_exact_normalization",
        "hello@cedarridgeglass.com",
        "{{website_integration_heavy_range}}",
        "not an automatic add-on",
        "repeated 'Take care'",
    ):
        assert_condition(marker in serialized, f"037 tests missing marker: {marker}")
    for test in tests:
        assert_condition(test.get("simulated_user_model") == "gemini-2.5-flash", f"{test.get('test_id')} simulated_user_model mismatch")
        assert_condition(test.get("evaluation_model") == "gemini-2.5-flash", f"{test.get('test_id')} evaluation_model mismatch")
        assert_condition(isinstance(test.get("simulation_max_turns"), int), f"{test.get('test_id')} missing max turns")
        assert_condition(6 <= int(test["simulation_max_turns"]) <= 12, f"{test.get('test_id')} max turns outside 6-12")


def assert_side_effect_boundaries() -> None:
    assert_condition(not git_diff_names(str(ACTIVE_UPLOAD_MANIFEST.relative_to(ROOT))), "active upload manifest was modified")
    procedure_diff = git_diff_names("runtime/providers/elevenlabs_agents/procedures")
    assert_condition(not procedure_diff, f"Procedures changed: {procedure_diff}")


def main() -> None:
    assert_policy()
    assert_analysis()
    assert_tests()
    assert_side_effect_boundaries()

    diff_check = subprocess.run(["git", "diff", "--check"], cwd=ROOT, text=True, capture_output=True, check=False)
    assert_condition(diff_check.returncode == 0, diff_check.stderr or diff_check.stdout)

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": CHECKPOINT_ID,
                "prompt_word_count": word_count(read(PROMPT)),
                "analysis_criteria_count": len(read_json(ANALYSIS_CONFIG)["success_evaluation_criteria"]),
                "test_count": 8,
                "active_upload_manifest_changed": False,
                "procedures_changed": False,
                "live_provider_calls_made": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
