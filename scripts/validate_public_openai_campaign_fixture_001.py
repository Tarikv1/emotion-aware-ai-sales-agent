#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core import campaign_registry  # noqa: E402


CHECKPOINT_ID = "PUBLIC-OPENAI-CAMPAIGN-FIXTURE-001"
FIXTURE_PATH = ROOT / "runtime" / "campaigns" / "examples" / "public-openai-chatgpt-plans.json"
SOURCE_MANIFEST_PATH = ROOT / "research" / "sources" / "public_openai_chatgpt_plans" / "source_manifest.json"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"

ALLOWED_DOMAINS = {"openai.com", "chatgpt.com", "help.openai.com", "platform.openai.com"}
REQUIRED_FIELDS = {
    "campaign_id",
    "fixture_type",
    "not_affiliated_disclaimer",
    "source_policy",
    "customer_facing_company_name",
    "customer_facing_offer_name",
    "product_or_offer_name",
    "product_or_offer_summary",
    "high_level_value_proposition",
    "customer_facing_call_objective",
    "primary_conversion_goal",
    "close_mode",
    "close_modes_supported",
    "human_followup_owner",
    "self_serve_close_target",
    "self_serve_close_url",
    "self_serve_close_spoken_label",
    "self_serve_close_channel_policy",
    "contact_sales_target",
    "agent_can_say",
    "agent_must_not_claim",
    "allowed_claims",
    "blocked_claims",
    "source_grounded_claims",
    "buyer_personas",
    "plan_catalog",
    "plan_comparison_rules",
    "qualification_dimensions",
    "objection_handling_facts",
    "next_step_rules",
    "regulated_or_sensitive_boundaries",
    "cross_campaign_leakage_forbidden",
}
REQUIRED_PLAN_IDS = {
    "free",
    "go",
    "plus",
    "pro",
    "business_codex",
    "business_chatgpt_codex",
    "enterprise",
}
REQUIRED_PLAN_FIELDS = {
    "plan_id",
    "display_name",
    "buyer_type",
    "price_text",
    "price_source_fact_id",
    "included_features",
    "limits_summary",
    "best_for",
    "not_best_for",
    "next_step",
    "caveats",
}
SIDE_EFFECT_KEYS = [
    "provider_calls_made",
    "local_llm_calls_made",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
]


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError(f"{path.relative_to(ROOT)} must be a JSON object")
    return payload


def domain_allowed(url: str) -> bool:
    host = urlparse(str(url or "")).netloc.lower()
    return bool(host and any(host == domain or host.endswith("." + domain) for domain in ALLOWED_DOMAINS))


def assert_condition(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def write_evidence(result: dict[str, Any], report: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(report, encoding="utf-8")


def text_blob(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(text_blob(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(text_blob(item) for item in value)
    return str(value or "")


def main() -> None:
    failures: list[str] = []
    assert_condition(failures, FIXTURE_PATH.is_file(), f"fixture missing: {FIXTURE_PATH.relative_to(ROOT)}")
    assert_condition(failures, SOURCE_MANIFEST_PATH.is_file(), f"source manifest missing: {SOURCE_MANIFEST_PATH.relative_to(ROOT)}")
    fixture = load_json(FIXTURE_PATH) if FIXTURE_PATH.is_file() else {}
    manifest = load_json(SOURCE_MANIFEST_PATH) if SOURCE_MANIFEST_PATH.is_file() else {}
    manifest_claims = {str(claim.get("fact_id")): claim for claim in manifest.get("claims") or [] if isinstance(claim, dict)}

    registry_validation = campaign_registry.validate_campaign_config(fixture)
    assert_condition(failures, registry_validation.get("valid") is True, f"campaign registry validation failed: {registry_validation}")
    loaded = campaign_registry.load_campaign_config(FIXTURE_PATH) if registry_validation.get("valid") else fixture

    missing = sorted(field for field in REQUIRED_FIELDS if loaded.get(field) in (None, "", [], {}))
    assert_condition(failures, not missing, f"fixture missing required fields: {missing}")
    assert_condition(failures, loaded.get("campaign_id") == "public-openai-chatgpt-plans", "campaign_id mismatch")
    assert_condition(failures, loaded.get("fixture_type") == "public_data_simulation", "fixture_type mismatch")
    assert_condition(failures, loaded.get("objective") == "self_serve_plan_fit", "objective must be self_serve_plan_fit")
    assert_condition(failures, loaded.get("not_affiliated_disclaimer") is True, "not_affiliated_disclaimer must be true")
    assert_condition(failures, loaded.get("cross_campaign_leakage_forbidden") is True, "cross_campaign_leakage_forbidden must be true")
    assert_condition(failures, loaded.get("should_speak_raw_url") is False, "should_speak_raw_url must be false")
    assert_condition(failures, loaded.get("link_available_in_packet") is True, "link_available_in_packet must be true")
    assert_condition(failures, loaded.get("can_send_email") is False, "can_send_email must be false")
    assert_condition(failures, "http" not in str(loaded.get("self_serve_close_spoken_label") or "").lower(), "self_serve_close_spoken_label must not include raw URL")

    for url_field in ("self_serve_close_target", "self_serve_close_url", "contact_sales_target"):
        assert_condition(failures, domain_allowed(str(loaded.get(url_field) or "")), f"{url_field} must use official domain")

    close_modes = set(campaign_registry.close_modes_supported(loaded))
    for mode in ("self_serve_purchase_link", "contact_sales"):
        assert_condition(failures, mode in close_modes, f"{mode} close mode missing")
    assert_condition(failures, "appointment_review" not in close_modes, "appointment_review should not be a primary close mode")

    source_claims = campaign_registry.source_grounded_claims(loaded)
    source_claim_ids = {str(claim.get("fact_id")) for claim in source_claims}
    assert_condition(failures, bool(source_claims), "source_grounded_claims must be populated")
    for claim in source_claims:
        fact_id = str(claim.get("fact_id") or "")
        assert_condition(failures, fact_id in manifest_claims, f"campaign source claim not in manifest: {fact_id}")
        assert_condition(failures, domain_allowed(str(claim.get("source_url") or "")), f"{fact_id}: non-official source_url")

    for fact_id in loaded.get("allowed_claims") or []:
        assert_condition(failures, str(fact_id) in manifest_claims, f"allowed claim is not source-backed in manifest: {fact_id}")

    plan_catalog = campaign_registry.plan_catalog(loaded)
    plan_ids = {str(plan.get("plan_id")) for plan in plan_catalog}
    assert_condition(failures, REQUIRED_PLAN_IDS <= plan_ids, f"missing plan ids: {sorted(REQUIRED_PLAN_IDS - plan_ids)}")
    close_by_plan: dict[str, str] = {}
    for plan in plan_catalog:
        plan_id = str(plan.get("plan_id") or "")
        missing_plan_fields = sorted(field for field in REQUIRED_PLAN_FIELDS if plan.get(field) in (None, "", [], {}))
        assert_condition(failures, not missing_plan_fields, f"{plan_id}: missing plan fields {missing_plan_fields}")
        assert_condition(failures, str(plan.get("price_source_fact_id") or "") in manifest_claims, f"{plan_id}: price_source_fact_id not source-backed")
        next_step = plan.get("next_step") or {}
        close_mode = str(next_step.get("close_mode") or "")
        close_by_plan[plan_id] = close_mode
        if plan_id in {"free", "go", "plus", "pro"}:
            assert_condition(failures, close_mode == "self_serve_purchase_link", f"{plan_id}: expected self_serve_purchase_link")
        if plan_id == "enterprise":
            assert_condition(failures, close_mode == "contact_sales", "enterprise: expected contact_sales")
        if plan_id in {"business_codex", "business_chatgpt_codex"}:
            assert_condition(failures, close_mode in {"self_serve_purchase_link", "contact_sales"}, f"{plan_id}: unsupported business close mode")

    safety = loaded.get("safety") or {}
    for key in SIDE_EFFECT_KEYS:
        assert_condition(failures, safety.get(key) is False, f"safety.{key} must be false")

    blocked_blob = text_blob(loaded.get("blocked_claims")).lower()
    for phrase in ("email", "calendar", "crm", "discount", "enterprise pricing", "affiliation"):
        assert_condition(failures, phrase in blocked_blob, f"blocked claims should cover {phrase}")

    full_text = text_blob(loaded)
    raw_emails = re.findall(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", full_text, flags=re.I)
    assert_condition(failures, not raw_emails, f"fixture must not contain real customer email addresses: {raw_emails}")
    assert_condition(failures, "provider_calls_made\": true" not in json.dumps(loaded), "provider side effect true found")

    category_counts = Counter(str((manifest_claims.get(fact_id) or {}).get("claim_category") or "unknown") for fact_id in loaded.get("allowed_claims") or [])
    result = {
        "status": "pass" if not failures else "fail",
        "checkpoint_id": CHECKPOINT_ID,
        "fixture": str(FIXTURE_PATH.relative_to(ROOT)),
        "registry_validation": registry_validation,
        "objective": loaded.get("objective"),
        "primary_conversion_goal": loaded.get("primary_conversion_goal"),
        "plan_ids": sorted(plan_ids),
        "close_modes_supported": sorted(close_modes),
        "close_by_plan": close_by_plan,
        "manifest_claim_count": len(manifest_claims),
        "campaign_source_grounded_claim_count": len(source_claims),
        "allowed_claim_count": len(loaded.get("allowed_claims") or []),
        "allowed_claim_categories": dict(sorted(category_counts.items())),
        **{key: False for key in SIDE_EFFECT_KEYS},
        "failures": failures,
    }
    report = "\n".join(
        [
            f"# {CHECKPOINT_ID}",
            "",
            f"- Status: `{result['status']}`",
            f"- Fixture: `{result['fixture']}`",
            f"- Plan categories covered: `{', '.join(result['plan_ids'])}`",
            f"- Close modes: `{', '.join(result['close_modes_supported'])}`",
            f"- Manifest claim count: `{result['manifest_claim_count']}`",
            f"- Campaign source-grounded claim objects: `{result['campaign_source_grounded_claim_count']}`",
            f"- Side effects false: `{all(result[key] is False for key in SIDE_EFFECT_KEYS)}`",
            f"- Failures: `{len(failures)}`",
            "",
        ]
    )
    write_evidence(result, report)
    if failures:
        print(json.dumps(result, indent=2, sort_keys=True))
        sys.exit(1)
    print(json.dumps({"status": "pass", "checkpoint_id": CHECKPOINT_ID, "plan_count": len(plan_catalog)}, indent=2))


if __name__ == "__main__":
    main()
