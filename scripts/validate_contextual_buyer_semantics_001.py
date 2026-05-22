#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_live_demo_001_agent_voice_call import (  # noqa: E402
    DEFAULT_CAMPAIGN_ID,
    DEFAULT_CASES_PATH,
    DEFAULT_STAGE,
    build_turn_packet,
)


CHECKPOINT_ID = "CONTEXTUAL-BUYER-SEMANTICS-001"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID


def normalize(text: str) -> str:
    return " ".join("".join(ch.lower() if ch.isalnum() else " " for ch in text).split())


def assert_condition(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def seed_state(
    *,
    previous_response: str,
    transcript: str = "seed",
    selected_gap: str | None = None,
    confirmed_gaps: list[str] | None = None,
    cleared_gaps: list[str] | None = None,
    extra_turns: int = 0,
    continuity_reason: str = "seed_context",
) -> dict[str, Any]:
    turns: list[dict[str, Any]] = []
    for index in range(extra_turns):
        turns.append(
            {
                "transcript": f"seed-{index}",
                "summary": {"final_response": "Seed diagnostic?", "call_control": "continue-call"},
                "continuity": {"applied": True, "reason": "seed_prior_diagnostic", "dialogue_focus": "qualification"},
                "conversation_memory": {
                    "selected_gap": selected_gap,
                    "confirmed_gaps": list(confirmed_gaps or []),
                    "cleared_gaps": list(cleared_gaps or []),
                },
                "dialogue_manager": {},
                "dialogue_pragmatics": {},
            }
        )
    turns.append(
        {
            "transcript": transcript,
            "summary": {"final_response": previous_response, "call_control": "continue-call"},
            "continuity": {
                "applied": True,
                "reason": continuity_reason,
                "dialogue_focus": "qualification" if selected_gap != "timing" else "timing",
                "selected_gap": selected_gap,
            },
            "conversation_memory": {
                "selected_gap": selected_gap,
                "confirmed_gaps": list(confirmed_gaps or []),
                "cleared_gaps": list(cleared_gaps or []),
                "no_pain_topics": list(cleared_gaps or []),
            },
            "dialogue_manager": {},
            "dialogue_pragmatics": {},
        }
    )
    return {"turns": turns}


def build_live_turn(transcript: str, state: dict[str, Any], *, session_id: str) -> dict[str, Any]:
    return build_turn_packet(
        transcript=transcript,
        campaign_id=DEFAULT_CAMPAIGN_ID,
        stage=DEFAULT_STAGE,
        input_type="speech-final",
        silence_count=0,
        cases_path=DEFAULT_CASES_PATH,
        private_out=TMP_DIR,
        live_tts=False,
        force_key_missing=False,
        timeout_seconds=8.0,
        session_id=session_id,
        session_state=state,
        asr_confidence=0.94,
        voice_turn_state="listening",
    )


def response(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("final_response") or "")


def tts_input_text(packet: dict[str, Any]) -> str:
    summary = packet.get("summary") or {}
    packet_tts = ((packet.get("packet") or {}).get("tts_delivery") or {})
    return str(summary.get("tts_input_text") or packet_tts.get("tts_input_text") or "")


def semantic_frame(packet: dict[str, Any]) -> dict[str, Any]:
    manager = packet.get("dialogue_manager") or {}
    return dict(manager.get("contextual_buyer_semantics") or (manager.get("state_before") or {}).get("contextual_buyer_semantics") or {})


def memory(packet: dict[str, Any]) -> dict[str, Any]:
    return dict(packet.get("demo_conversation_memory") or packet.get("conversation_memory") or {})


def manager_source(packet: dict[str, Any]) -> str:
    return str((((packet.get("dialogue_manager") or {}).get("selected_action") or {}).get("source")) or "")


def call_control(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("call_control") or "")


def question_count(text: str) -> int:
    return text.count("?")


def snapshot(packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "transcript": packet.get("transcript"),
        "response": response(packet),
        "tts_input_text": tts_input_text(packet),
        "call_control": call_control(packet),
        "semantic_frame": semantic_frame(packet),
        "manager_source": manager_source(packet),
        "memory": memory(packet),
        "continuity": packet.get("demo_session_continuity") or {},
        "provider_calls_made": bool((packet.get("summary") or {}).get("tts_provider_calls_made")),
        "local_llm_calls_made": bool(((packet.get("dialogue_manager") or {}).get("local_llm_calls_made"))),
    }


def assert_semantic(
    failures: list[str],
    packet: dict[str, Any],
    *,
    expected: str,
    label: str,
    target_gap: str | None = None,
    forbidden_semantics: set[str] | None = None,
) -> None:
    frame = semantic_frame(packet)
    actual = str(frame.get("semantic") or "")
    assert_condition(failures, bool(frame), f"{label}: semantic frame must be exposed in dialogue manager trace.")
    assert_condition(failures, actual == expected, f"{label}: expected semantic `{expected}`, got `{actual}`: {snapshot(packet)}")
    if target_gap is not None:
        assert_condition(failures, frame.get("target_gap") == target_gap, f"{label}: expected target_gap `{target_gap}`: {snapshot(packet)}")
    for forbidden in sorted(forbidden_semantics or set()):
        assert_condition(failures, actual != forbidden, f"{label}: must not classify as `{forbidden}`: {snapshot(packet)}")
    assert_condition(failures, manager_source(packet) == "contextual_buyer_semantics", f"{label}: manager source should be contextual semantics: {snapshot(packet)}")


def assert_spoken_contains(failures: list[str], packet: dict[str, Any], fragments: set[str], label: str) -> None:
    final_text = normalize(response(packet))
    tts_text = normalize(tts_input_text(packet) or response(packet))
    assert_condition(
        failures,
        any(fragment in final_text for fragment in fragments),
        f"{label}: final_response should contain one of {sorted(fragments)}: {response(packet)}",
    )
    assert_condition(
        failures,
        any(fragment in tts_text for fragment in fragments),
        f"{label}: tts_input_text should contain one of {sorted(fragments)}: {tts_input_text(packet)}",
    )


def assert_spoken_excludes(failures: list[str], packet: dict[str, Any], fragments: set[str], label: str) -> None:
    final_text = normalize(response(packet))
    tts_text = normalize(tts_input_text(packet) or response(packet))
    for fragment in sorted(fragments):
        assert_condition(failures, fragment not in final_text, f"{label}: final_response must not contain `{fragment}`: {response(packet)}")
        assert_condition(failures, fragment not in tts_text, f"{label}: tts_input_text must not contain `{fragment}`: {tts_input_text(packet)}")


def validate_context_matrix(failures: list[str], evidence: dict[str, Any]) -> None:
    cases = [
        {
            "label": "no_problem_after_permission",
            "utterance": "no problem",
            "state": seed_state(previous_response="Do you have a minute?"),
            "expected": "permission_acknowledgement",
            "contains": {"thanks", "quick fit check"},
            "excludes": {"workflow review", "what time"},
        },
        {
            "label": "no_problem_after_callback_diagnostic",
            "utterance": "no problem",
            "state": seed_state(
                previous_response="Do missed callbacks create a problem today?",
                selected_gap="callbacks",
                continuity_reason="callback_diagnostic",
            ),
            "expected": "current_gap_clear",
            "target_gap": "callbacks",
            "contains": {"callbacks are fine", "manual tracking", "handoffs"},
            "excludes": {"workflow review", "what time"},
        },
        {
            "label": "no_problem_after_callback_time_request",
            "utterance": "no problem",
            "state": seed_state(
                previous_response="I can call back later. What time should I call back?",
                selected_gap="timing",
                continuity_reason="callback_request_time_needed",
            ),
            "expected": "low_information_continue",
            "contains": {"what time should i call back"},
            "excludes": {"workflow review"},
        },
        {
            "label": "yeah_sure_after_permission",
            "utterance": "yeah sure",
            "state": seed_state(previous_response="Do you have a minute?"),
            "expected": "permission_acknowledgement",
            "contains": {"thanks", "quick fit check"},
        },
        {
            "label": "yeah_sure_after_review_usefulness",
            "utterance": "yeah sure",
            "state": seed_state(
                previous_response="Would a short workflow review be useful for this gap?",
                selected_gap="callbacks",
                confirmed_gaps=["callbacks"],
                continuity_reason="pragmatic_pain_review_offered",
            ),
            "expected": "appointment_review_interest",
            "target_gap": "callbacks",
            "contains": {"what time works", "workflow review"},
        },
        {
            "label": "yeah_sure_after_appointment_time_ask",
            "utterance": "yeah sure",
            "state": seed_state(
                previous_response="What time works for the quick call?",
                selected_gap="callbacks",
                confirmed_gaps=["callbacks"],
                continuity_reason="appointment_time_requested",
            ),
            "expected": "appointment_affirmed_without_time",
            "target_gap": "callbacks",
            "contains": {"need a time", "what time works"},
        },
        {
            "label": "all_clear_after_callback_diagnostic",
            "utterance": "it's all clear",
            "state": seed_state(
                previous_response="Do missed callbacks create a problem today?",
                selected_gap="callbacks",
                continuity_reason="callback_diagnostic",
            ),
            "expected": "current_gap_clear",
            "target_gap": "callbacks",
            "contains": {"callbacks are fine", "manual tracking", "handoffs"},
            "excludes": {"workflow review", "what time"},
        },
        {
            "label": "all_clear_after_manual_tracking_diagnostic",
            "utterance": "it's all clear",
            "state": seed_state(
                previous_response="Does manual tracking slow down demo follow-up today?",
                selected_gap="manual_tracking",
                continuity_reason="manual_tracking_diagnostic",
            ),
            "expected": "current_gap_clear",
            "target_gap": "manual_tracking",
            "contains": {"manual tracking is fine", "callbacks", "handoffs"},
            "excludes": {"workflow review", "what time"},
        },
        {
            "label": "all_clear_after_confirmed_pain",
            "utterance": "it's all clear",
            "state": seed_state(
                previous_response="Does manual tracking slow down demo follow-up today?",
                selected_gap="manual_tracking",
                confirmed_gaps=["callbacks"],
                continuity_reason="manual_tracking_diagnostic",
            ),
            "expected": "current_gap_clear",
            "target_gap": "manual_tracking",
            "contains": {"manual tracking is clear", "missed callbacks", "what time works"},
        },
        {
            "label": "callbacks_are_fine",
            "utterance": "callbacks are fine",
            "state": seed_state(
                previous_response="Do missed callbacks create a problem today?",
                selected_gap="callbacks",
                continuity_reason="callback_diagnostic",
            ),
            "expected": "current_gap_clear",
            "target_gap": "callbacks",
            "forbidden": {"callback_workflow_gap", "pain_confirmed"},
            "contains": {"callbacks are fine", "manual tracking", "handoffs"},
        },
        {
            "label": "manual_tracking_is_fine",
            "utterance": "manual tracking is fine",
            "state": seed_state(
                previous_response="Does manual tracking slow down demo follow-up today?",
                selected_gap="manual_tracking",
                continuity_reason="manual_tracking_diagnostic",
            ),
            "expected": "current_gap_clear",
            "target_gap": "manual_tracking",
            "forbidden": {"manual_tracking_objection", "pain_confirmed"},
            "contains": {"manual tracking is fine", "callbacks", "handoffs"},
        },
        {
            "label": "not_relevant_early",
            "utterance": "not relevant",
            "state": seed_state(previous_response="Do you have a minute?"),
            "expected": "not_relevant_early",
            "contains": {"understood", "stop here"},
            "call_control": "end-call",
            "excludes": {"workflow review", "which part", "what time"},
        },
        {
            "label": "not_relevant_mid_call",
            "utterance": "not relevant",
            "state": seed_state(
                previous_response="Do missed callbacks create a problem today?",
                selected_gap="callbacks",
                continuity_reason="callback_diagnostic",
            ),
            "expected": "not_relevant_mid_call",
            "contains": {"understood", "not an issue at all"},
            "max_questions": 1,
        },
        {
            "label": "not_relevant_late",
            "utterance": "not relevant",
            "state": seed_state(
                previous_response="Do missed callbacks create a problem today?",
                selected_gap="callbacks",
                confirmed_gaps=[],
                cleared_gaps=["callbacks", "manual_tracking"],
                extra_turns=3,
                continuity_reason="callback_diagnostic",
            ),
            "expected": "not_relevant_late",
            "contains": {"understood", "stop here"},
            "call_control": "end-call",
            "excludes": {"workflow review", "what time"},
        },
        {
            "label": "not_clear",
            "utterance": "not clear",
            "state": seed_state(
                previous_response="Do missed callbacks create a problem today?",
                selected_gap="callbacks",
                continuity_reason="callback_diagnostic",
            ),
            "expected": "confusion_not_clear",
            "forbidden": {"all_clear_no_pain", "current_gap_clear"},
            "contains": {"sorry", "i mean"},
            "excludes": {"workflow review", "what time"},
        },
        {
            "label": "not_all_clear",
            "utterance": "not all clear",
            "state": seed_state(
                previous_response="Do missed callbacks create a problem today?",
                selected_gap="callbacks",
                continuity_reason="callback_diagnostic",
            ),
            "expected": "confusion_not_clear",
            "forbidden": {"all_clear_no_pain", "current_gap_clear"},
            "contains": {"sorry", "i mean"},
            "excludes": {"workflow review", "what time"},
        },
        {
            "label": "dont_understand",
            "utterance": "I don't understand",
            "state": seed_state(
                previous_response="Do missed callbacks create a problem today?",
                selected_gap="callbacks",
                continuity_reason="callback_diagnostic",
            ),
            "expected": "confusion_not_clear",
            "contains": {"sorry", "i mean"},
            "excludes": {"workflow review", "what time"},
        },
        {
            "label": "what_do_you_mean_generic",
            "utterance": "what do you mean?",
            "state": seed_state(
                previous_response="Do missed callbacks create a problem today?",
                selected_gap="callbacks",
                continuity_reason="callback_diagnostic",
            ),
            "expected": "previous_question_clarification",
            "contains": {"i mean"},
        },
        {
            "label": "what_do_you_mean_term",
            "utterance": "what do you mean?",
            "state": seed_state(
                previous_response="Growth is the plan for follow-up reminders. Would a short workflow review be useful?",
                selected_gap="callbacks",
                confirmed_gaps=["callbacks"],
                continuity_reason="workflow_review_next_step",
            ),
            "expected": "term_question",
            "contains": {"growth", "routesignal"},
        },
    ]

    for case in cases:
        packet = build_live_turn(case["utterance"], case["state"], session_id=case["label"])
        evidence[case["label"]] = snapshot(packet)
        assert_semantic(
            failures,
            packet,
            expected=case["expected"],
            label=case["label"],
            target_gap=case.get("target_gap"),
            forbidden_semantics=case.get("forbidden"),
        )
        if case.get("contains"):
            assert_spoken_contains(failures, packet, set(case["contains"]), case["label"])
        if case.get("excludes"):
            assert_spoken_excludes(failures, packet, set(case["excludes"]), case["label"])
        if case.get("call_control"):
            assert_condition(
                failures,
                call_control(packet) == case["call_control"],
                f"{case['label']}: expected call_control `{case['call_control']}`: {snapshot(packet)}",
            )
        if case.get("max_questions") is not None:
            assert_condition(
                failures,
                question_count(response(packet)) <= int(case["max_questions"]),
                f"{case['label']}: response should use at most {case['max_questions']} question(s): {response(packet)}",
            )
        assert_condition(failures, not evidence[case["label"]]["provider_calls_made"], f"{case['label']}: provider calls must stay false.")
        assert_condition(failures, not evidence[case["label"]]["local_llm_calls_made"], f"{case['label']}: local LLM calls must stay false.")

    current_clear = evidence["callbacks_are_fine"]["memory"]
    assert_condition(
        failures,
        "callbacks" in set(current_clear.get("cleared_gaps") or []),
        f"callbacks_are_fine: conversation memory should store callbacks as cleared: {current_clear}",
    )
    manual_clear = evidence["manual_tracking_is_fine"]["memory"]
    assert_condition(
        failures,
        "manual_tracking" in set(manual_clear.get("cleared_gaps") or []),
        f"manual_tracking_is_fine: conversation memory should store manual_tracking as cleared: {manual_clear}",
    )
    confirmed_pain = evidence["all_clear_after_confirmed_pain"]["memory"]
    assert_condition(
        failures,
        "callbacks" in set(confirmed_pain.get("confirmed_gaps") or []),
        f"all_clear_after_confirmed_pain: clearing manual tracking must not erase confirmed callbacks: {confirmed_pain}",
    )


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# CONTEXTUAL-BUYER-SEMANTICS-001 Validator",
        "",
        f"- Passed: `{str(payload['passed']).lower()}`",
        f"- Failure count: `{payload['failure_count']}`",
        "- Provider calls made: `false`",
        "- Local LLM calls made: `false`",
        "",
        "## Failures",
        "",
    ]
    if payload["failures"]:
        lines.extend(f"- {failure}" for failure in payload["failures"])
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Matrix",
            "",
            "- Replays the same buyer phrases against different previous-agent-question contexts.",
            "- Requires contextual semantics in the dialogue manager trace.",
            "- Checks both final_response and tts_input_text where TTS dry-run metadata exists.",
            "- Keeps provider and local LLM calls disabled.",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    failures: list[str] = []
    evidence: dict[str, Any] = {}
    validate_context_matrix(failures, evidence)

    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "passed": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "provider_calls_made": False,
        "local_llm_calls_made": False,
        "opens_prod_102": False,
        "evidence": evidence,
    }
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    REPORT_PATH.write_text(render_report(payload), encoding="utf-8")
    if failures:
        raise AssertionError(f"{CHECKPOINT_ID} failed with {len(failures)} issue(s). See {RESULT_PATH}.")
    print(f"{CHECKPOINT_ID} validation passed.")


if __name__ == "__main__":
    main()
