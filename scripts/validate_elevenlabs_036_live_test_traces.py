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
CHECKPOINT_ID = "ELEVENLABS-036-natural-sales-scenarios"
TIMING_TEXT = "Great, I'll send it there by the end of the day."
TAKE_CARE_TEXT = "Take care."
ATOMIC_TIMING_GOODBYE_TEXT = "Great, I'll send it there by the end of the day. Take care."
HARD_STOP_RECOVERY_TEXT = "You're right. Have a good one."
GUARANTEE_CLOSE_TEXT = "That's right - no guarantee. I don't want to waste your time. Have a good one."

EXPECTED_TESTS: dict[str, dict[str, str]] = {
    "sim_036_email_confirmation_spoken_email_two_step": {
        "name": f"{CHECKPOINT_ID}::sim_036_email_confirmation_spoken_email_two_step",
        "kind": "email_two_step",
    },
    "sim_036_email_plus_free_question_confirmation": {
        "name": f"{CHECKPOINT_ID}::sim_036_email_plus_free_question_confirmation",
        "kind": "email_plus_free",
    },
    "sim_036_future_price_ballpark_no_overpricing": {
        "name": f"{CHECKPOINT_ID}::sim_036_future_price_ballpark_no_overpricing",
        "kind": "future_price",
    },
    "sim_036_scheduling_simple_request_vs_live_integration": {
        "name": f"{CHECKPOINT_ID}::sim_036_scheduling_simple_request_vs_live_integration",
        "kind": "scheduling",
    },
    "sim_036_crm_payment_capability_before_price": {
        "name": f"{CHECKPOINT_ID}::sim_036_crm_payment_capability_before_price",
        "kind": "crm",
    },
    "sim_036_custom_dashboard_scoped_separately": {
        "name": f"{CHECKPOINT_ID}::sim_036_custom_dashboard_scoped_separately",
        "kind": "dashboard",
    },
    "sim_036_free_mockup_visual_not_working_site": {
        "name": f"{CHECKPOINT_ID}::sim_036_free_mockup_visual_not_working_site",
        "kind": "visual",
    },
    "sim_036_next_step_questions_no_cta_fatigue": {
        "name": f"{CHECKPOINT_ID}::sim_036_next_step_questions_no_cta_fatigue",
        "kind": "cta",
    },
    "sim_036_guarantee_required_clean_disqualify": {
        "name": f"{CHECKPOINT_ID}::sim_036_guarantee_required_clean_disqualify",
        "kind": "guarantee",
    },
    "sim_036_goodbye_take_care_no_loop": {
        "name": f"{CHECKPOINT_ID}::sim_036_goodbye_take_care_no_loop",
        "kind": "goodbye",
    },
}

EXPECTED_TEST_ID_SET = set(EXPECTED_TESTS)

EMAIL_RE = re.compile(
    r"\[redacted_email\]|"
    r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}|"
    r"\b[a-z0-9._%+-]+(?:\s+[a-z0-9._%+-]+){0,4}\s+at\s+[a-z0-9.-]+(?:\s+[a-z0-9.-]+){0,6}\s+dot\s+(?:com|org|net|co)\b",
    re.IGNORECASE,
)
CONFIRM_RE = re.compile(r"\b(?:yes|yeah|yep|correct|that(?:'s| is) right|that email is right|got it)\b", re.IGNORECASE)
CONFIRM_PROMPT_RE = re.compile(r"\b(?:just to confirm|is that right|is that correct|correct\?)\b", re.IGNORECASE)
GOODBYE_RE = re.compile(r"\b(?:bye|goodbye)\b", re.IGNORECASE)
TERMINAL_THANKS_RE = re.compile(r"\b(?:thanks|thank you|i(?:'| wi)ll look for it|i(?:'| wi)ll look)\b", re.IGNORECASE)
TIMING_RE = re.compile(r"\bby the end of the day\b", re.IGNORECASE)
SEND_RE = re.compile(r"\b(?:i(?:'| wi)ll send|send it|send the mockup|sending|deliver|delivery)\b", re.IGNORECASE)
EMAIL_QUESTION_RE = re.compile(
    r"\b(?:best email|what(?:'s| is) the best email|where should i send|provide .*email|what email|email address)\b",
    re.IGNORECASE,
)
CTA_RE = re.compile(
    r"\b(?:would you like me to send|would you like to see|would you like me to show|would you like to proceed|want me to send|want me to show|see the mockup|send it over)\b",
    re.IGNORECASE,
)
ASK_ANYTHING_ELSE_RE = re.compile(r"\b(?:anything else|any other questions|further assistance|still there)\b", re.IGNORECASE)
PRICE_RE = re.compile(r"\b(?:\$ ?[2345](?:,\d{3})?|\d-\d thousand|two thousand|three thousand|four thousand|five thousand|[2345]k|grand)\b", re.IGNORECASE)
LOW_RANGE_RE = re.compile(r"\b(?:two thousand|three thousand|\$ ?2|\$ ?3|2k|3k)\b", re.IGNORECASE)
HIGH_RANGE_RE = re.compile(r"\b(?:three thousand|four thousand|five thousand|\$ ?3|\$ ?4|\$ ?5|3k|4k|5k)\b", re.IGNORECASE)
HEDGE_RE = re.compile(r"\b(?:could|can|might|may|usually|typically|depends|depending|potentially|scope)\b", re.IGNORECASE)
NO_PRESSURE_RE = re.compile(
    r"\b(?:free|no payment|no obligation|no contract|no automatic follow[- ]?up call|won't automatically follow up|you can reply .* if .* useful)\b",
    re.IGNORECASE,
)
NO_CALL_RE = re.compile(
    r"\b(?:no automatic follow[- ]?up call|no more calls|won't automatically follow up|won't follow up with calls|won't call you unless|unless you reach out|reply only if it's useful|reply to the email only if)\b",
    re.IGNORECASE,
)
PROMISE_RE = re.compile(r"\b(?:rankings|patient growth|guarantee|more calls|emergency calls)\b", re.IGNORECASE)
CAPABILITY_RE = re.compile(r"\b(?:connect|integration|integrate|jobber|payment|deposit|handoff)\b", re.IGNORECASE)
SIMPLE_HANDOFF_RE = re.compile(r"\b(?:simple form handoff|simple handoff|simple form|request form)\b", re.IGNORECASE)
REAL_INTEGRATION_RE = re.compile(r"\b(?:real integration|integrat(?:ion|e)|direct connection|sync)\b", re.IGNORECASE)
CUSTOM_SCOPE_RE = re.compile(r"\b(?:custom|scope|separately|secure login|accounts|database|permissions|security|integrations?|privacy|testing|maintenance)\b", re.IGNORECASE)
FIXED_PRICE_RE = re.compile(r"\b(?:exactly|fixed price|final price|definitely included|included in the normal package)\b", re.IGNORECASE)
VISUAL_RE = re.compile(r"\b(?:visual|picture|placement|layout|design|where .* would go|static image|placeholder)\b", re.IGNORECASE)
LIVE_FUNCTION_RE = re.compile(
    r"\b(?:live functionality|working website|working login|working booking|working elements|working system|payments?|login|calendar|database|calendar connection|clickable|interactive|booking engine|ecommerce|booking process|real booking page|functional prototype)\b",
    re.IGNORECASE,
)
NEGATION_RE = re.compile(r"\b(?:not|won't|wouldn't|does not|doesn't|isn't|just)\b", re.IGNORECASE)
RESCUE_PITCH_RE = re.compile(
    r"\b(?:mockup|email|online presence|customer journey|potential customers|inquiries|anything else|still there)\b",
    re.IGNORECASE,
)
COST_QUESTION_RE = re.compile(r"\b(?:how much|cost|expensive|price|total cost)\b", re.IGNORECASE)
SCHEDULING_RE = re.compile(r"\b(?:schedul(?:e|ing)|booking|bookings|appointment|request times|live calendar)\b", re.IGNORECASE)
SIMPLE_REQUEST_RE = re.compile(
    r"\b(?:request times|appointment request form|simple appointment request form|simple form handoff|don't need a live calendar|not a live calendar|without live calendar|just a way for people to request times)\b",
    re.IGNORECASE,
)
CHEAPER_COST_RE = re.compile(r"\b(?:cheaper|basic range|affordable)\b", re.IGNORECASE)
VISUAL_FUNCTIONALITY_OBJECTION_RE = re.compile(
    r"\b(?:picture|static image|placeholder|click|work|useful|good|booking system|booking process|demo|prototype|case stud(?:y|ies)|preview)\b",
    re.IGNORECASE,
)
VISUAL_ACCEPTANCE_RE = re.compile(
    r"\b(?:fine,? send it|send it|send over the mockup|yeah,? send|i guess i can see that|i could see the mockup|i can see the mockup|i'd like to see|i guess i could see|i guess i'd like to see)\b",
    re.IGNORECASE,
)
POSITIVE_DEMO_OFFER_RE = re.compile(
    r"\b(?:live demo|working demo|interactive demonstration|prototype|case stud(?:y|ies)|working preview|live preview|detailed demonstration|walkthrough|more detailed demonstration)\b",
    re.IGNORECASE,
)
NEGATED_DEMO_OFFER_RE = re.compile(r"\b(?:can't|cannot|won't|wouldn't|don't|doesn't|isn't|not|not provide|no)\b", re.IGNORECASE)


class Checks:
    def __init__(self) -> None:
        self.assertions: list[dict[str, Any]] = []
        self.failures: list[str] = []
        self.inconclusives: list[str] = []

    def record(self, name: str, passed: bool, detail: str = "", *, severity: str = "fail") -> None:
        item: dict[str, Any] = {"name": name, "passed": bool(passed)}
        if detail:
            item["detail"] = detail
        if not passed:
            item["severity"] = severity
            if severity == "inconclusive":
                self.inconclusives.append(f"{name}: {detail}")
            else:
                self.failures.append(f"{name}: {detail}")
        self.assertions.append(item)

    def check(self, name: str, condition: bool, detail: str) -> None:
        self.record(name, condition, detail, severity="fail")

    def inconclusive(self, name: str, condition: bool, detail: str) -> None:
        self.record(name, condition, detail, severity="inconclusive")

    @property
    def status(self) -> str:
        if self.failures:
            return "fail"
        if self.inconclusives:
            return "inconclusive"
        return "pass"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate sanitized ELEVENLABS-036 live test traces without trusting provider labels.")
    parser.add_argument("--input", required=True, type=Path, help="Sanitized capture JSON path")
    parser.add_argument("--output", type=Path, help="Optional JSON path for the independent validation summary")
    parser.add_argument(
        "--allow-partial-repeats",
        action="store_true",
        help="Permit duplicate test IDs and missing full-10 coverage for targeted repeat captures.",
    )
    return parser.parse_args()


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


def canonical_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split())


def text(event: dict[str, Any]) -> str:
    return canonical_text(event.get("message"))


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


def next_text_index(events: list[dict[str, Any]], start: int, wanted_role: str) -> int | None:
    for index in range(start + 1, len(events)):
        if role(events[index]) == wanted_role and text(events[index]):
            return index
    return None


def previous_text_index(events: list[dict[str, Any]], start: int, wanted_role: str) -> int | None:
    for index in range(start - 1, -1, -1):
        if role(events[index]) == wanted_role and text(events[index]):
            return index
    return None


def user_indices_matching(events: list[dict[str, Any]], pattern: re.Pattern[str]) -> list[int]:
    return [index for index, event in enumerate(events) if role(event) == "user" and pattern.search(text(event))]


def agent_indices_matching(events: list[dict[str, Any]], pattern: re.Pattern[str]) -> list[int]:
    return [index for index, event in enumerate(events) if role(event) == "agent" and pattern.search(text(event))]


def contains_goodbye(message: str) -> bool:
    return bool(GOODBYE_RE.search(message))


def contains_terminal_thanks(message: str) -> bool:
    return bool(TERMINAL_THANKS_RE.search(message))


def is_same_turn_confirmation_goodbye(message: str) -> bool:
    return bool(CONFIRM_RE.search(message)) and contains_goodbye(message)


def is_terminal_user_message(message: str) -> bool:
    if contains_goodbye(message):
        return True
    lowered = normalized(message)
    return contains_terminal_thanks(message) and "?" not in message and "and what" not in lowered and "what's" not in lowered


def normalized(text_value: str) -> str:
    return canonical_text(text_value).lower()


def agent_messages_between(events: list[dict[str, Any]], start: int, end: int | None = None) -> list[str]:
    stop = len(events) if end is None else end
    return [text(events[index]) for index in range(start, stop) if role(events[index]) == "agent" and text(events[index])]


def has_positive_demo_offer(message: str) -> bool:
    lowered = normalized(message)
    return bool(POSITIVE_DEMO_OFFER_RE.search(message)) and not NEGATED_DEMO_OFFER_RE.search(lowered)


def extract_terminal_end_call(checks: Checks, events: list[dict[str, Any]]) -> dict[str, Any]:
    terminal = {
        "present": False,
        "call_index": None,
        "result_index": None,
        "params": None,
        "message": None,
        "reason": None,
    }
    calls = [(index, call) for index, event in enumerate(events) for call in event_calls(event) if is_end_call(call)]
    checks.check("at_most_one_end_call", len(calls) <= 1, f"found {len(calls)} end_call calls")
    if not calls:
        return terminal
    call_index, call = calls[0]
    params, params_error = parse_end_call(call)
    checks.check("parse_end_call_params", params is not None, params_error or "invalid end_call params")
    checks.check("built_in_system_end_call", str(call.get("type", "")).lower() == "system", "end_call is not type system")
    if params is None:
        return terminal

    matching_results = [
        (index, result)
        for index, event in enumerate(events)
        for result in event_results(event)
        if request_id(result) and request_id(result) == request_id(call)
    ]
    successful = [(index, result) for index, result in matching_results if successful_result(result)]
    checks.check(
        "matching_end_call_result",
        len(successful) == 1 and bool(request_id(call)),
        f"expected one successful tool result for request_id {request_id(call)!r}, found {len(successful)}",
    )
    if len(successful) == 1:
        result_index, result = successful[0]
        result_payload = result.get("result")
        checks.check(
            "successful_end_call_result_payload",
            isinstance(result_payload, dict) and result_payload.get("result_type") == "end_call_success" and result_payload.get("status") == "success",
            "tool result payload must be end_call_success with status success",
        )
    else:
        result_index = None

    render_index = previous_text_index(events, call_index, "agent")
    rendered = events[render_index] if render_index is not None else {}
    spoken = params.get("system__message_to_speak")
    checks.check(
        "rendered_message_matches_tool_message",
        render_index is not None and text(rendered) == canonical_text(spoken),
        f"rendered agent message must match tool speech {spoken!r}",
    )
    terminal.update(
        {
            "present": True,
            "call_index": call_index,
            "result_index": result_index,
            "params": params,
            "message": canonical_text(spoken),
            "reason": canonical_text(params.get("reason")),
        }
    )
    if result_index is not None:
        later_events = events[result_index + 1 :]
        checks.check(
            "no_text_or_tool_after_end_call_result",
            not any(text(event) or event_calls(event) or event_results(event) for event in later_events),
            "trace contains text or tool activity after the successful end_call result",
        )
    return terminal


def find_email_flow(events: list[dict[str, Any]]) -> dict[str, Any]:
    email_turns = [index for index, event in enumerate(events) if role(event) == "user" and EMAIL_RE.search(text(event))]
    if not email_turns:
        return {}
    email_turn_index = email_turns[-1]
    confirm_prompt_index = next_text_index(events, email_turn_index, "agent")
    confirm_user_index = next_text_index(events, confirm_prompt_index or email_turn_index, "user") if confirm_prompt_index is not None else None
    post_confirmation_agent_index = next_text_index(events, confirm_user_index, "agent") if confirm_user_index is not None else None
    return {
        "email_turn_index": email_turn_index,
        "confirm_prompt_index": confirm_prompt_index,
        "confirm_user_index": confirm_user_index,
        "post_confirmation_agent_index": post_confirmation_agent_index,
    }


def validate_email_flow(
    checks: Checks,
    events: list[dict[str, Any]],
    flow: dict[str, Any],
    *,
    exact_email: str | None = None,
) -> dict[str, Any]:
    if not flow:
        checks.check("email_turn_found", False, "email turn not found")
        return flow

    email_turn_index = flow["email_turn_index"]
    confirm_prompt_index = flow.get("confirm_prompt_index")
    confirm_user_index = flow.get("confirm_user_index")
    checks.check("email_turn_found", email_turn_index is not None, "email turn not found")
    if confirm_prompt_index is None:
        checks.inconclusive("confirmation_prompt_after_email", False, "simulation ended before the agent could confirm the provided email")
        return flow
    prompt_text = text(events[confirm_prompt_index])
    checks.check("confirmation_prompt_before_send", bool(CONFIRM_PROMPT_RE.search(prompt_text)), "first agent response after email must confirm the email")
    checks.check("no_send_language_before_confirmation", not TIMING_RE.search(prompt_text) and not SEND_RE.search(prompt_text), "agent used send or timing language before explicit confirmation")
    checks.check("no_ask_for_best_email_again", not EMAIL_QUESTION_RE.search(prompt_text), "agent asked for the best email again instead of confirming it")
    checks.check("confirmation_prompt_contains_email", bool(EMAIL_RE.search(prompt_text)), "confirmation prompt must repeat the provided email")
    if exact_email is not None:
        checks.check("confirmation_prompt_uses_normalized_email", exact_email.lower() in normalized(prompt_text), f"confirmation prompt must contain normalized email {exact_email!r}")

    if confirm_user_index is None:
        checks.inconclusive("explicit_email_confirmation_turn", False, "simulation ended before the buyer confirmed the repeated email")
        return flow
    confirm_user_text = text(events[confirm_user_index])
    checks.check("explicit_email_confirmation_turn", bool(CONFIRM_RE.search(confirm_user_text)), "buyer did not explicitly confirm the repeated email")

    post_confirmation_agent_index = flow.get("post_confirmation_agent_index")
    if post_confirmation_agent_index is None:
        checks.inconclusive("post_confirmation_agent_turn", False, "simulation ended before the agent got the required post-confirmation response opportunity")
        return flow
    post_confirmation_text = text(events[post_confirmation_agent_index])
    same_turn_goodbye = is_same_turn_confirmation_goodbye(confirm_user_text)
    if same_turn_goodbye:
        checks.check(
            "same_turn_confirmation_goodbye_atomic_message",
            post_confirmation_text == ATOMIC_TIMING_GOODBYE_TEXT,
            f"same-turn confirmation plus goodbye must use {ATOMIC_TIMING_GOODBYE_TEXT!r}",
        )
    else:
        checks.check("post_confirmation_timing_present", TIMING_RE.search(post_confirmation_text) is not None, "post-confirmation agent turn must include by-end-of-day timing")
        checks.check("post_confirmation_timing_is_not_farewell", TAKE_CARE_TEXT not in post_confirmation_text and not contains_goodbye(post_confirmation_text), "confirmation without goodbye must not include a farewell")
    return flow


def validate_timing_dedup(checks: Checks, events: list[dict[str, Any]]) -> None:
    timing_messages = [text(event) for event in events if role(event) == "agent" and TIMING_RE.search(text(event))]
    checks.check("timing_spoken_at_most_once", len(timing_messages) <= 1, f"delivery timing appears {len(timing_messages)} times in agent speech")


def validate_late_goodbye_precedence(
    checks: Checks,
    events: list[dict[str, Any]],
    flow: dict[str, Any],
    terminal: dict[str, Any],
    *,
    require_terminal_after_goodbye: bool,
) -> None:
    confirm_user_index = flow.get("confirm_user_index")
    post_confirmation_agent_index = flow.get("post_confirmation_agent_index")
    if confirm_user_index is None or post_confirmation_agent_index is None:
        return
    confirm_user_text = text(events[confirm_user_index])
    if is_same_turn_confirmation_goodbye(confirm_user_text):
        return
    if text(events[post_confirmation_agent_index]) != TIMING_TEXT:
        return
    later_terminal_user_index = None
    for index in range(post_confirmation_agent_index + 1, len(events)):
        if role(events[index]) == "user" and is_terminal_user_message(text(events[index])):
            later_terminal_user_index = index
            break
    if later_terminal_user_index is None:
        return
    later_agent_index = next_text_index(events, later_terminal_user_index, "agent")
    if later_agent_index is None:
        if require_terminal_after_goodbye:
            checks.inconclusive("later_goodbye_terminal_response", False, "simulation ended after the buyer's later goodbye/terminal thanks before the required Take care response")
        return
    later_agent_text = text(events[later_agent_index])
    checks.check(
        "later_goodbye_requires_take_care_only",
        later_agent_text == TAKE_CARE_TEXT,
        f"after prior delivery timing, later goodbye/terminal thanks permits only {TAKE_CARE_TEXT!r}",
    )
    if terminal.get("present"):
        checks.check(
            "terminal_tool_message_after_late_goodbye_is_take_care_only",
            terminal.get("message") == TAKE_CARE_TEXT,
            f"terminal tool speech must be {TAKE_CARE_TEXT!r} after prior delivery timing",
        )


def validate_email_two_step(checks: Checks, events: list[dict[str, Any]], flow: dict[str, Any], terminal: dict[str, Any]) -> str:
    validate_email_flow(checks, events, flow, exact_email="hello@cedarridgeglass.com")
    email_turn_index = flow.get("email_turn_index")
    if email_turn_index is not None:
        checks.check(
            "spoken_email_turn_contains_unformatted_address",
            "hello at cedar ridge glass dot com" in normalized(text(events[email_turn_index])),
            "spoken email turn must contain the unformatted cedar ridge email",
        )
    confirm_user_index = flow.get("confirm_user_index")
    post_confirmation_agent_index = flow.get("post_confirmation_agent_index")
    if confirm_user_index is not None and post_confirmation_agent_index is not None:
        later_complaint_index = None
        for index in range(post_confirmation_agent_index + 1, len(events)):
            if role(events[index]) == "user" and "why are you still talking" in normalized(text(events[index])):
                later_complaint_index = index
                break
        if later_complaint_index is not None:
            recovery_index = next_text_index(events, later_complaint_index, "agent")
            if recovery_index is None:
                checks.inconclusive("hard_stop_recovery_turn", False, "simulation ended before the agent could answer the buyer's hard stop")
            else:
                checks.check(
                    "hard_stop_recovery_text",
                    text(events[recovery_index]) == HARD_STOP_RECOVERY_TEXT,
                    f"hard-stop recovery must be {HARD_STOP_RECOVERY_TEXT!r}",
                )
                checks.check(
                    "hard_stop_recovery_end_call_reason",
                    terminal.get("reason") == "Buyer requested no further contact",
                    "hard-stop recovery must end with reason 'Buyer requested no further contact'",
                )
    return "ELEVENLABS-036"


def validate_email_plus_free(checks: Checks, events: list[dict[str, Any]], flow: dict[str, Any]) -> str:
    validate_email_flow(checks, events, flow, exact_email="oakwoodkidsdental@gmail.com")
    relevant_agent_messages = [text(event) for event in events if role(event) == "agent" and text(event)]
    combined = " ".join(relevant_agent_messages)
    normalized_combined = normalized(combined)
    has_free_language = any(
        token in normalized_combined
        for token in ("free", "no payment", "no obligation", "no contract")
    )
    has_no_call_language = NO_CALL_RE.search(combined) is not None or "no automatic follow-up" in normalized_combined
    checks.check(
        "free_no_pressure_language_present",
        has_free_language and has_no_call_language,
        "agent must cover free/no-pressure language and no-call expectations across the relevant agent responses",
    )
    checks.check(
        "no_growth_or_rankings_claim",
        not PROMISE_RE.search(combined.replace("guarantee", "")),
        "agent must not promise patient growth or rankings in the no-pressure flow",
    )
    return "ELEVENLABS-036"


def validate_future_price(checks: Checks, events: list[dict[str, Any]], flow: dict[str, Any]) -> str:
    price_question_index = next((i for i, event in enumerate(events) if role(event) == "user" and "five grand surprise" in normalized(text(event))), None)
    checks.check("initial_price_question_found", price_question_index is not None, "initial price question not found")
    if price_question_index is not None:
        response_index = next_text_index(events, price_question_index, "agent")
        if response_index is None:
            checks.inconclusive("price_answer_after_initial_question", False, "simulation ended before the agent answered the initial price question")
        else:
            response_text = text(events[response_index])
            checks.check("price_answer_mentions_lower_range", LOW_RANGE_RE.search(response_text) is not None, "initial price answer must anchor the simple site in the lower approved range")
            checks.check("price_answer_is_ballpark", HEDGE_RE.search(response_text) is not None, "initial price answer must be framed as a range or ballpark")
            checks.check("price_answer_not_five_grand_default", "five thousand" not in normalized(response_text) and "$5" not in response_text, "initial price answer must not default the simple site to five thousand dollars")
            checks.check("price_answer_separates_simple_from_live", "simple" in normalized(response_text) and ("live" in normalized(response_text) or "calendar" in normalized(response_text) or "payment" in normalized(response_text)), "initial price answer must separate the simple request path from live booking/payment")
    follow_up_question_index = next((i for i, event in enumerate(events) if role(event) == "user" and "same as live booking" in normalized(text(event))), None)
    checks.check("simple_vs_live_follow_up_found", follow_up_question_index is not None, "simple-vs-live follow-up question not found")
    if follow_up_question_index is not None:
        response_index = next_text_index(events, follow_up_question_index, "agent")
        if response_index is None:
            checks.inconclusive("simple_vs_live_follow_up_answer", False, "simulation ended before the agent answered the simple-vs-live follow-up")
        else:
            response_text = text(events[response_index])
            checks.check("simple_request_called_lighter", "simple request form" in normalized(response_text) or "lighter option" in normalized(response_text), "follow-up answer must keep the request form as the lighter option")
            checks.check("live_booking_called_more_expensive", "live booking" in normalized(response_text) or "calendar integration" in normalized(response_text), "follow-up answer must distinguish live booking/calendar as the more expensive option")
    open_to_mockup_index = next((i for i, event in enumerate(events) if role(event) == "user" and "want to see what that mockup looks like first" in normalized(text(event))), None)
    if open_to_mockup_index is not None:
        response_index = next_text_index(events, open_to_mockup_index, "agent")
        if response_index is None:
            checks.inconclusive("natural_mockup_next_step_after_price", False, "simulation ended before the natural mockup next step after price resolution")
        else:
            response_text = text(events[response_index])
            checks.check("natural_mockup_next_step_after_price", EMAIL_QUESTION_RE.search(response_text) is not None, "after price is resolved and the buyer stays open, the next step must ask where to send the mockup")
    if flow:
        validate_email_flow(checks, events, flow)
        validate_late_goodbye_precedence(checks, events, flow, {"present": False}, require_terminal_after_goodbye=False)
    return "ELEVENLABS-036"


def validate_scheduling(checks: Checks, events: list[dict[str, Any]], flow: dict[str, Any]) -> str:
    first_schedule_index = next((i for i, event in enumerate(events) if role(event) == "user" and SCHEDULING_RE.search(text(event))), None)
    checks.check("initial_scheduling_question_found", first_schedule_index is not None, "initial scheduling question not found")
    if first_schedule_index is not None:
        response_index = next_text_index(events, first_schedule_index, "agent")
        if response_index is None:
            checks.inconclusive("scheduling_capability_answer", False, "simulation ended before the agent answered the scheduling question")
        else:
            response_text = text(events[response_index])
            initial_question_text = text(events[first_schedule_index])
            checks.check(
                "scheduling_initial_answer_separates_simple_from_live",
                SIMPLE_HANDOFF_RE.search(response_text) is not None and ("live" in normalized(response_text) or "calendar" in normalized(response_text) or REAL_INTEGRATION_RE.search(response_text) is not None),
                "initial scheduling answer must distinguish a simple request flow from a live calendar/integration path",
            )
            if COST_QUESTION_RE.search(initial_question_text) is None and CHEAPER_COST_RE.search(initial_question_text) is None:
                checks.check(
                    "scheduling_initial_answer_no_price_before_cost_question",
                    PRICE_RE.search(response_text) is None,
                    "initial scheduling answer must not quote ranges before the buyer asks about cost",
                )
    clarification_index = next((i for i, event in enumerate(events) if role(event) == "user" and SIMPLE_REQUEST_RE.search(text(event))), None)
    if clarification_index is not None:
        response_index = next_text_index(events, clarification_index, "agent")
        if response_index is None:
            checks.inconclusive("simple_request_clarification_answer", False, "simulation ended before the agent answered the simple request clarification")
        else:
            response_text = text(events[response_index])
            clarification_text = text(events[clarification_index])
            if COST_QUESTION_RE.search(clarification_text) is None and CHEAPER_COST_RE.search(clarification_text) is None:
                checks.check(
                    "simple_request_clarification_keeps_scope_split",
                    "request" in normalized(response_text) and ("live" in normalized(response_text) or "calendar" in normalized(response_text) or "integration" in normalized(response_text)),
                    "clarification answer must keep the request-times path distinct from a live calendar/integration",
                )
                checks.check(
                    "simple_request_clarification_no_price_before_cost_question",
                    PRICE_RE.search(response_text) is None,
                    "request-times clarification must not quote price before the buyer asks cost",
                )
    cost_question_index = next(
        (
            i
            for i, event in enumerate(events)
            if i >= (first_schedule_index or 0)
            and role(event) == "user"
            and (COST_QUESTION_RE.search(text(event)) or CHEAPER_COST_RE.search(text(event)))
        ),
        None,
    )
    checks.check("scheduling_cost_question_found", cost_question_index is not None, "scheduling cost question not found")
    if cost_question_index is not None:
        response_index = next_text_index(events, cost_question_index, "agent")
        if response_index is None:
            checks.inconclusive("scheduling_cost_answer", False, "simulation ended before the agent answered the scheduling cost question")
        else:
            response_text = text(events[response_index])
            normalized_response = normalized(response_text)
            checks.check("scheduling_cost_answer_has_simple_request_range", LOW_RANGE_RE.search(response_text) is not None, "scheduling cost answer must price the lighter request-times path in the approved lower range")
            checks.check(
                "scheduling_cost_answer_frames_whole_site_not_form_only",
                any(token in normalized_response for token in ("whole site", "website", "in total", "total cost", "total", "light website")),
                "scheduling cost answer must frame the range as a whole-site ballpark, not a standalone form-only custom quote",
            )
            if "live" in normalized_response or "calendar" in normalized_response or "advanced" in normalized_response or "integration" in normalized_response:
                checks.check(
                    "scheduling_cost_answer_has_live_range_when_live_path_mentioned",
                    HIGH_RANGE_RE.search(response_text) is not None,
                    "when the cost answer mentions live-calendar or advanced functionality, it must also give the heavier range",
                )
    open_to_mockup_index = next((i for i, event in enumerate(events) if role(event) == "user" and "i'd like to see that mockup" in normalized(text(event))), None)
    if open_to_mockup_index is not None:
        response_index = next_text_index(events, open_to_mockup_index, "agent")
        if response_index is None:
            checks.inconclusive("natural_mockup_next_step_after_scheduling", False, "simulation ended before the natural next step after the buyer agreed to see the mockup")
        else:
            checks.check("natural_mockup_next_step_after_scheduling", EMAIL_QUESTION_RE.search(text(events[response_index])) is not None, "after the buyer agrees to the mockup, the next step must ask where to send it")
    if flow:
        validate_email_flow(checks, events, flow)
        validate_late_goodbye_precedence(checks, events, flow, {"present": False}, require_terminal_after_goodbye=False)
    return "ELEVENLABS-036"


def validate_crm(checks: Checks, events: list[dict[str, Any]], flow: dict[str, Any]) -> str:
    capability_question_index = next((i for i, event in enumerate(events) if role(event) == "user" and ("jobber" in normalized(text(event)) or "deposit payments" in normalized(text(event)))), None)
    checks.check("crm_capability_question_found", capability_question_index is not None, "initial CRM/payment capability question not found")
    if capability_question_index is not None:
        response_index = next_text_index(events, capability_question_index, "agent")
        if response_index is None:
            checks.inconclusive("crm_capability_answer", False, "simulation ended before the agent answered the capability question")
        else:
            response_text = text(events[response_index])
            checks.check("crm_answers_capability_before_price", CAPABILITY_RE.search(response_text) is not None, "first CRM response must address capability before price")
            checks.check("crm_first_answer_no_price_numbers", PRICE_RE.search(response_text) is None, "first CRM response must not quote price before the buyer asks cost")
            checks.check("crm_first_answer_says_handoff_vs_integration", SIMPLE_HANDOFF_RE.search(response_text) is not None and REAL_INTEGRATION_RE.search(response_text) is not None, "first CRM response must distinguish simple handoff from real integration")
    cost_question_index = next((i for i, event in enumerate(events) if role(event) == "user" and "what kind of price does that add" in normalized(text(event))), None)
    checks.check("crm_cost_question_found", cost_question_index is not None, "CRM cost question not found")
    if cost_question_index is not None:
        response_index = next_text_index(events, cost_question_index, "agent")
        if response_index is None:
            checks.inconclusive("crm_cost_answer", False, "simulation ended before the agent answered the CRM cost question")
        else:
            response_text = text(events[response_index])
            checks.check("crm_cost_answer_integration_range", HIGH_RANGE_RE.search(response_text) is not None, "CRM cost answer must map the real integration toward the heavier range")
            checks.check("crm_cost_answer_handoff_range", LOW_RANGE_RE.search(response_text) is not None, "CRM cost answer must keep the simple handoff as the lighter option")
            checks.check("crm_cost_answer_depends_on_system", HEDGE_RE.search(response_text) is not None, "CRM cost answer must say the real number depends on the system")
    combined = " ".join(text(event) for event in events if role(event) == "agent")
    checks.check("crm_natural_mockup_next_step", "mockup" in normalized(combined), "CRM trace must contain a natural mockup next step after capability and price are answered")
    if flow:
        validate_email_flow(checks, events, flow)
    return "ELEVENLABS-036"


def validate_dashboard(checks: Checks, events: list[dict[str, Any]], flow: dict[str, Any]) -> str:
    dashboard_question_index = next((i for i, event in enumerate(events) if role(event) == "user" and "progress dashboard" in normalized(text(event))), None)
    checks.check("dashboard_question_found", dashboard_question_index is not None, "dashboard/login question not found")
    if dashboard_question_index is not None:
        response_index = next_text_index(events, dashboard_question_index, "agent")
        if response_index is None:
            checks.inconclusive("dashboard_scope_answer", False, "simulation ended before the agent answered the dashboard question")
        else:
            response_text = text(events[response_index])
            driver_hits = sum(1 for token in ("accounts", "database", "permissions", "security", "integrations") if token in normalized(response_text))
            checks.check("dashboard_scoped_as_custom_work", "custom" in normalized(response_text) or "scope" in normalized(response_text), "dashboard answer must scope the login/dashboard as custom work")
            checks.check("dashboard_scope_driver_keywords", driver_hits >= 3, "dashboard answer must name concrete scope drivers before pricing it")
    combined = " ".join(text(event) for event in events if role(event) == "agent")
    checks.check(
        "dashboard_mockup_visual_boundary",
        "mockup" in normalized(combined) and ("visual" in normalized(combined) or "placement" in normalized(combined)) and ("wouldn't include" in normalized(combined) or "scoped separately" in normalized(combined) or "custom work" in normalized(combined)),
        "dashboard trace must separate visual mockup placement from working dashboard software",
    )
    price_messages = [text(event) for event in events if role(event) == "agent" and PRICE_RE.search(text(event))]
    if price_messages:
        fixed = [message for message in price_messages if FIXED_PRICE_RE.search(message) and not HEDGE_RE.search(message)]
        checks.check("dashboard_no_fixed_price_before_scope", not fixed, "dashboard trace gives a fixed first-call dashboard price before scope")
    checks.check("dashboard_no_paid_consultation_push", "paid consultation" not in normalized(combined), "dashboard trace must not make a paid consultation the first-call goal")
    if flow:
        validate_email_flow(checks, events, flow)
        validate_late_goodbye_precedence(checks, events, flow, {"present": False}, require_terminal_after_goodbye=False)
    return "ELEVENLABS-036"


def validate_visual(checks: Checks, events: list[dict[str, Any]], flow: dict[str, Any]) -> str:
    scope_question_index = next((i for i, event in enumerate(events) if role(event) == "user" and "class booking system" in normalized(text(event))), None)
    checks.check("visual_scope_question_found", scope_question_index is not None, "visual-scope question not found")
    boundary_index = None
    if scope_question_index is not None:
        boundary_index = next_text_index(events, scope_question_index, "agent")
        if boundary_index is None:
            checks.inconclusive("visual_scope_boundary_answer", False, "simulation ended before the agent answered the visual-vs-live scope question")
        else:
            boundary_text = text(events[boundary_index])
            checks.check("visual_scope_says_visual_not_live", VISUAL_RE.search(boundary_text) is not None and LIVE_FUNCTION_RE.search(boundary_text) is not None and NEGATION_RE.search(boundary_text) is not None, "scope answer must say the mockup is visual and not live functionality")
    if scope_question_index is not None and boundary_index is not None:
        early_email_questions = [
            index
            for index in range(scope_question_index + 1, boundary_index)
            if role(events[index]) == "agent" and EMAIL_QUESTION_RE.search(text(events[index]))
        ]
        checks.check("no_email_before_scope_boundary", not early_email_questions, "agent asked for email before clarifying the mockup scope")
    click_question_index = next((i for i, event in enumerate(events) if role(event) == "user" and "no way to click" in normalized(text(event))), None)
    if click_question_index is not None:
        click_response_index = next_text_index(events, click_question_index, "agent")
        if click_response_index is None:
            checks.inconclusive("clickability_boundary_answer", False, "simulation ended before the agent answered the clickability follow-up")
        else:
            click_response = text(events[click_response_index])
            checks.check("clickability_boundary_answer", ("clickable" in normalized(click_response) or "interactive" in normalized(click_response)) and NEGATION_RE.search(click_response) is not None, "clickability follow-up must say the mockup is not clickable or interactive")
    if boundary_index is not None:
        first_functionality_objection_index = next(
            (
                i
                for i in range(boundary_index + 1, len(events))
                if role(events[i]) == "user" and VISUAL_FUNCTIONALITY_OBJECTION_RE.search(text(events[i]))
            ),
            None,
        )
        explicit_acceptance_index = None
        if first_functionality_objection_index is not None:
            explicit_acceptance_index = next(
                (
                    i
                    for i in range(first_functionality_objection_index + 1, len(events))
                    if role(events[i]) == "user" and VISUAL_ACCEPTANCE_RE.search(text(events[i]))
                ),
                None,
            )
            stop_index = explicit_acceptance_index if explicit_acceptance_index is not None else len(events)
            pre_acceptance_agent_messages = agent_messages_between(events, first_functionality_objection_index + 1, stop_index)
            repeated_ctas = [message for message in pre_acceptance_agent_messages if CTA_RE.search(message) or EMAIL_QUESTION_RE.search(message)]
            checks.check(
                "visual_no_repeated_mockup_cta_before_acceptance",
                len(repeated_ctas) == 0,
                f"agent repeated mockup CTA/email ask {len(repeated_ctas)} time(s) after functionality objections and before explicit acceptance",
            )
        invented_demo_messages = [
            text(events[i])
            for i in range(boundary_index, len(events))
            if role(events[i]) == "agent" and has_positive_demo_offer(text(events[i]))
        ]
        checks.check(
            "visual_no_invented_live_demo_or_case_study_offer",
            len(invented_demo_messages) == 0,
            f"agent invented live demo/prototype/case-study/working-preview offers: {invented_demo_messages}",
        )
    if flow:
        validate_email_flow(checks, events, flow)
    return "ELEVENLABS-036"


def validate_cta(checks: Checks, events: list[dict[str, Any]], flow: dict[str, Any]) -> str:
    concern_start = next((i for i, event in enumerate(events) if role(event) == "user" and "what happens after you send it" in normalized(text(event))), None)
    checks.check("cta_concern_sequence_found", concern_start is not None, "practical concern sequence not found")
    opt_in_index = next((i for i, event in enumerate(events) if role(event) == "user" and "send it over" in normalized(text(event))), None)
    checks.check("cta_send_opt_in_found", opt_in_index is not None, "buyer send-it-over opt-in not found")
    if concern_start is not None and opt_in_index is not None:
        concern_window = [
            text(events[index])
            for index in range(concern_start + 1, opt_in_index)
            if role(events[index]) == "agent"
        ]
        email_asks = [message for message in concern_window if EMAIL_QUESTION_RE.search(message)]
        cta_asks = [message for message in concern_window if CTA_RE.search(message)]
        combined = " ".join(concern_window)
        checks.check("cta_no_email_request_before_opt_in", not email_asks, "agent asked for email before the buyer finished the concern sequence")
        checks.check("cta_no_repeated_send_asks", len(cta_asks) == 0, f"agent repeated CTA/send asks {len(cta_asks)} time(s) while practical concerns were still unresolved")
        checks.check("cta_concern_answers_present", bool(concern_window), "concern sequence must contain agent answers before the buyer opts in")
    if opt_in_index is not None:
        response_index = next_text_index(events, opt_in_index, "agent")
        if response_index is None:
            checks.inconclusive("cta_email_question_after_opt_in", False, "simulation ended before the agent made the natural email ask after the buyer opted in")
        else:
            checks.check("cta_email_question_after_opt_in", EMAIL_QUESTION_RE.search(text(events[response_index])) is not None, "after send-it-over opt-in, the next agent turn must ask for the email")
    if flow:
        validate_email_flow(checks, events, flow)
        validate_late_goodbye_precedence(checks, events, flow, {"present": False}, require_terminal_after_goodbye=False)
    return "ELEVENLABS-036"


def validate_guarantee(checks: Checks, events: list[dict[str, Any]], terminal: dict[str, Any]) -> str:
    guarantee_index = next((i for i, event in enumerate(events) if role(event) == "user" and "guarantee page-one seo" in normalized(text(event))), None)
    checks.check("guarantee_requirement_found", guarantee_index is not None, "guarantee-only requirement not found")
    combined = " ".join(text(event) for event in events if role(event) == "agent")
    checks.check(
        "guarantee_honesty_warning_present",
        "nobody can honestly guarantee" in normalized(combined) and "be careful with anyone selling it that way" in normalized(combined),
        "guarantee disqualification must warn that nobody can honestly guarantee those outcomes",
    )
    checks.check(
        "guarantee_distinguishes_foundation_from_outcomes",
        "foundation" in normalized(combined) and "site experience" in normalized(combined),
        "guarantee disqualification must distinguish foundation/site experience from guaranteed outcomes",
    )
    checks.check(
        "guarantee_no_rescue_pitch_or_email_ask",
        RESCUE_PITCH_RE.search(combined.replace("site experience", "")) is None,
        "guarantee disqualification must not rescue-pitch the mockup, ask for email, or reopen the sale",
    )
    final_user_index = next((i for i in range(len(events) - 1, -1, -1) if role(events[i]) == "user" and "no guarantee means no point" in normalized(text(events[i]))), None)
    if final_user_index is not None:
        final_agent_index = next_text_index(events, final_user_index, "agent")
        if final_agent_index is None:
            checks.inconclusive("guarantee_clean_close_after_final_rejection", False, "simulation ended before the agent gave the clean disqualifying close")
        else:
            checks.check("guarantee_clean_close_after_final_rejection", text(events[final_agent_index]) == GUARANTEE_CLOSE_TEXT, f"final guarantee close must be {GUARANTEE_CLOSE_TEXT!r}")
    checks.check("guarantee_end_call_present", terminal.get("present") is True, "guarantee disqualification must end with one end_call")
    if terminal.get("present"):
        checks.check(
            "guarantee_end_call_reason",
            terminal.get("reason") == "Guarantee requirement makes Atlas a bad fit and the conversation is complete",
            "guarantee end_call must use the exact bad-fit completion reason",
        )
    return "ELEVENLABS-036"


def validate_goodbye(checks: Checks, events: list[dict[str, Any]], flow: dict[str, Any], terminal: dict[str, Any]) -> str:
    contract = "ELEVENLABS-039 precedence over ELEVENLABS-036 goodbye overlap"
    validate_email_flow(checks, events, flow)
    checks.check("goodbye_end_call_present", terminal.get("present") is True, "terminal goodbye trace must end with one end_call")
    if not flow:
        terminal_user_index = next((i for i in range(len(events) - 1, -1, -1) if role(events[i]) == "user" and is_terminal_user_message(text(events[i]))), None)
        if terminal_user_index is not None:
            checks.check(
                "goodbye_no_email_pending_outcome",
                False,
                "buyer ended before email capture and confirmation, so the goodbye cannot count as a completed mockup outcome",
            )
        return contract
    confirm_user_index = flow.get("confirm_user_index")
    post_confirmation_agent_index = flow.get("post_confirmation_agent_index")
    if confirm_user_index is None or post_confirmation_agent_index is None:
        terminal_user_index = next((i for i in range(len(events) - 1, -1, -1) if role(events[i]) == "user" and is_terminal_user_message(text(events[i]))), None)
        if terminal_user_index is not None:
            checks.check(
                "goodbye_pending_email_outcome",
                False,
                "buyer ended before the email confirmation flow was fully completed, so the goodbye cannot pass as complete",
            )
        return contract
    confirm_text = text(events[confirm_user_index])
    if is_same_turn_confirmation_goodbye(confirm_text):
        checks.check(
            "same_turn_confirmation_goodbye_exact_tool_reason",
            terminal.get("reason") == "Email confirmed and buyer ended the conversation",
            "same-turn confirmation plus goodbye must use the exact email-confirmed terminal reason",
        )
        checks.check(
            "same_turn_confirmation_goodbye_atomic_message",
            text(events[post_confirmation_agent_index]) == ATOMIC_TIMING_GOODBYE_TEXT and terminal.get("message") == ATOMIC_TIMING_GOODBYE_TEXT,
            f"same-turn confirmation plus goodbye must render and speak {ATOMIC_TIMING_GOODBYE_TEXT!r}",
        )
    else:
        checks.check("prior_turn_timing_exact", text(events[post_confirmation_agent_index]) == TIMING_TEXT, f"confirmation without goodbye must first say only {TIMING_TEXT!r}")
        validate_late_goodbye_precedence(checks, events, flow, terminal, require_terminal_after_goodbye=True)
    if terminal.get("present") and terminal.get("message") == ATOMIC_TIMING_GOODBYE_TEXT and str(events and checks.status == "pass") and terminal.get("message"):
        checks.record("provider_label_conflict_expected", True, "039 precedence explicitly overrides the legacy 036 only-Take-care label when confirmation and goodbye occur in the same user turn")
    return contract


def validate_run(run: dict[str, Any]) -> dict[str, Any]:
    test_id = str(run.get("test_id", "")).strip()
    expected = EXPECTED_TESTS.get(test_id)
    checks = Checks()
    if expected is None:
        return {
            "test_id": test_id,
            "test_name": run.get("test_name"),
            "test_run_id": run.get("test_run_id"),
            "independent_status": "fail",
            "effective_contract": "none",
            "provider_status": run.get("status"),
            "provider_condition_result": run.get("condition_result"),
            "assertions": [{"name": "expected_test_id", "passed": False, "detail": "unexpected test id", "severity": "fail"}],
            "failures": ["expected_test_id: unexpected test id"],
            "inconclusives": [],
        }

    checks.check("expected_test_name", run.get("test_name") == expected["name"], f"expected test_name {expected['name']!r}")
    events_raw = run.get("agent_responses")
    checks.check("ordered_agent_responses_present", isinstance(events_raw, list), "agent_responses is not a list")
    events = [event for event in as_list(events_raw)]
    terminal = extract_terminal_end_call(checks, events)
    validate_timing_dedup(checks, events)
    flow = find_email_flow(events)

    kind = expected["kind"]
    if kind == "email_two_step":
        contract = validate_email_two_step(checks, events, flow, terminal)
    elif kind == "email_plus_free":
        contract = validate_email_plus_free(checks, events, flow)
    elif kind == "future_price":
        contract = validate_future_price(checks, events, flow)
    elif kind == "scheduling":
        contract = validate_scheduling(checks, events, flow)
    elif kind == "crm":
        contract = validate_crm(checks, events, flow)
    elif kind == "dashboard":
        contract = validate_dashboard(checks, events, flow)
    elif kind == "visual":
        contract = validate_visual(checks, events, flow)
    elif kind == "cta":
        contract = validate_cta(checks, events, flow)
    elif kind == "guarantee":
        contract = validate_guarantee(checks, events, terminal)
    elif kind == "goodbye":
        contract = validate_goodbye(checks, events, flow, terminal)
    else:
        checks.check("known_test_kind", False, f"unknown validation kind: {kind}")
        contract = "none"

    return {
        "test_id": test_id,
        "test_name": run.get("test_name"),
        "test_run_id": run.get("test_run_id"),
        "independent_status": checks.status,
        "effective_contract": contract,
        "provider_status": run.get("status"),
        "provider_condition_result": run.get("condition_result"),
        "provider_evaluator_rationale": run.get("evaluator_rationale"),
        "assertions": checks.assertions,
        "failures": checks.failures,
        "inconclusives": checks.inconclusives,
    }


def summarize_status(global_failures: list[str], tests: list[dict[str, Any]]) -> str:
    if global_failures or any(test.get("independent_status") == "fail" for test in tests):
        return "fail"
    if any(test.get("independent_status") == "inconclusive" for test in tests):
        return "inconclusive"
    return "pass"


def main() -> int:
    args = parse_args()
    global_failures: list[str] = []
    tests: list[dict[str, Any]] = []
    payload: dict[str, Any] = {}
    input_run_ids: list[str] = []

    try:
        document = read_json(args.input)
        payload = capture_payload(document)
        if payload.get("agent_id") != EXPECTED_AGENT_ID:
            global_failures.append(f"agent_id must be {EXPECTED_AGENT_ID}")
        if payload.get("checkpoint_id") not in (None, "", CHECKPOINT_ID):
            global_failures.append(f"checkpoint_id must be {CHECKPOINT_ID}")
        runs_raw = payload.get("test_runs")
        if not isinstance(runs_raw, list):
            raise ValueError("payload.test_runs must be a list")
        runs = [run for run in runs_raw if isinstance(run, dict)]
        if len(runs) != len(runs_raw):
            global_failures.append("all test_runs entries must be JSON objects")
        input_run_ids = [str(run.get("test_id", "")).strip() for run in runs]
        duplicates = sorted({test_id for test_id in input_run_ids if input_run_ids.count(test_id) > 1 and test_id})
        if duplicates and not args.allow_partial_repeats:
            global_failures.append(f"duplicate test_id(s): {duplicates}")
        unexpected = sorted(test_id for test_id in set(input_run_ids) if test_id not in EXPECTED_TEST_ID_SET)
        if unexpected:
            global_failures.append(f"unexpected test_id(s): {unexpected}")
        tests = [validate_run(run) for run in runs]
    except ValueError as exc:
        global_failures.append(str(exc))

    seen_ids = {test.get("test_id") for test in tests}
    missing_ids = sorted(EXPECTED_TEST_ID_SET - seen_ids)
    coverage_complete = seen_ids == EXPECTED_TEST_ID_SET and len(tests) == len(EXPECTED_TEST_ID_SET)
    if missing_ids and not args.allow_partial_repeats:
        global_failures.append(f"missing test_id(s): {missing_ids}")
    if len(tests) != len(EXPECTED_TEST_ID_SET) and not args.allow_partial_repeats:
        global_failures.append(f"expected exactly {len(EXPECTED_TEST_ID_SET)} test runs, found {len(tests)}")

    provider_status_entries = [
        {
            "test_id": test.get("test_id"),
            "test_run_id": test.get("test_run_id"),
            "status": test.get("provider_status"),
        }
        for test in tests
    ]
    provider_condition_entries = [
        {
            "test_id": test.get("test_id"),
            "test_run_id": test.get("test_run_id"),
            "condition_result": test.get("provider_condition_result"),
        }
        for test in tests
    ]
    summary = {
        "checkpoint_id": CHECKPOINT_ID,
        "agent_id": payload.get("agent_id"),
        "invocation_id": payload.get("invocation_id"),
        "independent_status": summarize_status(global_failures, tests),
        "allow_partial_repeats": args.allow_partial_repeats,
        "coverage_complete": coverage_complete,
        "input_test_ids": input_run_ids,
        "missing_test_ids": missing_ids,
        "global_failures": global_failures,
        "provider_labels": {
            "status_entries": provider_status_entries,
            "condition_result_entries": provider_condition_entries,
        },
        "tests": tests,
    }

    rendered = json.dumps(summary, indent=2, ensure_ascii=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if summary["independent_status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
