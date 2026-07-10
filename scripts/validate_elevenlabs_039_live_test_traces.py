#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


EXPECTED_AGENT_ID = "agent_7801kt0g32zxf4f8x5zkykj7syty"
CHECKPOINT_ID = "ELEVENLABS-039-end-call-edge-case-hardening"
EXPECTED_TESTS = {
    "sim_039_hard_stop_overrides_pending_email": {
        "name": f"{CHECKPOINT_ID}::sim_039_hard_stop_overrides_pending_email",
        "reason": "Buyer requested no further contact",
        "message": "Got it. Take care.",
        "critical": ("remove me", "don't call again"),
        "kind": "hard_stop",
    },
    "sim_039_delivery_timing_not_repeated": {
        "name": f"{CHECKPOINT_ID}::sim_039_delivery_timing_not_repeated",
        "reason": "Buyer explicitly ended the completed conversation",
        "message": "Take care.",
        "kind": "delivery",
    },
    "sim_039_gatekeeper_callback_atomic_end_call": {
        "name": f"{CHECKPOINT_ID}::sim_039_gatekeeper_callback_atomic_end_call",
        "reason": "Gatekeeper callback window confirmed",
        "message": "Got it, I'll try then. Take care.",
        "critical": ("owner is usually available tomorrow morning",),
        "kind": "callback",
    },
    "sim_039_gatekeeper_note_atomic_end_call": {
        "name": f"{CHECKPOINT_ID}::sim_039_gatekeeper_note_atomic_end_call",
        "reason": "Gatekeeper note completed",
        "message": "Got it, thank you. Take care.",
        "critical": ("i'll let the owner know emma from atlas called about the mockup",),
        "kind": "note",
    },
}
TIMING_TEXT = "Great, I'll send it there by the end of the day."
DELIVERY_CONFIRMATION = "Yes, that's right."
DELIVERY_GOODBYE = "Okay, thanks, bye."
SEND_LANGUAGE_RE = re.compile(r"\b(?:send|sending|sent|email|e-mail|deliver|delivery|mockup)\b", re.IGNORECASE)
CALLBACK_NOTE_FORBIDDEN_RE = re.compile(
    r"\b(?:pitch|email|e-mail|send|mockup|callback|call back|follow[- ]?up|owner|available|tomorrow|website)\b",
    re.IGNORECASE,
)


class Checks:
    def __init__(self) -> None:
        self.assertions: list[dict[str, Any]] = []
        self.failures: list[str] = []

    def check(self, name: str, condition: bool, detail: str) -> None:
        item: dict[str, Any] = {"name": name, "passed": bool(condition)}
        if not condition:
            item["detail"] = detail
            self.failures.append(f"{name}: {detail}")
        self.assertions.append(item)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON input {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("input must contain a JSON object")
    return value


def capture_payload(document: dict[str, Any]) -> dict[str, Any]:
    payload = document.get("payload", document)
    if not isinstance(payload, dict):
        raise ValueError("input payload must be a JSON object")
    stored_hash = document.get("payload_sha256")
    if stored_hash:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        actual_hash = hashlib.sha256(canonical).hexdigest()
        if stored_hash != actual_hash:
            raise ValueError("payload_sha256 does not match the sanitized payload")
    return payload


def text(event: dict[str, Any]) -> str:
    value = event.get("message")
    return value if isinstance(value, str) else ""


def role(event: dict[str, Any]) -> str:
    return str(event.get("role", "")).lower()


def as_list(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def event_calls(event: dict[str, Any]) -> list[dict[str, Any]]:
    return as_list(event.get("tool_calls"))


def event_results(event: dict[str, Any]) -> list[dict[str, Any]]:
    return as_list(event.get("tool_results"))


def tool_name(item: dict[str, Any]) -> str:
    return str(item.get("tool_name") or item.get("name") or item.get("tool") or "").lower()


def request_id(item: dict[str, Any]) -> str:
    return str(item.get("request_id") or item.get("tool_call_id") or "")


def is_end_call(item: dict[str, Any]) -> bool:
    return tool_name(item) in {"end_call", "system__end_call"}


def has_tool_event(event: dict[str, Any]) -> bool:
    return bool(event_calls(event) or event_results(event))


def successful_result(item: dict[str, Any]) -> bool:
    if item.get("blocked") is True or item.get("is_blocked") is True or item.get("is_error") is True or item.get("success") is False:
        return False
    if item.get("error") not in (None, "", [], {}):
        return False
    if str(item.get("status", "")).lower() in {"error", "failed", "blocked", "pending"}:
        return False
    if item.get("success") is True:
        return True
    for key in ("result", "response", "output"):
        if key in item and item[key] not in (None, "", [], {}):
            return True
    return False


def parse_end_call(call: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    params = call.get("params_as_json")
    if not isinstance(params, str):
        return None, "end_call params_as_json is missing or not a string"
    try:
        parsed = json.loads(params)
    except json.JSONDecodeError as exc:
        return None, f"end_call params_as_json is invalid JSON: {exc.msg}"
    if not isinstance(parsed, dict):
        return None, "end_call params_as_json must decode to an object"
    return parsed, None


def find_critical_index(events: list[dict[str, Any]], item: dict[str, Any]) -> int | None:
    if item.get("kind") == "delivery":
        for index in range(len(events) - 1, -1, -1):
            if role(events[index]) == "user" and text(events[index]) == DELIVERY_GOODBYE:
                return index
        return None
    needles = tuple(str(value).lower() for value in item.get("critical", ()))
    if not needles:
        return None
    for index in range(len(events) - 1, -1, -1):
        if role(events[index]) == "user" and all(needle in text(events[index]).lower() for needle in needles):
            return index
    return None


def all_trace_calls(events: list[dict[str, Any]]) -> list[tuple[int, dict[str, Any]]]:
    return [(index, call) for index, event in enumerate(events) for call in event_calls(event)]


def validate_terminal_structure(
    checks: Checks,
    events: list[dict[str, Any]],
    expected: dict[str, Any],
) -> tuple[int | None, int | None, dict[str, Any] | None]:
    calls = all_trace_calls(events)
    end_calls = [(index, call) for index, call in calls if is_end_call(call)]
    checks.check("exactly_one_end_call", len(end_calls) == 1, f"found {len(end_calls)} end_call calls")
    checks.check("no_additional_tool_call", len(calls) == 1, f"found {len(calls)} total tool calls")
    if not end_calls:
        return None, None, None

    call_index, call = end_calls[0]
    checks.check("built_in_system_end_call", str(call.get("type", "")).lower() == "system", "end_call is not type system")
    checks.check("tool_was_called", call.get("tool_has_been_called") is not False, "tool_has_been_called is false")
    params, params_error = parse_end_call(call)
    checks.check("parse_params_as_json", params is not None, params_error or "invalid params")
    if params is None:
        return call_index, None, None
    checks.check(
        "exact_reason",
        params.get("reason") == expected["reason"],
        f"expected {expected['reason']!r}, got {params.get('reason')!r}",
    )
    checks.check(
        "exact_system_message_to_speak",
        params.get("system__message_to_speak") == expected["message"],
        f"expected {expected['message']!r}, got {params.get('system__message_to_speak')!r}",
    )

    matching_results = [
        (index, result)
        for index, event in enumerate(events)
        for result in event_results(event)
        if request_id(result) and request_id(result) == request_id(call)
    ]
    successful = [(index, result) for index, result in matching_results if successful_result(result)]
    all_results = [result for event in events for result in event_results(event)]
    checks.check("no_additional_tool_result", len(all_results) == 1, f"found {len(all_results)} total tool results")
    checks.check(
        "matching_successful_tool_result",
        len(successful) == 1 and bool(request_id(call)),
        f"expected one successful result for request_id {request_id(call)!r}, found {len(successful)}",
    )
    checks.check(
        "no_error_or_block",
        bool(successful) and all(successful_result(result) for _, result in matching_results),
        "matching tool result is missing, errored, blocked, or pending",
    )
    result_index = successful[0][0] if len(successful) == 1 else None
    if len(successful) == 1:
        result_payload = successful[0][1].get("result")
        checks.check(
            "successful_end_call_result_payload",
            isinstance(result_payload, dict)
            and result_payload.get("result_type") == "end_call_success"
            and result_payload.get("status") == "success"
            and result_payload.get("reason") == expected["reason"],
            "tool result payload must be end_call_success with the exact terminal reason",
        )

    if result_index is not None:
        later_events = events[result_index + 1 :]
        checks.check(
            "no_text_or_tool_after_result",
            not any(text(event) or has_tool_event(event) for event in later_events),
            "trace contains text or a tool event after the successful end_call result",
        )

    rendered_index = call_index - 1
    rendered = events[rendered_index] if rendered_index >= 0 else {}
    checks.check(
        "direct_preceding_rendered_tool_message",
        rendered_index >= 0
        and role(rendered) == "agent"
        and text(rendered) == expected["message"]
        and not has_tool_event(rendered),
        "the directly preceding agent event is not exactly the tool-bound message",
    )
    return call_index, result_index, params


def validate_terminal_gap(
    checks: Checks,
    events: list[dict[str, Any]],
    expected: dict[str, Any],
    call_index: int | None,
    critical_index: int | None,
) -> None:
    if call_index is None or critical_index is None:
        checks.check("critical_buyer_turn_found", False, "critical buyer turn or end_call is missing")
        return
    checks.check(
        "critical_buyer_turn_is_terminal_trigger",
        role(events[critical_index]) == "user",
        "critical turn is not a user event",
    )
    failures: list[str] = []
    allowed_index = call_index - 1
    for index in range(critical_index + 1, call_index):
        event = events[index]
        if index == allowed_index and role(event) == "agent" and text(event) == expected["message"] and not has_tool_event(event):
            continue
        if text(event) or has_tool_event(event) or role(event) in {"agent", "assistant", "user"}:
            failures.append(f"event {index} is not the permitted rendered tool message")
    checks.check("no_standalone_assistant_or_tool_between_trigger_and_end_call", not failures, "; ".join(failures) or "")


def validate_hard_stop(checks: Checks, events: list[dict[str, Any]], critical_index: int | None, result_index: int | None) -> None:
    if critical_index is None:
        checks.check("hard_stop_trigger_found", False, "hard-stop buyer turn not found")
        return
    end = result_index if result_index is not None else len(events)
    post_stop_messages = [text(event) for event in events[critical_index + 1 : end + 1] if text(event)]
    checks.check(
        "hard_stop_has_no_email_or_send_language_after_stop",
        not any(SEND_LANGUAGE_RE.search(message) for message in post_stop_messages),
        "email, delivery, mockup, or send language appears after the hard stop",
    )


def validate_delivery(checks: Checks, events: list[dict[str, Any]], call_index: int | None, params: dict[str, Any] | None) -> None:
    confirmation_indices = [index for index, event in enumerate(events) if role(event) == "user" and text(event) == DELIVERY_CONFIRMATION]
    checks.check("exact_email_confirmation_found", len(confirmation_indices) == 1, f"found {len(confirmation_indices)} exact confirmations")
    if len(confirmation_indices) != 1 or call_index is None:
        return
    confirmation_index = confirmation_indices[0]
    timing_index = confirmation_index + 1
    goodbye_index = confirmation_index + 2
    timing_event = events[timing_index] if timing_index < len(events) else {}
    goodbye_event = events[goodbye_index] if goodbye_index < len(events) else {}
    checks.check(
        "exact_post_confirmation_timing_without_tool",
        role(timing_event) == "agent" and text(timing_event) == TIMING_TEXT and not has_tool_event(timing_event),
        "exact delivery timing-only agent event is missing after confirmation",
    )
    checks.check(
        "exact_buyer_goodbye_after_timing",
        role(goodbye_event) == "user" and text(goodbye_event) == DELIVERY_GOODBYE,
        "exact buyer goodbye does not directly follow the timing event",
    )
    post_confirmation_timing = [
        text(event)
        for event in events[confirmation_index + 1 :]
        if role(event) in {"agent", "assistant"} and TIMING_TEXT in text(event)
    ]
    checks.check(
        "timing_appears_once_post_confirmation",
        post_confirmation_timing == [TIMING_TEXT],
        f"expected one post-confirmation timing line, found {len(post_confirmation_timing)}",
    )
    serialized_params = json.dumps(params or {}, ensure_ascii=True)
    checks.check("timing_not_in_final_tool_params", TIMING_TEXT not in serialized_params, "delivery timing appears in final tool params")
    checks.check("delivery_tool_has_no_extra_text_turn", call_index == goodbye_index + 2, "terminal tool call is not immediately after the rendered final message")


def validate_callback_or_note(checks: Checks, events: list[dict[str, Any]], critical_index: int | None, call_index: int | None, kind: str) -> None:
    if critical_index is None or call_index is None:
        return
    forbidden: list[str] = []
    for index in range(critical_index + 1, call_index):
        message = text(events[index])
        if role(events[index]) in {"agent", "assistant"} and index != call_index - 1 and message:
            forbidden.append(f"event {index} contains an extra assistant turn")
        if message and CALLBACK_NOTE_FORBIDDEN_RE.search(message) and index != call_index - 1:
            forbidden.append(f"event {index} contains pitch, email, or callback language")
    checks.check(
        f"{kind}_has_no_pre_terminal_pitch_email_or_callback_ask",
        not forbidden,
        "; ".join(forbidden) or "",
    )


def validate_run(run: dict[str, Any]) -> dict[str, Any]:
    test_id = str(run.get("test_id", ""))
    expected = EXPECTED_TESTS.get(test_id)
    checks = Checks()
    if expected is None:
        return {
            "test_id": test_id,
            "test_name": run.get("test_name"),
            "test_run_id": run.get("test_run_id"),
            "independent_status": "fail",
            "assertions": [{"name": "expected_test_id", "passed": False, "detail": "unexpected test id"}],
            "failures": ["expected_test_id: unexpected test id"],
            "provider_status": run.get("status"),
            "provider_condition_result": run.get("condition_result"),
        }
    checks.check("expected_test_name", run.get("test_name") == expected["name"], f"expected {expected['name']!r}")
    events = run.get("agent_responses")
    checks.check("ordered_agent_responses_present", isinstance(events, list), "agent_responses is not a list")
    if not isinstance(events, list):
        events = []
    events = [event for event in events if isinstance(event, dict)]
    critical_index = find_critical_index(events, expected)
    checks.check("critical_buyer_turn_found", critical_index is not None, "critical buyer turn not found")
    call_index, result_index, params = validate_terminal_structure(checks, events, expected)
    validate_terminal_gap(checks, events, expected, call_index, critical_index)
    if expected["kind"] == "hard_stop":
        validate_hard_stop(checks, events, critical_index, result_index)
    elif expected["kind"] == "delivery":
        validate_delivery(checks, events, call_index, params)
    else:
        validate_callback_or_note(checks, events, critical_index, call_index, expected["kind"])
    return {
        "test_id": test_id,
        "test_name": run.get("test_name"),
        "test_run_id": run.get("test_run_id"),
        "independent_status": "pass" if not checks.failures else "fail",
        "provider_status": run.get("status"),
        "provider_condition_result": run.get("condition_result"),
        "provider_evaluator_rationale": run.get("evaluator_rationale"),
        "assertions": checks.assertions,
        "failures": checks.failures,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate sanitized ELEVENLABS-039 live test traces without trusting provider verdicts.")
    parser.add_argument("--input", required=True, type=Path, help="Sanitized capture JSON path")
    parser.add_argument("--output", type=Path, help="Optional JSON path for the independent validation summary")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    global_failures: list[str] = []
    try:
        document = read_json(args.input)
        payload = capture_payload(document)
        if payload.get("agent_id") != EXPECTED_AGENT_ID:
            global_failures.append(f"agent_id must be {EXPECTED_AGENT_ID}")
        runs = payload.get("test_runs")
        if not isinstance(runs, list):
            raise ValueError("payload.test_runs must be a list")
        ids = [str(run.get("test_id", "")) for run in runs if isinstance(run, dict)]
        if len(runs) != 4:
            global_failures.append(f"expected exactly four test runs, found {len(runs)}")
        if set(ids) != set(EXPECTED_TESTS) or len(ids) != len(set(ids)):
            global_failures.append(f"expected one run for each test id, found {ids}")
        test_summaries = [validate_run(run) for run in runs if isinstance(run, dict)]
        if len(test_summaries) != 4:
            global_failures.append("all test runs must be JSON objects")
    except ValueError as exc:
        global_failures.append(str(exc))
        test_summaries = []
        payload = {}

    independent_pass = not global_failures and all(item.get("independent_status") == "pass" for item in test_summaries)
    summary = {
        "checkpoint_id": CHECKPOINT_ID,
        "agent_id": payload.get("agent_id"),
        "invocation_id": payload.get("invocation_id"),
        "independent_status": "pass" if independent_pass else "fail",
        "provider_labels": {
            "statuses": {item.get("test_id"): item.get("provider_status") for item in test_summaries},
            "condition_results": {item.get("test_id"): item.get("provider_condition_result") for item in test_summaries},
        },
        "global_failures": global_failures,
        "tests": test_summaries,
    }
    rendered = json.dumps(summary, indent=2, ensure_ascii=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if independent_pass else 1


if __name__ == "__main__":
    sys.exit(main())
