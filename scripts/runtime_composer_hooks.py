#!/usr/bin/env python3
from __future__ import annotations

from typing import Any


HOOK_SURFACE = "candidate_response_wording_only"


def _text_blob(*parts: Any) -> str:
    return " ".join(str(part or "") for part in parts).lower()


def _hint_blob(advisory_hints: list[dict[str, Any]]) -> str:
    return _text_blob(
        *[
            " ".join(
                [
                    str(hint.get("item_id", "")),
                    str(hint.get("hint", "")),
                    str(hint.get("guardrail", "")),
                ]
            )
            for hint in advisory_hints
        ]
    )


def _contains_any(text: str, tokens: list[str]) -> bool:
    return any(token in text for token in tokens)


def _disabled_packet(enabled: bool, blocked_reason: str = "") -> dict[str, Any]:
    return {
        "enabled": enabled,
        "status": "disabled" if not enabled else "blocked",
        "applied": False,
        "hook_id": "",
        "hook_name": "",
        "hook_basis": [],
        "blocked_reason": blocked_reason,
        "protected_context_preserved": False,
        "no_evaluation_labels_used": True,
        "allowed_runtime_surface": HOOK_SURFACE,
        "original_candidate_response": "",
        "final_candidate_response": "",
    }


def _not_applicable_packet(
    candidate_response: str,
    *,
    protected_context_preserved: bool = False,
    blocked_reason: str = "",
) -> dict[str, Any]:
    return {
        "enabled": True,
        "status": "not_applicable" if not blocked_reason else "blocked",
        "applied": False,
        "hook_id": "",
        "hook_name": "",
        "hook_basis": [],
        "blocked_reason": blocked_reason,
        "protected_context_preserved": protected_context_preserved,
        "no_evaluation_labels_used": True,
        "allowed_runtime_surface": HOOK_SURFACE,
        "original_candidate_response": candidate_response,
        "final_candidate_response": candidate_response,
    }


def _applied_packet(
    *,
    hook_id: str,
    hook_name: str,
    hook_basis: list[str],
    candidate_response: str,
    hooked_response: str,
) -> dict[str, Any]:
    return {
        "enabled": True,
        "status": "applied",
        "applied": True,
        "hook_id": hook_id,
        "hook_name": hook_name,
        "hook_basis": hook_basis,
        "blocked_reason": "",
        "protected_context_preserved": False,
        "no_evaluation_labels_used": True,
        "allowed_runtime_surface": HOOK_SURFACE,
        "original_candidate_response": candidate_response,
        "final_candidate_response": hooked_response,
    }


def _is_generic_candidate(candidate_response: str) -> bool:
    text = candidate_response.lower()
    return _contains_any(
        text,
        [
            "price, fit, timing, or exact product details",
            "concrete reason for reaching out",
        ],
    )


def _protected_context(decision: dict[str, Any], retrieval: dict[str, Any]) -> bool:
    flags = set(str(flag) for flag in retrieval.get("context_flags", []))
    if flags.intersection({"do_not_call", "customer_refusal", "human_escalation", "protected_script"}):
        return True
    if str(decision.get("call_control", "")) in {"end-call", "hang-up", "transfer-or-escalate"}:
        return True
    if str(decision.get("next_action", "")) in {"suppress-contact", "escalate", "transfer-or-escalate"}:
        return True
    return False


def _hook_basis(transcript_signal: bool, advisory_signal: bool) -> list[str]:
    basis: list[str] = []
    if transcript_signal:
        basis.append("transcript_signal")
    if advisory_signal:
        basis.append("retrieval_advisory_hint")
    return basis


def choose_runtime_composer_hook(
    *,
    transcript: str,
    candidate_response: str,
    advisory_hints: list[dict[str, Any]],
) -> tuple[str, str, list[str]] | None:
    transcript_text = transcript.lower()
    hints = _hint_blob(advisory_hints)
    combined = f"{transcript_text} {hints}"

    price_signal = _contains_any(
        transcript_text,
        ["too_expensive", "too expensive", "price", "pricing", "cost", "expensive", "worth", "terms"],
    )
    price_hint = _contains_any(hints, ["objection", "price", "pricing", "cost", "compare"])
    if price_signal and price_hint:
        if "timeline" in transcript_text or "timing" in transcript_text:
            return (
                "price_objection_clarifier",
                "That makes sense. Is the bigger concern the cost, the value you would get back, or the timing for reviewing it?",
                _hook_basis(True, True),
            )
        return (
            "price_objection_clarifier",
            "That makes sense. Is the bigger concern the price, the terms, or whether the value is worth reviewing now?",
            _hook_basis(True, True),
        )

    callback_signal = _contains_any(
        transcript_text,
        ["time to think", "do not rush", "don't rush", "callback", "call back", "later", "not now"],
    )
    callback_hint = _contains_any(hints, ["timing", "callback", "pause", "freedom", "no next step"])
    if callback_signal and callback_hint:
        return (
            "callback_request_low_commitment",
            "That makes sense. Would a brief callback later help, or should we first clarify fit, timing, or anything you need verified before reviewing it?",
            _hook_basis(True, True),
        )

    commitment_signal = _contains_any(
        transcript_text,
        ["locked into", "commitment", "contract", "eligibility", "eligible", "fit", "before any close"],
    )
    commitment_hint = _contains_any(combined, ["commitment", "eligibility", "fit", "objection", "autonomy"])
    if commitment_signal and commitment_hint:
        return (
            "sale_eligible_fit_check",
            "That makes sense. Before any commitment, should we confirm fit, timing, or eligibility for your situation?",
            _hook_basis(True, True),
        )

    trust_signal = _contains_any(transcript_text, ["trust", "legitimate", "real company", "verify"])
    trust_hint = _contains_any(hints, ["trust", "proof", "evidence", "company context"])
    if trust_signal and trust_hint:
        return (
            "trust_repair_verification",
            "Fair. I can keep this low-pressure: should I share what can be verified about the company, or would you prefer a specialist follow-up?",
            _hook_basis(True, True),
        )

    return None


def apply_runtime_composer_hooks(
    candidate_response: str,
    *,
    enabled: bool,
    decision: dict[str, Any],
    transcript: str,
    retrieval: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    if not enabled:
        packet = _disabled_packet(False)
        packet["original_candidate_response"] = candidate_response
        packet["final_candidate_response"] = candidate_response
        return candidate_response, packet

    if retrieval.get("enabled") is not True:
        packet = _disabled_packet(True, "retrieval_not_enabled")
        packet["original_candidate_response"] = candidate_response
        packet["final_candidate_response"] = candidate_response
        return candidate_response, packet

    if _protected_context(decision, retrieval):
        return candidate_response, _not_applicable_packet(
            candidate_response,
            protected_context_preserved=True,
            blocked_reason="protected_context",
        )

    if retrieval.get("status") != "retrieved" or not retrieval.get("advisory_hints"):
        return candidate_response, _not_applicable_packet(candidate_response, blocked_reason="no_retrieved_hints")

    if not _is_generic_candidate(candidate_response):
        return candidate_response, _not_applicable_packet(candidate_response)

    selected = choose_runtime_composer_hook(
        transcript=transcript,
        candidate_response=candidate_response,
        advisory_hints=list(retrieval.get("advisory_hints", [])),
    )
    if selected is None:
        return candidate_response, _not_applicable_packet(candidate_response)

    hook_id, hooked_response, hook_basis = selected
    hook_names = {
        "price_objection_clarifier": "price objection clarifier",
        "callback_request_low_commitment": "callback request low commitment",
        "sale_eligible_fit_check": "sale eligible fit check",
        "trust_repair_verification": "trust repair verification",
    }
    return hooked_response, _applied_packet(
        hook_id=hook_id,
        hook_name=hook_names[hook_id],
        hook_basis=hook_basis,
        candidate_response=candidate_response,
        hooked_response=hooked_response,
    )
