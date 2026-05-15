#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CHECKPOINT_ID = "PROD-047-campaign-profile-contract-validator"
CHECKPOINT_NAME = "Campaign Profile Contract Validator"
NEXT_CHECKPOINT_ID = "PROD-048-native-german-wording-review"

ALLOWED_LANGUAGES = ["en", "de"]
ALLOWED_FIELD_SHAPES = [
    "full_sentence",
    "noun_phrase",
    "route_label",
    "written_info_object",
    "boundary_sentence",
    "pricing_sentence",
    "identity_reason_sentence",
    "verification_sentence",
    "next_step_label",
]
ALLOWED_SOURCE_BOUNDARIES = [
    "synthetic_test_fixture",
    "company_approved",
    "public_source_informed",
    "human_reviewed",
    "legal_review_required",
    "blocked",
]
ALLOWED_REVIEW_STATUSES = [
    "machine_validated",
    "source_informed",
    "native_speaker_review_required",
    "native_speaker_reviewed",
    "legal_review_required",
    "approved_for_internal_demo",
    "approved_for_voice",
    "approved_for_customer_use",
]

BOUNDARY_FALSE_FIELDS = [
    "runtime_behavior_changed",
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

REQUIRED_SAFETY_DEFAULTS = {
    "payment_collection_allowed": False,
    "contract_signing_allowed": False,
    "decision_maker_bypass_forbidden": True,
    "production_runtime_promotion_allowed": False,
    "voice_playback_unblocked": False,
    "public_demo_polish_unblocked": False,
    "retrieval_enabled": False,
    "provider_calls_made": False,
    "llm_used": False,
    "private_data_read": False,
}

FIELD_CONTRACTS = {
    "pricing_summary": "pricing_sentence",
    "pricing_boundary_text": "boundary_sentence",
    "caller_identity": "noun_phrase",
    "approved_identity_reason_sentence": "identity_reason_sentence",
    "approved_written_summary": "written_info_object",
    "approved_email_followup_scope": "written_info_object",
    "no_payment_boundary": "boundary_sentence",
    "approved_verification_response": "verification_sentence",
    "support_route": "route_label",
    "cancellation_route": "route_label",
    "approved_technical_scope": "full_sentence",
    "security_review_boundary": "boundary_sentence",
    "regulated_advice_boundary_text": "boundary_sentence",
    "approved_gap_isolation_question": "full_sentence",
    "approved_review_summary": "written_info_object",
    "approved_sale_ready_next_step": "next_step_label",
    "callback_boundary": "boundary_sentence",
    "do_not_call_boundary": "boundary_sentence",
}

REQUIRED_POLICY_GROUPS = {
    "price_first": ["pricing_summary", "pricing_boundary_text"],
    "identity_repair": ["caller_identity", "approved_identity_reason_sentence"],
    "written_info_and_email_boundary": ["approved_written_summary", "approved_email_followup_scope"],
    "scam_and_payment_safety": ["no_payment_boundary", "approved_verification_response"],
    "support_and_cancellation_routing": ["support_route", "cancellation_route"],
    "technical_security_handoff": ["approved_technical_scope", "security_review_boundary"],
    "coverage_healthcare_boundary": ["regulated_advice_boundary_text"],
    "existing_provider_gap": ["approved_gap_isolation_question"],
    "decision_maker_review": ["approved_review_summary"],
    "sale_ready_guarded_next_step": ["approved_sale_ready_next_step"],
    "callback_request": ["callback_boundary"],
    "do_not_call": ["do_not_call_boundary"],
}

GERMAN_BLOCKED_CUSTOMER_TERMS = [
    "freigegeben",
    "verkaufsteil",
    "vertriebsteil",
    "support-warteschlange",
    "kündigungs-warteschlange",
    "spezialistenweg",
    "passungsfrage",
    "sale-ready",
    "bei beim",
    "um ein kurzer",
    "fuer",
    "rueckruf",
    "pruef",
    "naechst",
]

ENGLISH_BLOCKED_CUSTOMER_TERMS = [
    "approved",
    "sales path",
    "sale-ready",
    "specialist path",
    "qualified reviewer path",
    "log a callback",
    "campaign",
    "support queue",
]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def make_field(
    value: str,
    shape: str,
    source_boundary: str,
    review_statuses: list[str],
    customer_facing: bool = True,
    template_requires_shape: str | None = None,
    source_note: str = "Synthetic fixture text for deterministic campaign-profile contract validation.",
) -> dict[str, Any]:
    field = {
        "value": value,
        "shape": shape,
        "source_boundary": source_boundary,
        "review_statuses": review_statuses,
        "customer_facing": customer_facing,
        "source_note": source_note,
    }
    if template_requires_shape:
        field["template_requires_shape"] = template_requires_shape
    return field


def base_profile(language: str) -> dict[str, Any]:
    source = "public_source_informed" if language == "de" else "synthetic_test_fixture"
    review_statuses = ["machine_validated", "source_informed", "native_speaker_review_required"] if language == "de" else ["machine_validated"]
    if language == "de":
        fields = {
            "pricing_summary": make_field("Das Starter-Paket liegt bei 29 Euro pro Nutzer und Monat.", "pricing_sentence", source, review_statuses),
            "pricing_boundary_text": make_field("Die genauen Bedingungen werden schriftlich geprüft.", "boundary_sentence", source, review_statuses),
            "caller_identity": make_field("Maya von RouteSignal", "noun_phrase", source, review_statuses),
            "approved_identity_reason_sentence": make_field("Ich rufe an, weil wir kurz klären möchten, wer bei Ihnen für Rückrufe und Nachverfolgung zuständig ist.", "identity_reason_sentence", source, review_statuses),
            "approved_written_summary": make_field("eine kurze Zusammenfassung per E-Mail", "written_info_object", source, review_statuses),
            "approved_email_followup_scope": make_field("die Informationen per E-Mail", "written_info_object", source, review_statuses),
            "no_payment_boundary": make_field("In diesem Gespräch frage ich nicht nach Zahlungsdaten, Kartendaten oder Passwörtern.", "boundary_sentence", source, review_statuses),
            "approved_verification_response": make_field("Sie können die Informationen über die offizielle Seite prüfen.", "verification_sentence", source, review_statuses),
            "support_route": make_field("den zuständigen Support", "route_label", source, review_statuses),
            "cancellation_route": make_field("die zuständige Stelle für Kündigungen", "route_label", source, review_statuses),
            "approved_technical_scope": make_field("Das System kann Zuständigkeiten für Rückrufe und Nachverfolgung abbilden.", "full_sentence", source, review_statuses),
            "security_review_boundary": make_field("Technische oder Sicherheitsdetails sollte eine zuständige Fachperson prüfen.", "boundary_sentence", source, review_statuses),
            "regulated_advice_boundary_text": make_field("Ich gebe in diesem Gespräch keine medizinische Beratung und keine Beratung zum Versicherungsschutz.", "boundary_sentence", source, review_statuses),
            "approved_gap_isolation_question": make_field("Sinnvoll wäre nur zu prüfen, ob trotz Ihrer aktuellen Lösung noch Rückrufe oder Nachverfolgungen liegen bleiben.", "full_sentence", source, review_statuses),
            "approved_review_summary": make_field("eine kurze Zusammenfassung zur Prüfung", "written_info_object", source, review_statuses),
            "approved_sale_ready_next_step": make_field("den nächsten Schritt", "next_step_label", source, review_statuses),
            "callback_boundary": make_field("Ich kann einen Rückruf vormerken; heute entsteht keine Verpflichtung.", "boundary_sentence", source, review_statuses),
            "do_not_call_boundary": make_field("Sie sollen hierzu nicht mehr angerufen werden.", "boundary_sentence", source, review_statuses),
        }
    else:
        fields = {
            "pricing_summary": make_field("The starter plan is 29 per user per month.", "pricing_sentence", source, review_statuses),
            "pricing_boundary_text": make_field("Exact terms are sent in writing.", "boundary_sentence", source, review_statuses),
            "caller_identity": make_field("Maya from RouteSignal", "noun_phrase", source, review_statuses),
            "approved_identity_reason_sentence": make_field("I am calling to check who handles callback ownership and follow-up routing.", "identity_reason_sentence", source, review_statuses),
            "approved_written_summary": make_field("a one-page summary", "written_info_object", source, review_statuses),
            "approved_email_followup_scope": make_field("the email summary", "written_info_object", source, review_statuses),
            "no_payment_boundary": make_field("This call does not collect payment, card, or sensitive details.", "boundary_sentence", source, review_statuses),
            "approved_verification_response": make_field("You can verify the information through the official page.", "verification_sentence", source, review_statuses),
            "support_route": make_field("the support team", "route_label", source, review_statuses),
            "cancellation_route": make_field("the cancellation team", "route_label", source, review_statuses),
            "approved_technical_scope": make_field("The system can track callback ownership and follow-up routing.", "full_sentence", source, review_statuses),
            "security_review_boundary": make_field("Technical or security details should be checked by the right specialist.", "boundary_sentence", source, review_statuses),
            "regulated_advice_boundary_text": make_field("This call does not provide medical, health, or coverage advice.", "boundary_sentence", source, review_statuses),
            "approved_gap_isolation_question": make_field("The only fit question is whether callbacks or follow-ups still fall through with the current setup.", "full_sentence", source, review_statuses),
            "approved_review_summary": make_field("a short review summary", "written_info_object", source, review_statuses),
            "approved_sale_ready_next_step": make_field("the next step", "next_step_label", source, review_statuses),
            "callback_boundary": make_field("I can note a callback request without creating a commitment today.", "boundary_sentence", source, review_statuses),
            "do_not_call_boundary": make_field("You should not be called about this again.", "boundary_sentence", source, review_statuses),
        }
    return {
        "campaign_id": f"campaign-prod-047-valid-{language}",
        "contract_version": "prod-047.v1",
        "language": language,
        "review_statuses": review_statuses,
        "safety_defaults": copy.deepcopy(REQUIRED_SAFETY_DEFAULTS),
        "regulated_context": {"coverage_or_healthcare_sensitive": True},
        "close_criteria": {
            "sale_ready_allowed": True,
            "criteria_satisfied": True,
            "criteria": ["customer explicitly asks for next step", "no payment collection", "no contract signing"],
        },
        "fields": fields,
    }


def example_profiles() -> dict[str, dict[str, Any]]:
    valid_en = base_profile("en")
    valid_en["campaign_id"] = "campaign-prod-047-valid-en-internal-review"
    valid_de = base_profile("de")
    valid_de["campaign_id"] = "campaign-prod-047-valid-de-source-informed"

    invalid_de_fragment = copy.deepcopy(valid_de)
    invalid_de_fragment["campaign_id"] = "campaign-prod-047-invalid-de-fragment-interpolation"
    invalid_de_fragment["fields"]["pricing_summary"]["value"] = "Preisrahmen bei beim Starter-Paket"
    invalid_de_fragment["fields"]["approved_identity_reason_sentence"] = make_field(
        "um ein kurzer Abgleich zur Zuständigkeit",
        "noun_phrase",
        "public_source_informed",
        invalid_de_fragment["review_statuses"],
        template_requires_shape="identity_reason_sentence",
    )

    invalid_en_internal = copy.deepcopy(valid_en)
    invalid_en_internal["campaign_id"] = "campaign-prod-047-invalid-en-internal-copy"
    invalid_en_internal["fields"]["approved_written_summary"]["value"] = "the approved campaign summary"
    invalid_en_internal["fields"]["support_route"]["value"] = "the support queue"
    invalid_en_internal["fields"]["approved_sale_ready_next_step"]["value"] = "sale-ready next step"

    invalid_payment = copy.deepcopy(valid_en)
    invalid_payment["campaign_id"] = "campaign-prod-047-invalid-payment-enabled"
    invalid_payment["safety_defaults"]["payment_collection_allowed"] = True

    invalid_regulated = copy.deepcopy(valid_en)
    invalid_regulated["campaign_id"] = "campaign-prod-047-invalid-missing-regulated-boundary"
    invalid_regulated["fields"].pop("regulated_advice_boundary_text", None)

    invalid_native = copy.deepcopy(valid_de)
    invalid_native["campaign_id"] = "campaign-prod-047-invalid-missing-native-review-status"
    invalid_native["review_statuses"] = ["machine_validated", "source_informed"]
    for field in invalid_native["fields"].values():
        field["review_statuses"] = ["machine_validated", "source_informed"]

    invalid_sale_ready = copy.deepcopy(valid_en)
    invalid_sale_ready["campaign_id"] = "campaign-prod-047-invalid-sale-ready-without-close-criteria"
    invalid_sale_ready["close_criteria"]["criteria_satisfied"] = False

    invalid_routes = copy.deepcopy(valid_de)
    invalid_routes["campaign_id"] = "campaign-prod-047-invalid-support-cancellation-route-label"
    invalid_routes["fields"]["support_route"]["value"] = "Support-Warteschlange"
    invalid_routes["fields"]["cancellation_route"]["value"] = "Kündigungs-Warteschlange"

    invalid_identity = copy.deepcopy(valid_en)
    invalid_identity["campaign_id"] = "campaign-prod-047-incomplete-identity-reason"
    invalid_identity["fields"].pop("approved_identity_reason_sentence", None)

    return {
        "campaign-prod-047-valid-en-internal-review": valid_en,
        "campaign-prod-047-valid-de-source-informed": valid_de,
        "campaign-prod-047-invalid-de-fragment-interpolation": invalid_de_fragment,
        "campaign-prod-047-invalid-en-internal-copy": invalid_en_internal,
        "campaign-prod-047-invalid-payment-enabled": invalid_payment,
        "campaign-prod-047-invalid-missing-regulated-boundary": invalid_regulated,
        "campaign-prod-047-invalid-missing-native-review-status": invalid_native,
        "campaign-prod-047-invalid-sale-ready-without-close-criteria": invalid_sale_ready,
        "campaign-prod-047-invalid-support-cancellation-route-label": invalid_routes,
        "campaign-prod-047-incomplete-identity-reason": invalid_identity,
    }


EXAMPLE_FILE_NAMES = {
    "campaign-prod-047-valid-en-internal-review": "campaign-prod-047-valid-en-internal-review.json",
    "campaign-prod-047-valid-de-source-informed": "campaign-prod-047-valid-de-source-informed.json",
    "campaign-prod-047-invalid-de-fragment-interpolation": "campaign-prod-047-invalid-de-fragment-interpolation.json",
    "campaign-prod-047-invalid-en-internal-copy": "campaign-prod-047-invalid-en-internal-copy.json",
    "campaign-prod-047-invalid-payment-enabled": "campaign-prod-047-invalid-payment-enabled.json",
    "campaign-prod-047-invalid-missing-regulated-boundary": "campaign-prod-047-invalid-missing-regulated-boundary.json",
    "campaign-prod-047-invalid-missing-native-review-status": "campaign-prod-047-invalid-missing-native-review-status.json",
    "campaign-prod-047-invalid-sale-ready-without-close-criteria": "campaign-prod-047-invalid-sale-ready-without-close-criteria.json",
    "campaign-prod-047-invalid-support-cancellation-route-label": "campaign-prod-047-invalid-support-cancellation-route-label.json",
    "campaign-prod-047-incomplete-identity-reason": "campaign-prod-047-incomplete-identity-reason.json",
}


def write_example_profiles(base_dir: Path | None = None) -> list[Path]:
    target_dir = base_dir or ROOT / "runtime" / "campaigns" / "examples"
    paths = []
    for campaign_id, profile in example_profiles().items():
        path = target_dir / EXAMPLE_FILE_NAMES[campaign_id]
        write_json(path, profile)
        paths.append(path)
    return paths


def schema_payload() -> dict[str, Any]:
    return {
        "schema_id": "campaign-profile-contract-prod-047-v1",
        "allowed_languages": ALLOWED_LANGUAGES,
        "allowed_field_shapes": ALLOWED_FIELD_SHAPES,
        "allowed_source_boundaries": ALLOWED_SOURCE_BOUNDARIES,
        "allowed_review_statuses": ALLOWED_REVIEW_STATUSES,
        "required_safety_defaults": REQUIRED_SAFETY_DEFAULTS,
        "field_contracts": FIELD_CONTRACTS,
        "profile_required_keys": [
            "campaign_id",
            "contract_version",
            "language",
            "review_statuses",
            "safety_defaults",
            "regulated_context",
            "close_criteria",
            "fields",
        ],
        "customer_facing_field_required_keys": ["value", "shape", "source_boundary", "review_statuses", "customer_facing"],
    }


def guard_matrix_payload() -> dict[str, Any]:
    return {
        "matrix_id": "campaign-guard-matrix-prod-047-v1",
        "policy_groups": {
            group: {
                "required_field_ids": fields,
                "field_shapes": {field: FIELD_CONTRACTS[field] for field in fields},
                "blocked_until_contract_validated": True,
            }
            for group, fields in REQUIRED_POLICY_GROUPS.items()
        },
        "hard_safety_defaults": REQUIRED_SAFETY_DEFAULTS,
        "promotion_boundaries": {
            "voice_requires": ["valid contract", "native_speaker_reviewed for German", "approved_for_voice"],
            "public_demo_requires": ["valid contract", "approved_for_internal_demo", "no blocked review status"],
            "customer_use_requires": ["valid contract", "human_reviewed or company_approved source boundaries", "approved_for_customer_use", "legal review if required"],
        },
    }


def text_hits(value: str, markers: list[str]) -> list[str]:
    lowered = value.lower()
    return [marker for marker in markers if marker.lower() in lowered]


def duplicate_specialist_hit(value: str) -> bool:
    lowered = value.lower()
    return lowered.count("zuständige fachperson") > 1


def validate_campaign_profile(profile: dict[str, Any]) -> dict[str, Any]:
    campaign_id = str(profile.get("campaign_id", "unknown-campaign"))
    language = profile.get("language")
    fields = profile.get("fields") if isinstance(profile.get("fields"), dict) else {}
    review_statuses = profile.get("review_statuses") if isinstance(profile.get("review_statuses"), list) else []
    safety_defaults = profile.get("safety_defaults") if isinstance(profile.get("safety_defaults"), dict) else {}
    close_criteria = profile.get("close_criteria") if isinstance(profile.get("close_criteria"), dict) else {}

    missing_fields: list[dict[str, Any]] = []
    invalid_fields: list[dict[str, Any]] = []
    unsafe_fields: list[dict[str, Any]] = []
    internal_customer_facing_terms: list[dict[str, Any]] = []
    language_shape_errors: list[dict[str, Any]] = []
    source_boundary_errors: list[dict[str, Any]] = []
    review_status_errors: list[dict[str, Any]] = []
    safety_boundary_errors: list[dict[str, Any]] = []

    if language not in ALLOWED_LANGUAGES:
        review_status_errors.append({"field": "language", "message": "language must be `en` or `de`; future languages are blocked until reviewed"})

    if not review_statuses:
        review_status_errors.append({"field": "review_statuses", "message": "campaign must declare language-specific review statuses"})
    for status in review_statuses:
        if status not in ALLOWED_REVIEW_STATUSES:
            review_status_errors.append({"field": "review_statuses", "value": status, "message": "unknown review status"})
    if language == "de" and not ({"native_speaker_review_required", "native_speaker_reviewed"} & set(review_statuses)):
        review_status_errors.append({"field": "review_statuses", "message": "German profiles must declare native_speaker_review_required or native_speaker_reviewed"})

    for key, expected_value in REQUIRED_SAFETY_DEFAULTS.items():
        if safety_defaults.get(key) is not expected_value:
            safety_boundary_errors.append({"field": key, "expected": expected_value, "actual": safety_defaults.get(key)})

    for group, required_field_ids in REQUIRED_POLICY_GROUPS.items():
        for field_id in required_field_ids:
            if field_id not in fields:
                missing_fields.append({"policy_group": group, "field_id": field_id, "message": "required policy field is missing"})

    for field_id, expected_shape in FIELD_CONTRACTS.items():
        if field_id not in fields:
            continue
        field = fields[field_id]
        if not isinstance(field, dict):
            invalid_fields.append({"field_id": field_id, "message": "field must be an object"})
            continue
        value = str(field.get("value", ""))
        shape = field.get("shape")
        source_boundary = field.get("source_boundary")
        field_review_statuses = field.get("review_statuses") if isinstance(field.get("review_statuses"), list) else []
        customer_facing = field.get("customer_facing") is True and field.get("internal_only") is not True

        if not value.strip():
            invalid_fields.append({"field_id": field_id, "message": "field value is empty"})
        if shape not in ALLOWED_FIELD_SHAPES:
            invalid_fields.append({"field_id": field_id, "shape": shape, "message": "unknown field shape"})
        elif shape != expected_shape:
            language_shape_errors.append({"field_id": field_id, "expected_shape": expected_shape, "actual_shape": shape})
        if field.get("template_requires_shape") and field.get("template_requires_shape") != shape:
            language_shape_errors.append({"field_id": field_id, "template_requires_shape": field["template_requires_shape"], "actual_shape": shape})
        if source_boundary not in ALLOWED_SOURCE_BOUNDARIES:
            source_boundary_errors.append({"field_id": field_id, "source_boundary": source_boundary, "message": "unknown source boundary"})
        if source_boundary == "blocked":
            source_boundary_errors.append({"field_id": field_id, "message": "blocked source boundary cannot be used"})
        if not field_review_statuses:
            review_status_errors.append({"field_id": field_id, "message": "field must declare review statuses"})
        for status in field_review_statuses:
            if status not in ALLOWED_REVIEW_STATUSES:
                review_status_errors.append({"field_id": field_id, "value": status, "message": "unknown field review status"})
        if language == "de" and customer_facing:
            hits = text_hits(value, GERMAN_BLOCKED_CUSTOMER_TERMS)
            if hits:
                internal_customer_facing_terms.append({"field_id": field_id, "hits": hits, "value": value})
            if duplicate_specialist_hit(value):
                language_shape_errors.append({"field_id": field_id, "message": "duplicated `zuständige Fachperson` in same customer-facing field"})
        if language == "en" and customer_facing:
            hits = text_hits(value, ENGLISH_BLOCKED_CUSTOMER_TERMS)
            if hits:
                internal_customer_facing_terms.append({"field_id": field_id, "hits": hits, "value": value})

    if close_criteria.get("sale_ready_allowed") is True and close_criteria.get("criteria_satisfied") is not True:
        safety_boundary_errors.append({"field": "close_criteria.criteria_satisfied", "message": "sale-ready next step requires satisfied close criteria"})

    policy_group_readiness = {}
    for group, required_field_ids in REQUIRED_POLICY_GROUPS.items():
        group_missing = [item for item in missing_fields if item["policy_group"] == group]
        group_invalid = [
            item
            for item in invalid_fields + language_shape_errors + source_boundary_errors + review_status_errors + internal_customer_facing_terms
            if item.get("field_id") in required_field_ids
        ]
        policy_group_readiness[group] = {
            "required_field_ids": required_field_ids,
            "ready_for_regression": not group_missing and not group_invalid,
            "ready_for_internal_product_review": not group_missing and not group_invalid and not safety_boundary_errors,
            "blocked_for_voice": True,
            "blocked_for_public_demo": True,
            "blocked_for_customer_use": True,
            "blocking_issue_count": len(group_missing) + len(group_invalid),
        }

    is_valid = not any(
        [
            missing_fields,
            invalid_fields,
            unsafe_fields,
            internal_customer_facing_terms,
            language_shape_errors,
            source_boundary_errors,
            review_status_errors,
            safety_boundary_errors,
        ]
    )
    readiness = {
        "valid_for_regression_only": is_valid,
        "valid_for_internal_product_review": is_valid and ("machine_validated" in review_statuses or "source_informed" in review_statuses),
        "blocked_for_voice": True,
        "blocked_for_public_demo": True,
        "blocked_for_customer_use": True,
    }
    if is_valid and "approved_for_voice" in review_statuses and (language != "de" or "native_speaker_reviewed" in review_statuses):
        readiness["blocked_for_voice"] = False
    if is_valid and "approved_for_internal_demo" in review_statuses:
        readiness["blocked_for_public_demo"] = False
    if is_valid and "approved_for_customer_use" in review_statuses and "legal_review_required" not in review_statuses:
        readiness["blocked_for_customer_use"] = False

    recommended_fix = []
    if missing_fields:
        recommended_fix.append("Add missing required policy fields with explicit shape, source boundary, and review status.")
    if internal_customer_facing_terms:
        recommended_fix.append("Rewrite customer-facing fields to remove internal, queue, approval, or malformed language.")
    if language_shape_errors:
        recommended_fix.append("Correct field shapes or split full-sentence fields from noun-phrase/route-label fields.")
    if source_boundary_errors:
        recommended_fix.append("Replace blocked or unknown source boundaries with reviewed source-boundary values.")
    if review_status_errors:
        recommended_fix.append("Add required language-specific review statuses before promotion.")
    if safety_boundary_errors:
        recommended_fix.append("Restore hard safety defaults and close criteria.")

    return {
        "campaign_id": campaign_id,
        "language": language,
        "is_valid": is_valid,
        "readiness": readiness,
        "policy_group_readiness": policy_group_readiness,
        "missing_fields": missing_fields,
        "invalid_fields": invalid_fields,
        "unsafe_fields": unsafe_fields,
        "internal_customer_facing_terms": internal_customer_facing_terms,
        "language_shape_errors": language_shape_errors,
        "source_boundary_errors": source_boundary_errors,
        "review_status_errors": review_status_errors,
        "safety_boundary_errors": safety_boundary_errors,
        "recommended_fix": recommended_fix or ["No deterministic contract fix required for offline/internal review."],
    }


def validation_cases(example_paths: list[Path]) -> list[dict[str, Any]]:
    expected_valid = {
        "campaign-prod-047-valid-en-internal-review": True,
        "campaign-prod-047-valid-de-source-informed": True,
    }
    cases = []
    for path in example_paths:
        profile = read_json(path)
        campaign_id = profile["campaign_id"]
        cases.append(
            {
                "case_id": campaign_id.replace("campaign-prod-047-", ""),
                "campaign_id": campaign_id,
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "expected_valid": expected_valid.get(campaign_id, False),
            }
        )
    return cases
