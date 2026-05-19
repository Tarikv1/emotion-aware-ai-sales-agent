#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import statistics
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core import live_voice_session_policy as session_policy  # noqa: E402
from runtime.core.dialogue_reasoner import build_reasoning_context, reason_about_turn  # noqa: E402
from runtime.core.dialogue_reasoner_async_enrichment import (  # noqa: E402
    build_async_enrichment_request,
    complete_async_enrichment,
)
from runtime.core.realtime_turns import build_runtime_decision  # noqa: E402
from runtime.providers.dialogue_reasoner_llm_client import OpenAICompatibleReasonerConfig  # noqa: E402
from scripts.run_live_demo_001_agent_voice_call import (  # noqa: E402
    DEFAULT_CASES_PATH,
    build_turn_packet,
    load_campaign,
)

CHECKPOINT_ID = "LIVE-DEMO-002-conversation-stability-callback-disambiguation"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
RUNNER_PATH = ROOT / "scripts" / "run_live_demo_001_agent_voice_call.py"
BENCHMARK_PATH = ROOT / "scripts" / "run_live_demo_002_llm_enrichment_benchmark.py"
CAMPAIGN_ID = "campaign-prod-005-b2b-software"
CAMPAIGN = load_campaign(CAMPAIGN_ID, DEFAULT_CASES_PATH)
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID


def safe_env() -> dict[str, str]:
    env = os.environ.copy()
    for name in [
        "DIALOGUE_REASONER_API_KEY",
        "DIALOGUE_REASONER_BASE_URL",
        "DIALOGUE_REASONER_MODEL",
        "ELEVENLABS_API_KEY",
        "ELEVENLABS_VOICE_ID",
        "ELEVENLABS_VOICE_ID_EN",
        "OPENAI_API_KEY",
        "OPENROUTER_API_KEY",
        "TOGETHER_API_KEY",
        "GROQ_API_KEY",
    ]:
        env.pop(name, None)
    return env


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9$]+", " ", text.lower()).strip()


def assert_condition(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def append_turn(state: dict[str, Any], packet: dict[str, Any]) -> None:
    state.setdefault("turns", []).append(
        {
            "transcript": packet.get("transcript", ""),
            "summary": packet.get("summary", {}),
            "continuity": packet.get("demo_session_continuity", {}),
            "conversation_memory": packet.get("demo_conversation_memory") or packet.get("conversation_memory") or {},
        }
    )


def build_demo_turn(transcript: str, state: dict[str, Any], *, session_id: str) -> dict[str, Any]:
    return build_turn_packet(
        transcript=transcript,
        campaign_id=CAMPAIGN_ID,
        stage="relevance-check",
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


def run_sequence(transcripts: list[str], *, session_id: str) -> list[dict[str, Any]]:
    state: dict[str, Any] = {"turns": []}
    packets: list[dict[str, Any]] = []
    for transcript in transcripts:
        packet = build_demo_turn(transcript, state, session_id=session_id)
        packets.append(packet)
        append_turn(state, packet)
    return packets


def response_reopens_generic_menu(response: str) -> bool:
    lowered = response.lower()
    return any(
        fragment in lowered
        for fragment in [
            "price, fit, timing",
            "price, fit, timing, or exact product details",
            "to make this useful",
            "main concern about price",
        ]
    )


def asks_for_callback_time(response: str) -> bool:
    lowered = response.lower()
    return any(
        fragment in lowered
        for fragment in [
            "what time",
            "when should i",
            "note for the callback",
            "call you back",
            "callback time",
        ]
    )


def explains_workflow_callbacks(response: str) -> bool:
    lowered = response.lower()
    return any(
        fragment in lowered
        for fragment in [
            "callback reminder",
            "follow-up reminder",
            "missed follow-up",
            "inbound demo",
            "without a next step",
            "owner",
            "next step visible",
        ]
    )


def sales_progresses(response: str) -> bool:
    lowered = response.lower()
    return "?" in response and any(
        fragment in lowered
        for fragment in [
            "which gap",
            "which part",
            "where does",
            "where is",
            "would a short",
            "should i keep",
            "frequent enough",
            "worth reviewing",
            "workflow review",
            "next step",
            "check",
        ]
    )


def full_customer_echo_violation(transcript: str, response: str) -> bool:
    customer = normalize(transcript)
    spoken = normalize(response)
    if not customer or not spoken:
        return False
    words = customer.split()
    if len(words) >= 4 and spoken.startswith(" ".join(words[: min(len(words), 7)])):
        return True
    if len(words) >= 5 and customer in spoken:
        return True
    return False


def validate_callback_workflow_gap(failures: list[str], evidence: dict[str, Any]) -> None:
    state = {"turns": []}
    opener = build_demo_turn("__agent_open__", state, session_id="callback-workflow-gap")
    append_turn(state, opener)
    ack = build_demo_turn("okay", state, session_id="callback-workflow-gap")
    append_turn(state, ack)

    cases = [
        "callbacks are the problem",
        "it is probably the callbacks",
        "missed callbacks happen more often than handoffs",
        "what do you mean by callbacks",
        "are callbacks appointments or reminders",
        "callback reminders are where we struggle",
        "demo callbacks keep slipping",
        "our team misses follow-ups",
    ]
    records = []
    for transcript in cases:
        packet = build_demo_turn(transcript, state, session_id=f"callback-workflow-gap-{len(records)}")
        response = packet["summary"]["final_response"]
        semantic = session_policy.callback_semantic_from_transcript(session_policy.normalize_text(transcript), state)
        realtime = build_runtime_decision(
            {
                "case_id": f"callback-workflow-{len(records) + 1}",
                "customer_input": {
                    "transcript": transcript,
                    "stage": "relevance-check",
                    "input_type": "speech-final",
                    "silence_count": 0,
                }
            },
            campaign=CAMPAIGN,
        )
        records.append(
            {
                "transcript": transcript,
                "response": response,
                "semantic": semantic,
                "summary": packet["summary"],
                "continuity": packet["demo_session_continuity"],
                "realtime_sales_difficulty": realtime.get("sales_difficulty"),
            }
        )
        assert_condition(
            failures,
            semantic == "callback_workflow_gap",
            f"Expected callback_workflow_gap semantic for {transcript!r}, got {semantic!r}",
        )
        assert_condition(
            failures,
            realtime.get("sales_difficulty") != "callback-request",
            f"Realtime classifier treated workflow callback as scheduling: {transcript!r} -> {realtime}",
        )
        assert_condition(
            failures,
            packet["summary"].get("sales_difficulty") != "callback-request",
            f"Live demo treated workflow callback as scheduling: {transcript!r} -> {packet['summary']}",
        )
        assert_condition(
            failures,
            not asks_for_callback_time(response),
            f"Workflow callback response asked for scheduling time: {transcript!r} -> {response}",
        )
        assert_condition(
            failures,
            explains_workflow_callbacks(response),
            f"Workflow callback response did not explain/map callback gap: {transcript!r} -> {response}",
        )
        assert_condition(
            failures,
            sales_progresses(response),
            f"Workflow callback response did not steer to a sales-progressing next step: {response}",
        )
    evidence["callback_workflow_gap"] = records


def validate_callback_scheduling(failures: list[str], evidence: dict[str, Any]) -> None:
    state = {"turns": []}
    cases = [
        ("call me back later", "callback_scheduling_request"),
        ("can you call me tomorrow", "callback_scheduling_request"),
        ("not now, call me later", "callback_scheduling_request"),
        ("tomorrow at 3 works", "callback_time_confirmation"),
    ]
    records = []
    for transcript, expected_semantic in cases:
        packet = build_demo_turn(transcript, state, session_id="callback-scheduling-controls")
        response = packet["summary"]["final_response"]
        semantic = session_policy.callback_semantic_from_transcript(session_policy.normalize_text(transcript), state)
        records.append(
            {
                "transcript": transcript,
                "expected_semantic": expected_semantic,
                "semantic": semantic,
                "response": response,
                "summary": packet["summary"],
                "continuity": packet["demo_session_continuity"],
            }
        )
        assert_condition(
            failures,
            semantic == expected_semantic,
            f"Expected {expected_semantic} for scheduling transcript {transcript!r}, got {semantic!r}",
        )
        if expected_semantic == "callback_time_confirmation":
            assert_condition(
                failures,
                packet["summary"].get("call_control") == "schedule-and-end",
                f"Time confirmation should schedule and end: {transcript!r} -> {packet['summary']}",
            )
        else:
            assert_condition(
                failures,
                asks_for_callback_time(response),
                f"Scheduling request should ask for a callback time: {transcript!r} -> {response}",
            )
        assert_condition(
            failures,
            not (explains_workflow_callbacks(response) and expected_semantic != "callback_workflow_gap"),
            f"Scheduling request should not be treated as product workflow explanation: {transcript!r} -> {response}",
        )
        append_turn(state, packet)
    evidence["callback_scheduling_controls"] = records


def validate_repetition_and_echo(failures: list[str], evidence: dict[str, Any]) -> None:
    transcripts = [
        "__agent_open__",
        "hmm okay",
        "I did not understand what you asked",
        "callbacks are the problem",
        "what do you mean by callbacks",
        "tell me more",
        "why does that matter",
        "how much does it cost",
        "I am not sure it fits us",
        "no",
        "what next",
        "send me the short summary",
    ]
    packets = run_sequence(transcripts, session_id="stability-12-turn")
    responses = [packet["summary"]["final_response"] for packet in packets]
    reasons = [packet["demo_session_continuity"].get("reason") for packet in packets]
    memories = [packet.get("demo_conversation_memory") or packet.get("conversation_memory") for packet in packets]
    evidence["stability_12_turn"] = [
        {
            "turn": index + 1,
            "transcript": packet["transcript"],
            "response": packet["summary"]["final_response"],
            "continuity": packet["demo_session_continuity"],
            "memory": packet.get("demo_conversation_memory") or packet.get("conversation_memory"),
            "stability_guard": packet.get("demo_conversation_stability_guard"),
        }
        for index, packet in enumerate(packets)
    ]
    assert_condition(failures, len(responses) == len(set(responses)), f"12-turn scenario replayed a final response: {responses}")
    assert_condition(
        failures,
        not any(response_reopens_generic_menu(response) for response in responses[2:]),
        f"12-turn scenario reopened generic focus menu: {responses}",
    )
    assert_condition(
        failures,
        all("avoid repeating" not in response.lower() and "same question" not in response.lower() for response in responses),
        f"Internal anti-loop language leaked into responses: {responses}",
    )
    assert_condition(
        failures,
        any(memory and memory.get("selected_gap") == "callbacks" for memory in memories),
        f"Conversation memory should retain selected callback gap: {memories}",
    )
    assert_condition(
        failures,
        any(reason and "callback" in str(reason) for reason in reasons),
        f"Callback scenario should use explicit callback route reasons: {reasons}",
    )
    for packet in packets:
        assert_condition(
            failures,
            not full_customer_echo_violation(packet["transcript"], packet["summary"]["final_response"]),
            f"Response echoed customer sentence: {packet['transcript']!r} -> {packet['summary']['final_response']}",
        )


def validate_long_stress(failures: list[str], evidence: dict[str, Any]) -> None:
    transcripts = [
        "__agent_open__",
        "okay",
        "callbacks are the problem",
        "tell me more",
        "why does that matter",
        "what does the product do",
        "what do you mean by callbacks",
        "how much does it cost",
        "what is included in the $59 version",
        "does it replace my CRM",
        "we use a shared inbox",
        "I don't know",
        "no",
        "what next",
        "what about handoffs",
        "can you explain that",
        "is this for small teams",
        "I need to ask my manager",
        "what would the summary say",
        "how short is the review",
        "why not just track it manually",
        "what if Salesforce is involved",
        "does it have SOC 2",
        "okay that is interesting",
        "so what should we check first",
        "call me back later",
        "tomorrow at 3 works",
    ]
    packets = run_sequence(transcripts, session_id="stability-long-turn")
    responses = [packet["summary"]["final_response"] for packet in packets]
    question_types = [
        (packet.get("demo_conversation_memory") or packet.get("conversation_memory") or {}).get("last_agent_question_type")
        for packet in packets
    ]
    evidence["stress_turn_count"] = len(packets)
    evidence["stress_session_turn_indexes"] = [packet.get("session_turn_index") for packet in packets]
    evidence["stress_duplicate_response_count"] = len(responses) - len(set(responses))
    evidence["stress_question_type_counts"] = dict(Counter(item for item in question_types if item))
    assert_condition(failures, len(packets) >= 25, "Stress sample should include at least 25 validation turns.")
    assert_condition(
        failures,
        packets[-1].get("session_turn_index", 0) >= len(transcripts),
        f"Live packet indexing suggests a hard turn cap: {[packet.get('session_turn_index') for packet in packets]}",
    )
    assert_condition(failures, len(responses) == len(set(responses)), f"Stress scenario replayed final response: {responses}")
    repeated_question_types = {
        key: count for key, count in Counter(item for item in question_types if item).items() if count > 8 and key != "none"
    }
    assert_condition(
        failures,
        not repeated_question_types,
        f"Stress scenario repeated question type too often: {repeated_question_types}",
    )


def validate_echo_examples(failures: list[str], evidence: dict[str, Any]) -> None:
    state = {"turns": []}
    examples = [
        "callbacks are the problem",
        "what do you mean by callbacks",
        "I don't know what you're talking about",
        "you called me, you should ask",
    ]
    records = []
    for transcript in examples:
        packet = build_demo_turn(transcript, state, session_id=f"echo-{len(records)}")
        response = packet["summary"]["final_response"]
        records.append({"transcript": transcript, "response": response, "guard": packet.get("demo_conversation_stability_guard")})
        assert_condition(
            failures,
            not full_customer_echo_violation(transcript, response),
            f"Echo example response mirrored customer phrase: {transcript!r} -> {response}",
        )
        assert_condition(
            failures,
            sales_progresses(response),
            f"Echo example did not clarify or progress the sales conversation: {response}",
        )
    evidence["echo_examples"] = records


def validate_casual_conversation(failures: list[str], evidence: dict[str, Any]) -> None:
    state = {"turns": []}
    examples = [
        "who are you again?",
        "why are you calling?",
        "you called me",
        "I don't have a question",
        "I don't know",
    ]
    records = []
    for transcript in examples:
        packet = build_demo_turn(transcript, state, session_id=f"casual-{len(records)}")
        response = packet["summary"]["final_response"]
        records.append({"transcript": transcript, "response": response, "summary": packet["summary"]})
        assert_condition(
            failures,
            any(term in response.lower() for term in ["northstar", "routesignal", "demo", "callback", "handoff", "follow-up", "workflow"]),
            f"Casual/normal gap drifted away from sales purpose: {transcript!r} -> {response}",
        )
        assert_condition(
            failures,
            not response_reopens_generic_menu(response),
            f"Casual/normal gap reopened generic menu: {transcript!r} -> {response}",
        )
        assert_condition(
            failures,
            packet["dialogue_reasoner_async_enrichment"]["provider_call_made"] is False,
            f"Casual validation must not call LLM provider: {packet['dialogue_reasoner_async_enrichment']}",
        )
    evidence["casual_conversation"] = records


def validate_llm_boundary(failures: list[str], evidence: dict[str, Any]) -> None:
    state = {"turns": []}
    packet = build_demo_turn("what does the workflow include", state, session_id="llm-boundary")
    deterministic = reason_about_turn(packet["transcript"], state, CAMPAIGN, mode="baseline")
    request = build_async_enrichment_request(
        transcript=packet["transcript"],
        context=build_reasoning_context(packet["transcript"], state, CAMPAIGN),
        deterministic_reasoning=deterministic,
        case_goal=CHECKPOINT_ID,
        customer_response_text=packet["summary"]["final_response"],
        response_packet_id="llm-boundary:1",
    )
    provider_error = complete_async_enrichment(
        request,
        {
            "provider_calls_made": True,
            "text_sent_to_provider": True,
            "api_key_value_logged": False,
            "latency_ms": 913.2,
            "http_status": None,
            "error": "synthetic timeout",
            "raw_response_stored": False,
        },
        customer_response_text_after_provider=packet["summary"]["final_response"],
    )
    provider_schema_failure = complete_async_enrichment(
        request,
        {
            "provider_calls_made": True,
            "text_sent_to_provider": True,
            "api_key_value_logged": False,
            "latency_ms": 321.4,
            "http_status": 200,
            "content": "{\"dialogue_act\":\"override\",\"final_response\":\"mutate me\"}",
            "raw_response_stored": False,
        },
        customer_response_text_after_provider=packet["summary"]["final_response"],
    )
    evidence["llm_boundary"] = {
        "dry_turn_async_packet": packet["dialogue_reasoner_async_enrichment"],
        "request": request,
        "provider_error": provider_error,
        "provider_schema_failure": provider_schema_failure,
    }
    assert_condition(
        failures,
        packet["dialogue_reasoner_async_enrichment"]["provider_call_made"] is False,
        "Live demo dry validation must not make provider calls.",
    )
    assert_condition(
        failures,
        request["customer_response_snapshot"]["available_before_provider"] is True,
        f"Customer response should exist before provider result: {request}",
    )
    for completed in [provider_error, provider_schema_failure]:
        assert_condition(
            failures,
            completed["provider_result_applied_after_response"] is False,
            f"Provider result must not be applied after response: {completed}",
        )
        assert_condition(
            failures,
            completed["runtime_route_override_allowed"] is False and completed["mutates_final_response"] is False,
            f"Provider result must not override route or mutate response: {completed}",
        )
        assert_condition(
            failures,
            completed["final_response_changed_by_provider"] is False,
            f"Provider result changed final response: {completed}",
        )
        assert_condition(failures, completed.get("latency_ms") is not None, f"Provider latency missing: {completed}")
        assert_condition(
            failures,
            completed["status"] == "ignored" and completed.get("ignored_by_live_turn") is True,
            f"Provider timeout/schema failure should become ignored enrichment: {completed}",
        )
    assert_condition(
        failures,
        OpenAICompatibleReasonerConfig(None, None, None).temperature != 0.0,
        "Default reasoner temperature should not be forced to 0.0.",
    )


def validate_no_hard_turn_cap(failures: list[str], evidence: dict[str, Any]) -> None:
    source = RUNNER_PATH.read_text(encoding="utf-8")
    forbidden = [
        'session_state["turns"] = session_state["turns"][-8:]',
        "session_state['turns'] = session_state['turns'][-8:]",
    ]
    evidence["hard_turn_cap_source_check"] = {"forbidden_fragments_found": [item for item in forbidden if item in source]}
    assert_condition(
        failures,
        not any(item in source for item in forbidden),
        "Live server must not hard-limit runtime session turns to 8.",
    )


def validate_benchmark_scaffold(failures: list[str], evidence: dict[str, Any]) -> None:
    assert_condition(failures, BENCHMARK_PATH.exists(), "Optional LLM enrichment benchmark scaffold is missing.")
    if not BENCHMARK_PATH.exists():
        return
    completed = subprocess.run(
        [sys.executable, str(BENCHMARK_PATH), "--out", str(TMP_DIR / "benchmark.json")],
        cwd=ROOT,
        env=safe_env(),
        text=True,
        capture_output=True,
        check=False,
        timeout=240,
    )
    assert_condition(
        failures,
        completed.returncode == 0,
        f"Benchmark scaffold dry-run failed: stdout={completed.stdout[-1000:]} stderr={completed.stderr[-1000:]}",
    )
    if (TMP_DIR / "benchmark.json").exists():
        payload = json.loads((TMP_DIR / "benchmark.json").read_text(encoding="utf-8"))
        evidence["benchmark_scaffold"] = payload
        for field in [
            "median_latency_ms",
            "p95_latency_ms",
            "schema_failure_rate",
            "callback_semantic_accuracy",
            "repetition_rate",
            "echo_violation_count",
            "route_override_violations",
            "final_response_mutation_violations",
        ]:
            assert_condition(failures, field in payload["metrics"], f"Benchmark metrics missing {field}: {payload}")
        assert_condition(
            failures,
            payload["provider_calls_made"] is False,
            f"Benchmark scaffold must not call provider by default: {payload}",
        )


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        f"# {CHECKPOINT_ID}",
        "",
        f"- Passed: `{str(payload['passed']).lower()}`",
        f"- Failure count: `{payload['failure_count']}`",
        f"- Provider calls made: `{str(payload['provider_calls_made']).lower()}`",
        f"- Stress turn count: `{payload['evidence'].get('stress_turn_count')}`",
        f"- Stress duplicate responses: `{payload['evidence'].get('stress_duplicate_response_count')}`",
        "",
        "## Failures",
        "",
    ]
    if payload["failures"]:
        lines.extend(f"- {failure}" for failure in payload["failures"])
    else:
        lines.append("- None")
    lines.extend(["", "## Boundary", ""])
    lines.extend(
        [
            "- Validation is text-only and provider-off by default.",
            "- Deterministic runtime owns final customer-facing speech.",
            "- LLM enrichment evidence is optional, ignored on timeout/schema failure, and cannot mutate protected route fields or final response.",
            "- Fixed-length 12-turn and 27-turn scenarios are samples only, not runtime caps.",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    failures: list[str] = []
    evidence: dict[str, Any] = {}

    validate_no_hard_turn_cap(failures, evidence)
    validate_callback_workflow_gap(failures, evidence)
    validate_callback_scheduling(failures, evidence)
    validate_repetition_and_echo(failures, evidence)
    validate_long_stress(failures, evidence)
    validate_echo_examples(failures, evidence)
    validate_casual_conversation(failures, evidence)
    validate_llm_boundary(failures, evidence)
    validate_benchmark_scaffold(failures, evidence)

    provider_calls_made = any(
        bool(record.get("provider_call_made"))
        for group in evidence.values()
        if isinstance(group, list)
        for record in group
        if isinstance(record, dict)
    )
    latencies = [
        item.get("latency_ms")
        for item in [
            evidence.get("llm_boundary", {}).get("provider_error", {}),
            evidence.get("llm_boundary", {}).get("provider_schema_failure", {}),
        ]
        if item.get("latency_ms") is not None
    ]
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "passed": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "provider_calls_made": provider_calls_made,
        "provider_latency_ms": {
            "median": statistics.median(latencies) if latencies else None,
            "p95": max(latencies) if latencies else None,
        },
        "evidence": evidence,
    }
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    REPORT_PATH.write_text(render_report(payload), encoding="utf-8")
    if failures:
        raise AssertionError(f"{CHECKPOINT_ID} failed with {len(failures)} issue(s). See {RESULT_PATH}.")
    print(f"{CHECKPOINT_ID} validation passed.")


if __name__ == "__main__":
    main()
