#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "ELEVENLABS-040-detailed-pricing-control"
CHECKPOINT_BASE_REF = "f90e0bb"

DEFAULTS_PATH = "runtime/providers/elevenlabs_agents/variables/mikes_kitchen_dynamic_variable_defaults.json"
PROMPT_PATH = "runtime/providers/elevenlabs_agents/prompts/web_design_atlas_sales_prompt.md"
OFFER_PATH = "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_offer_facts.md"
PRICE_PATH = "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_price_scope_cost_drivers.md"
OUTPUT_PATH = "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_output_quality_rules.md"
TESTS_PATH = "runtime/providers/elevenlabs_agents/tests/web_design_detailed_pricing_control_tests.json"
PATCHER_PATH = "scripts/apply_elevenlabs_040_detailed_pricing_control.py"
VALIDATOR_PATH = "scripts/validate_elevenlabs_040_detailed_pricing_control.py"
PACKAGE_MANIFEST_PATH = "runtime/providers/elevenlabs_agents/manifests/web_design_detailed_pricing_control.package.json"
CAPTURE_PATH = "scripts/capture_elevenlabs_040_test_invocation.py"
TRACE_VALIDATOR_PATH = "scripts/validate_elevenlabs_040_live_test_traces.py"
ACTIVE_MANIFEST_PATH = "runtime/providers/elevenlabs_agents/manifests/web_design_sales_spine_compression.package.json"
ANALYSIS_CONFIG_PATH = "runtime/providers/elevenlabs_agents/analysis/atlas_web_studio_analysis_config.json"
ANALYSIS_SETUP_PATH = "runtime/providers/elevenlabs_agents/analysis/atlas_web_studio_analysis_setup.md"
PROCEDURES_DIR_PATH = "runtime/providers/elevenlabs_agents/procedures"
TESTS_DIR_PATH = "runtime/providers/elevenlabs_agents/tests"
ALLOWED_NEW_TEST = TESTS_PATH

DEFAULTS = ROOT / DEFAULTS_PATH
PROMPT = ROOT / PROMPT_PATH
OFFER = ROOT / OFFER_PATH
PRICE = ROOT / PRICE_PATH
OUTPUT = ROOT / OUTPUT_PATH
TESTS = ROOT / TESTS_PATH
PATCHER = ROOT / PATCHER_PATH

CHECKPOINT_DIFF_PATHS = (
    VALIDATOR_PATH,
    DEFAULTS_PATH,
    PROMPT_PATH,
    OFFER_PATH,
    PRICE_PATH,
    OUTPUT_PATH,
    TESTS_PATH,
    PACKAGE_MANIFEST_PATH,
    PATCHER_PATH,
    CAPTURE_PATH,
    TRACE_VALIDATOR_PATH,
)

EXPECTED_PRICE_DEFAULTS = {
    "website_starting_price": "$500",
    "website_basic_site_range": "$900-$1,500",
    "website_light_feature_range": "$1,800-$3,000",
    "website_workflow_content_range": "$2,800-$4,500",
    "website_integration_heavy_range": "$4,000-$6,500",
    "website_premium_price_anchor": "$6,500",
}

EXPECTED_TEST_IDS = [
    "sim_040_capability_question_no_unprompted_price",
    "sim_040_free_mockup_question_no_paid_price",
    "sim_040_basic_site_direct_price",
    "sim_040_existing_site_request_form_add_on",
    "sim_040_new_site_booking_whole_project",
    "sim_040_multi_feature_no_price_stacking",
    "sim_040_direct_crm_integration_existing_site",
    "sim_040_portal_requires_scope",
    "sim_040_budget_fit_direct_answer",
    "sim_040_care_plan_only_when_asked",
]

PROMPT_MARKERS = (
    "Paid-price gate: disclose paid pricing only after the buyer explicitly asks price, cost, fee, range, ballpark, budget, affordability, monthly charge, or add-on cost.",
    "Capability, scope, mockup, free, catch, contract, and ordinary-interest questions never unlock paid pricing.",
    "After price intent: new website -> one whole-project band; compatible existing site -> one relevant add-on range; unclear -> ask whether this is a new site or an addition.",
    "Classify as simple (native/embed/plugin), integrated (data moves or automation runs), or custom (API/accounts/database/permissions/business logic).",
    "Quote one relevant range, name one scope driver, and ask at most one necessary question.",
    "Never read the menu.",
    "One or two independent add-ons may be discussed; three or more move to a whole-project band.",
    "Never add ranges into a final quote or charge overlapping work twice.",
    "Portals, dashboards, APIs, accounts, databases, complex payments, inventory sync, marketplaces, and custom logic require scope without a fixed price or ceiling.",
)

PRICING_KB_MARKERS = (
    "Quick Launch",
    "$500-$800",
    "Essential Local",
    "{{website_basic_site_range}}",
    "Custom Business",
    "{{website_light_feature_range}}",
    "Growth Website",
    "{{website_workflow_content_range}}",
    "Integration Website",
    "{{website_integration_heavy_range}}",
    "Starter Ecommerce",
    "$2,500-$5,000",
    "Advanced Ecommerce",
    "$5,000-$10,000+",
    "Portal or Web Application",
    "Scoped separately",
    "Additional standard page",
    "$125-$250 per page",
    "Appointment-request form",
    "$100-$250 on an existing site",
    "Direct CRM or API integration",
    "$1,000-$2,500+",
    "Essential Care",
    "$79 per month",
    "Business Care",
    "$149 per month",
    "Growth Care",
    "$249 per month",
    "domain registration",
    "third-party platform subscriptions",
    "premium plugins and application fees",
    "transaction and payment-processing fees",
    "custom photography or video",
    "ongoing SEO campaigns",
)

OUTPUT_MARKERS = (
    "Never disclose a paid price before explicit buyer price intent.",
    "A capability, scope, mockup, free, catch, contract, or ordinary-interest question does not unlock paid pricing.",
    "Do not read the package or feature menu aloud.",
    "Do not add three or more features into a final quote.",
    "Do not charge twice for overlapping work.",
    "Use one relevant range and at most one material scope question.",
    "Do not quote a fixed price or ceiling for portals, dashboards, APIs, accounts, databases, or custom business logic.",
)

PATCHER_MARKERS = (
    'AGENT_ID = "agent_7801kt0g32zxf4f8x5zkykj7syty"',
    'AGENT_NAME = "web design"',
    'CONFIRM_TOKEN = "confirm-provider-write"',
    '"llm": "gpt-5.5"',
    '"temperature": 0.1',
    '"thinking_budget": None',
    '"reasoning_effort": "none"',
    'KB_DOCS = (',
    '"atlas_offer_facts.md"',
    '"atlas_price_scope_cost_drivers.md"',
    '"atlas_output_quality_rules.md"',
    "def merged_dynamic_variables(",
    "dynamic_variable_placeholders",
    "def patch_body(",
    '"prompt": {"prompt": PROMPT_PATH.read_text(encoding="utf-8").strip()}',
    "def canonical_sha256(",
    "def collateral_state(",
    "unrelated_tool_fingerprint",
    "analysis_criterion_ids_in_order",
    "procedures_inactive",
    "confirm-provider-write",
    "plan_only_missing_confirmation",
    '"provider_writes_made": False',
)


def fail(message: str) -> None:
    raise AssertionError(message)


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def read(path: Path) -> str:
    assert_condition(path.is_file(), f"Missing file: {path.relative_to(ROOT).as_posix()}")
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(read(path))
    assert_condition(isinstance(payload, dict), f"{path.relative_to(ROOT).as_posix()} must contain a JSON object")
    return payload


def assert_markers(label: str, text: str, markers: tuple[str, ...]) -> None:
    missing = [marker for marker in markers if marker not in text]
    assert_condition(not missing, f"{label} missing markers: {missing}")


def word_count(text: str) -> int:
    return len(re.findall(r"\b\S+\b", text))


def git(args: list[str], *, repo_root: Path = ROOT) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_condition(completed.returncode == 0, completed.stderr.strip() or completed.stdout.strip() or f"git {' '.join(args)} failed")
    return completed


def ensure_base_ref(base_ref: str, *, repo_root: Path = ROOT) -> None:
    git(["rev-parse", "--verify", f"{base_ref}^{{commit}}"], repo_root=repo_root)


def git_changed_paths_since(base_ref: str, *paths: str, repo_root: Path = ROOT) -> list[str]:
    completed = git(
        ["diff", "--name-only", "--diff-filter=ACDMRTUXB", base_ref, "--", *paths],
        repo_root=repo_root,
    )
    return [line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()]


def git_diff_check(base_ref: str, *paths: str, repo_root: Path = ROOT) -> None:
    completed = git(["diff", "--check", base_ref, "--", *paths], repo_root=repo_root)
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)


def validate_change_boundaries(*, repo_root: Path = ROOT, base_ref: str = CHECKPOINT_BASE_REF) -> None:
    ensure_base_ref(base_ref, repo_root=repo_root)

    analysis_diff = git_changed_paths_since(
        base_ref,
        ANALYSIS_CONFIG_PATH,
        ANALYSIS_SETUP_PATH,
        repo_root=repo_root,
    )
    assert_condition(not analysis_diff, f"Analysis files changed: {analysis_diff}")

    manifest_diff = git_changed_paths_since(base_ref, ACTIVE_MANIFEST_PATH, repo_root=repo_root)
    assert_condition(not manifest_diff, f"Active manifest changed: {manifest_diff}")

    procedure_diff = git_changed_paths_since(base_ref, PROCEDURES_DIR_PATH, repo_root=repo_root)
    assert_condition(not procedure_diff, f"Procedures changed: {procedure_diff}")

    test_diff = git_changed_paths_since(base_ref, TESTS_DIR_PATH, repo_root=repo_root)
    unexpected = [path for path in test_diff if path != ALLOWED_NEW_TEST]
    assert_condition(not unexpected, f"Existing tests changed: {unexpected}")


def validate_dynamic_defaults() -> None:
    defaults = read_json(DEFAULTS)
    for key, expected in EXPECTED_PRICE_DEFAULTS.items():
        assert_condition(defaults.get(key) == expected, f"{key} mismatch")
    assert_condition(
        defaults.get("website_price_disclosure_rule")
        == "only discuss paid pricing after explicit buyer price, cost, fee, range, ballpark, budget, affordability, monthly-charge, or add-on-cost intent; capability, scope, mockup, free, catch, contract, and ordinary-interest questions do not unlock paid pricing",
        "website_price_disclosure_rule mismatch",
    )


def validate_prompt_policy() -> None:
    prompt = read(PROMPT)
    assert_markers("prompt", prompt, PROMPT_MARKERS)
    assert_condition(word_count(prompt) <= 1900, "compact prompt exceeds 1,900 words")


def validate_pricing_kb() -> None:
    combined = read(OFFER) + "\n" + read(PRICE)
    assert_markers("pricing KB", combined, PRICING_KB_MARKERS)


def validate_output_rules() -> None:
    output = read(OUTPUT)
    assert_markers("output rules", output, OUTPUT_MARKERS)


def validate_tests() -> None:
    payload = read_json(TESTS)
    assert_condition(payload.get("package_id") == CHECKPOINT_ID, "040 package_id mismatch")
    tests = payload.get("tests")
    assert_condition(isinstance(tests, list), "040 tests must be a list")
    assert_condition(len(tests) == 10, "040 tests must contain exactly ten simulations")
    assert_condition([item.get("test_id") for item in tests] == EXPECTED_TEST_IDS, "040 test IDs/order mismatch")
    assert_condition(
        all(item.get("simulated_user_model") == "gemini-2.5-flash" for item in tests),
        "simulated-user model mismatch",
    )
    assert_condition(
        all(item.get("evaluation_model") == "gemini-2.5-flash" for item in tests),
        "evaluation model mismatch",
    )
    assert_condition(
        all(isinstance(item.get("simulation_max_turns"), int) and 6 <= int(item["simulation_max_turns"]) <= 12 for item in tests),
        "040 simulation_max_turns must stay within 6-12",
    )


def validate_live_patcher() -> None:
    patcher = read(PATCHER)
    assert_markers("040 live patcher", patcher, PATCHER_MARKERS)


def main() -> int:
    try:
        validate_prompt_policy()
        validate_pricing_kb()
        validate_output_rules()
        validate_tests()
        validate_live_patcher()
        validate_dynamic_defaults()
        validate_change_boundaries()
        git_diff_check(CHECKPOINT_BASE_REF, *CHECKPOINT_DIFF_PATHS)
    except AssertionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": CHECKPOINT_ID,
                "prompt_word_count": word_count(read(PROMPT)),
                "test_count": len(EXPECTED_TEST_IDS),
                "active_manifest_changed": False,
                "procedures_changed": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
