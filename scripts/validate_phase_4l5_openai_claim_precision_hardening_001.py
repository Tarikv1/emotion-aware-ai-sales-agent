#!/usr/bin/env python3
from __future__ import annotations

import ast
from collections import Counter
import json
import os
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import validate_phase_4l2_openai_primary_universal_sales_eval_001 as phase4l2  # noqa: E402
from scripts import validate_phase_4l3_openai_spoken_sales_quality_multiturn_001 as phase4l3  # noqa: E402
from scripts import validate_phase_4l4_openai_source_refresh_plan_taxonomy_001 as phase4l4  # noqa: E402


CHECKPOINT_ID = "PHASE-4L5-OPENAI-CLAIM-PRECISION-HARDENING-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
SOURCE_MANIFEST_PATH = ROOT / "research" / "sources" / "public_openai_chatgpt_plans" / "source_manifest.json"
FIXTURE_PATH = ROOT / "runtime" / "campaigns" / "examples" / "public-openai-chatgpt-plans.json"

CLAIM_PRECISION_CATEGORIES = [
    "stable_source_claim",
    "current_terms_claim_requires_caveat",
    "source_conflict_or_ambiguous",
    "unsupported_do_not_say",
    "official_route_only",
]
OFFICIAL_SOURCES_INSPECTED = [
    {
        "url": "https://chatgpt.com/pricing/",
        "source_type": "official_pricing_page",
        "use": "current plan table, Go feature rows, ads note, model/limit rows, Business/Enterprise grouping",
    },
    {
        "url": "https://help.openai.com/en/articles/11989085-what-is-chatgpt-go",
        "source_type": "official_help_article",
        "use": "Go positioning, Go feature wording, availability, ads note, API boundary, pricing caveat",
    },
    {
        "url": "https://help.openai.com/en/articles/6950777-what-is-chatgpt-plus",
        "source_type": "official_help_article",
        "use": "Plus price, API boundary, limits caveat, privacy-training caveat",
    },
    {
        "url": "https://help.openai.com/en/articles/9793128-what-is-chatgpt-pro",
        "source_type": "official_help_article",
        "use": "Pro tier pricing, usage multipliers, upgrade path, promo caveats",
    },
    {
        "url": "https://help.openai.com/en/articles/8792828-what-is-chatgpt-business",
        "source_type": "official_help_article",
        "use": "Business seat types, pricing caveats, API boundary, workspace data caveat",
    },
    {
        "url": "https://help.openai.com/en/articles/8265053-what-is-chatgpt-enterprise",
        "source_type": "official_help_article",
        "use": "Enterprise admin/security positioning, seat-type limits, contact-sales/API boundaries",
    },
    {
        "url": "https://help.openai.com/en/articles/7730893-data-controls-in-chatgpt",
        "source_type": "official_help_article",
        "use": "consumer training opt-out and Temporary Chat caveats",
    },
    {
        "url": "https://openai.com/enterprise-privacy/",
        "source_type": "official_privacy_page",
        "use": "business-data ownership/control and security-control wording",
    },
]
AMBIGUOUS_OR_CONFLICT_RISK_CLAIMS_FOUND = [
    {
        "claim_id": "go_features_001",
        "risk": "Go feature exactness",
        "reason": "The Go help article broadly names projects, tasks, and custom GPTs while the pricing feature table marks Tasks as not included for Go.",
        "new_category": "source_conflict_or_ambiguous",
    },
    {
        "claim_id": "go_pricing_availability_ads",
        "risk": "Go current terms",
        "reason": "Go pricing, availability, and ads language are current-term surfaces that can change and should route to official pages.",
        "new_category": "current_terms_claim_requires_caveat",
    },
    {
        "claim_id": "model_access_and_usage_limits",
        "risk": "model and limit exactness",
        "reason": "Plan table model names, model access, context windows, and usage limits are fast-changing and should not be guaranteed in speech.",
        "new_category": "official_route_only",
    },
    {
        "claim_id": "enterprise_security_compliance",
        "risk": "security and compliance guarantees",
        "reason": "Business and Enterprise admin/security claims are official-source summaries, not guarantees that a buyer's policy is satisfied.",
        "new_category": "official_route_only",
    },
    {
        "claim_id": "privacy_training_consumer_business",
        "risk": "privacy/training overclaim",
        "reason": "Privacy and training claims depend on plan, settings, terms, and exceptions; responses must not turn them into blanket guarantees.",
        "new_category": "current_terms_claim_requires_caveat",
    },
]
CLAIMS_CHANGED_OR_DOWNGRADED = [
    "go_features_001",
    "pricing_plan_set_001",
    "plus_features_001",
    "pro_features_001",
    "pro_tiers_100_200_001",
    "business_standard_seat_price_001",
    "business_standard_seat_includes_codex_001",
    "business_no_training_workspace_data_001",
    "enterprise_overview_001",
    "enterprise_security_admin_features_001",
    "consumer_data_controls_opt_out_001",
    "temporary_chat_training_boundary_001",
    "enterprise_privacy_no_training_default_001",
    "enterprise_privacy_controls_001",
    "limits_vary_by_plan_model_001",
]
RESPONSE_CHANGES_MADE = [
    "Go overview no longer lists tasks, projects, custom GPTs, images, files, data analysis, and memory as a confident combined buyer-facing list.",
    "Go feature-exact questions use conservative wording and route exact feature availability to the official ChatGPT plans page.",
    "Go vs Plus feature-difference questions give a high-level distinction and route exact plan-table differences to official sources.",
    "Exact Go pricing, terms, model access, limits, and regional availability route to official OpenAI pages.",
    "Go ads answers use cautious future-testing wording and avoid guarantees.",
    "Enterprise/security answers refuse compliance guarantees and route to official sales/security review.",
]
FALSE_FLAGS = phase4l2.FALSE_FLAGS
FORBIDDEN_IMPORT_ROOTS = {"elevenlabs", "httpx", "openai", "requests", "ultravox", "urllib"}
SHADOW_ENV_GATES = phase4l2.SHADOW_ENV_GATES
UNSUPPORTED_EXACT_RESPONSE_PHRASES = [
    "Go is mainly for more access to common tools such as image generation, file uploads, data analysis, memory, projects, tasks, and custom GPTs.",
    "Go adds more access to common tools like image generation, file uploads, data analysis, memory, projects, tasks, and custom GPTs.",
    "Go includes tasks, projects, and custom GPTs",
    "Go always includes",
    "guaranteed access to",
    "guaranteed compliant",
    "your data is never used",
]

CLAIM_CONFLICT_CASES: list[dict[str, Any]] = [
    {
        "case_id": "go_feature_exactness",
        "buyer_utterance": "Does Go include tasks, projects, and custom GPTs?",
        "expected_behavior": "Conservative answer, no confident unsupported exact Go feature list if sources are ambiguous.",
        "must_include_all": ["go", "official"],
        "must_include_any": [["feature", "availability", "plan"], ["check", "current", "source", "page"]],
        "must_not_include": ["go includes tasks, projects, and custom gpts", "go always includes"],
    },
    {
        "case_id": "go_vs_plus_feature_detail",
        "buyer_utterance": "Exactly what does Plus have that Go does not?",
        "expected_behavior": "High-level distinction, route exact feature table to official page.",
        "must_include_all": ["go", "plus", "official"],
        "must_include_any": [["exact", "feature table", "plan page"], ["stronger", "advanced", "broader"]],
        "must_not_include": ["the exact difference is"],
    },
    {
        "case_id": "go_pricing",
        "buyer_utterance": "What is the exact current Go price?",
        "expected_behavior": "Do not invent; route to official pricing page.",
        "must_include_all": ["go", "official"],
        "must_include_any": [["pricing page", "plans page"], ["exact", "current", "can change"]],
        "must_not_include": ["20 dollars", "100 dollar", "200 dollar", "$20", "$100", "$200"],
    },
    {
        "case_id": "go_availability",
        "buyer_utterance": "Is Go available in my country?",
        "expected_behavior": "Source-bounded; route current availability to official help/pricing.",
        "must_include_all": ["go", "official"],
        "must_include_any": [["availability", "country", "supported"], ["current", "can change", "check"]],
    },
    {
        "case_id": "go_ads",
        "buyer_utterance": "Will Go include ads?",
        "expected_behavior": "Cautious wording based on official note; do not overstate.",
        "must_include_all": ["go", "ads"],
        "must_include_any": [["may", "testing", "future"], ["official", "help", "faq"]],
        "must_not_include": ["will include ads", "will not include ads", "never include ads"],
    },
    {
        "case_id": "api_boundary",
        "buyer_utterance": "Does Go include API usage?",
        "expected_behavior": "API separate; route API pricing separately.",
        "must_include_all": ["api", "separate"],
        "must_include_any": [["pricing", "billed independently"], ["chatgpt subscriptions", "chatgpt plan"]],
    },
    {
        "case_id": "enterprise_security_exactness",
        "buyer_utterance": "Can you guarantee Enterprise is compliant with our policy?",
        "expected_behavior": "No guarantee; contact-sales/security review route.",
        "must_include_all": ["enterprise"],
        "must_include_any": [["cannot", "can't"], ["guarantee", "compliance"], ["contact sales", "security review", "official"]],
        "must_not_include": ["guaranteed compliant", "will satisfy your policy"],
    },
    {
        "case_id": "model_version_exactness",
        "buyer_utterance": "Does Go always include GPT-5.5 Thinking and Pro models?",
        "expected_behavior": "Avoid unsupported exact guarantee; route to official plan table.",
        "must_include_all": ["go", "official"],
        "must_include_any": [["model", "models"], ["plan table", "plans page", "limits"], ["cannot guarantee", "do not guarantee", "can't guarantee"]],
        "must_not_include": ["go always includes", "gpt-5.5 pro is included in go"],
    },
]


def normalize(value: str) -> str:
    return phase4l2.normalize(value)


def contains_any(text: str, needles: list[str]) -> bool:
    return phase4l2.contains_any(text, needles)


def contains_all(text: str, needles: list[str]) -> bool:
    return phase4l2.contains_all(text, needles)


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def claims_from_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    claims = payload.get("claims")
    if not isinstance(claims, list):
        claims = payload.get("source_grounded_claims")
    return [item for item in claims or [] if isinstance(item, dict)]


def claim_precision_metadata_status() -> dict[str, Any]:
    manifest = read_json(SOURCE_MANIFEST_PATH)
    fixture = read_json(FIXTURE_PATH)
    manifest_claims = claims_from_payload(manifest)
    fixture_claims = claims_from_payload(fixture)
    allowed = set(CLAIM_PRECISION_CATEGORIES)
    missing_manifest = [
        str(item.get("fact_id") or "")
        for item in manifest_claims
        if str(item.get("claim_precision_category") or "") not in allowed
    ]
    missing_fixture = [
        str(item.get("fact_id") or "")
        for item in fixture_claims
        if str(item.get("claim_precision_category") or "") not in allowed
    ]
    manifest_categories = {
        str(item.get("category_id") or "")
        for item in manifest.get("claim_precision_categories") or []
        if isinstance(item, dict)
    }
    fixture_categories = {
        str(item.get("category_id") or "")
        for item in fixture.get("claim_precision_categories") or []
        if isinstance(item, dict)
    }
    category_counts = Counter(
        str(item.get("claim_precision_category") or "") for item in manifest_claims if item.get("claim_precision_category")
    )
    conflict_claims = [
        str(item.get("fact_id") or "")
        for item in manifest_claims
        if item.get("claim_precision_category") == "source_conflict_or_ambiguous"
    ]
    return {
        "manifest_categories_present": sorted(manifest_categories),
        "fixture_categories_present": sorted(fixture_categories),
        "manifest_claims_missing_precision_category": missing_manifest,
        "fixture_claims_missing_precision_category": missing_fixture,
        "manifest_claim_precision_category_counts": dict(sorted(category_counts.items())),
        "source_conflict_or_ambiguous_claim_ids": conflict_claims,
    }


def evaluate_claim_conflict_case(case: dict[str, Any]) -> dict[str, Any]:
    run = phase4l2.run_turn_sequence([case["buyer_utterance"]])
    response = str(run.get("final_response") or "")
    frame = run.get("final_frame") if isinstance(run.get("final_frame"), dict) else {}
    failures: list[str] = []
    if not response.strip():
        failures.append("final response was empty")
    if not contains_all(response, list(case.get("must_include_all") or [])):
        failures.append("required response terms missing")
    for group in case.get("must_include_any") or []:
        if not contains_any(response, list(group)):
            failures.append(f"required any-term group missing: {group}")
    if contains_any(response, list(case.get("must_not_include") or [])):
        failures.append("forbidden response term present")
    if contains_any(response, UNSUPPORTED_EXACT_RESPONSE_PHRASES):
        failures.append("unsupported exact feature or guarantee phrase present")
    if phase4l2.response_word_count(response) > 95:
        failures.append("response was too long for spoken sales use")
    contamination = phase4l2.contamination_hits_in_text(response)
    if contamination:
        failures.append(f"response contains RouteSignal contamination: {contamination}")
    return {
        "case_id": case["case_id"],
        "buyer_utterance": case["buyer_utterance"],
        "expected_behavior": case["expected_behavior"],
        "actual_semantic_action_response_summary": {
            "semantic": str(frame.get("semantic") or ""),
            "dialogue_focus": str(frame.get("dialogue_focus") or ""),
            "action_id": str(frame.get("action_id") or "continue_with_session_policy"),
            "response_summary": response.split(".")[0].strip(),
        },
        "actual_response": response,
        "pass": not failures,
        "failures": failures,
    }


def unsupported_exact_response_hits(case_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for item in case_results:
        response = str(item.get("actual_response") or "")
        terms = [phrase for phrase in UNSUPPORTED_EXACT_RESPONSE_PHRASES if phrase.lower() in response.lower()]
        if terms:
            hits.append({"case_id": item["case_id"], "terms": terms})
    return hits


def route_signal_hits(case_results: list[dict[str, Any]], phase4l4_result: dict[str, Any]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for item in case_results:
        terms = phase4l2.contamination_hits_in_text(str(item.get("actual_response") or ""))
        if terms:
            hits.append({"matrix": "claim_conflict_cases_4l5", "case_id": item["case_id"], "terms": terms})
    for item in phase4l4_result.get("routesignal_contamination_hits") or []:
        if isinstance(item, dict):
            hits.append({"matrix": "phase4l4", **item})
    return hits


def build_result() -> dict[str, Any]:
    case_results = [evaluate_claim_conflict_case(case) for case in CLAIM_CONFLICT_CASES]
    case_failures = [item for item in case_results if not item["pass"]]
    precision_metadata = claim_precision_metadata_status()
    phase4l2_result = phase4l2.build_result()
    phase4l3_result = phase4l3.build_result()
    phase4l4_result = phase4l4.build_result()
    phase4l3_single_turn_regressions = int(phase4l3_result.get("single_turn_4l2_regression_count") or 0)
    phase4l3_multi_turn_fails = int((phase4l3_result.get("multi_turn_pass_fail_count") or {}).get("fail") or 0)
    phase4l4_go_fails = int((phase4l4_result.get("go_specific_pass_fail_count") or {}).get("fail") or 0)
    route_hits = route_signal_hits(case_results, phase4l4_result)
    exact_hits = unsupported_exact_response_hits(case_results)
    metadata_ok = (
        set(CLAIM_PRECISION_CATEGORIES).issubset(set(precision_metadata["manifest_categories_present"]))
        and set(CLAIM_PRECISION_CATEGORIES).issubset(set(precision_metadata["fixture_categories_present"]))
        and not precision_metadata["manifest_claims_missing_precision_category"]
        and not precision_metadata["fixture_claims_missing_precision_category"]
        and "go_features_001" in precision_metadata["source_conflict_or_ambiguous_claim_ids"]
    )
    all_pass = (
        metadata_ok
        and not case_failures
        and not exact_hits
        and phase4l2_result.get("status") == "pass"
        and phase4l3_result.get("status") == "pass"
        and phase4l4_result.get("status") == "pass"
        and phase4l3_single_turn_regressions == 0
        and phase4l3_multi_turn_fails == 0
        and phase4l4_go_fails == 0
        and not route_hits
    )
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "pass" if all_pass else "fail",
        "primary_benchmark_campaign": "public OpenAI ChatGPT plans",
        "official_sources_inspected": OFFICIAL_SOURCES_INSPECTED,
        "claim_precision_categories": CLAIM_PRECISION_CATEGORIES,
        "claim_precision_metadata_status": precision_metadata,
        "ambiguous_conflict_risk_claims_found": AMBIGUOUS_OR_CONFLICT_RISK_CLAIMS_FOUND,
        "claims_changed_or_downgraded": CLAIMS_CHANGED_OR_DOWNGRADED,
        "response_changes_made": RESPONSE_CHANGES_MADE,
        "claim_conflict_case_results": case_results,
        "claim_conflict_pass_fail_count": {
            "pass": sum(1 for item in case_results if item["pass"]),
            "fail": sum(1 for item in case_results if not item["pass"]),
        },
        "unsupported_exact_response_hits": exact_hits,
        "phase4l2_regression_status": "pass" if phase4l2_result.get("status") == "pass" else "fail",
        "phase4l2_single_turn_regression_count": int((phase4l2_result.get("pass_fail_count") or {}).get("fail") or 0),
        "phase4l3_regression_status": "pass"
        if phase4l3_result.get("status") == "pass" and phase4l3_single_turn_regressions == 0 and phase4l3_multi_turn_fails == 0
        else "fail",
        "phase4l3_single_turn_4l2_regression_count": phase4l3_single_turn_regressions,
        "phase4l3_multi_turn_fail_count": phase4l3_multi_turn_fails,
        "phase4l4_regression_status": "pass" if phase4l4_result.get("status") == "pass" and phase4l4_go_fails == 0 else "fail",
        "phase4l4_go_specific_fail_count": phase4l4_go_fails,
        "routesignal_contamination_count": len(route_hits),
        "routesignal_contamination_hits": route_hits,
        "selector_response_replacement_status": "blocked",
        "no_side_effect_confirmation": {
            "selector_control_allowed": False,
            "live_selector_control_recommended": False,
            "response_replacement_performed": False,
            "provider_model_tts_crm_email_calendar_payment_account_side_effect_path_enabled": False,
            "raw_private_transcript_or_audio_added_to_public_evidence": False,
            "live_readiness_claimed": False,
        },
        "no_live_readiness_confirmation": True,
        **{key: False for key in FALSE_FLAGS},
    }


def build_report(result: dict[str, Any]) -> str:
    counts = Counter("pass" if item["pass"] else "fail" for item in result["claim_conflict_case_results"])
    lines = [
        f"# {CHECKPOINT_ID}",
        "",
        f"- Status: {result['status']}",
        "- Primary benchmark campaign: public OpenAI ChatGPT plans",
        f"- Claim-conflict case pass count: {counts['pass']}",
        f"- Claim-conflict case fail count: {counts['fail']}",
        f"- 4L2 regression status: {result['phase4l2_regression_status']}",
        f"- 4L3 regression status: {result['phase4l3_regression_status']}",
        f"- 4L4 regression status: {result['phase4l4_regression_status']}",
        f"- RouteSignal contamination count: {result['routesignal_contamination_count']}",
        "- Selector control remains blocked.",
        "- Response replacement remains blocked.",
        "- No provider/model/TTS/CRM/email/calendar/payment/account side-effect path was enabled.",
        "- No raw private transcript/audio was added to public evidence.",
        "- No live readiness claim was made.",
        "",
        "## Official Sources Inspected",
        "",
    ]
    for source in result["official_sources_inspected"]:
        lines.append(f"- {source['url']} ({source['source_type']}): {source['use']}")
    lines.extend(["", "## Claim Precision Categories", ""])
    for category in result["claim_precision_categories"]:
        lines.append(f"- {category}")
    lines.extend(["", "## Ambiguous / Conflict-Risk Claims Found", ""])
    for item in result["ambiguous_conflict_risk_claims_found"]:
        lines.append(f"- {item['claim_id']}: {item['risk']} -> {item['new_category']}; {item['reason']}")
    lines.extend(["", "## Claims Changed Or Downgraded", ""])
    for fact_id in result["claims_changed_or_downgraded"]:
        lines.append(f"- {fact_id}")
    lines.extend(["", "## Response Changes Made", ""])
    for item in result["response_changes_made"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Claim-Conflict Case Matrix", ""])
    for item in result["claim_conflict_case_results"]:
        summary = item["actual_semantic_action_response_summary"]
        lines.extend(
            [
                f"### {item['case_id']}",
                "",
                f"- Buyer utterance: {item['buyer_utterance']}",
                f"- Expected behavior: {item['expected_behavior']}",
                f"- Actual semantic/action/response summary: semantic={summary['semantic']}; action={summary['action_id']}; focus={summary['dialogue_focus']}; summary={summary['response_summary']}",
                f"- Pass: {str(item['pass']).lower()}",
                f"- Failures: {json.dumps(item['failures'])}",
                f"- Actual response: {item['actual_response']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Regression Status",
            "",
            f"- 4L2 single-turn regression count: {result['phase4l2_single_turn_regression_count']}",
            f"- 4L3 single-turn 4L2 regression count: {result['phase4l3_single_turn_4l2_regression_count']}",
            f"- 4L3 multi-turn fail count: {result['phase4l3_multi_turn_fail_count']}",
            f"- 4L4 Go-specific fail count: {result['phase4l4_go_specific_fail_count']}",
            "",
            "## No-side-effect Confirmation",
            "",
            "- Selector control blocked: true",
            "- Live selector control recommended: false",
            "- Response replacement blocked: true",
            "- Side-effect provider paths enabled: false",
            "- Live readiness claimed: false",
        ]
    )
    return "\n".join(lines) + "\n"


def validate_artifacts(failures: list[str], expected: dict[str, Any]) -> None:
    if not RESULT_PATH.is_file():
        failures.append("result.json missing")
        return
    if not REPORT_PATH.is_file():
        failures.append("report.md missing")
    actual = read_json(RESULT_PATH)
    keys = [
        "checkpoint_id",
        "status",
        "official_sources_inspected",
        "claim_precision_categories",
        "claim_precision_metadata_status",
        "ambiguous_conflict_risk_claims_found",
        "claims_changed_or_downgraded",
        "response_changes_made",
        "claim_conflict_case_results",
        "claim_conflict_pass_fail_count",
        "unsupported_exact_response_hits",
        "phase4l2_regression_status",
        "phase4l3_regression_status",
        "phase4l4_regression_status",
        "routesignal_contamination_count",
        "selector_response_replacement_status",
    ]
    for key in keys:
        if actual.get(key) != expected.get(key):
            failures.append(f"{key} mismatch")
    if actual.get("status") != "pass":
        failures.append(f"result status must be pass, got {actual.get('status')!r}")
    for key in FALSE_FLAGS:
        if actual.get(key) is not False:
            failures.append(f"{key} must be false: {actual.get(key)!r}")
    no_side_effect = actual.get("no_side_effect_confirmation")
    if not isinstance(no_side_effect, dict):
        failures.append("no_side_effect_confirmation missing")
    else:
        for key, expected_value in {
            "selector_control_allowed": False,
            "live_selector_control_recommended": False,
            "response_replacement_performed": False,
            "provider_model_tts_crm_email_calendar_payment_account_side_effect_path_enabled": False,
            "raw_private_transcript_or_audio_added_to_public_evidence": False,
            "live_readiness_claimed": False,
        }.items():
            if no_side_effect.get(key) is not expected_value:
                failures.append(f"no_side_effect_confirmation.{key} must be {expected_value!r}")
    if actual.get("no_live_readiness_confirmation") is not True:
        failures.append("no_live_readiness_confirmation must be true")


def validate_report(failures: list[str]) -> None:
    if not REPORT_PATH.is_file():
        return
    text = REPORT_PATH.read_text(encoding="utf-8")
    required = [
        "Official Sources Inspected",
        "Claim Precision Categories",
        "Ambiguous / Conflict-Risk Claims Found",
        "Claims Changed Or Downgraded",
        "Response Changes Made",
        "Claim-Conflict Case Matrix",
        "Regression Status",
        "RouteSignal contamination count",
        "Selector control remains blocked.",
        "Response replacement remains blocked.",
        "No provider/model/TTS/CRM/email/calendar/payment/account side-effect path was enabled.",
        "No live readiness claim was made.",
    ]
    for phrase in required:
        if phrase not in text:
            failures.append(f"report missing phrase: {phrase}")
    for case in CLAIM_CONFLICT_CASES:
        if case["case_id"] not in text:
            failures.append(f"report missing claim-conflict case id: {case['case_id']}")


def validate_environment_and_imports(failures: list[str]) -> None:
    forbidden = sorted(imported_roots(Path(__file__)) & FORBIDDEN_IMPORT_ROOTS)
    if forbidden:
        failures.append(f"validator imports forbidden provider/network roots: {forbidden}")
    enabled_gates = [name for name in SHADOW_ENV_GATES if os.environ.get(name) == "1"]
    if enabled_gates:
        failures.append(f"shadow selector write/control env gates must not be enabled: {enabled_gates}")


def write_artifacts() -> None:
    result = build_result()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(build_report(result), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--write-artifacts"]:
        write_artifacts()
        print(json.dumps({"status": "wrote", "checkpoint_id": CHECKPOINT_ID}, indent=2, sort_keys=True))
        return 0
    if argv:
        print(json.dumps({"status": "fail", "failures": [f"unknown arguments: {argv}"]}, indent=2))
        return 2

    failures: list[str] = []
    expected = build_result()
    if expected["status"] != "pass":
        failures.append("current OpenAI 4L5 claim precision harness has failing cases")
    validate_artifacts(failures, expected)
    validate_report(failures)
    validate_environment_and_imports(failures)
    if failures:
        print(json.dumps({"status": "fail", "failures": failures}, indent=2, sort_keys=True))
        raise AssertionError(f"{CHECKPOINT_ID} failed with {len(failures)} issue(s).")
    print(json.dumps({"status": "pass", "checkpoint_id": CHECKPOINT_ID}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
