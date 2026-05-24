from __future__ import annotations

import json
from copy import deepcopy
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from runtime.core import universal_sales_knowledge
from runtime.core import vertical_sales_playbooks


CAMPAIGN_REGISTRY_ID = "CAMPAIGN-REGISTRY-001"
SCHEMA_VERSION = 1
ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN_ROOT = ROOT / "runtime" / "campaigns"
DEFAULT_CONFIG_ROOT = CAMPAIGN_ROOT / "examples"

SAFETY_FLAGS = {
    "provider_calls_made": False,
    "local_llm_calls_made": False,
    "sends_email": False,
    "creates_calendar_event": False,
    "writes_crm": False,
    "opens_prod_102": False,
}

SUPPORTED_CLOSE_MODES = {
    "self_serve_purchase_link",
    "contact_sales",
    "send_info_capture",
    "appointment_review",
    "no_fit_close",
}

SUPPORTED_OBJECTIVES = {
    "appointment_setting",
    "self_serve_plan_fit",
}

SOURCE_GROUNDED_CLAIM_FIELDS = {
    "fact_id",
    "claim",
    "source_title",
    "source_url",
    "retrieved_at_utc",
    "source_type",
    "allowed_in_speech",
    "requires_caveat",
    "caveat_text",
    "plan_ids",
    "claim_category",
    "exact_quote_excerpt_optional",
    "normalized_speech_version",
}

REQUIRED_TOP_LEVEL_FIELDS = {
    "campaign_id",
    "client_name",
    "product_or_offer_name",
    "vertical_id",
    "objective",
    "human_followup_owner",
    "appointment_target",
    "allowed_claims",
    "blocked_claims",
    "diagnostic_gaps",
    "core_diagnostic_gaps",
    "gap_order",
    "caller_identity",
    "language",
}

REQUIRED_GAP_FIELDS = {
    "campaign_gap_id",
    "label",
    "universal_pain_dimensions",
    "qualification_dimensions",
    "definition",
    "causal_story",
    "customer_language",
    "evidence_positive",
    "evidence_negative",
    "diagnostic_questions",
    "value_bridge",
    "review_focus",
    "next_gap_candidates",
}

PRIVATE_PATH_PARTS = {"private", "private-restricted"}
SCHEMA_FILE_NAME = "campaign_config.schema.json"


class CampaignRegistryError(ValueError):
    """Base class for controlled campaign registry failures."""


class CampaignConfigValidationError(CampaignRegistryError):
    """Raised when a campaign config fails the local loading contract."""

    def __init__(self, failures: list[str]):
        self.failures = list(failures)
        super().__init__("invalid campaign config: " + "; ".join(self.failures))


class CampaignConfigNotFoundError(CampaignRegistryError):
    """Raised when a campaign config path or id cannot be resolved."""


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item or "")]
    return [str(value)] if str(value or "") else []


def _path_parts(path: Path) -> set[str]:
    return {part.lower() for part in path.parts}


def _relative_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def _assert_loadable_path(path: Path) -> None:
    resolved = path.expanduser().resolve()
    parts = _path_parts(resolved)
    if parts & PRIVATE_PATH_PARTS:
        raise CampaignConfigValidationError([f"private customer data path is not loadable: {_relative_path(resolved)}"])
    if resolved.suffix.lower() != ".json":
        raise CampaignConfigValidationError([f"campaign config must be a JSON file: {_relative_path(resolved)}"])


def _read_json_object(path: Path) -> dict[str, Any]:
    _assert_loadable_path(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CampaignConfigNotFoundError(f"campaign config not found: {_relative_path(path)}") from exc
    except JSONDecodeError as exc:
        raise CampaignConfigValidationError([f"invalid JSON in {_relative_path(path)}: {exc.msg}"]) from exc
    if not isinstance(payload, dict):
        raise CampaignConfigValidationError([f"campaign config must be a JSON object: {_relative_path(path)}"])
    return payload


def _normalized_config(config: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(config)
    offer = normalized.get("product_or_offer_name") or normalized.get("offer_name") or normalized.get("product_name")
    if offer:
        normalized.setdefault("product_or_offer_name", str(offer))
        normalized.setdefault("offer_name", str(offer))
        normalized.setdefault("product_name", str(offer))
    safety = dict(SAFETY_FLAGS)
    if isinstance(normalized.get("safety"), dict):
        safety.update(normalized["safety"])
    normalized["safety"] = safety
    return normalized


def _missing_required_fields(config: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for field in sorted(REQUIRED_TOP_LEVEL_FIELDS):
        if field not in config:
            missing.append(field)
            continue
        value = config.get(field)
        if field == "allowed_claims":
            if not isinstance(value, list):
                missing.append(field)
        elif value in (None, "", [], {}):
            missing.append(field)
    return missing


def _validate_string_list(
    failures: list[str],
    config: dict[str, Any],
    field: str,
    *,
    allow_empty: bool = False,
) -> list[str]:
    if field not in config:
        failures.append(f"{field}: missing")
        return []
    value = config.get(field)
    if not isinstance(value, list):
        failures.append(f"{field}: must be a list")
        return []
    normalized = _string_list(value)
    if not allow_empty and not normalized:
        failures.append(f"{field}: must be populated")
    if len(normalized) != len(value):
        failures.append(f"{field}: entries must be non-empty strings")
    return normalized


def _validate_caller_identity(failures: list[str], value: Any) -> None:
    if not isinstance(value, dict) or not value:
        failures.append("caller_identity: must be a populated object")
        return
    required = {"representative_name", "relationship_to_offer"}
    missing = sorted(field for field in required if not str(value.get(field) or "").strip())
    if missing:
        failures.append(f"caller_identity: missing fields {missing}")


def _validate_safety(failures: list[str], config: dict[str, Any]) -> None:
    safety = config.get("safety") or {}
    if not isinstance(safety, dict):
        failures.append("safety: must be an object when present")
        return
    for key, expected in SAFETY_FLAGS.items():
        if safety.get(key, expected) is not expected:
            failures.append(f"safety.{key}: must default to {expected}")


def _validate_close_modes(failures: list[str], config: dict[str, Any]) -> None:
    modes = config.get("close_modes_supported")
    if modes is None:
        return
    normalized = _string_list(modes)
    if not isinstance(modes, list):
        failures.append("close_modes_supported: must be a list when present")
        return
    if len(normalized) != len(modes):
        failures.append("close_modes_supported: entries must be non-empty strings")
    unknown = sorted(set(normalized) - SUPPORTED_CLOSE_MODES)
    if unknown:
        failures.append(f"close_modes_supported: unknown close modes {unknown}")


def _validate_source_grounded_claims(failures: list[str], config: dict[str, Any]) -> None:
    claims = config.get("source_grounded_claims")
    if claims is None:
        return
    if not isinstance(claims, list):
        failures.append("source_grounded_claims: must be a list when present")
        return
    seen: set[str] = set()
    for index, claim in enumerate(claims, start=1):
        if not isinstance(claim, dict):
            failures.append(f"source_grounded_claims[{index}]: must be an object")
            continue
        missing = sorted(field for field in SOURCE_GROUNDED_CLAIM_FIELDS if field not in claim)
        if missing:
            failures.append(f"source_grounded_claims[{index}]: missing fields {missing}")
        fact_id = str(claim.get("fact_id") or "")
        if not fact_id:
            failures.append(f"source_grounded_claims[{index}].fact_id: must be populated")
        elif fact_id in seen:
            failures.append(f"source_grounded_claims[{index}].fact_id: duplicate {fact_id}")
        seen.add(fact_id)
        if not isinstance(claim.get("plan_ids"), list):
            failures.append(f"source_grounded_claims[{index}].plan_ids: must be a list")
        if claim.get("allowed_in_speech") is True and not str(claim.get("normalized_speech_version") or "").strip():
            failures.append(f"source_grounded_claims[{index}].normalized_speech_version: required for speech")
        if claim.get("requires_caveat") is True and not str(claim.get("caveat_text") or "").strip():
            failures.append(f"source_grounded_claims[{index}].caveat_text: required when requires_caveat is true")


def _validate_gap_record(
    failures: list[str],
    gap_id: str,
    gap: Any,
    *,
    all_gap_ids: set[str],
    universal_pain_ids: set[str],
    qualification_ids: set[str],
) -> None:
    if not isinstance(gap, dict):
        failures.append(f"diagnostic_gaps.{gap_id}: must be an object")
        return

    missing = sorted(field for field in REQUIRED_GAP_FIELDS if gap.get(field) in (None, "", [], {}))
    if missing:
        failures.append(f"diagnostic_gaps.{gap_id}: missing fields {missing}")

    campaign_gap_id = str(gap.get("campaign_gap_id") or "")
    if campaign_gap_id and campaign_gap_id != gap_id:
        failures.append(f"diagnostic_gaps.{gap_id}.campaign_gap_id: must match diagnostic gap key")

    universal_pains = _validate_string_list(
        failures,
        gap,
        "universal_pain_dimensions",
    )
    qualifications = _validate_string_list(
        failures,
        gap,
        "qualification_dimensions",
    )
    for field in ["customer_language", "evidence_positive", "evidence_negative", "diagnostic_questions"]:
        _validate_string_list(failures, gap, field)
    next_candidates = _validate_string_list(failures, gap, "next_gap_candidates", allow_empty=True)

    unknown_pains = sorted(set(universal_pains) - universal_pain_ids)
    if unknown_pains:
        failures.append(f"diagnostic_gaps.{gap_id}: unknown universal_pain_dimensions {unknown_pains}")
    unknown_qualifications = sorted(set(qualifications) - qualification_ids)
    if unknown_qualifications:
        failures.append(f"diagnostic_gaps.{gap_id}: unknown qualification_dimensions {unknown_qualifications}")
    unknown_next = sorted(set(next_candidates) - all_gap_ids)
    if unknown_next:
        failures.append(f"diagnostic_gaps.{gap_id}: unknown next_gap_candidates {unknown_next}")


def validate_campaign_config(config: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(config, dict):
        return {
            "valid": False,
            "registry_id": CAMPAIGN_REGISTRY_ID,
            "schema_version": SCHEMA_VERSION,
            "campaign_id": None,
            "vertical_id": None,
            "failures": ["campaign config must be a dict"],
        }

    normalized = _normalized_config(config)
    missing = _missing_required_fields(normalized)
    if missing:
        failures.append(f"missing required fields: {missing}")

    campaign_id = str(normalized.get("campaign_id") or "")
    vertical_id = str(normalized.get("vertical_id") or "")
    if vertical_id and vertical_id not in set(vertical_sales_playbooks.all_vertical_ids()):
        failures.append(f"unsupported vertical_id: {vertical_id}")

    if normalized.get("objective") not in SUPPORTED_OBJECTIVES:
        failures.append(f"objective: must be one of {sorted(SUPPORTED_OBJECTIVES)}")
    if normalized.get("allowed_claims") is not None:
        _validate_string_list(failures, normalized, "allowed_claims", allow_empty=True)
    if normalized.get("blocked_claims") is not None:
        _validate_string_list(failures, normalized, "blocked_claims", allow_empty=True)
    if normalized.get("caller_identity") is not None:
        _validate_caller_identity(failures, normalized.get("caller_identity"))
    _validate_safety(failures, normalized)
    _validate_close_modes(failures, normalized)
    _validate_source_grounded_claims(failures, normalized)

    vertical_cautions = vertical_sales_playbooks.vertical_regulated_cautions(vertical_id)
    if vertical_cautions:
        blocked_claims = _string_list(normalized.get("blocked_claims"))
        if not blocked_claims:
            failures.append("blocked_claims: regulated verticals require at least one blocked claim")
        configured_cautions = _validate_string_list(failures, normalized, "regulated_cautions")
        missing_cautions = sorted(set(vertical_cautions) - set(configured_cautions))
        if missing_cautions:
            failures.append(f"regulated_cautions: missing vertical cautions {missing_cautions}")
        unknown_cautions = sorted(set(configured_cautions) - set(universal_sales_knowledge.all_regulated_caution_ids()))
        if unknown_cautions:
            failures.append(f"regulated_cautions: unknown cautions {unknown_cautions}")

    diagnostic_gaps = normalized.get("diagnostic_gaps")
    if not isinstance(diagnostic_gaps, dict) or not diagnostic_gaps:
        failures.append("diagnostic_gaps: must be a populated object")
        diagnostic_gaps = {}
    all_gap_ids = set(str(gap_id) for gap_id in diagnostic_gaps)

    core_gaps = _validate_string_list(failures, normalized, "core_diagnostic_gaps")
    gap_order = _validate_string_list(failures, normalized, "gap_order")
    unknown_core = sorted(set(core_gaps) - all_gap_ids)
    if unknown_core:
        failures.append(f"core_diagnostic_gaps: unknown gaps {unknown_core}")
    unknown_order = sorted(set(gap_order) - all_gap_ids)
    if unknown_order:
        failures.append(f"gap_order: unknown gaps {unknown_order}")
    missing_from_order = sorted(all_gap_ids - set(gap_order))
    if missing_from_order:
        failures.append(f"gap_order: missing diagnostic gaps {missing_from_order}")
    duplicate_order = sorted(gap_id for gap_id in set(gap_order) if gap_order.count(gap_id) > 1)
    if duplicate_order:
        failures.append(f"gap_order: duplicate gaps {duplicate_order}")

    universal_pain_ids = set(universal_sales_knowledge.all_generic_pain_dimension_ids())
    qualification_ids = set(universal_sales_knowledge.all_qualification_dimension_ids())
    for gap_id, gap in diagnostic_gaps.items():
        _validate_gap_record(
            failures,
            str(gap_id),
            gap,
            all_gap_ids=all_gap_ids,
            universal_pain_ids=universal_pain_ids,
            qualification_ids=qualification_ids,
        )

    return {
        "valid": not failures,
        "registry_id": CAMPAIGN_REGISTRY_ID,
        "schema_version": SCHEMA_VERSION,
        "campaign_id": campaign_id or None,
        "vertical_id": vertical_id or None,
        "failures": failures,
        "safety": deepcopy(normalized.get("safety") or SAFETY_FLAGS),
    }


def load_campaign_config(path: str | Path) -> dict[str, Any]:
    resolved = Path(path).expanduser().resolve()
    payload = _read_json_object(resolved)
    normalized = _normalized_config(payload)
    validation = validate_campaign_config(normalized)
    if validation.get("valid") is not True:
        raise CampaignConfigValidationError([str(item) for item in validation.get("failures") or []])
    return normalized


def _candidate_config_paths(root: Path) -> list[Path]:
    if not root.exists():
        return []
    if root.is_file():
        return [root]
    return sorted(
        path
        for path in root.rglob("*.json")
        if path.name != SCHEMA_FILE_NAME and "schema" not in _path_parts(path.relative_to(root))
    )


def _looks_like_registry_config(payload: dict[str, Any]) -> bool:
    if "campaign_id" not in payload:
        return False
    return any(
        marker in payload
        for marker in [
            "vertical_id",
            "diagnostic_gaps",
            "core_diagnostic_gaps",
            "gap_order",
            "product_or_offer_name",
        ]
    )


def campaign_registry_entry(config: dict[str, Any], path: Path | None = None) -> dict[str, Any]:
    normalized = _normalized_config(config if isinstance(config, dict) else {})
    validation = validate_campaign_config(normalized)
    valid = validation.get("valid") is True
    return {
        "registry_id": CAMPAIGN_REGISTRY_ID,
        "campaign_id": normalized.get("campaign_id"),
        "vertical_id": normalized.get("vertical_id"),
        "product_or_offer_name": normalized.get("product_or_offer_name"),
        "appointment_target": normalized.get("appointment_target"),
        "path": _relative_path(path.resolve()) if path else None,
        "valid": valid,
        "validation_status": "valid" if valid else "invalid",
        "failures": list(validation.get("failures") or []),
    }


def list_campaign_configs(root: Path | None = None) -> list[dict[str, Any]]:
    search_root = (root or DEFAULT_CONFIG_ROOT).expanduser().resolve()
    entries: list[dict[str, Any]] = []
    for path in _candidate_config_paths(search_root):
        try:
            payload = _read_json_object(path)
        except CampaignRegistryError as exc:
            entries.append(
                {
                    "registry_id": CAMPAIGN_REGISTRY_ID,
                    "campaign_id": None,
                    "vertical_id": None,
                    "product_or_offer_name": None,
                    "appointment_target": None,
                    "path": _relative_path(path),
                    "valid": False,
                    "validation_status": "invalid",
                    "failures": [str(exc)],
                }
            )
            continue
        if not _looks_like_registry_config(payload):
            continue
        entries.append(campaign_registry_entry(payload, path))
    return entries


def resolve_campaign_config(path_or_id: str | Path) -> dict[str, Any]:
    value = Path(path_or_id) if isinstance(path_or_id, Path) else Path(str(path_or_id))
    raw = str(path_or_id)
    if value.exists() or value.suffix.lower() == ".json" or any(sep in raw for sep in ("/", "\\")):
        return load_campaign_config(value)

    target_id = raw.strip()
    for entry in list_campaign_configs():
        if entry.get("campaign_id") == target_id or Path(str(entry.get("path") or "")).stem == target_id:
            path_value = entry.get("path")
            if not path_value:
                break
            return load_campaign_config(ROOT / str(path_value))
    raise CampaignConfigNotFoundError(f"campaign config id not found: {target_id}")


def validate_campaign_registry(root: Path | None = None) -> dict[str, Any]:
    entries = list_campaign_configs(root)
    failures: list[str] = []
    for entry in entries:
        if entry.get("valid") is not True:
            failures.append(f"{entry.get('path')}: {entry.get('failures')}")
    return {
        "valid": not failures,
        "registry_id": CAMPAIGN_REGISTRY_ID,
        "schema_version": SCHEMA_VERSION,
        "root": _relative_path((root or DEFAULT_CONFIG_ROOT).expanduser().resolve()),
        "campaign_count": len(entries),
        "entries": entries,
        "failures": failures,
        **dict(SAFETY_FLAGS),
    }


def source_grounded_claims(config: dict[str, Any] | None) -> list[dict[str, Any]]:
    claims = (config or {}).get("source_grounded_claims") or []
    if not isinstance(claims, list):
        return []
    return [deepcopy(claim) for claim in claims if isinstance(claim, dict)]


def source_claim_lookup(config: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    return {
        str(claim.get("fact_id")): claim
        for claim in source_grounded_claims(config)
        if str(claim.get("fact_id") or "")
    }


def source_claims_for(
    config: dict[str, Any] | None,
    *,
    claim_category: str | None = None,
    plan_ids: list[str] | tuple[str, ...] | set[str] | None = None,
    allowed_in_speech: bool | None = None,
) -> list[dict[str, Any]]:
    wanted_plans = {str(plan_id) for plan_id in (plan_ids or []) if str(plan_id or "")}
    matches: list[dict[str, Any]] = []
    for claim in source_grounded_claims(config):
        if claim_category and str(claim.get("claim_category") or "") != claim_category:
            continue
        if allowed_in_speech is not None and bool(claim.get("allowed_in_speech")) is not allowed_in_speech:
            continue
        claim_plans = {str(plan_id) for plan_id in (claim.get("plan_ids") or []) if str(plan_id or "")}
        if wanted_plans and claim_plans and not (wanted_plans & claim_plans):
            continue
        matches.append(claim)
    return matches


def render_source_grounded_claims(
    config: dict[str, Any] | None,
    *,
    claim_category: str | None = None,
    plan_ids: list[str] | tuple[str, ...] | set[str] | None = None,
    limit: int = 3,
    include_caveats: bool = True,
) -> str:
    lines: list[str] = []
    for claim in source_claims_for(
        config,
        claim_category=claim_category,
        plan_ids=plan_ids,
        allowed_in_speech=True,
    )[: max(0, limit)]:
        speech = str(claim.get("normalized_speech_version") or claim.get("claim") or "").strip()
        if not speech:
            continue
        if include_caveats and claim.get("requires_caveat"):
            caveat = str(claim.get("caveat_text") or "").strip()
            if caveat and caveat.lower() not in speech.lower():
                speech = f"{speech} {caveat}"
        lines.append(speech)
    return " ".join(lines)


def close_modes_supported(config: dict[str, Any] | None) -> list[str]:
    modes = _string_list((config or {}).get("close_modes_supported"))
    return [mode for mode in modes if mode in SUPPORTED_CLOSE_MODES]


def plan_catalog(config: dict[str, Any] | None) -> list[dict[str, Any]]:
    catalog = (config or {}).get("plan_catalog") or []
    if not isinstance(catalog, list):
        return []
    return [deepcopy(plan) for plan in catalog if isinstance(plan, dict)]


def plan_record(config: dict[str, Any] | None, plan_id: str) -> dict[str, Any]:
    for plan in plan_catalog(config):
        if str(plan.get("plan_id") or "") == str(plan_id):
            return plan
    return {}


__all__ = [
    "CAMPAIGN_REGISTRY_ID",
    "CampaignConfigNotFoundError",
    "CampaignConfigValidationError",
    "CampaignRegistryError",
    "campaign_registry_entry",
    "close_modes_supported",
    "list_campaign_configs",
    "load_campaign_config",
    "plan_catalog",
    "plan_record",
    "render_source_grounded_claims",
    "resolve_campaign_config",
    "source_claim_lookup",
    "source_claims_for",
    "source_grounded_claims",
    "validate_campaign_config",
    "validate_campaign_registry",
]
