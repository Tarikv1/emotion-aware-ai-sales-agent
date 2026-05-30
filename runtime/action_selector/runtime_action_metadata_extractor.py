from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.action_selector.action_selector_contract import action_labels
from runtime.action_selector.runtime_action_metadata_contract import (
    FALSE_BOUNDARY_FIELDS,
    RuntimeActionMetadata,
    RUNTIME_ACTION_METADATA_FIELDS,
)


MAP_PATH = Path(__file__).resolve().parent / "runtime_to_action_label_map.json"


def _string(value: Any) -> str:
    return str(value or "").strip()


def _lower(value: Any) -> str:
    return _string(value).casefold()


def _read_map() -> dict[str, Any]:
    payload = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _values_for_key(payload: Any, key: str) -> list[Any]:
    values: list[Any] = []
    if isinstance(payload, dict):
        for item_key, item_value in payload.items():
            if item_key == key:
                values.append(item_value)
            values.extend(_values_for_key(item_value, key))
    elif isinstance(payload, list):
        for item in payload:
            values.extend(_values_for_key(item, key))
    return values


def _first_scalar(payload: Any, keys: tuple[str, ...]) -> str:
    for key in keys:
        for value in _values_for_key(payload, key):
            if isinstance(value, (str, int, float, bool)) and _string(value):
                return _string(value)
    return ""


def _all_scalar_text(payload: Any) -> str:
    values: list[str] = []
    if isinstance(payload, dict):
        for value in payload.values():
            values.append(_all_scalar_text(value))
    elif isinstance(payload, list):
        for value in payload:
            values.append(_all_scalar_text(value))
    elif isinstance(payload, (str, int, float, bool)):
        values.append(_string(payload))
    return " ".join(value for value in values if value)


def _contains_any(value: str, needles: list[str]) -> bool:
    text = _lower(value)
    return any(_lower(needle) in text for needle in needles)


def _response_text(runtime_result: dict[str, Any]) -> str:
    return _first_scalar(
        runtime_result,
        (
            "agent_response",
            "candidate_response",
            "final_response",
            "bridge_response",
            "response",
            "response_text",
        ),
    )


def _response_hash(text: str) -> str:
    if not text:
        return ""
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _metadata_available(runtime_result: dict[str, Any]) -> bool:
    if not runtime_result:
        return False
    return any(
        _values_for_key(runtime_result, key)
        for key in (
            "runtime_decision",
            "semantic_frame",
            "action_id",
            "semantic",
            "next_action",
            "next_commercial_action",
            "buyer_decision_stage",
            "current_buyer_question_type",
            "response_strategy",
        )
    )


def _combined(*parts: str) -> str:
    return " | ".join(part for part in parts if part)


def _build_unmapped_metadata(runtime_result: dict[str, Any], turn_context: dict[str, Any] | None) -> dict[str, Any]:
    context = dict(turn_context or {})
    source = deepcopy(runtime_result)
    response_text = _response_text(source)
    all_text = _all_scalar_text(source)
    sales_move = _combined(
        _first_scalar(source, ("runtime_action_hint", "action_id", "semantic", "next_action", "next_commercial_action", "dialogue_focus")),
        _first_scalar(source, ("current_buyer_question_type", "last_objection_handled", "commercial_intent")),
    )
    decision_stage = _combined(
        _first_scalar(source, ("buyer_decision_stage", "commercial_stage", "current_buyer_question_type", "response_mode")),
        _first_scalar(source, ("sales_difficulty", "interest_state")),
    )
    recommended_path = _combined(
        _first_scalar(source, ("runtime_recommended_path", "openai_recommended_path", "last_recommendation_given", "recommended_path")),
        _first_scalar(source, ("buyer_fit_level", "recommendation_confidence")),
    )
    active_frame = _combined(
        _first_scalar(source, ("active_decision_frame", "decision_frame")),
        _first_scalar(source, ("target_topic", "target_gap")),
    )
    safety_boundary = _contains_any(all_text, ["boundary", "cannot send", "cannot book", "cannot create", "crm", "calendar", "payment", "raw url"])
    terminal_state = _contains_any(all_text, ["terminal", "end_call_stop_request", "stop here", "goodbye"])
    no_fit_state = _contains_any(all_text, ["no_fit", "wrong_product", "free_enough", "not_interested", "low_intent", "buyer_fit_level low"])
    if _contains_any(all_text, ["already_told", "already told"]):
        repair_state = "already_told_you"
    elif _contains_any(all_text, ["asr", "uncertain_tool", "ambiguous_tool"]):
        repair_state = "asr_uncertainty"
    elif _contains_any(all_text, ["correction", "buyer_correction"]):
        repair_state = "buyer_correction"
    elif _contains_any(all_text, ["repeat", "duplicate", "avoid_repetition"]):
        repair_state = "avoid_repetition"
    else:
        repair_state = ""
    source_grounding = ""
    explicit_source_signal_text = _combined(sales_move, decision_stage, recommended_path, active_frame)
    if _contains_any(explicit_source_signal_text, ["source", "affiliation", "official"]):
        source_grounding = "public_or_source_grounded"

    return RuntimeActionMetadata(
        runtime_metadata_available=_metadata_available(source),
        campaign_id=_first_scalar(source, ("campaign_id",)) or _string(context.get("campaign_id")),
        turn_id=_first_scalar(source, ("turn_id", "case_id", "replay_case_id")) or _string(context.get("turn_id")),
        runtime_response_text_available=bool(response_text),
        runtime_response_text_hash=_response_hash(response_text),
        runtime_call_control=_first_scalar(source, ("call_control",)),
        runtime_decision_stage=decision_stage,
        runtime_sales_move=sales_move,
        runtime_response_strategy=_combined(
            _first_scalar(source, ("response_strategy", "selected_strategy")),
            _first_scalar(source, ("response_variation_key",)),
        ),
        runtime_recommended_path=recommended_path,
        runtime_active_decision_frame=active_frame,
        runtime_safety_boundary=safety_boundary,
        runtime_terminal_state=terminal_state,
        runtime_no_fit_state=no_fit_state,
        runtime_repair_state=repair_state,
        runtime_source_grounding_state=source_grounding,
        extraction_warnings=[] if source else ["runtime_result_missing"],
    ).to_dict()


def _field(metadata: dict[str, Any], field: str) -> str:
    if field == "_all_signal_text":
        return _all_scalar_text(metadata)
    return _string(metadata.get(field))


def _mapping_matches(metadata: dict[str, Any], required: dict[str, Any]) -> bool:
    for field in required.get("flag_true", []):
        if metadata.get(field) is not True:
            return False
    for field in required.get("flag_false", []):
        if metadata.get(field) is not False:
            return False
    equals = required.get("field_equals") if isinstance(required.get("field_equals"), dict) else {}
    for field, values in equals.items():
        allowed = values if isinstance(values, list) else [values]
        if _lower(metadata.get(field)) not in {_lower(value) for value in allowed}:
            return False
    contains = required.get("field_contains_any") if isinstance(required.get("field_contains_any"), dict) else {}
    if contains:
        matched_any_field = False
        for field, needles in contains.items():
            needle_list = needles if isinstance(needles, list) else [needles]
            if _contains_any(_field(metadata, field), [str(item) for item in needle_list]):
                matched_any_field = True
        if not matched_any_field:
            return False
    not_contains = required.get("field_not_contains_any") if isinstance(required.get("field_not_contains_any"), dict) else {}
    for field, needles in not_contains.items():
        needle_list = needles if isinstance(needles, list) else [needles]
        if _contains_any(_field(metadata, field), [str(item) for item in needle_list]):
            return False
    return True


def map_runtime_metadata_to_action_id(metadata: dict[str, Any]) -> dict[str, Any]:
    if metadata.get("runtime_metadata_available") is not True:
        return {
            "runtime_action_id": "",
            "runtime_action_confidence": 0.0,
            "runtime_action_reason": "runtime_metadata_unavailable",
        }
    mappings = _read_map().get("mappings")
    if isinstance(mappings, list):
        for entry in mappings:
            if not isinstance(entry, dict):
                continue
            required = entry.get("required_conditions") if isinstance(entry.get("required_conditions"), dict) else {}
            action_id = _string(entry.get("selector_action_id"))
            if action_id in action_labels() and _mapping_matches(metadata, required):
                return {
                    "runtime_action_id": action_id,
                    "runtime_action_confidence": float(entry.get("confidence") or 0.0),
                    "runtime_action_reason": _string(entry.get("mapping_id") or entry.get("notes")),
                }
    direct = _first_controlled_action_id(metadata)
    if direct:
        return {
            "runtime_action_id": direct,
            "runtime_action_confidence": 0.7,
            "runtime_action_reason": "direct_controlled_action_id_signal",
        }
    return {
        "runtime_action_id": "",
        "runtime_action_confidence": 0.0,
        "runtime_action_reason": "no_runtime_mapping_matched",
    }


def _first_controlled_action_id(metadata: dict[str, Any]) -> str:
    labels = set(action_labels())
    for field in ("runtime_sales_move", "runtime_decision_stage", "runtime_response_strategy"):
        for token in _field(metadata, field).replace("|", " ").split():
            normalized = token.strip()
            if normalized in labels:
                return normalized
    return ""


def extract_runtime_action_metadata(runtime_result: dict, turn_context: dict | None = None) -> dict:
    try:
        source = deepcopy(runtime_result) if isinstance(runtime_result, dict) else {}
        metadata = _build_unmapped_metadata(source, turn_context)
        mapping = map_runtime_metadata_to_action_id(metadata)
        metadata.update(mapping)
        warnings = list(metadata.get("extraction_warnings") or [])
        if metadata.get("runtime_metadata_available") is True and not metadata.get("runtime_action_id"):
            warnings.append("runtime_action_id_unmapped")
        metadata["extraction_warnings"] = warnings
        return metadata
    except Exception as exc:
        failed = RuntimeActionMetadata(
            runtime_metadata_available=False,
            extraction_warnings=[f"runtime_action_metadata_extraction_failed:{type(exc).__name__}"],
        ).to_dict()
        failed["runtime_action_reason"] = "extraction_failed"
        return failed


def validate_runtime_action_metadata(metadata: dict) -> list[str]:
    failures: list[str] = []
    missing = sorted(set(RUNTIME_ACTION_METADATA_FIELDS) - set(metadata))
    if missing:
        failures.append(f"missing_runtime_metadata_fields:{missing}")
    for key in FALSE_BOUNDARY_FIELDS:
        if metadata.get(key) is not False:
            failures.append(f"{key}_must_be_false")
    action_id = _string(metadata.get("runtime_action_id"))
    if action_id and action_id not in action_labels():
        failures.append(f"runtime_action_id_not_controlled:{action_id}")
    if metadata.get("runtime_response_text_available") is True and not metadata.get("runtime_response_text_hash"):
        failures.append("runtime_response_text_hash_required")
    forbidden_raw_keys = {"response_text", "agent_response", "candidate_response", "final_response", "buyer_utterance_text"}
    present = sorted(forbidden_raw_keys & set(metadata))
    if present:
        failures.append(f"metadata_contains_raw_text_keys:{present}")
    return failures


def redact_runtime_metadata_for_public_evidence(metadata: dict) -> dict:
    redacted = deepcopy(metadata)
    for key in ("response_text", "agent_response", "candidate_response", "final_response", "buyer_utterance_text"):
        redacted.pop(key, None)
    redacted["raw_private_data"] = False
    return redacted
