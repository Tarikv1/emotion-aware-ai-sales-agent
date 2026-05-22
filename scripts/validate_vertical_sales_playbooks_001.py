#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CHECKPOINT_ID = "VERTICAL-SALES-PLAYBOOKS-001"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"

REQUIRED_VERTICAL_IDS = {
    "b2b_saas",
    "insurance",
    "telecom",
    "home_services",
    "healthcare_admin_or_medical_equipment",
    "automotive_service",
    "membership_or_subscription",
    "retail_or_ecommerce_support_sales",
}

OPTIONAL_VERTICAL_IDS = {
    "financial_or_payment_sensitive",
    "education_or_training",
    "travel_or_hospitality",
}

REQUIRED_VERTICAL_FIELDS = {
    "vertical_id",
    "schema_version",
    "description",
    "typical_call_center_contexts",
    "common_buyer_roles",
    "common_sales_stages",
    "likely_qualification_dimensions",
    "common_pain_dimensions",
    "common_objection_families",
    "safe_discovery_questions",
    "safe_value_bridge_principles",
    "appointment_or_followup_patterns",
    "right_person_or_authority_patterns",
    "send_info_patterns",
    "regulated_cautions",
    "blocked_claim_types",
    "human_escalation_triggers",
    "campaign_config_required_fields",
}

REGULATED_VERTICALS_REQUIRING_CAUTIONS = {
    "insurance",
    "healthcare_admin_or_medical_equipment",
    "telecom",
    "home_services",
    "automotive_service",
    "membership_or_subscription",
    "retail_or_ecommerce_support_sales",
}

FORBIDDEN_CAMPAIGN_TERMS = [
    "RouteSignal",
    "Northstar",
    "Starter",
    "Growth",
    "demo lead",
    "inbound demo",
    "workflow review with Northstar",
    "$29",
    "$59",
]

FORBIDDEN_CLAIM_PHRASES = [
    "saves money",
    "guaranteed approval",
    "covered by insurance",
    "best price",
    "compliant",
    "certified",
    "guaranteed results",
]


def assert_condition(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def write_evidence(result: dict[str, Any], report: str) -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(report, encoding="utf-8")


def module_source_text() -> str:
    return (ROOT / "runtime" / "core" / "vertical_sales_playbooks.py").read_text(encoding="utf-8")


def build_report(result: dict[str, Any]) -> str:
    status = "pass" if result["status"] == "pass" else "fail"
    lines = [
        "# VERTICAL-SALES-PLAYBOOKS-001",
        "",
        f"Status: {status}",
        "",
        "## Contract",
        "",
        "- Non-integrated vertical sales adapter skeletons.",
        "- Uses universal sales knowledge IDs where possible.",
        "- No campaign migration or runtime routing integration in this phase.",
        "",
        "## Vertical IDs",
        "",
    ]
    for vertical_id in result.get("vertical_ids", []):
        lines.append(f"- {vertical_id}")
    lines.extend(
        [
            "",
            "## Regulated Caution Coverage",
            "",
        ]
    )
    for vertical_id, cautions in sorted((result.get("regulated_caution_coverage") or {}).items()):
        lines.append(f"- {vertical_id}: {', '.join(cautions) if cautions else 'none'}")
    lines.extend(
        [
            "",
            "## Forbidden Terms",
            "",
            f"- Campaign term check passed: {str(result['forbidden_campaign_terms_check']['passed']).lower()}",
            f"- Forbidden campaign terms found: {', '.join(result['forbidden_campaign_terms_check']['found_terms']) if result['forbidden_campaign_terms_check']['found_terms'] else 'none'}",
            f"- Forbidden claim phrases found: {', '.join(result['forbidden_claim_phrase_check']['found_terms']) if result['forbidden_claim_phrase_check']['found_terms'] else 'none'}",
            "",
            "## Suggested Universal Additions",
            "",
            f"- Count: {len(result.get('suggested_universal_additions') or [])}",
        ]
    )
    if result.get("suggested_universal_additions"):
        for addition in result["suggested_universal_additions"]:
            lines.append(f"- {addition}")
    if result["failures"]:
        lines.extend(["", "## Failures", ""])
        for failure in result["failures"]:
            lines.append(f"- {failure}")
    return "\n".join(lines) + "\n"


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def validate_vertical_records(
    failures: list[str],
    universal: Any,
    vertical_module: Any,
) -> dict[str, Any]:
    playbooks = vertical_module.VERTICAL_SALES_PLAYBOOKS
    assert_condition(failures, isinstance(playbooks, dict), "VERTICAL_SALES_PLAYBOOKS must be a dict")
    assert_condition(failures, REQUIRED_VERTICAL_IDS.issubset(playbooks), f"missing required vertical ids {sorted(REQUIRED_VERTICAL_IDS - set(playbooks))}")

    universal_stage_ids = set(universal.all_sales_stage_ids())
    universal_qualification_ids = set(universal.all_qualification_dimension_ids())
    universal_pain_ids = set(universal.all_generic_pain_dimension_ids())
    universal_objection_ids = set(universal.all_objection_family_ids())
    universal_caution_ids = set(universal.all_regulated_caution_ids())

    regulated_caution_coverage: dict[str, list[str]] = {}
    for vertical_id, record in playbooks.items():
        assert_condition(
            failures,
            vertical_id in REQUIRED_VERTICAL_IDS or vertical_id in OPTIONAL_VERTICAL_IDS,
            f"{vertical_id}: unexpected vertical id",
        )
        assert_condition(failures, isinstance(record, dict), f"{vertical_id}: record must be a dict")
        if not isinstance(record, dict):
            continue
        assert_condition(failures, record.get("vertical_id") == vertical_id, f"{vertical_id}: vertical_id field must match key")
        assert_condition(failures, record.get("schema_version") == 1, f"{vertical_id}: schema_version must be 1")
        for field in sorted(REQUIRED_VERTICAL_FIELDS):
            assert_condition(failures, bool(record.get(field)), f"{vertical_id}.{field}: must be populated")

        assert_condition(failures, len(_as_list(record.get("common_buyer_roles"))) >= 3, f"{vertical_id}: needs at least 3 common buyer roles")
        assert_condition(failures, len(_as_list(record.get("likely_qualification_dimensions"))) >= 3, f"{vertical_id}: needs at least 3 qualification dimensions")
        assert_condition(failures, len(_as_list(record.get("common_pain_dimensions"))) >= 3, f"{vertical_id}: needs at least 3 pain dimensions")
        assert_condition(failures, len(_as_list(record.get("common_objection_families"))) >= 3, f"{vertical_id}: needs at least 3 objection families")
        assert_condition(failures, len(_as_list(record.get("safe_discovery_questions"))) >= 3, f"{vertical_id}: needs at least 3 safe discovery questions")
        assert_condition(failures, len(_as_list(record.get("blocked_claim_types"))) >= 2, f"{vertical_id}: needs at least 2 blocked claim types")
        assert_condition(failures, len(_as_list(record.get("human_escalation_triggers"))) >= 1, f"{vertical_id}: needs at least 1 escalation trigger")

        unknown_stages = set(_as_list(record.get("common_sales_stages"))) - universal_stage_ids
        unknown_qualifications = set(_as_list(record.get("likely_qualification_dimensions"))) - universal_qualification_ids
        unknown_pains = set(_as_list(record.get("common_pain_dimensions"))) - universal_pain_ids
        unknown_objections = set(_as_list(record.get("common_objection_families"))) - universal_objection_ids
        unknown_cautions = set(_as_list(record.get("regulated_cautions"))) - universal_caution_ids
        assert_condition(failures, not unknown_stages, f"{vertical_id}: unknown sales stage ids {sorted(unknown_stages)}")
        assert_condition(failures, not unknown_qualifications, f"{vertical_id}: unknown qualification ids {sorted(unknown_qualifications)}")
        assert_condition(failures, not unknown_pains, f"{vertical_id}: unknown pain ids {sorted(unknown_pains)}")
        assert_condition(failures, not unknown_objections, f"{vertical_id}: unknown objection ids {sorted(unknown_objections)}")
        assert_condition(failures, not unknown_cautions, f"{vertical_id}: unknown regulated caution ids {sorted(unknown_cautions)}")

        cautions = _as_list(record.get("regulated_cautions"))
        regulated_caution_coverage[vertical_id] = sorted(str(item) for item in cautions)
        if vertical_id in REGULATED_VERTICALS_REQUIRING_CAUTIONS:
            assert_condition(failures, bool(cautions), f"{vertical_id}: regulated vertical must include at least one regulated caution")

    return {
        "vertical_ids": sorted(playbooks),
        "regulated_caution_coverage": regulated_caution_coverage,
    }


def validate_helpers(failures: list[str], vertical_module: Any, vertical_ids: list[str]) -> None:
    for vertical_id in vertical_ids:
        record = vertical_module.vertical_playbook(vertical_id)
        assert_condition(failures, isinstance(record, dict) and record.get("vertical_id") == vertical_id, f"vertical_playbook({vertical_id}) must return record")
        assert_condition(failures, isinstance(vertical_module.vertical_required_campaign_fields(vertical_id), list), f"vertical_required_campaign_fields({vertical_id}) must return list")
        assert_condition(failures, isinstance(vertical_module.vertical_regulated_cautions(vertical_id), list), f"vertical_regulated_cautions({vertical_id}) must return list")
        assert_condition(failures, isinstance(vertical_module.vertical_safe_discovery_questions(vertical_id), list), f"vertical_safe_discovery_questions({vertical_id}) must return list")
        assert_condition(failures, isinstance(vertical_module.vertical_blocked_claim_types(vertical_id), list), f"vertical_blocked_claim_types({vertical_id}) must return list")
    assert_condition(failures, REQUIRED_VERTICAL_IDS.issubset(set(vertical_module.all_vertical_ids())), "all_vertical_ids() must include required verticals")
    for caution_id in [
        "insurance",
        "healthcare_admin_or_medical_equipment",
        "telecom_contract_or_coverage",
    ]:
        mapped = vertical_module.vertical_ids_for_regulated_caution(caution_id)
        assert_condition(failures, isinstance(mapped, list), f"vertical_ids_for_regulated_caution({caution_id}) must return list")


def main() -> int:
    failures: list[str] = []
    try:
        from runtime.core import universal_sales_knowledge as universal  # noqa: WPS433
        from runtime.core import vertical_sales_playbooks as vertical_module  # noqa: WPS433
    except Exception as exc:  # pragma: no cover - used for red validation before module exists
        failures.append(f"module import failed: {exc!r}")
        result = {
            "status": "fail",
            "checkpoint_id": CHECKPOINT_ID,
            "failures": failures,
            "vertical_ids": [],
            "regulated_caution_coverage": {},
            "suggested_universal_additions": [],
            "forbidden_campaign_terms_check": {"passed": False, "found_terms": [], "checked_terms": FORBIDDEN_CAMPAIGN_TERMS},
            "forbidden_claim_phrase_check": {"passed": False, "found_terms": [], "checked_terms": FORBIDDEN_CLAIM_PHRASES},
            "safety": {
                "provider_calls_made": False,
                "local_llm_calls_made": False,
                "sends_email": False,
                "creates_calendar_event": False,
                "writes_crm": False,
                "opens_prod_102": False,
            },
        }
        write_evidence(result, build_report(result))
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1

    validation_result = vertical_module.validate_vertical_sales_playbooks(universal)
    assert_condition(failures, isinstance(validation_result, dict), "validate_vertical_sales_playbooks() must return a dict")
    assert_condition(failures, validation_result.get("valid") is True, f"validate_vertical_sales_playbooks() failed: {validation_result}")

    record_evidence = validate_vertical_records(failures, universal, vertical_module)
    vertical_ids = record_evidence.get("vertical_ids") or []
    validate_helpers(failures, vertical_module, vertical_ids)

    suggested_additions = list(vertical_module.SUGGESTED_UNIVERSAL_ADDITIONS)
    unjustified = [item for item in suggested_additions if not isinstance(item, dict) or not item.get("reason")]
    assert_condition(failures, not unjustified, f"suggested_universal_additions must be empty or justified: {unjustified}")

    source_text = module_source_text()
    found_campaign_terms = [term for term in FORBIDDEN_CAMPAIGN_TERMS if term.lower() in source_text.lower()]
    found_claim_phrases = [term for term in FORBIDDEN_CLAIM_PHRASES if term.lower() in source_text.lower()]
    assert_condition(failures, not found_campaign_terms, f"forbidden campaign terms found: {found_campaign_terms}")
    assert_condition(failures, not found_claim_phrases, f"forbidden claim phrases found: {found_claim_phrases}")

    safety = {
        "provider_calls_made": False,
        "local_llm_calls_made": False,
        "sends_email": False,
        "creates_calendar_event": False,
        "writes_crm": False,
        "opens_prod_102": False,
    }
    result = {
        "status": "pass" if not failures else "fail",
        "checkpoint_id": CHECKPOINT_ID,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "phase_1_2_3_backpatch_required": False,
        "vertical_ids": vertical_ids,
        "required_vertical_ids": sorted(REQUIRED_VERTICAL_IDS),
        "optional_vertical_ids_present": sorted(set(vertical_ids) & OPTIONAL_VERTICAL_IDS),
        "regulated_caution_coverage": record_evidence.get("regulated_caution_coverage") or {},
        "suggested_universal_additions": suggested_additions,
        "forbidden_campaign_terms_check": {
            "passed": not found_campaign_terms,
            "found_terms": found_campaign_terms,
            "checked_terms": FORBIDDEN_CAMPAIGN_TERMS,
        },
        "forbidden_claim_phrase_check": {
            "passed": not found_claim_phrases,
            "found_terms": found_claim_phrases,
            "checked_terms": FORBIDDEN_CLAIM_PHRASES,
        },
        "safety": safety,
        "helper_functions_checked": [
            "vertical_playbook",
            "all_vertical_ids",
            "vertical_ids_for_regulated_caution",
            "validate_vertical_sales_playbooks",
            "vertical_required_campaign_fields",
            "vertical_regulated_cautions",
            "vertical_safe_discovery_questions",
            "vertical_blocked_claim_types",
        ],
        "generated_evidence": {
            "result_json": str(RESULT_PATH.relative_to(ROOT)),
            "report_md": str(REPORT_PATH.relative_to(ROOT)),
        },
        "failures": failures,
    }
    write_evidence(result, build_report(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
