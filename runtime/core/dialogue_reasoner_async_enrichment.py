from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

from runtime.core.dialogue_reasoner_hybrid import (
    HYBRID_REASONING_SCHEMA_FIELDS,
    HYBRID_REASONER_ID,
    PROTECTED_ROUTE_FIELDS,
    parse_hybrid_reasoning_packet,
    render_hybrid_reasoning_prompt,
    score_hybrid_reasoning_case,
    should_call_llm_reasoning,
)


ASYNC_ENRICHMENT_REASONER_ID = "DIALOGUE-REASONER-004"
ASYNC_ENRICHMENT_SCHEMA_VERSION = 1


def response_fingerprint(text: str | None) -> str:
    if not text:
        return ""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _json_fingerprint(payload: dict[str, Any]) -> str:
    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _locked_route(deterministic_reasoning: dict[str, Any]) -> dict[str, Any]:
    return {field: deterministic_reasoning.get(field) for field in sorted(PROTECTED_ROUTE_FIELDS)}


def _response_snapshot(customer_response_text: str | None) -> dict[str, Any]:
    text = customer_response_text or ""
    return {
        "available_before_provider": bool(text.strip()),
        "text_logged": False,
        "text_fingerprint": response_fingerprint(text),
        "char_count": len(text),
        "immutable_by_provider": True,
    }


def async_enrichment_boundary_packet() -> dict[str, Any]:
    return {
        "reasoner_id": ASYNC_ENRICHMENT_REASONER_ID,
        "schema_version": ASYNC_ENRICHMENT_SCHEMA_VERSION,
        "upstream_hybrid_reasoner_id": HYBRID_REASONER_ID,
        "default_enabled": False,
        "provider_calls_made": False,
        "text_sent_to_provider": False,
        "customer_response_blocked_on_provider": False,
        "provider_result_applied_after_response": False,
        "provider_result_received_after_response": False,
        "ignored_by_live_turn": True,
        "runtime_route_override_allowed": False,
        "mutates_final_response": False,
        "protected_route_fields": sorted(PROTECTED_ROUTE_FIELDS),
        "opens_prod_102": False,
    }


def render_async_enrichment_prompt(
    *,
    transcript: str,
    context: dict[str, Any],
    deterministic_reasoning: dict[str, Any],
    case_goal: str = "",
) -> str:
    return render_hybrid_reasoning_prompt(
        transcript=transcript,
        context=context,
        deterministic_reasoning=deterministic_reasoning,
        case_goal=case_goal,
    )


def build_async_enrichment_request(
    *,
    transcript: str,
    context: dict[str, Any],
    deterministic_reasoning: dict[str, Any],
    case_goal: str = "",
    customer_response_text: str | None = None,
    response_packet_id: str | None = None,
) -> dict[str, Any]:
    provider_allowed = should_call_llm_reasoning(deterministic_reasoning)
    prompt = (
        render_async_enrichment_prompt(
            transcript=transcript,
            context=context,
            deterministic_reasoning=deterministic_reasoning,
            case_goal=case_goal,
        )
        if provider_allowed
        else ""
    )
    return {
        "reasoner_id": ASYNC_ENRICHMENT_REASONER_ID,
        "schema_version": ASYNC_ENRICHMENT_SCHEMA_VERSION,
        "upstream_hybrid_reasoner_id": HYBRID_REASONER_ID,
        "status": "queued" if provider_allowed else "not_eligible",
        "blocked_reason": None if provider_allowed else "protected-route-or-boundary",
        "queued_before_provider": provider_allowed,
        "provider_call_allowed": provider_allowed,
        "provider_call_made": False,
        "text_sent_to_provider": False,
        "api_key_value_logged": False,
        "raw_response_stored": False,
        "customer_response_blocked_on_provider": False,
        "provider_result_applied_after_response": False,
        "provider_result_received_after_response": False,
        "ignored_by_live_turn": True,
        "runtime_route_override_allowed": False,
        "mutates_final_response": False,
        "final_response_changed_by_provider": False,
        "opens_prod_102": False,
        "response_packet_id": response_packet_id,
        "customer_response_snapshot": _response_snapshot(customer_response_text),
        "locked_deterministic_route": _locked_route(deterministic_reasoning),
        "deterministic_reasoning_fingerprint": _json_fingerprint(deterministic_reasoning),
        "prompt_char_count": len(prompt),
        "prompt_stored": False,
        "hybrid_schema_fields": list(HYBRID_REASONING_SCHEMA_FIELDS),
    }


def complete_async_enrichment(
    request_packet: dict[str, Any],
    provider_call: dict[str, Any],
    *,
    case: dict[str, Any] | None = None,
    customer_response_text_after_provider: str | None = None,
) -> dict[str, Any]:
    completed = deepcopy(request_packet)
    completed.update(
        {
            "provider_call_made": provider_call.get("provider_calls_made") is True,
            "text_sent_to_provider": provider_call.get("text_sent_to_provider") is True,
            "api_key_value_logged": provider_call.get("api_key_value_logged") is True,
            "latency_ms": provider_call.get("latency_ms"),
            "http_status": provider_call.get("http_status"),
            "usage": provider_call.get("usage") or {},
            "raw_response_stored": provider_call.get("raw_response_stored") is True,
            "provider_result_received_after_response": provider_call.get("provider_calls_made") is True,
            "provider_result_applied_after_response": False,
            "ignored_by_live_turn": True,
            "customer_response_blocked_on_provider": False,
            "runtime_route_override_allowed": False,
            "mutates_final_response": False,
            "opens_prod_102": False,
        }
    )
    before = str((request_packet.get("customer_response_snapshot") or {}).get("text_fingerprint") or "")
    after = response_fingerprint(customer_response_text_after_provider) if customer_response_text_after_provider is not None else before
    completed["final_response_changed_by_provider"] = bool(before and after and before != after)
    if not request_packet.get("provider_call_allowed"):
        completed["status"] = "not_eligible"
        completed["blocked_reason"] = "protected-route-or-boundary"
        return completed
    if provider_call.get("error"):
        completed.update(
            {
                "status": "ignored",
                "error": provider_call["error"],
                "ignored_reason": "provider_error_or_timeout",
                "mismatches": {"provider_error": provider_call["error"]},
            }
        )
        return completed
    try:
        reasoning_packet = parse_hybrid_reasoning_packet(str(provider_call.get("content") or ""))
        scored = score_hybrid_reasoning_case(reasoning_packet, case) if case is not None else {"pass": True, "mismatches": {}}
        completed.update(
            {
                "status": "completed" if scored["pass"] else "failed",
                "hybrid_reasoning": reasoning_packet,
                "pass": scored["pass"],
                "mismatches": scored["mismatches"],
            }
        )
    except Exception as exc:
        completed.update(
            {
                "status": "ignored",
                "error": str(exc),
                "ignored_reason": "parse_or_schema_error",
                "schema_failure_ignored": True,
                "mismatches": {"parse_or_schema_error": str(exc)},
            }
        )
    return completed
