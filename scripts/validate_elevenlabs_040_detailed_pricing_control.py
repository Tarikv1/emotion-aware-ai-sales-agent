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

EXPECTED_MODIFIED_PRODUCT_FILES = [
    PROMPT_PATH,
    OFFER_PATH,
    PRICE_PATH,
    OUTPUT_PATH,
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

KB_REQUEST_SOURCE_MARKERS = {
    "atlas_offer_facts.md": (
        "Quick Launch: `$500-$800`",
        "Essential Local: `{{website_basic_site_range}}`",
        "Integration Website: `{{website_integration_heavy_range}}`",
    ),
    "atlas_price_scope_cost_drivers.md": (
        "After explicit price intent, Emma must answer by the first or second price ask.",
        "Base Package Ladder",
        "{{website_integration_heavy_range}}",
    ),
    "atlas_output_quality_rules.md": (
        "Pricing Quote Discipline",
        "Never disclose a paid price before explicit buyer price intent.",
        "Do not read the package or feature menu aloud.",
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


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("ascii")).hexdigest()


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

    requests = patcher.patch_requests(agent, {"target_kb_docs": {name: {"id": doc_id, "source_path": f"runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/{name}"} for name, doc_id in patcher.KNOWN_KB_DOC_IDS.items()}})
    for request in requests:
        if request["request_id"].startswith("update_kb_file::"):
            source_evidence = request.get("source_evidence")
            assert_condition(isinstance(source_evidence, dict), f"{request['request_id']} missing source_evidence")
            source_path = ROOT / source_evidence["source_path"]
            source_bytes = source_path.read_bytes()
            assert_condition(source_evidence.get("source_sha256") == sha256_bytes(source_bytes), f"{request['request_id']} source sha mismatch")
            assert_condition(source_evidence.get("source_byte_length") == len(source_bytes), f"{request['request_id']} source byte length mismatch")
            markers = source_evidence.get("markers")
            assert_condition(isinstance(markers, list) and markers, f"{request['request_id']} missing source markers")
            assert_condition(all(isinstance(marker, str) and marker in source_path.read_text(encoding="utf-8") for marker in markers), f"{request['request_id']} source marker mismatch")
        elif request["request_id"] == "patch_agent::prompt_dynamic_variables":
            assert_condition(request.get("body_canonical_json_sha256") == canonical_sha256(request["body"]), "agent patch request canonical digest mismatch")

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


def validate_live_evidence_artifacts() -> None:
    if not LIVE_EVIDENCE_DIR.is_dir():
        return

    pre_snapshot = read_json(LIVE_EVIDENCE_DIR / "live_agent_pre_patch_snapshot.json")
    post_snapshot = read_json(LIVE_EVIDENCE_DIR / "live_agent_post_patch_snapshot.json")
    patch_plan = read_json(LIVE_EVIDENCE_DIR / "live_agent_patch_plan.json")
    patch_requests = read_json(LIVE_EVIDENCE_DIR / "live_agent_patch_requests.json")
    patch_result = read_json(LIVE_EVIDENCE_DIR / "live_agent_patch_result.json")

    attempts = patch_result.get("provider_write_attempts")
    assert_condition(isinstance(attempts, list) and len(attempts) == 4, "live evidence must retain four provider write attempts")
    first_attempt_at = attempts[0].get("attempted_at_utc")
    assert_condition(isinstance(first_attempt_at, str) and first_attempt_at, "first provider attempt timestamp missing")

    assert_condition("snapshot_serialized_at_utc" in pre_snapshot, "pre snapshot must separate serialization timestamp")
    assert_condition(pre_snapshot.get("snapshot_serialized_at_utc") == "2026-07-11T19:16:54Z", "pre snapshot must preserve original serialized timestamp")
    assert_condition(pre_snapshot.get("live_readback_time_recorded") is False, "completed-run pre fetch time must be explicitly marked unrecorded")
    assert_condition(pre_snapshot.get("live_readback_at_utc") is None, "completed-run pre fetch time must not be invented")
    ordering = pre_snapshot.get("verified_ordering", {})
    assert_condition(ordering.get("pre_state_fetched_before_provider_write_attempts") is True, "pre snapshot ordering metadata missing")
    assert_condition(ordering.get("first_provider_write_attempt_at_utc") == first_attempt_at, "pre snapshot first-attempt timestamp mismatch")
    assert_condition("control flow" in str(ordering.get("basis", "")).lower(), "pre snapshot ordering basis must cite control flow")

    assert_condition("snapshot_serialized_at_utc" in post_snapshot, "post snapshot must separate serialization timestamp")
    assert_condition("live_readback_time_recorded" in post_snapshot, "post snapshot must state readback timestamp recording status")

    source_commit = patch_requests.get("source_evidence_commit")
    assert_condition(source_commit == "336ff778b4beaa05a73996eef93318a7e5163eb1", "current evidence must label unchanged source commit")
    assert_condition(patch_plan.get("source_evidence_commit") == source_commit, "plan/source request source commit mismatch")
    assert_condition(patch_requests.get("source_evidence_origin") == "post_hoc_from_unchanged_repo_commit_not_network_capture", "requests must label post-hoc source evidence")
    assert_condition(patch_plan.get("source_evidence_origin") == "post_hoc_from_unchanged_repo_commit_not_network_capture", "plan must label post-hoc source evidence")

    requests = patch_requests.get("requests")
    assert_condition(isinstance(requests, list) and len(requests) == 4, "live patch request artifact must contain four requests")
    evidence_by_id = patch_plan.get("request_source_evidence_by_id")
    assert_condition(isinstance(evidence_by_id, dict), "patch plan missing request_source_evidence_by_id")
    for request in requests:
        request_id = request.get("request_id")
        assert_condition(request_id in evidence_by_id, f"patch plan missing source evidence for {request_id}")
        if str(request_id).startswith("update_kb_file::"):
            source_evidence = request.get("source_evidence")
            assert_condition(isinstance(source_evidence, dict), f"{request_id} missing source_evidence")
            assert_condition(source_evidence == evidence_by_id[request_id], f"{request_id} plan/request source evidence mismatch")
            source_path = ROOT / source_evidence["source_path"]
            source_bytes = source_path.read_bytes()
            markers = KB_REQUEST_SOURCE_MARKERS[source_path.name]
            assert_condition(source_evidence.get("source_sha256") == sha256_bytes(source_bytes), f"{request_id} source sha mismatch")
            assert_condition(source_evidence.get("source_byte_length") == len(source_bytes), f"{request_id} source length mismatch")
            assert_condition(tuple(source_evidence.get("markers", ())) == markers, f"{request_id} marker list mismatch")
            assert_condition(source_evidence.get("evidence_origin") == "post_hoc_from_unchanged_repo_commit_not_network_capture", f"{request_id} evidence origin mismatch")
        elif request_id == "patch_agent::prompt_dynamic_variables":
            assert_condition(request.get("body_canonical_json_sha256") == canonical_sha256(request.get("body")), "agent request canonical digest mismatch")
            assert_condition(evidence_by_id[request_id].get("body_canonical_json_sha256") == request.get("body_canonical_json_sha256"), "agent plan/request digest mismatch")
            assert_condition(evidence_by_id[request_id].get("evidence_origin") == "post_hoc_from_sanitized_request_body_not_network_capture", "agent digest origin mismatch")


def main() -> int:
    try:
        validate_prompt_policy()
        validate_pricing_kb()
        validate_output_rules()
        validate_tests()
        validate_live_patcher()
        validate_live_evidence_artifacts()
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
