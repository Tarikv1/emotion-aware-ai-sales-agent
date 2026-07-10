#!/usr/bin/env python3
from __future__ import annotations

import json
import importlib.util
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "ELEVENLABS-039-end-call-edge-case-hardening"

PROMPT = ROOT / "runtime/providers/elevenlabs_agents/prompts/web_design_atlas_sales_prompt.md"
CLOSE = ROOT / "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_close_and_followup_playbook.md"
OUTPUT = ROOT / "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_output_quality_rules.md"
OFFER = ROOT / "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_offer_facts.md"
ANALYSIS_CONFIG = ROOT / "runtime/providers/elevenlabs_agents/analysis/atlas_web_studio_analysis_config.json"
ANALYSIS_SETUP = ROOT / "runtime/providers/elevenlabs_agents/analysis/atlas_web_studio_analysis_setup.md"
TESTS = ROOT / "runtime/providers/elevenlabs_agents/tests/web_design_end_call_edge_case_tests.json"
APPLY_038 = ROOT / "scripts/apply_elevenlabs_038_end_call_terminal_control.py"
TRACE_CAPTURE = ROOT / "scripts/capture_elevenlabs_039_test_invocation.py"
TRACE_VALIDATOR = ROOT / "scripts/validate_elevenlabs_039_live_test_traces.py"
INDEPENDENT_HARDENING_APPLY = ROOT / "scripts/apply_elevenlabs_039_independent_test_hardening.py"
INDEPENDENT_TEST_RUNNER = ROOT / "scripts/run_elevenlabs_039_tests.py"
ACTIVE_UPLOAD_MANIFEST = ROOT / "runtime/providers/elevenlabs_agents/manifests/web_design_sales_spine_compression.package.json"
PROCEDURES_DIR = ROOT / "runtime/providers/elevenlabs_agents/procedures"

EXPECTED_TEST_IDS = {
    "sim_039_hard_stop_overrides_pending_email",
    "sim_039_delivery_timing_not_repeated",
    "sim_039_gatekeeper_callback_atomic_end_call",
    "sim_039_gatekeeper_note_atomic_end_call",
}

REVISED_END_CALL_DESCRIPTION = (
    "End the call only when the conversation is genuinely complete. Call this tool once when the buyer explicitly "
    "ends a completed conversation, gives a hard stop or do-not-call request, a completed gatekeeper callback or "
    "note outcome is reached, or a guarantee-only disqualification reaches its terminal conclusion. Before ending, "
    "answer any live direct question or unresolved concern, confirm any pending email destination, and confirm any "
    "agreed callback window. Exception: a hard stop or do-not-call request overrides pending email confirmation, "
    "callback, and every unfinished sales action; end immediately without confirming email or continuing the pitch. "
    "Include by-the-end-of-day delivery timing only when it has not already been stated, or when email confirmation "
    "and goodbye occur in the same buyer turn. Use the tool's message field as the single final spoken line. Do not "
    "speak a separate farewell before invoking the tool. Do not end while email confirmation is pending, the buyer "
    "accepted the mockup but no email is known, or the buyer is still asking about price, process, capability, scope, "
    "or another unresolved concern, except for the hard-stop/do-not-call override. Do not call this tool more than once."
)


def fail(message: str) -> None:
    raise AssertionError(message)


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def read(path: Path) -> str:
    assert_condition(path.is_file(), f"Missing file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(read(path))
    assert_condition(isinstance(payload, dict), f"{path.relative_to(ROOT)} must contain a JSON object")
    return payload


def assert_markers(label: str, text: str, markers: tuple[str, ...]) -> None:
    missing = [marker for marker in markers if marker not in text]
    assert_condition(not missing, f"{label} missing markers: {missing}")


def apply_end_call_description() -> str:
    spec = importlib.util.spec_from_file_location("apply_elevenlabs_038", APPLY_038)
    assert_condition(spec is not None and spec.loader is not None, "could not load apply utility")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return str(getattr(module, "END_CALL_DESCRIPTION", ""))


def git_diff_names(*paths: str) -> list[str]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", "--", *paths],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def word_count(text: str) -> int:
    return len(re.findall(r"\b\S+\b", text))


def validate_repo_policy_text() -> None:
    prompt = read(PROMPT)
    close = read(CLOSE)
    output = read(OUTPUT)
    offer = read(OFFER)
    analysis = json.dumps(read_json(ANALYSIS_CONFIG), ensure_ascii=False) + "\n" + read(ANALYSIS_SETUP)
    apply_script = read(APPLY_038)

    assert_condition(
        apply_end_call_description() == REVISED_END_CALL_DESCRIPTION,
        "revised end_call description missing from apply utility",
    )
    assert_condition('prompt.pop("tools", None)' not in apply_script, "patch utility still deletes prompt.tools")

    assert_markers(
        "prompt 039 end-call edge cases",
        prompt,
        (
            "`end_call` is the only terminal mechanism for completed live calls",
            "Email confirmation alone is not terminal: \"Yes, that's right\" after an email repeat means state timing only and wait; never call `end_call`",
            "Use it exactly once",
            "sole final spoken line in the tool",
            "Do not speak a separate farewell before invoking it",
            "Pending email confirmation blocks `end_call`, except a hard stop or do-not-call request",
            "hard stop or do-not-call request overrides email confirmation, accepted mockup, callback, process, and every unfinished sales action",
            "If the buyer confirms email and says goodbye in the same turn",
            "Buyer confirms email without goodbye -> Delivery timing is \"by the end of the day\". Output exactly: \"Great, I'll send it there by the end of the day.\"",
            "Stop after the period; no question, check-in, farewell, or `end_call`",
            "If by-the-end-of-day timing was already stated earlier, do not repeat it",
            "Same turn means the buyer's latest single utterance contains both confirmation and goodbye",
            "Completed gatekeeper callback and completed gatekeeper-note outcomes use one terminal `end_call`",
            "\"The owner is usually available tomorrow morning\" means callback window known",
            "No separate confirmation or waiting",
            "means note accepted even if Emma did not offer it first",
            "No callback, email, or next-step ask",
            "reason: \"Email confirmed and buyer ended the conversation\"",
            "message: \"Great, I'll send it there by the end of the day. Take care.\"",
            "reason: \"Buyer requested no further contact\"",
            "message: \"Got it. Take care.\"",
            "Do not confirm the pending email",
            "reason: \"Gatekeeper callback window confirmed\"",
            "message: \"Got it, I'll try then. Take care.\"",
            "reason: \"Gatekeeper note completed\"",
            "message: \"Got it, thank you. Take care.\"",
        ),
    )
    assert_condition(
        prompt.index("Delivery timing already stated, then goodbye")
        < prompt.index("Email confirmed plus goodbye in the same turn"),
        "prior-delivery-timing example must precede the competing same-turn example",
    )
    assert_markers(
        "close playbook 039 edge cases",
        close,
        (
            "A hard stop, do-not-call request, or remove-me request outranks pending email confirmation",
            "must not confirm the email, must not send the mockup, and must invoke `end_call` immediately",
            "This is not an email-confirmation failure",
            "If delivery timing has not yet been stated and email confirmation plus goodbye appear in the same turn",
            "If the buyer confirms the email without saying goodbye, state the delivery timing without a farewell and wait for the buyer",
            "If delivery timing was already stated in an earlier turn, do not repeat it",
            "The final tool message should then be only \"Take care.\"",
            "Callback window known",
            "confirm the window inside the single final tool message",
            "Note accepted",
            "thank the gatekeeper briefly inside the single final tool message",
            "Do not speak a separate confirmation and then call the tool",
        ),
    )
    assert_markers(
        "output rules 039 edge cases",
        output,
        (
            "Hard stop overrides email-confirmation flow",
            "Email confirmation without a goodbye is not terminal",
            "Do not repeat delivery timing in the final farewell if already stated",
            "Gatekeeper callback/note close must be one atomic tool message",
            "Do not leak `end_call`, tool names, arguments, reasons, or internal terminal state to the buyer",
            "Do not speak a callback confirmation separately before terminal tool invocation",
            "Do not speak a farewell separately before terminal tool invocation",
            "Do not repeat \"Take care.\"",
            "Do not add policy wording to the final tool message",
        ),
    )
    assert_markers(
        "offer facts confirmation-only close",
        offer,
        (
            "After email confirmation without goodbye, say only",
            "Do not add a farewell or invoke `end_call` until the buyer explicitly ends the conversation",
        ),
    )
    stale_confirmation_farewell = "Great, I'll send it there by the end of the day. Have a good one."
    assert_condition(stale_confirmation_farewell not in close, "close playbook still approves a confirmation-only farewell")
    assert_condition(stale_confirmation_farewell not in offer, "offer facts still approve a confirmation-only farewell")
    stale_callback_close = "Got it, I'll call back then. Thanks."
    assert_condition(stale_callback_close not in output, "output rules still approve a standalone callback close")
    assert_markers(
        "analysis 039 edge cases",
        analysis,
        (
            "pending email is abandoned without confirmation",
            "no mockup send language, discovery, objection handling, or callback follows",
            "If the buyer gives an email and then gives a hard stop/do-not-call request",
            "Immediate terminal `end_call` is correct and must not be graded as skipped email confirmation",
            "if already stated, it is not required again in the terminal message",
            "confirmation and goodbye occur in the same turn, it appears in the atomic final message",
            "confirmation without goodbye gets delivery timing without `end_call` or a farewell",
            "timing is mechanically repeated in a later farewell",
            "callback window or note is confirmed briefly",
            "one terminal `end_call` follows through the same atomic final message",
            "call remains open after callback/note completion",
        ),
    )


def validate_apply_utility() -> None:
    script = read(APPLY_038)
    assert_markers(
        "patch utility unrelated-tool preservation",
        script,
        (
            "def unrelated_tool_fingerprint(",
            "non_end_call_legacy_tools",
            "built_in_tools_excluding_end_call",
            "tool_ids",
            "mcp_server_ids",
            "native_mcp_server_ids",
            "def normalize_end_call_tools(",
            '"atlas_offer_facts.md"',
            "prompt.tools is not a list",
            "assert_unrelated_tool_fingerprint_unchanged",
            "unrelated_tool_fingerprint_before.json",
            "unrelated_tool_fingerprint_after.json",
        ),
    )


def validate_trace_utilities() -> None:
    capture = read(TRACE_CAPTURE)
    validator = read(TRACE_VALIDATOR)
    assert_markers(
        "039 trace capture",
        capture,
        (
            "/v1/convai/test-invocations/",
            "EXPECTED_AGENT_ID",
            "provider_test_id",
            "payload_sha256",
            "SENSITIVE_KEY_RE",
            "sanitize_agent_response",
            "ELEVENLABS_API_KEY",
        ),
    )
    assert_markers(
        "039 independent trace validator",
        validator,
        (
            "independent_status",
            "provider_labels",
            'params.get("reason")',
            "exact_system_message_to_speak",
            "successful_end_call_result_payload",
            "no_additional_tool_result",
            "direct_preceding_rendered_tool_message",
            "exact_post_confirmation_timing_without_tool",
            "timing_appears_once_post_confirmation",
            "no_text_or_tool_after_result",
        ),
    )


def validate_independent_live_utilities() -> None:
    apply_script = read(INDEPENDENT_HARDENING_APPLY)
    runner = read(INDEPENDENT_TEST_RUNNER)
    assert_markers(
        "039 independent live hardening apply utility",
        apply_script,
        (
            "confirm-provider-write",
            "confirm-dashboard-test-update",
            "--test-only",
            "source_ids = (test_only,)",
            "protected_agent_state",
            "unrelated_tool_fingerprint",
            "test_semantics",
            "folder_parent_id",
            "multipart_update_file",
            '"PUT"',
            "plan_only_missing_exact_confirmations",
            "simulations_run",
            "outbound_calls_made",
        ),
    )
    assert_markers(
        "039 independent test runner",
        runner,
        (
            "confirm-simulations",
            "live test semantic mismatch",
            "/run-tests",
            '"repeat_count": 1',
            "wait_timeout_seconds",
            "final_run_statuses",
            "completed",
        ),
    )


def validate_tests() -> int:
    payload = read_json(TESTS)
    assert_condition(payload.get("package_id") == CHECKPOINT_ID, "039 package_id mismatch")
    assert_condition(payload.get("test_type") == "simulation", "039 tests must be simulation tests")
    tests = payload.get("tests")
    assert_condition(isinstance(tests, list) and len(tests) == 4, "039 tests must contain exactly four simulations")
    ids = {str(test.get("test_id")) for test in tests if isinstance(test, dict)}
    assert_condition(ids == EXPECTED_TEST_IDS, f"039 test IDs mismatch: {sorted(ids)}")
    serialized = json.dumps(payload, ensure_ascii=False)
    assert_markers(
        "039 test semantics",
        serialized,
        (
            "use send or mockup-delivery language",
            "reason 'Buyer requested no further contact'",
            "system__message_to_speak exactly 'Got it. Take care.'",
            "reason 'Buyer explicitly ended the completed conversation'",
            "system__message_to_speak exactly 'Take care.'",
            "The seeded history must contain end-of-day delivery timing exactly once before the goodbye",
            "Great, I'll send it there by the end of the day.",
            "Delivery timing must not be repeated in the terminal message or any later turn",
            "Got it, I'll try then. Take care.",
            "reason 'Gatekeeper callback window confirmed'",
            "Got it, thank you. Take care.",
            "reason 'Gatekeeper note completed'",
            "must not renew the pitch",
            "ask for email",
            "ask for a callback window after the note is accepted",
            "No agent-authored text or tool event after the successful end_call result",
        ),
    )
    for test in tests:
        assert_condition(test.get("simulated_user_model") == "gemini-2.5-flash", f"{test.get('test_id')} simulated_user_model mismatch")
        assert_condition(test.get("evaluation_model") == "gemini-2.5-flash", f"{test.get('test_id')} evaluation_model mismatch")
        assert_condition(isinstance(test.get("simulation_max_turns"), int), f"{test.get('test_id')} missing max turns")
        assert_condition(6 <= int(test["simulation_max_turns"]) <= 10, f"{test.get('test_id')} max turns outside 6-10")

    required_history_tails = {
        "sim_039_hard_stop_overrides_pending_email": "remove me and don't call again",
        "sim_039_delivery_timing_not_repeated": "okay, thanks, bye",
        "sim_039_gatekeeper_callback_atomic_end_call": "owner is usually available tomorrow morning",
        "sim_039_gatekeeper_note_atomic_end_call": "i'll let the owner know emma from atlas called about the mockup",
    }
    tests_by_id = {str(test.get("test_id")): test for test in tests}
    for test_id, required_tail in required_history_tails.items():
        chat_history = tests_by_id[test_id].get("chat_history")
        assert_condition(isinstance(chat_history, list) and chat_history, f"{test_id} must seed its critical buyer turn in chat history")
        assert_condition(str(chat_history[-1].get("role")) == "user", f"{test_id} chat history must end with the critical buyer turn")
        assert_condition(required_tail in str(chat_history[-1].get("message", "")).lower(), f"{test_id} critical buyer turn mismatch")

    delivery_test = next(test for test in tests if test.get("test_id") == "sim_039_delivery_timing_not_repeated")
    chat_history = delivery_test.get("chat_history")
    assert_condition(isinstance(chat_history, list) and len(chat_history) >= 4, "delivery timing test must seed confirmation, timing, and goodbye history")
    history_messages = [str(item.get("message", "")) for item in chat_history if isinstance(item, dict)]
    history_roles = [str(item.get("role", "")) for item in chat_history if isinstance(item, dict)]
    assert_condition(
        any(role == "user" and "that's right" in message.lower() for role, message in zip(history_roles, history_messages)),
        "delivery timing history must establish explicit email confirmation",
    )
    timing_messages = [message for role, message in zip(history_roles, history_messages) if role == "agent" and "by the end of the day" in message.lower()]
    assert_condition(timing_messages == ["Great, I'll send it there by the end of the day."], "delivery timing history must seed the exact timing statement once")
    assert_condition(str(chat_history[-1].get("role")) == "user", "delivery timing history must end with the buyer goodbye")
    assert_condition(history_messages[-1] == "Okay, thanks, bye.", "delivery timing history must end with the exact buyer goodbye")
    delivery_scenario = str(delivery_test.get("simulation_scenario", "")).lower()
    assert_condition("already contains" in delivery_scenario and "delivery" in delivery_scenario, "delivery timing scenario must declare the already-stated timing state")
    assert_condition("do not add another buyer" in delivery_scenario, "delivery timing scenario must not add a post-goodbye buyer turn")
    assert_condition("allow emma one final turn" in delivery_scenario, "delivery timing scenario must allow terminal tool execution")
    delivery_success = str(delivery_test.get("success_condition", ""))
    assert_condition(
        "seeded history must contain end-of-day delivery timing exactly once before the goodbye"
        in delivery_success,
        "delivery timing evaluator must verify the seeded timing state",
    )
    assert_condition(
        "reason 'Buyer explicitly ended the completed conversation'" in delivery_success,
        "delivery timing evaluator must require the exact terminal reason",
    )
    assert_condition("system__message_to_speak exactly 'Take care.'" in delivery_success, "delivery timing evaluator must inspect the tool-bound message")
    assert_condition("do not count that same line as a separate farewell" in delivery_success, "delivery timing evaluator must understand ElevenLabs tool-message rendering")

    hard_stop_success = str(tests_by_id["sim_039_hard_stop_overrides_pending_email"].get("success_condition", ""))
    assert_condition("reason 'Buyer requested no further contact'" in hard_stop_success, "hard-stop evaluator must require the exact reason")
    assert_condition("system__message_to_speak exactly 'Got it. Take care.'" in hard_stop_success, "hard-stop evaluator must inspect tool speech")

    callback_success = str(tests_by_id["sim_039_gatekeeper_callback_atomic_end_call"].get("success_condition", ""))
    assert_condition("reason 'Gatekeeper callback window confirmed'" in callback_success, "callback evaluator must require the exact reason")
    assert_condition("system__message_to_speak exactly 'Got it, I'll try then. Take care.'" in callback_success, "callback evaluator must inspect tool speech")

    note_success = str(tests_by_id["sim_039_gatekeeper_note_atomic_end_call"].get("success_condition", ""))
    assert_condition("reason 'Gatekeeper note completed'" in note_success, "gatekeeper-note evaluator must require the exact reason")
    assert_condition("system__message_to_speak exactly 'Got it, thank you. Take care.'" in note_success, "gatekeeper-note evaluator must inspect tool speech")

    for test_id, test in tests_by_id.items():
        success = str(test.get("success_condition", ""))
        assert_condition(
            "No agent-authored text or tool event after the successful end_call result" in success,
            f"{test_id} must reject post-terminal events",
        )

    boundaries = str(payload.get("evaluation_notes", {}).get("boundaries", ""))
    assert_condition("explicit user opt-in" in boundaries, "039 dashboard execution must remain explicit opt-in")
    assert_condition("Do not run outbound calls" in boundaries, "039 tests must continue to prohibit outbound calls")
    return len(tests)


def validate_analysis_count() -> int:
    criteria = read_json(ANALYSIS_CONFIG).get("success_evaluation_criteria")
    assert_condition(isinstance(criteria, list), "analysis criteria missing")
    assert_condition(len(criteria) <= 30, "ElevenLabs Analysis criteria cap exceeded")
    return len(criteria)


def validate_manifest_boundaries() -> None:
    manifest = read_json(ACTIVE_UPLOAD_MANIFEST)
    recommended = manifest.get("active_kb_recommendation", {}).get("recommended_upload_docs", [])
    assert_condition(isinstance(recommended, list) and len(recommended) == 17, "active KB upload set must remain 17 docs")
    forbidden_fragments = (
        "runtime/providers/elevenlabs_agents/tests",
        "runtime/providers/elevenlabs_agents/analysis",
        "research/experiments/generated",
        "atlas_web_studio_web_design_campaign.md",
        "atlas_web_studio_web_design_campaign_overlay.md",
        "atlas_web_studio_web_design_campaign_profile.md",
    )
    for item in recommended:
        item_text = str(item)
        for forbidden in forbidden_fragments:
            assert_condition(forbidden not in item_text, f"forbidden KB upload item present: {item_text}")
    assert_condition(not git_diff_names(str(ACTIVE_UPLOAD_MANIFEST.relative_to(ROOT))), "active KB upload manifest was modified")
    if PROCEDURES_DIR.exists():
        procedure_diff = git_diff_names(str(PROCEDURES_DIR.relative_to(ROOT)))
        assert_condition(not procedure_diff, f"Procedures changed: {procedure_diff}")


def main() -> None:
    validate_repo_policy_text()
    validate_apply_utility()
    validate_trace_utilities()
    validate_independent_live_utilities()
    test_count = validate_tests()
    criteria_count = validate_analysis_count()
    validate_manifest_boundaries()

    diff_check = subprocess.run(["git", "diff", "--check"], cwd=ROOT, text=True, capture_output=True, check=False)
    assert_condition(diff_check.returncode == 0, diff_check.stderr or diff_check.stdout)

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": CHECKPOINT_ID,
                "prompt_word_count": word_count(read(PROMPT)),
                "analysis_criteria_count": criteria_count,
                "test_count": test_count,
                "active_upload_manifest_changed": False,
                "procedures_changed": False,
                "dashboard_test_execution_not_performed_by_validator": True,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
