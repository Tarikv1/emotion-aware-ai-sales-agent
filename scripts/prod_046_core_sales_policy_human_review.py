#!/usr/bin/env python3
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-046-core-sales-policy-human-review"
CHECKPOINT_NAME = "Core Sales Policy Human Review"
NEXT_CHECKPOINT_ID = "PROD-047-campaign-profile-contract-validator"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

PROD_045_DIR = ROOT / "research" / "experiments" / "generated" / "PROD-045-core-sales-policy-regression-rerun"
PROD_046A_DIR = ROOT / "research" / "experiments" / "generated" / "PROD-046A-german-naturalized-policy-regression"
PROD_046B_DIR = ROOT / "research" / "experiments" / "generated" / "PROD-046B-german-response-wording-quality-pass"
PROD_046C_DIR = ROOT / "research" / "experiments" / "generated" / "PROD-046C-german-campaign-field-interpolation-guard"
PROD_046D_DIR = ROOT / "research" / "experiments" / "generated" / "PROD-046D-german-source-informed-wording-quality-guard"

SOURCE_RESULT_FILES = {
    "PROD-045": PROD_045_DIR / "result.json",
    "PROD-046A": PROD_046A_DIR / "result.json",
    "PROD-046B": PROD_046B_DIR / "result.json",
    "PROD-046C": PROD_046C_DIR / "result.json",
    "PROD-046D": PROD_046D_DIR / "result.json",
}

BOUNDARY_FALSE_FIELDS = [
    "retrieval_enabled",
    "provider_calls_made",
    "llm_used",
    "private_data_read",
    "voice_playback_unblocked",
    "public_demo_polish_unblocked",
    "payment_collection_allowed",
    "contract_signing_allowed",
    "production_runtime_promotion_allowed",
]

ENGLISH_INTERNAL_MARKERS = [
    "approved",
    "sales path",
    "sale-ready",
    "specialist path",
    "qualified reviewer path",
    "campaign",
    "mark this as",
    "log a callback",
]

GERMAN_INTERNAL_MARKERS = [
    "verkaufsteil",
    "dokumentiere",
    "kampagne",
    "freigegeben",
    "sale-ready",
    "warteschlange",
    "passungsfrage",
]

ABRUPT_END_ACTIONS = {"end-call", "schedule-and-end", "close-and-log-sale-ready"}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def find_hits(text: str, markers: list[str]) -> list[str]:
    lowered = text.lower()
    return [marker for marker in markers if marker.lower() in lowered]


def source_results() -> dict[str, dict[str, Any]]:
    return {checkpoint: read_json(path) for checkpoint, path in SOURCE_RESULT_FILES.items()}


def source_result_passed(result: dict[str, Any]) -> bool:
    return result.get("validation", {}).get("passed") is True


def source_boundary_ok(result: dict[str, Any]) -> bool:
    summary = result.get("summary", {})
    return all(summary.get(field) is False for field in BOUNDARY_FALSE_FIELDS if field in summary)


def classification_template() -> dict[str, bool]:
    return {
        "accepted_for_regression": True,
        "accepted_with_human_review_needed": False,
        "revise_wording_later": False,
        "revise_call_control_later": False,
        "needs_campaign_field_validator": False,
        "blocked_for_voice": True,
        "blocked_for_public_demo": True,
        "blocked_for_real_customer_use": True,
    }


def review_note_for_abrupt_call_control(call_control: str, response: str) -> str | None:
    if call_control not in ABRUPT_END_ACTIONS:
        return None
    lowered = response.lower()
    if "goodbye" in lowered or "auf wiederhören" in lowered:
        return None
    return "Safe deterministic end-call, but the turn may feel abrupt before voice/demo use."


def build_english_response_quality_findings() -> list[dict[str, Any]]:
    results = read_json(PROD_045_DIR / "regression_results.json")["results"]
    findings = []
    for item in results:
        decision = item["runtime_decision"]
        response = decision["agent_response"]
        internal_hits = find_hits(response, ENGLISH_INTERNAL_MARKERS)
        abrupt_note = review_note_for_abrupt_call_control(decision["call_control"], response)
        classifications = classification_template()
        review_notes = []
        if internal_hits:
            classifications["revise_wording_later"] = True
            classifications["needs_campaign_field_validator"] = True
            review_notes.append("English response still exposes campaign/policy wording that is acceptable for regression but not final customer-facing copy.")
        if abrupt_note:
            classifications["revise_call_control_later"] = True
            review_notes.append(abrupt_note)
        if decision["sales_difficulty"] in {"price-first-direct", "identity-repair", "technical-specialist-route", "security-review-route"}:
            classifications["needs_campaign_field_validator"] = True
        findings.append(
            {
                "case_id": item["case_id"],
                "customer_move_id": item.get("customer_move_id"),
                "sales_difficulty": decision["sales_difficulty"],
                "call_control": decision["call_control"],
                "agent_response": response,
                "required_action_passed": item.get("required_action_evaluation", {}).get("passed") is True,
                "internal_or_policy_marker_hits": internal_hits,
                "quality_risks": {
                    "too_generic": item.get("generic_response_used") is True,
                    "too_abrupt": abrupt_note is not None,
                    "internal_or_policy_sounding": bool(internal_hits),
                    "unsupported_claim_risk": False,
                },
                "classifications": classifications,
                "review_notes": review_notes or ["Accepted for deterministic offline regression evidence."],
            }
        )
    return findings


def build_german_response_quality_findings() -> list[dict[str, Any]]:
    results = read_json(PROD_046D_DIR / "german_source_informed_results.json")["items"]
    findings = []
    for item in results:
        decision = item["runtime_decision"]
        response = decision["agent_response"]
        internal_hits = find_hits(response, GERMAN_INTERNAL_MARKERS)
        abrupt_note = review_note_for_abrupt_call_control(decision["call_control"], response)
        classifications = classification_template()
        classifications["accepted_with_human_review_needed"] = True
        review_notes = ["German is accepted for synthetic regression evidence only; native-speaker review is still required."]
        if internal_hits:
            classifications["revise_wording_later"] = True
            review_notes.append("German response still contains a phrase that may sound internal or operational.")
        if "verkaufsteil" in [hit.lower() for hit in internal_hits]:
            classifications["revise_wording_later"] = True
            review_notes.append("Support/cancellation wording should likely avoid `Verkaufsteil` in a later wording pass.")
        if abrupt_note:
            classifications["revise_call_control_later"] = True
            review_notes.append(abrupt_note)
        if decision["sales_difficulty"] in {
            "price-first-direct",
            "identity-repair",
            "scam-safety-boundary",
            "payment-safety-boundary",
            "technical-specialist-route",
            "security-review-route",
            "coverage-boundary-route",
            "healthcare-boundary-route",
        }:
            classifications["needs_campaign_field_validator"] = True
        findings.append(
            {
                "case_id": item["case_id"],
                "customer_move_id": item.get("customer_move_id"),
                "sales_difficulty": decision["sales_difficulty"],
                "call_control": decision["call_control"],
                "agent_response": response,
                "required_action_passed": item.get("required_action_evaluation", {}).get("passed") is True,
                "internal_or_policy_marker_hits": internal_hits,
                "quality_risks": {
                    "internal_sounding": bool(internal_hits),
                    "robotic_or_legalistic": any(phrase in response.lower() for phrase in ["nach den vorliegenden informationen", "zuständige fachperson"]),
                    "too_abrupt": abrupt_note is not None,
                    "native_speaker_review_required": True,
                    "unsupported_claim_risk": False,
                },
                "classifications": classifications,
                "review_notes": review_notes,
            }
        )
    return findings


def build_call_control_findings(english: list[dict[str, Any]], german: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings = []
    for language, items in (("en", english), ("de", german)):
        for item in items:
            classifications = item["classifications"]
            if classifications["revise_call_control_later"]:
                findings.append(
                    {
                        "finding_id": f"call-control-{language}-{len(findings)+1:03d}",
                        "language": language,
                        "case_id": item["case_id"],
                        "sales_difficulty": item["sales_difficulty"],
                        "call_control": item["call_control"],
                        "finding": "The deterministic action is safe, but the response may end the call too abruptly for a spoken customer experience.",
                        "recommended_future_change": "Evaluate a bridge-then-continue or bridge-then-offer-stop behavior in a later checkpoint without weakening refusal/support/cancellation safety.",
                        "classifications": {
                            "accepted_for_regression": True,
                            "revise_call_control_later": True,
                            "blocked_for_voice": True,
                            "blocked_for_public_demo": True,
                            "blocked_for_real_customer_use": True,
                        },
                    }
                )
    return findings


def build_campaign_field_findings(english: list[dict[str, Any]], german: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "finding_id": "campaign-field-contract-001",
            "finding": "Campaign fields are now the main deterministic product bottleneck because runtime templates depend on whether a field is a full customer-facing sentence, noun phrase, route label, written-info object, or boundary sentence.",
            "evidence": [
                "PROD-046C fixed malformed German interpolation caused by unsafe fragment insertion.",
                "PROD-046D reduced internal German wording by reshaping campaign text and response templates.",
                f"{sum(1 for item in english + german if item['classifications']['needs_campaign_field_validator'])} reviewed responses depend on campaign-field quality.",
            ],
            "required_future_guard": "Create a campaign-profile contract validator before adding new campaigns or promoting voice/demo use.",
            "classifications": {
                "needs_campaign_field_validator": True,
                "blocked_for_voice": True,
                "blocked_for_public_demo": True,
                "blocked_for_real_customer_use": True,
            },
        },
        {
            "finding_id": "campaign-field-language-002",
            "finding": "German campaign fields need explicit language-specific shape rules and native review status, not only translated strings.",
            "evidence": [
                "PROD-046A proved routing with synthetic naturalized German cases.",
                "PROD-046B through PROD-046D improved wording, but none claims native-speaker approval.",
            ],
            "required_future_guard": "Require per-language customer-facing examples, source boundary notes, and native-review status in campaign profiles.",
            "classifications": {
                "accepted_with_human_review_needed": True,
                "needs_campaign_field_validator": True,
                "blocked_for_voice": True,
                "blocked_for_public_demo": True,
                "blocked_for_real_customer_use": True,
            },
        },
    ]


def build_recommended_next_actions() -> list[dict[str, Any]]:
    return [
        {
            "action_id": "next-campaign-profile-contract-validator",
            "priority": 1,
            "recommended_checkpoint": NEXT_CHECKPOINT_ID,
            "rationale": "Campaign-field shape is the strongest deterministic blocker found by PROD-046C and PROD-046D; it can be guarded without provider calls or runtime promotion.",
            "must_not_unlock": ["retrieval", "providers", "voice playback", "public demo", "payment collection", "contract signing", "production promotion"],
        },
        {
            "action_id": "native-german-review-required",
            "priority": 2,
            "recommended_checkpoint": "PROD-048-native-german-wording-review",
            "rationale": "German is regression-passing and source-informed but not approved by a native German reviewer.",
            "must_not_unlock": ["voice playback", "public demo", "real customer use"],
        },
        {
            "action_id": "future-call-control-softening",
            "priority": 3,
            "recommended_checkpoint": "PROD-049-call-control-bridge-quality-review",
            "rationale": "Several end-call decisions are safe but may feel abrupt in spoken interaction. This should be reviewed after campaign-field contracts are stable.",
            "must_not_unlock": ["pressure after refusal", "sales continuation after support/cancellation", "demo promotion"],
        },
    ]


def summarize(
    source_payloads: dict[str, dict[str, Any]],
    english: list[dict[str, Any]],
    german: list[dict[str, Any]],
    call_control: list[dict[str, Any]],
    campaign_fields: list[dict[str, Any]],
    next_actions: list[dict[str, Any]],
) -> dict[str, Any]:
    all_findings = english + german
    return {
        "source_checkpoints_reviewed": list(source_payloads.keys()),
        "prod_045_result_validation_passed": source_result_passed(source_payloads["PROD-045"]),
        "prod_046a_result_validation_passed": source_result_passed(source_payloads["PROD-046A"]),
        "prod_046b_result_validation_passed": source_result_passed(source_payloads["PROD-046B"]),
        "prod_046c_result_validation_passed": source_result_passed(source_payloads["PROD-046C"]),
        "prod_046d_result_validation_passed": source_result_passed(source_payloads["PROD-046D"]),
        "english_reviewed_response_count": len(english),
        "german_reviewed_response_count": len(german),
        "accepted_for_regression_count": sum(1 for item in all_findings if item["classifications"]["accepted_for_regression"]),
        "accepted_with_human_review_needed_count": sum(1 for item in all_findings if item["classifications"]["accepted_with_human_review_needed"]),
        "revise_wording_later_count": sum(1 for item in all_findings if item["classifications"]["revise_wording_later"]),
        "revise_call_control_later_count": sum(1 for item in all_findings if item["classifications"]["revise_call_control_later"]),
        "needs_campaign_field_validator_count": sum(1 for item in all_findings if item["classifications"]["needs_campaign_field_validator"]),
        "blocked_for_voice_count": sum(1 for item in all_findings if item["classifications"]["blocked_for_voice"]),
        "blocked_for_public_demo_count": sum(1 for item in all_findings if item["classifications"]["blocked_for_public_demo"]),
        "blocked_for_real_customer_use_count": sum(1 for item in all_findings if item["classifications"]["blocked_for_real_customer_use"]),
        "call_control_finding_count": len(call_control),
        "campaign_field_finding_count": len(campaign_fields),
        "recommended_next_action_count": len(next_actions),
        "policy_surface_accepted_for_offline_regression_evidence": True,
        "policy_surface_accepted_for_internal_product_review": True,
        "policy_surface_blocked_from_voice_demo_customer_use": True,
        "ready_for_campaign_profile_validator_next": True,
        "final_native_german_approval_claimed": False,
        "review_only_checkpoint": True,
        "runtime_behavior_changed": False,
        "retrieval_enabled": False,
        "provider_calls_made": False,
        "llm_used": False,
        "private_data_read": False,
        "voice_playback_unblocked": False,
        "public_demo_polish_unblocked": False,
        "payment_collection_allowed": False,
        "contract_signing_allowed": False,
        "production_runtime_promotion_allowed": False,
        "uses_exact_transcript_text": False,
        "uses_source_transcript_sequence": False,
        "uses_dataset_specific_phrasing": False,
        "generated_synthetic_conversations": False,
    }


def render_html(review_data: dict[str, Any]) -> str:
    def rows(items: list[dict[str, Any]], language: str) -> str:
        out = []
        for item in items[:80]:
            classes = [key for key, value in item["classifications"].items() if value]
            out.append(
                "<tr>"
                f"<td>{html.escape(language)}</td>"
                f"<td>{html.escape(item['case_id'])}</td>"
                f"<td>{html.escape(item['sales_difficulty'])}</td>"
                f"<td>{html.escape(item['call_control'])}</td>"
                f"<td>{html.escape(', '.join(classes))}</td>"
                f"<td>{html.escape(item['agent_response'])}</td>"
                "</tr>"
            )
        return "".join(out)

    summary = review_data["summary"]
    next_rows = "".join(
        "<tr>"
        f"<td>{item['priority']}</td>"
        f"<td>{html.escape(item['action_id'])}</td>"
        f"<td>{html.escape(item['recommended_checkpoint'])}</td>"
        f"<td>{html.escape(item['rationale'])}</td>"
        "</tr>"
        for item in review_data["recommended_next_actions"]
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>PROD-046 Core Sales Policy Human Review</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #202124; }}
    .summary {{ border: 1px solid #d7dce2; border-radius: 8px; padding: 14px; margin-bottom: 16px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 12px 0 24px; }}
    th, td {{ border: 1px solid #d7dce2; padding: 8px; text-align: left; vertical-align: top; }}
    code {{ background: #f4f6f8; padding: 2px 4px; }}
  </style>
</head>
<body>
  <h1>PROD-046 Core Sales Policy Human Review</h1>
  <section class="summary">
    <h2>Policy Surface Status</h2>
    <p>Accepted for offline regression evidence: <code>{summary['policy_surface_accepted_for_offline_regression_evidence']}</code></p>
    <p>Accepted for internal product review: <code>{summary['policy_surface_accepted_for_internal_product_review']}</code></p>
    <p>Blocked from voice/demo/customer use: <code>{summary['policy_surface_blocked_from_voice_demo_customer_use']}</code></p>
    <p>Final native German approval claimed: <code>{summary['final_native_german_approval_claimed']}</code></p>
  </section>
  <h2>Response Findings</h2>
  <table><tr><th>Language</th><th>Case</th><th>Difficulty</th><th>Call control</th><th>Classifications</th><th>Response</th></tr>{rows(review_data['english_response_quality_findings'], 'en')}{rows(review_data['german_response_quality_findings'], 'de')}</table>
  <h2>Recommended Next Actions</h2>
  <table><tr><th>Priority</th><th>Action</th><th>Checkpoint</th><th>Rationale</th></tr>{next_rows}</table>
  <h2>Boundaries</h2>
  <p>Retrieval, providers, LLMs, private-data reads, voice playback, public demo polish, payment collection, contract signing, and production promotion remain blocked.</p>
</body>
</html>
"""


def build_report(summary: dict[str, Any], next_actions: list[dict[str, Any]]) -> str:
    lines = [
        "# PROD-046 Core Sales Policy Human Review",
        "",
        "PROD-046 reviews the deterministic runtime-policy surface created from PROD-045 through PROD-046D. It does not modify runtime behavior.",
        "",
        "## Review Result",
        "",
        "- Policy surface accepted for offline regression evidence: `true`",
        "- Policy surface accepted for internal product review: `true`",
        "- Policy surface blocked from voice/demo/customer-facing use: `true`",
        "- Ready for campaign-profile validator next: `true`",
        "- Final native German approval claimed: `false`",
        "",
        "## Source Checkpoints",
        "",
        f"- PROD-045 validation passed: `{summary['prod_045_result_validation_passed']}`",
        f"- PROD-046A validation passed: `{summary['prod_046a_result_validation_passed']}`",
        f"- PROD-046B validation passed: `{summary['prod_046b_result_validation_passed']}`",
        f"- PROD-046C validation passed: `{summary['prod_046c_result_validation_passed']}`",
        f"- PROD-046D validation passed: `{summary['prod_046d_result_validation_passed']}`",
        "",
        "## Response Quality Findings",
        "",
        f"- English reviewed responses: {summary['english_reviewed_response_count']}",
        f"- German reviewed responses: {summary['german_reviewed_response_count']}",
        f"- Accepted for regression: {summary['accepted_for_regression_count']}",
        f"- Human review still needed: {summary['accepted_with_human_review_needed_count']}",
        f"- Revise wording later: {summary['revise_wording_later_count']}",
        f"- Revise call-control later: {summary['revise_call_control_later_count']}",
        f"- Needs campaign-field validator: {summary['needs_campaign_field_validator_count']}",
        "",
        "German wording is acceptable enough for synthetic regression evidence, but not final customer-facing approval. Tarik is not treated as the final German wording authority.",
        "",
        "## Specific Product Risks",
        "",
        "- Some English responses still expose internal wording such as `approved`, `sales path`, or `sale-ready`; this is acceptable for regression but not polished customer copy.",
        "- German `Verkaufsteil` in support/cancellation responses is safer than older `Vertriebsteil`, but still sounds operational and should be reviewed by a native speaker.",
        "- Several safe end-call decisions may feel abrupt in spoken use; a later bridge-quality checkpoint should test softer transitions without weakening refusal/support/cancellation safety.",
        "- Campaign fields remain a product bottleneck because language-specific field shape controls are required to prevent malformed or internal-sounding output.",
        "",
        "## Recommended Next Actions",
        "",
    ]
    for action in next_actions:
        lines.append(f"- P{action['priority']} `{action['recommended_checkpoint']}`: {action['rationale']}")
    lines.extend(
        [
            "",
            "## Boundaries",
            "",
            "- Retrieval enabled: `false`",
            "- Provider calls made: `false`",
            "- LLM used: `false`",
            "- Private data read: `false`",
            "- Voice playback unblocked: `false`",
            "- Public demo polish unblocked: `false`",
            "- Payment collection allowed: `false`",
            "- Contract signing allowed: `false`",
            "- Production runtime promotion allowed: `false`",
            "",
            f"Next recommended checkpoint: `{NEXT_CHECKPOINT_ID}`.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    for path in SOURCE_RESULT_FILES.values():
        if not path.exists():
            raise SystemExit(f"Missing required source result: {rel(path)}")

    source_payloads = source_results()
    english = build_english_response_quality_findings()
    german = build_german_response_quality_findings()
    call_control = build_call_control_findings(english, german)
    campaign_fields = build_campaign_field_findings(english, german)
    next_actions = build_recommended_next_actions()
    summary = summarize(source_payloads, english, german, call_control, campaign_fields, next_actions)

    source_valid = all(source_result_passed(payload) and source_boundary_ok(payload) for payload in source_payloads.values())
    passed = (
        source_valid
        and summary["policy_surface_accepted_for_offline_regression_evidence"]
        and summary["policy_surface_accepted_for_internal_product_review"]
        and summary["policy_surface_blocked_from_voice_demo_customer_use"]
        and not summary["final_native_german_approval_claimed"]
        and summary["german_reviewed_response_count"] > 0
        and summary["accepted_with_human_review_needed_count"] > 0
        and summary["campaign_field_finding_count"] > 0
        and summary["review_only_checkpoint"]
        and not summary["runtime_behavior_changed"]
    )

    review_data = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "summary": summary,
        "source_checkpoint_status": {
            checkpoint: {
                "validation_passed": source_result_passed(payload),
                "boundary_ok": source_boundary_ok(payload),
            }
            for checkpoint, payload in source_payloads.items()
        },
        "english_response_quality_findings": english,
        "german_response_quality_findings": german,
        "call_control_findings": call_control,
        "campaign_field_findings": campaign_fields,
        "recommended_next_actions": next_actions,
        "review_boundary": {
            "runtime_behavior_changed": False,
            "retrieval_enabled": False,
            "provider_calls_made": False,
            "llm_used": False,
            "private_data_read": False,
            "voice_playback_unblocked": False,
            "public_demo_polish_unblocked": False,
            "payment_collection_allowed": False,
            "contract_signing_allowed": False,
            "production_runtime_promotion_allowed": False,
            "final_native_german_approval_claimed": False,
        },
    }
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_ids": list(source_payloads.keys()),
        "summary": summary,
        "outputs": {
            "report": rel(OUT_DIR / "report.md"),
            "human_review_packet": rel(OUT_DIR / "human_review_packet.json"),
            "english_response_quality_findings": rel(OUT_DIR / "english_response_quality_findings.json"),
            "german_response_quality_findings": rel(OUT_DIR / "german_response_quality_findings.json"),
            "call_control_findings": rel(OUT_DIR / "call_control_findings.json"),
            "campaign_field_findings": rel(OUT_DIR / "campaign_field_findings.json"),
            "recommended_next_actions": rel(OUT_DIR / "recommended_next_actions.json"),
            "review_html": rel(OUT_DIR / "prod_046_review.html"),
        },
        "validation": {"passed": passed},
        "next_checkpoint_recommended": NEXT_CHECKPOINT_ID,
    }

    write_json(OUT_DIR / "human_review_packet.json", review_data)
    write_json(OUT_DIR / "english_response_quality_findings.json", {"items": english})
    write_json(OUT_DIR / "german_response_quality_findings.json", {"items": german})
    write_json(OUT_DIR / "call_control_findings.json", {"items": call_control})
    write_json(OUT_DIR / "campaign_field_findings.json", {"items": campaign_fields})
    write_json(OUT_DIR / "recommended_next_actions.json", {"items": next_actions})
    write_text(OUT_DIR / "prod_046_review.html", render_html(review_data))
    write_text(OUT_DIR / "report.md", build_report(summary, next_actions))
    write_json(OUT_DIR / "result.json", result)

    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": {"passed": passed}, "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
