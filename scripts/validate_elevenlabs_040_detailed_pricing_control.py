#!/usr/bin/env python3
from __future__ import annotations

import json
import hashlib
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
LIVE_EVIDENCE_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

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

EXPECTED_SHARED_CONTEXT_DEFAULTS = {
    "business_name": "Acme Dental",
    "business_type": "dental clinic",
    "city": "Phoenix",
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

EXPECTED_TEST_CRITERIA = [
    (
        "Buyer asks whether Atlas can add booking, CRM, and payments but never asks cost.",
        "Pass: confident capability answer, no dollar amount, range, package, starting price, or care-plan price.",
        8,
    ),
    (
        "Buyer asks whether the mockup is really free and whether there is a catch.",
        "Pass: process-risk answer only; no paid website price.",
        8,
    ),
    (
        "Buyer explicitly asks what a basic three-to-five-page local-business site costs.",
        "Pass: one `$900-$1,500` whole-project range and one relevant driver at most.",
        6,
    ),
    (
        "Buyer states they have an existing compatible site and asks the cost of adding a simple appointment-request form.",
        "Pass: one `$100-$250` add-on range; no whole-site package dump.",
        6,
    ),
    (
        "Buyer asks what a new straightforward site with a simple request form costs, then asks about live calendar integration.",
        "Pass: `$900-$1,500` for simple request; later one higher relevant band for live integration; no add-on/whole-site confusion.",
        10,
    ),
    (
        "Buyer asks for a new site with booking, CRM, payments, service-area pages, and a blog, then asks total cost.",
        "Pass: one likely whole-project band and scope driver; no arithmetic sum or feature-menu recital.",
        8,
    ),
    (
        "Buyer has an existing compatible site and asks what a direct CRM integration costs.",
        "Pass: `$1,000-$2,500+`, an API/data-flow caveat, and no claim that every behavior is included.",
        8,
    ),
    (
        "Buyer asks how much a parent portal with accounts and progress dashboards costs.",
        "Pass: no numeric quote or ceiling; scope accounts, data, permissions, security, and integrations.",
        8,
    ),
    (
        "Buyer says the budget is `$1,200` and asks whether a basic site fits.",
        "Pass: direct fit answer against `$900-$1,500`; no unrelated package menu.",
        6,
    ),
    (
        "Buyer first asks about ordinary site capability, then explicitly asks monthly hosting and maintenance cost.",
        "Pass: no care price before the ongoing-cost question; after it, one relevant `$79`, `$149`, or `$249` plan with scope.",
        10,
    ),
]

EXPECTED_MODIFIED_PRODUCT_FILES = [
    PROMPT_PATH,
    OFFER_PATH,
    PRICE_PATH,
    OUTPUT_PATH,
]

REQUIRED_DEFAULT_KB_DOCS = (
    "atlas_offer_facts.md",
    "atlas_price_scope_cost_drivers.md",
    "atlas_output_quality_rules.md",
)

PROMPT_MARKERS = (
    "Process-risk follow-ups/summaries: answer only; no CTA until explicit \"send it.\"",
    "Price-source lock: use only approved Campaign Facts/active-pricing-KB values; never invent, narrow, average, or endorse buyer-suggested numbers.",
    "Runtime price map: 3-5 page new site -> {{website_basic_site_range}}; compatible existing-site appointment request -> $100-$250; direct CRM/API add-on -> $1,000-$2,500+; new site plus standard integration -> {{website_integration_heavy_range}}; care -> next rule; portal/dashboard -> scope without a number.",
    "Care after ongoing-cost intent: hosting/maintenance -> $79 only. Context answers never unlock project price. Never volunteer care tiers. Included/extra, \"higher/different plan?\", and plan-count/list questions: no new price or recap. $149/$249 only when current buyer turn directly asks that level's cost.",
    "Paid-price gate: disclose paid pricing only after the buyer explicitly asks price, cost, fee, range, ballpark, budget, affordability, monthly charge, or add-on cost.",
    "Capability/context/scope never unlock price; new/existing or feature answers are not price intent.",
    "After price intent: new website -> one whole-project band, never an existing-site add-on; compatible existing site -> one relevant add-on; unclear -> ask whether new or addition.",
    "CRM price before new/existing -> ask that only, no number. Full-site/all-features before its feature list -> ask features only. \"Do custom integrations cost extra?\" -> \"Yes. Which integration do you mean?\" No number. Unclear embed/standard/direct -> ask which, no number.",
    "CRM simple-vs-full cost: direct range only; never appointment-request price. Handoff $250-$600 only after explicit scope change and handoff-price ask.",
    "CRM/portal logistics exact: \"We collect that during scoping if you move forward.\" No contact invention, mockup, or email CTA.",
    "Classify as simple (native/embed/plugin), integrated (data moves or automation runs), or custom (API/accounts/database/permissions/business logic).",
    "Quote one relevant range, name one scope driver, and ask at most one necessary question.",
    "After any quote, range/driver/scope/included/lower-end/new-vs-add-on follow-ups are price-only: answer and stop; no mockup/send/email pitch. Resume only after topic change or mockup request.",
    "Never read the menu.",
    "Three-plus total-cost -> $4,000-$6,500 whole-project only; later same-project feature/sync turns never use basic/add-on numbers.",
    "Never add ranges into a final quote or charge overlapping work twice.",
    "Portals/dashboards/APIs/accounts/databases/complex-payments/inventory-sync/marketplaces/custom-logic require scope, no number. Scope-start/timing questions stay portal-only: answer and stop, no mockup/send/email.",
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
    "If support need is unclear, default to Essential Care",
    "Do not recite all three care plans in one answer.",
    "domain registration",
    "third-party platform subscriptions",
    "premium plugins and application fees",
    "transaction and payment-processing fees",
    "custom photography or video",
    "ongoing SEO campaigns",
)

OUTPUT_MARKERS = (
    "Never use general-market, industry-average, or unsupported invented prices.",
    "Never disclose a paid price before explicit buyer price intent.",
    "A capability, scope, mockup, free, catch, contract, or ordinary-interest question does not unlock paid pricing.",
    "After Emma quotes a price, any follow-up about range, budget, drivers, scope, or new-vs-add-on stays in a price-only lane until that chain ends.",
    "In that lane, answer only the asked price issue: no mockup mention, mockup CTA, email ask, or renewed sales transition unless the buyer newly accepts or requests the mockup.",
    "Do not read the package or feature menu aloud.",
    "Do not add three or more features into a final quote.",
    "Do not charge twice for overlapping work.",
    "Use one relevant range and at most one material scope question.",
    "For care, quote exactly one relevant plan after ongoing-cost intent; default to Essential Care if support need is unclear.",
    "Do not quote a fixed price or ceiling for portals, dashboards, APIs, accounts, databases, or custom business logic.",
)

FORBIDDEN_WEAK_PRICE_FOLLOWUP_MARKERS = (
    "During live price follow-ups, answer the asked price issue without repeating the mockup CTA unless the buyer has newly accepted the mockup.",
    "Then one CTA; basic forms are not custom.",
)

FORBIDDEN_UNSUPPORTED_PRICE_MARKERS = (
    "$3,000-$8,000",
    "$3,000 - $8,000",
    "three thousand to eight thousand",
    "$3,000-$5,000",
    "$3,000 - $5,000",
    "around three thousand dollars",
)

KB_REQUEST_SOURCE_MARKERS = {
    "atlas_offer_facts.md": (
        "Quick Launch: `$500-$800`",
        "Essential Local: `{{website_basic_site_range}}`",
        "Integration Website: `{{website_integration_heavy_range}}`",
    ),
    "atlas_price_scope_cost_drivers.md": (
        "If support need is unclear, default to Essential Care",
        "Base Package Ladder",
        "{{website_integration_heavy_range}}",
    ),
    "atlas_output_quality_rules.md": (
        "Pricing Quote Discipline",
        "Never disclose a paid price before explicit buyer price intent.",
        "For care, quote exactly one relevant plan after ongoing-cost intent; default to Essential Care if support need is unclear.",
    ),
}

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
SOURCE_EVIDENCE_ORIGIN = "repo_head_source_before_provider_write_not_network_capture"
REQUIRED_NEW_SOURCE_EVIDENCE_FIELDS = (
    "source_git_blob_sha256",
    "source_git_blob_length",
    "upload_sha256",
    "upload_length",
    "newline_mode",
)
LEGACY_SOURCE_EVIDENCE_ALLOWLIST = {
    (
        "1e8af8510b072d5fe08501af7229abac5208bdf8",
        "update_kb_file::atlas_price_scope_cost_drivers.md",
        "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_price_scope_cost_drivers.md",
        "df6f06af92ad57ca5679b848c909f56cc34905fc78fa3a3fd888861913cbfd54",
        14394,
    ): "legacy_git_blob_old_fields",
    (
        "1e8af8510b072d5fe08501af7229abac5208bdf8",
        "update_kb_file::atlas_output_quality_rules.md",
        "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_output_quality_rules.md",
        "5f6f68f5ec26640a55658d374c5729bfdc23d10745a4c194ed245d4aa486425e",
        19064,
    ): "legacy_worktree_line_endings",
}


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


def read_json_anywhere(path: Path) -> dict[str, Any]:
    assert_condition(path.is_file(), f"Missing file: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert_condition(isinstance(payload, dict), f"{path} must contain a JSON object")
    return payload


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("ascii")).hexdigest()


def assert_markers(label: str, text: str, markers: tuple[str, ...]) -> None:
    missing = [marker for marker in markers if marker not in text]
    assert_condition(not missing, f"{label} missing markers: {missing}")


def assert_no_forbidden_unsupported_prices(label: str, text: str) -> None:
    lowered = text.lower()
    found = [marker for marker in FORBIDDEN_UNSUPPORTED_PRICE_MARKERS if marker.lower() in lowered]
    assert_condition(not found, f"{label} contains unsupported pricing markers: {found}")


def assert_absent_markers(label: str, text: str, markers: tuple[str, ...]) -> None:
    found = [marker for marker in markers if marker in text]
    assert_condition(not found, f"{label} contains forbidden markers: {found}")


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


def git_show_file_bytes(commit: str, source_path: str, *, repo_root: Path = ROOT) -> bytes:
    completed = subprocess.run(
        ["git", "show", f"{commit}:{source_path}"],
        cwd=repo_root,
        capture_output=True,
        check=False,
    )
    assert_condition(completed.returncode == 0, completed.stderr.decode("utf-8", errors="replace").strip() or f"git show {commit}:{source_path} failed")
    return completed.stdout


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
    assert_no_forbidden_unsupported_prices("prompt", prompt)
    assert_absent_markers("prompt", prompt, FORBIDDEN_WEAK_PRICE_FOLLOWUP_MARKERS)
    assert_condition(word_count(prompt) <= 1900, "compact prompt exceeds 1,900 words")


def validate_pricing_kb() -> None:
    combined = read(OFFER) + "\n" + read(PRICE)
    assert_markers("pricing KB", combined, PRICING_KB_MARKERS)


def validate_output_rules() -> None:
    output = read(OUTPUT)
    assert_markers("output rules", output, OUTPUT_MARKERS)
    assert_no_forbidden_unsupported_prices("output rules", output)
    assert_absent_markers("output rules", output, FORBIDDEN_WEAK_PRICE_FOLLOWUP_MARKERS[:1])


def validate_tests() -> None:
    payload = read_json(TESTS)
    manifest = read_json(ROOT / PACKAGE_MANIFEST_PATH)
    assert_condition(manifest.get("package_id") == CHECKPOINT_ID, "040 manifest package_id mismatch")
    assert_condition(manifest.get("prompt_files") == [], "040 test-only manifest must not expose prompt_files for operational upload")
    assert_condition(manifest.get("knowledge_base_docs") == [], "040 test-only manifest must not expose KB docs for operational upload")
    assert_condition(
        manifest.get("modified_product_files") == EXPECTED_MODIFIED_PRODUCT_FILES,
        "040 modified_product_files mismatch",
    )
    assert_condition(
        manifest.get("baseline_tests") == [TESTS_PATH],
        "040 manifest baseline_tests mismatch",
    )
    assert_condition(manifest.get("active_upload") is False, "040 active_upload must stay false")
    assert_condition(manifest.get("active_kb_upload_manifest") is False, "040 active_kb_upload_manifest must stay false")
    upload_intent = manifest.get("upload_intent", {})
    assert_condition(upload_intent.get("knowledge_base_upload_required") is False, "040 manifest must not require KB upload")

    assert_condition(payload.get("package_id") == CHECKPOINT_ID, "040 package_id mismatch")
    dynamic_variables = payload.get("dynamic_variables")
    assert_condition(isinstance(dynamic_variables, dict), "040 dynamic_variables must be an object")
    for key, expected in EXPECTED_SHARED_CONTEXT_DEFAULTS.items():
        assert_condition(dynamic_variables.get(key) == expected, f"040 shared context {key} mismatch")
    for key, expected in EXPECTED_PRICE_DEFAULTS.items():
        assert_condition(dynamic_variables.get(key) == expected, f"040 shared dynamic variable {key} mismatch")
    tests = payload.get("tests")
    assert_condition(isinstance(tests, list), "040 tests must be a list")
    assert_condition(len(tests) == 10, "040 tests must contain exactly ten simulations")
    assert_condition([item.get("test_id") for item in tests] == EXPECTED_TEST_IDS, "040 test IDs/order mismatch")
    assert_condition(
        [
            (item.get("simulation_scenario"), item.get("success_condition"), item.get("simulation_max_turns"))
            for item in tests
        ]
        == EXPECTED_TEST_CRITERIA,
        "040 scenarios/success conditions/turn limits changed",
    )
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


def import_live_patcher() -> Any:
    scripts_path = str(ROOT / "scripts")
    if scripts_path not in sys.path:
        sys.path.insert(0, scripts_path)
    import apply_elevenlabs_040_detailed_pricing_control as patcher

    return patcher


def sample_agent_for_patcher() -> dict[str, Any]:
    return {
        "agent_id": "agent_7801kt0g32zxf4f8x5zkykj7syty",
        "name": "web design",
        "conversation_config": {
            "agent": {
                "first_message": "Hello.",
                "dynamic_variables": {
                    "dynamic_variable_placeholders": {
                        "business_name": "Acme Dental",
                        "business_type": "dental clinic",
                        "city": "Phoenix",
                        "website_basic_site_range": "$100-$200",
                        "unrelated_operational_flag": "keep-me-structurally",
                    }
                },
                "prompt": {
                    "prompt": "Atlas Web Studio\nMission: earn permission",
                    "llm": "gpt-5.5",
                    "temperature": 0.1,
                    "thinking_budget": None,
                    "reasoning_effort": "none",
                    "tools": [],
                    "built_in_tools": {"end_call": {"name": "end_call"}},
                    "tool_ids": [],
                    "mcp_server_ids": [],
                    "native_mcp_server_ids": [],
                },
            },
            "tts": {"voice_id": "voice_123"},
        },
        "platform_settings": {
            "evaluation": {
                "criteria": [{"id": f"criterion_{index:02d}"} for index in range(30)]
            }
        },
        "phone_numbers": [],
        "whatsapp_accounts": [],
        "procedures": [],
    }


def validate_live_patcher_semantics() -> None:
    patcher = import_live_patcher()
    agent = sample_agent_for_patcher()

    parsed = patcher.parse_args([])
    assert_condition(getattr(parsed, "confirm_provider_write") is None, "040 patcher must dry-run by default")
    assert_condition(tuple(patcher.KB_DOCS) == REQUIRED_DEFAULT_KB_DOCS, "040 patcher KB_DOCS literal default mismatch")
    assert_condition(patcher.parse_target_kb_docs(getattr(parsed, "target_kb_doc", None)) == REQUIRED_DEFAULT_KB_DOCS, "040 patcher must target literal three-doc default")
    subset_parsed = patcher.parse_args(["--target-kb-doc", "atlas_output_quality_rules.md"])
    subset = patcher.parse_target_kb_docs(subset_parsed.target_kb_doc)
    assert_condition(subset == ("atlas_output_quality_rules.md",), "040 patcher subset target parsing mismatch")
    for bad_targets in ([""], ["atlas_output_quality_rules.md", "atlas_output_quality_rules.md"], ["not_a_real_doc.md"]):
        try:
            patcher.parse_target_kb_docs(bad_targets)
        except ValueError:
            pass
        else:
            fail(f"040 patcher accepted malformed target KB docs: {bad_targets}")

    snapshot = patcher.snapshot_payload(
        phase="pre_patch",
        agent=agent,
        preflight={"knowledge_base_ids_in_order": [], "unrelated_tool_fingerprint": {}, "analysis_criterion_ids_in_order": [], "procedures_inactive": True, "collateral_state_sha256": "sample"},
        live_readback_at_utc="2026-07-11T19:10:00Z",
        serialized_at_utc="2026-07-11T19:10:05Z",
    )
    assert_condition(snapshot.get("captured_at_utc") == "2026-07-11T19:10:00Z", "snapshot captured_at_utc must be live readback time")
    assert_condition(snapshot.get("live_readback_at_utc") == "2026-07-11T19:10:00Z", "snapshot live_readback_at_utc missing")
    assert_condition(snapshot.get("snapshot_serialized_at_utc") == "2026-07-11T19:10:05Z", "snapshot serialization timestamp missing")
    assert_condition(snapshot.get("live_readback_time_recorded") is True, "snapshot must state live readback time was recorded")

    body = patcher.patch_body(agent)
    assert_condition(set(body) == {"conversation_config"}, "patch_body top-level keys must stay minimal")
    agent_body = body.get("conversation_config", {}).get("agent", {})
    assert_condition(set(agent_body) == {"prompt", "dynamic_variables"}, "patch_body agent keys must stay prompt/dynamic-only")
    assert_condition(set(agent_body.get("prompt", {})) == {"prompt"}, "patch_body prompt keys must stay prompt-text-only")
    placeholders = agent_body["dynamic_variables"]["dynamic_variable_placeholders"]
    assert_condition(placeholders["business_name"] == "Acme Dental", "merge must preserve unrelated placeholder values in live PATCH body")
    for key, expected in EXPECTED_PRICE_DEFAULTS.items():
        assert_condition(placeholders.get(key) == expected, f"patch_body must merge exact {key}")
    assert_condition(len(set(EXPECTED_PRICE_DEFAULTS) & set(placeholders)) == 6, "patch_body must expose exactly six approved price defaults")

    head_commit = git(["rev-parse", "HEAD"]).stdout.strip()
    requests = patcher.patch_requests(
        agent,
        {"target_kb_docs": {name: {"id": doc_id, "source_path": f"runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/{name}"} for name, doc_id in patcher.KNOWN_KB_DOC_IDS.items()}},
        source_commit=head_commit,
    )
    for request in requests:
        if request["request_id"].startswith("update_kb_file::"):
            source_evidence = request.get("source_evidence")
            assert_condition(isinstance(source_evidence, dict), f"{request['request_id']} missing source_evidence")
            source_path = ROOT / source_evidence["source_path"]
            source_bytes = git_show_file_bytes(head_commit, str(source_path.relative_to(ROOT)).replace("\\", "/"))
            source_sha = sha256_bytes(source_bytes)
            assert_condition(source_evidence.get("source_sha256") == source_sha, f"{request['request_id']} source sha mismatch")
            assert_condition(source_evidence.get("source_byte_length") == len(source_bytes), f"{request['request_id']} source byte length mismatch")
            assert_condition(source_evidence.get("source_git_blob_sha256") == source_sha, f"{request['request_id']} git blob sha mismatch")
            assert_condition(source_evidence.get("source_git_blob_byte_length") == len(source_bytes), f"{request['request_id']} git blob length mismatch")
            assert_condition(source_evidence.get("source_git_blob_length") == len(source_bytes), f"{request['request_id']} git blob length mismatch")
            assert_condition(source_evidence.get("upload_sha256") == source_sha, f"{request['request_id']} upload byte sha mismatch")
            assert_condition(source_evidence.get("upload_length") == len(source_bytes), f"{request['request_id']} upload byte length mismatch")
            assert_condition(source_evidence.get("newline_mode") in {"git_blob_lf", "git_blob_crlf", "worktree_crlf_normalized_to_git_lf"}, f"{request['request_id']} newline mode mismatch")
            markers = source_evidence.get("markers")
            assert_condition(isinstance(markers, list) and markers, f"{request['request_id']} missing source markers")
            source_text = source_bytes.decode("utf-8")
            assert_condition(all(isinstance(marker, str) and marker in source_text for marker in markers), f"{request['request_id']} source marker mismatch")
        elif request["request_id"] == "patch_agent::prompt_dynamic_variables":
            assert_condition(request.get("body_canonical_json_sha256") == canonical_sha256(request["body"]), "agent patch request canonical digest mismatch")

    subset_requests = patcher.patch_requests(
        agent,
        {"target_kb_docs": {name: {"id": doc_id, "source_path": f"runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/{name}"} for name, doc_id in patcher.KNOWN_KB_DOC_IDS.items()}},
        target_kb_doc_names=("atlas_output_quality_rules.md",),
        source_commit=head_commit,
    )
    assert_condition(
        [request["request_id"] for request in subset_requests]
        == ["update_kb_file::atlas_output_quality_rules.md", "patch_agent::prompt_dynamic_variables"],
        "subset dry-run must plan exactly one KB update plus one agent PATCH",
    )
    subset_plan = patcher.plan_payload(
        preflight={"target_kb_docs": {}},
        requests=subset_requests,
        target_kb_doc_names=("atlas_output_quality_rules.md",),
        provider_writes_allowed=False,
        ledger_summary=None,
        source_commit=head_commit,
    )
    assert_condition(subset_plan["planned_provider_write_count"] == 2, "subset plan must report exactly two planned writes")
    assert_condition(subset_plan["planned_kb_write_count"] == 1, "subset plan must report one planned KB write")
    assert_condition(subset_plan["planned_agent_patch_count"] == 1, "subset plan must report one planned agent PATCH")
    assert_condition(subset_plan["kb_documents_planned_for_in_place_update"] == ["atlas_output_quality_rules.md"], "subset plan must name only selected KB doc")

    redacted = patcher.sanitize(
        {
            "dynamic_variable_placeholders": {
                "business_name": "Acme Dental",
                "business_type": "dental clinic",
                "city": "Phoenix",
                "owner_email": "owner@example.com",
                "owner_phone": "+1 212 555 0188",
                "website_basic_site_range": "$900-$1,500",
                "website_price_disclosure_rule": "only after price intent",
            }
        }
    )
    rendered = json.dumps(redacted, sort_keys=True)
    for forbidden in ("Acme Dental", "dental clinic", "Phoenix", "owner@example.com", "212 555 0188"):
        assert_condition(forbidden not in rendered, f"sanitized evidence leaked synthetic customer value {forbidden!r}")
    redacted_placeholders = redacted["dynamic_variable_placeholders"]
    for key in ("business_name", "business_type", "city", "owner_email", "owner_phone"):
        assert_condition(key in redacted_placeholders, f"sanitized evidence must preserve placeholder key {key}")
        assert_condition(str(redacted_placeholders[key]).startswith("[REDACTED"), f"sanitized placeholder {key} must redact value")
    assert_condition(redacted_placeholders["website_basic_site_range"] == "$900-$1,500", "approved pricing placeholder must remain visible")
    assert_condition(redacted_placeholders["website_price_disclosure_rule"] == "only after price intent", "approved control placeholder must remain visible")

    ledger = patcher.ProviderWriteLedger()
    request = {"request_id": "update_kb_file::atlas_offer_facts.md", "method": "PATCH", "endpoint": "/example"}

    def failing_write() -> dict[str, Any]:
        raise RuntimeError("PATCH failed with 503: provider unavailable")

    try:
        patcher.attempt_provider_write(ledger, request, failing_write)
    except RuntimeError as exc:
        assert_condition("503" in str(exc), "injected provider failure should preserve exact status text")
    else:
        fail("injected provider failure did not raise")
    failure_payload = ledger.failure_payload(
        checkpoint_id=CHECKPOINT_ID,
        error="PATCH failed with 503: provider unavailable",
    )
    assert_condition(failure_payload["provider_writes_made"] is True, "attempted write must count as provider_writes_made")
    assert_condition(failure_payload["provider_write_attempt_count"] == 1, "attempt count mismatch after injected failure")
    assert_condition(failure_payload["provider_write_success_count"] == 0, "success count mismatch after injected failure")
    assert_condition(failure_payload["provider_write_attempts"][0]["request_id"] == request["request_id"], "attempt request_id missing")

    provider_echo = RuntimeError(
        "PATCH /v1/convai/agents/agent_7801kt0g32zxf4f8x5zkykj7syty failed with 400: "
        "{\"type\":\"invalid_request\",\"message\":\"bad dynamic variables\","
        "\"dynamic_variable_placeholders\":{\"business_name\":\"Acme Dental\",\"city\":\"Phoenix\","
        "\"contact_email\":\"owner@example.com\",\"contact_phone\":\"+1 212 555 0188\","
        "\"website_basic_site_range\":\"$900-$1,500\"},"
        "\"authorization\":\"Bearer live-secret-token\"}"
    )
    sanitized_error = patcher.safe_evidence_error_message(provider_echo)
    error_failure_payload = ledger.failure_payload(
        checkpoint_id=CHECKPOINT_ID,
        error=sanitized_error,
    )
    rendered_error_payload = json.dumps(error_failure_payload, sort_keys=True)
    for forbidden in (
        "Acme Dental",
        "Phoenix",
        "owner@example.com",
        "212 555 0188",
        "live-secret-token",
        "Bearer live-secret-token",
    ):
        assert_condition(forbidden not in rendered_error_payload, f"failure evidence leaked provider echo {forbidden!r}")
    for diagnostic in ("400", "invalid_request", "bad dynamic variables"):
        assert_condition(diagnostic in rendered_error_payload, f"failure evidence lost diagnostic value {diagnostic!r}")
    assert_condition(error_failure_payload["provider_writes_made"] is True, "error payload must retain attempted write state")
    assert_condition(error_failure_payload["provider_write_attempt_count"] == 1, "error payload attempt count mismatch")
    assert_condition(error_failure_payload["provider_write_success_count"] == 0, "error payload success count mismatch")

    plain_error_fixtures = (
        RuntimeError(
            "PATCH failed with 400 invalid_request: business_name=Acme Dental city=Austin "
            "message=bad dynamic variables"
        ),
        RuntimeError(
            "PATCH failed with 400 invalid_request: business_name: Mike's Kitchen city: Austin "
            "business_type: restaurant message: bad dynamic variables"
        ),
        RuntimeError(
            "PATCH failed with 400 invalid_request: business_name='Mike's Kitchen' city='Austin' "
            "message='bad dynamic variables'"
        ),
        RuntimeError(
            "PATCH failed with 400 invalid_request: customer_name=Jane Owner contact_email=owner@example.com "
            "contact_phone=+1 212 555 0188 address=123 Main Street service_type=roof repair "
            "authorization=Bearer plain-secret-token message=bad dynamic variables"
        ),
    )
    for fixture in plain_error_fixtures:
        sanitized_plain = patcher.safe_evidence_error_message(fixture)
        plain_payload = ledger.failure_payload(
            checkpoint_id=CHECKPOINT_ID,
            error=sanitized_plain,
        )
        rendered_plain = json.dumps(plain_payload, sort_keys=True)
        for forbidden in (
            "Acme",
            "Dental",
            "Mike",
            "Kitchen",
            "Austin",
            "restaurant",
            "Jane",
            "Owner",
            "owner@example.com",
            "212 555 0188",
            "123 Main Street",
            "roof repair",
            "plain-secret-token",
        ):
            assert_condition(forbidden not in rendered_plain, f"plain failure evidence leaked provider echo {forbidden!r}")
        for diagnostic in ("400", "invalid_request", "bad dynamic variables"):
            assert_condition(diagnostic in rendered_plain, f"plain failure evidence lost diagnostic value {diagnostic!r}")
        assert_condition(plain_payload["provider_write_attempt_count"] == 1, "plain error payload attempt count mismatch")
        assert_condition(plain_payload["provider_write_success_count"] == 0, "plain error payload success count mismatch")


def validate_live_patcher() -> None:
    patcher = read(PATCHER)
    assert_markers("040 live patcher", patcher, PATCHER_MARKERS)
    validate_live_patcher_semantics()


def assert_source_commit_shape(value: Any, label: str) -> str:
    assert_condition(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None, f"{label} source evidence commit must be a full 40-character sha")
    return value


def assert_provenance_agrees(*payloads: dict[str, Any]) -> tuple[str, str]:
    commits = [assert_source_commit_shape(payload.get("source_evidence_commit"), label) for label, payload in zip(("plan", "requests", "result"), payloads)]
    origins = [payload.get("source_evidence_origin") for payload in payloads]
    assert_condition(len(set(commits)) == 1, "plan/requests/result source evidence commit mismatch")
    assert_condition(all(origin == SOURCE_EVIDENCE_ORIGIN for origin in origins), "plan/requests/result source evidence origin mismatch")
    git(["rev-parse", "--verify", f"{commits[0]}^{{commit}}"])
    return commits[0], str(origins[0])


def assert_provider_counts(payload: dict[str, Any], *, expected_attempts: int, expected_successes: int, label: str) -> None:
    attempts = payload.get("provider_write_attempts")
    successes = payload.get("provider_write_successes")
    assert_condition(isinstance(attempts, list), f"{label} provider_write_attempts must be a list")
    assert_condition(isinstance(successes, list), f"{label} provider_write_successes must be a list")
    assert_condition(payload.get("provider_write_attempt_count") == expected_attempts, f"{label} provider write attempt count mismatch")
    assert_condition(payload.get("provider_write_success_count") == expected_successes, f"{label} provider write success count mismatch")
    assert_condition(len(attempts) == expected_attempts, f"{label} provider write attempt count malformed")
    assert_condition(len(successes) == expected_successes, f"{label} provider write success count malformed")
    if expected_attempts:
        attempt_ids = [item.get("request_id") for item in attempts if isinstance(item, dict)]
        success_ids = [item.get("request_id") for item in successes if isinstance(item, dict)]
        assert_condition(len(attempt_ids) == expected_attempts and all(isinstance(item, str) and item for item in attempt_ids), f"{label} provider write attempt request IDs malformed")
        assert_condition(len(success_ids) == expected_successes and all(isinstance(item, str) and item for item in success_ids), f"{label} provider write success request IDs malformed")


def expected_request_ids_for_targets(target_names: list[str]) -> list[str]:
    return [f"update_kb_file::{name}" for name in target_names] + ["patch_agent::prompt_dynamic_variables"]


def expected_source_path_for_request_id(request_id: str) -> str:
    assert_condition(request_id.startswith("update_kb_file::"), f"{request_id} source path request id mismatch")
    doc_name = request_id.split("::", 1)[1]
    assert_condition(doc_name in {Path(OFFER_PATH).name, Path(PRICE_PATH).name, Path(OUTPUT_PATH).name}, f"{request_id} source path doc mismatch")
    return f"runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/{doc_name}"


def source_bytes_for_commit(source_commit: str, source_path: str, current_head: str) -> bytes:
    return git_show_file_bytes(source_commit, source_path)


def assert_text_bytes(label: str, value: bytes) -> str:
    assert_condition(b"\0" not in value, f"{label} binary source content")
    try:
        return value.decode("utf-8")
    except UnicodeDecodeError as exc:
        fail(f"{label} non-UTF-8 source content: {exc}")


def validate_git_blob_source_evidence(source_evidence: dict[str, Any], *, request_id: str, blob_bytes: bytes) -> None:
    for field in REQUIRED_NEW_SOURCE_EVIDENCE_FIELDS:
        assert_condition(field in source_evidence, f"{request_id} missing required source evidence field {field}")
    blob_sha = sha256_bytes(blob_bytes)
    blob_length = len(blob_bytes)
    assert_condition(source_evidence.get("upload_sha256") == blob_sha, f"{request_id} upload byte sha mismatch")
    assert_condition(source_evidence.get("upload_length") == blob_length, f"{request_id} upload byte length mismatch")
    assert_condition(source_evidence.get("source_sha256") == source_evidence.get("upload_sha256"), f"{request_id} source sha alias mismatch")
    assert_condition(source_evidence.get("source_byte_length") == source_evidence.get("upload_length"), f"{request_id} source length alias mismatch")
    assert_condition(source_evidence.get("source_git_blob_sha256") == blob_sha, f"{request_id} git blob sha mismatch")
    assert_condition(source_evidence.get("source_git_blob_length") == blob_length, f"{request_id} git blob length mismatch")
    if "source_git_blob_byte_length" in source_evidence:
        assert_condition(source_evidence.get("source_git_blob_byte_length") == blob_length, f"{request_id} git blob byte length mismatch")
    assert_condition(
        source_evidence.get("newline_mode") in {"git_blob_lf", "git_blob_crlf", "worktree_crlf_normalized_to_git_lf"},
        f"{request_id} newline mode mismatch",
    )


def legacy_allowlist_mode(source_evidence: dict[str, Any], *, request_id: str, source_path: str, source_commit: str) -> str | None:
    legacy_key = (
        source_commit,
        request_id,
        source_path,
        source_evidence.get("source_sha256"),
        source_evidence.get("source_byte_length"),
    )
    return LEGACY_SOURCE_EVIDENCE_ALLOWLIST.get(legacy_key)


def validate_legacy_git_blob_old_fields(
    source_evidence: dict[str, Any],
    *,
    request_id: str,
    source_path: str,
    source_commit: str,
    current_head: str,
    source_blob_bytes: bytes,
) -> None:
    assert_condition(legacy_allowlist_mode(source_evidence, request_id=request_id, source_path=source_path, source_commit=source_commit) == "legacy_git_blob_old_fields", f"{request_id} legacy allowlist mismatch")
    source_text = assert_text_bytes(f"{request_id} legacy", source_blob_bytes)
    current_head_blob = git_show_file_bytes(current_head, source_path)
    assert_condition(current_head_blob == source_blob_bytes, f"{request_id} legacy current HEAD blob mismatch")
    assert_condition(source_evidence.get("source_sha256") == sha256_bytes(source_blob_bytes), f"{request_id} legacy git blob sha mismatch")
    assert_condition(source_evidence.get("source_byte_length") == len(source_blob_bytes), f"{request_id} legacy git blob length mismatch")
    markers = KB_REQUEST_SOURCE_MARKERS[Path(source_path).name]
    missing_markers = [marker for marker in markers if marker not in source_text]
    assert_condition(not missing_markers, f"{request_id} historical source markers missing: {missing_markers}")


def validate_legacy_worktree_line_endings(
    source_evidence: dict[str, Any],
    *,
    request_id: str,
    source_path: str,
    source_commit: str,
    current_head: str,
    source_blob_bytes: bytes,
) -> None:
    assert_condition(legacy_allowlist_mode(source_evidence, request_id=request_id, source_path=source_path, source_commit=source_commit) == "legacy_worktree_line_endings", f"{request_id} legacy allowlist mismatch")
    source_text = assert_text_bytes(f"{request_id} legacy", source_blob_bytes)
    current_head_blob = git_show_file_bytes(current_head, source_path)
    assert_condition(current_head_blob == source_blob_bytes, f"{request_id} legacy current HEAD blob mismatch")
    worktree_bytes = (ROOT / source_path).read_bytes()
    assert_text_bytes(f"{request_id} legacy worktree", worktree_bytes)
    legacy_upload_sha = sha256_bytes(worktree_bytes)
    assert_condition(source_evidence.get("source_sha256") == legacy_upload_sha, f"{request_id} legacy upload sha mismatch")
    assert_condition(source_evidence.get("source_byte_length") == len(worktree_bytes), f"{request_id} legacy upload length mismatch")
    assert_condition(b"\r\n" in worktree_bytes, f"{request_id} legacy worktree line endings missing")
    assert_condition(worktree_bytes.replace(b"\r\n", b"\n") == source_blob_bytes, f"{request_id} legacy CRLF normalization mismatch")
    markers = KB_REQUEST_SOURCE_MARKERS[Path(source_path).name]
    missing_markers = [marker for marker in markers if marker not in source_text]
    assert_condition(not missing_markers, f"{request_id} historical source markers missing: {missing_markers}")


def validate_source_evidence_for_commit(requests: list[dict[str, Any]], evidence_by_id: dict[str, Any], *, source_commit: str, current_head: str) -> dict[str, Any]:
    legacy_ids: list[str] = []
    legacy_line_ending_ids: list[str] = []
    for request in requests:
        request_id = request.get("request_id")
        assert_condition(isinstance(request_id, str) and request_id, "request missing request_id")
        assert_condition(request_id in evidence_by_id, f"patch plan missing source evidence for {request_id}")
        if request_id.startswith("update_kb_file::"):
            source_evidence = request.get("source_evidence")
            assert_condition(isinstance(source_evidence, dict), f"{request_id} missing source_evidence")
            assert_condition(source_evidence == evidence_by_id[request_id], f"{request_id} plan/request source evidence mismatch")
            source_path = source_evidence.get("source_path")
            assert_condition(isinstance(source_path, str) and source_path, f"{request_id} source path missing")
            expected_source_path = expected_source_path_for_request_id(request_id)
            assert_condition(source_path == expected_source_path, f"{request_id} source path mismatch")
            markers = KB_REQUEST_SOURCE_MARKERS[Path(source_path).name]
            source_bytes = source_bytes_for_commit(source_commit, source_path, current_head)
            source_sha_matches = source_evidence.get("source_sha256") == sha256_bytes(source_bytes)
            source_length_matches = source_evidence.get("source_byte_length") == len(source_bytes)
            if source_sha_matches and source_length_matches:
                legacy_mode = legacy_allowlist_mode(source_evidence, request_id=request_id, source_path=source_path, source_commit=source_commit)
                if legacy_mode == "legacy_git_blob_old_fields" and any(field not in source_evidence for field in REQUIRED_NEW_SOURCE_EVIDENCE_FIELDS):
                    validate_legacy_git_blob_old_fields(
                        source_evidence,
                        request_id=request_id,
                        source_path=source_path,
                        source_commit=source_commit,
                        current_head=current_head,
                        source_blob_bytes=source_bytes,
                    )
                    source_text = source_bytes.decode("utf-8")
                    legacy_ids.append(request_id)
                else:
                    source_text = assert_text_bytes(request_id, source_bytes)
                    validate_git_blob_source_evidence(source_evidence, request_id=request_id, blob_bytes=source_bytes)
            else:
                if all(field in source_evidence for field in REQUIRED_NEW_SOURCE_EVIDENCE_FIELDS):
                    fail(f"{request_id} source sha mismatch")
                validate_legacy_worktree_line_endings(
                    source_evidence,
                    request_id=request_id,
                    source_path=source_path,
                    source_commit=source_commit,
                    current_head=current_head,
                    source_blob_bytes=source_bytes,
                )
                source_text = source_bytes.decode("utf-8")
                legacy_ids.append(request_id)
                legacy_line_ending_ids.append(request_id)
            assert_condition(tuple(source_evidence.get("markers", ())) == markers, f"{request_id} marker list mismatch")
            missing_markers = [marker for marker in markers if marker not in source_text]
            assert_condition(not missing_markers, f"{request_id} historical source markers missing: {missing_markers}")
            assert_condition(source_evidence.get("evidence_origin") == SOURCE_EVIDENCE_ORIGIN, f"{request_id} evidence origin mismatch")
        elif request_id == "patch_agent::prompt_dynamic_variables":
            assert_condition(request.get("body_canonical_json_sha256") == canonical_sha256(request.get("body")), "agent request canonical digest mismatch")
            agent_evidence = evidence_by_id[request_id]
            assert_condition(isinstance(agent_evidence, dict), "agent plan source evidence must be an object")
            assert_condition(agent_evidence.get("body_canonical_json_sha256") == request.get("body_canonical_json_sha256"), "agent plan/request digest mismatch")
            assert_condition(agent_evidence.get("evidence_origin") in {"sanitized_request_body_before_provider_write_not_network_capture", "post_hoc_from_sanitized_request_body_not_network_capture"}, "agent digest origin mismatch")
        else:
            fail(f"unknown live evidence request id {request_id}")
    return {
        "source_evidence_mode": "legacy_worktree_line_endings" if legacy_line_ending_ids else ("legacy_allowlisted" if legacy_ids else "git_blob"),
        "legacy_allowlisted_request_ids": legacy_ids,
        "legacy_worktree_line_endings_request_ids": legacy_line_ending_ids,
    }


def validate_live_evidence_artifacts(
    evidence_dir: Path | None = None,
    *,
    require_existing_evidence: bool = False,
) -> dict[str, Any]:
    evidence_dir = LIVE_EVIDENCE_DIR if evidence_dir is None else evidence_dir
    if not evidence_dir.is_dir():
        assert_condition(not require_existing_evidence, f"Missing live evidence dir: {evidence_dir}")
        return {"status": "absent"}

    pre_snapshot = read_json_anywhere(evidence_dir / "live_agent_pre_patch_snapshot.json")
    post_snapshot = read_json_anywhere(evidence_dir / "live_agent_post_patch_snapshot.json")
    patch_plan = read_json_anywhere(evidence_dir / "live_agent_patch_plan.json")
    patch_requests = read_json_anywhere(evidence_dir / "live_agent_patch_requests.json")
    patch_result = read_json_anywhere(evidence_dir / "live_agent_patch_result.json")

    source_commit, _origin = assert_provenance_agrees(patch_plan, patch_requests, patch_result)
    requests = patch_requests.get("requests")
    assert_condition(isinstance(requests, list) and all(isinstance(request, dict) for request in requests), "live patch request artifact must contain request objects")
    target_names = patch_plan.get("kb_documents_planned_for_in_place_update")
    assert_condition(isinstance(target_names, list) and all(isinstance(name, str) for name in target_names), "patch plan must declare selected KB targets")
    expected_ids = expected_request_ids_for_targets(target_names)
    request_ids = [request.get("request_id") for request in requests]
    assert_condition(request_ids == expected_ids, f"live patch requests must match selected guarded subset: expected {expected_ids}, got {request_ids}")
    expected_count = len(expected_ids)
    for payload_label, payload in (("plan", patch_plan), ("requests", patch_requests), ("result", patch_result)):
        assert_condition(payload.get("planned_provider_write_count") == expected_count, f"{payload_label} planned provider write count mismatch")
        assert_condition(payload.get("planned_kb_write_count") == len(target_names), f"{payload_label} planned KB write count mismatch")
        assert_condition(payload.get("planned_agent_patch_count") == 1, f"{payload_label} planned agent patch count mismatch")
    evidence_by_id = patch_plan.get("request_source_evidence_by_id")
    assert_condition(isinstance(evidence_by_id, dict), "patch plan missing request_source_evidence_by_id")

    assert_condition("snapshot_serialized_at_utc" in pre_snapshot, "pre snapshot must separate serialization timestamp")
    assert_condition("snapshot_serialized_at_utc" in post_snapshot, "post snapshot must separate serialization timestamp")
    assert_condition("live_readback_time_recorded" in post_snapshot, "post snapshot must state readback timestamp recording status")

    current_head = git(["rev-parse", "HEAD"]).stdout.strip()
    source_summary = validate_source_evidence_for_commit(requests, evidence_by_id, source_commit=source_commit, current_head=current_head)
    provider_writes_allowed = patch_requests.get("provider_writes_allowed")
    status = patch_result.get("status")
    if source_commit != current_head:
        if status == "passed":
            assert_provider_counts(patch_result, expected_attempts=expected_count, expected_successes=expected_count, label="historical result")
        else:
            assert_provider_counts(patch_result, expected_attempts=0, expected_successes=0, label="historical result")
        return {"status": "excluded_valid_historical_source_commit", "source_evidence_commit": source_commit, **source_summary}

    if provider_writes_allowed is False and status == "plan_only_missing_confirmation":
        assert_provider_counts(patch_requests, expected_attempts=0, expected_successes=0, label="plan-only requests")
        assert_provider_counts(patch_result, expected_attempts=0, expected_successes=0, label="plan-only result")
        assert_condition(patch_result.get("provider_writes_made") is False, "plan-only result must report zero writes made")
        assert_condition(post_snapshot.get("phase") == "not_written", "plan-only post snapshot must be not_written")
    elif provider_writes_allowed is True and status == "passed":
        assert_provider_counts(patch_requests, expected_attempts=expected_count, expected_successes=expected_count, label="live requests")
        assert_provider_counts(patch_result, expected_attempts=expected_count, expected_successes=expected_count, label="live result")
        attempt_ids = [item.get("request_id") for item in patch_result["provider_write_attempts"]]
        success_ids = [item.get("request_id") for item in patch_result["provider_write_successes"]]
        assert_condition(attempt_ids == expected_ids, f"live result attempt IDs mismatch: {attempt_ids}")
        assert_condition(success_ids == expected_ids, f"live result success IDs mismatch: {success_ids}")
        assert_condition(post_snapshot.get("phase") == "post_patch", "live-passed post snapshot must be post_patch")
        assert_condition(post_snapshot.get("live_readback_time_recorded") is True, "live-passed post readback timestamp must be recorded")
        assert_condition(isinstance(post_snapshot.get("live_readback_at_utc"), str) and post_snapshot.get("live_readback_at_utc"), "live-passed post readback timestamp missing")
    else:
        fail(f"unsupported live evidence mode: provider_writes_allowed={provider_writes_allowed!r}, status={status!r}")
    return {"status": "validated_current_source_commit", "source_evidence_commit": source_commit, **source_summary}


def main() -> int:
    try:
        validate_prompt_policy()
        validate_pricing_kb()
        validate_output_rules()
        validate_tests()
        validate_live_patcher()
        live_evidence_validation = validate_live_evidence_artifacts()
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
                "live_evidence_validation": live_evidence_validation,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
